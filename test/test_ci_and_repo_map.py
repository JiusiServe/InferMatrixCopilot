"""P2 remainder: CI log adapters + normalized signatures + repo_map tool
(design §V2.1(c), §V2.0.2, §V2.2.4)."""

import asyncio
import json

from omni_copilot.ci.normalize import normalize_signature
from omni_copilot.ci.providers import (BuildkiteLogs, GithubActionsLogs,
                                       provider_for)
from omni_copilot.engine.builtin_steps import register_builtin_steps
from omni_copilot.engine.registry import StepRegistry
from omni_copilot.engine.step import StepContext
from omni_copilot.profiles.repo_map import RepoMap, build_index


# -- signature normalization ------------------------------------------------------

def test_normalize_strips_run_noise_keeps_signal():
    a = ("E ImportError at 2026-07-10T02:14:33Z in /tmp/pytest-1234/run/x.py:412 "
         "(commit 93f2ab7de) after 12.3s at 0x7f2b9c")
    b = ("E ImportError at 2026-07-09T23:01:07Z in /tmp/pytest-9876/other/x.py:498 "
         "(commit 04c1d2e88) after 3.1s at 0x55aa11")
    assert normalize_signature(a) == normalize_signature(b)
    # small literal numbers are signal, not noise
    assert normalize_signature("assert 1 == 2") != normalize_signature("assert 1 == 3")


def test_group_failures_uses_normalized_signatures(settings, trace, tmp_path):
    registry = register_builtin_steps(StepRegistry())
    failures = [
        {"name": "t1", "log": "E   Timeout after 12.5s in /tmp/run-111/x.log"},
        {"name": "t2", "log": "E   Timeout after 3.2s in /tmp/run-999/y.log"},
    ]
    state = {"ci_failures": failures, "task_spec": {"pr": 7}}
    ctx = StepContext(settings=settings, state=state, params={},
                      run_dir=tmp_path / "run", trace=trace)
    result = asyncio.run(registry.get("pr.group_failures").handler(ctx))
    assert result.ok
    assert len(state["failure_groups"]) == 1  # same root cause, one group


# -- providers ---------------------------------------------------------------------

def test_buildkite_provider_enriches_from_link():
    api = "https://api.buildkite.com/v2/organizations/vllm/pipelines/omni-ci/builds/2520"
    responses = {
        api: {"jobs": [
            {"id": "j1", "name": "gpu-test", "state": "failed"},
            {"id": "j2", "name": "docs", "state": "passed"},
        ]},
        f"{api}/jobs/j1/log": {"content": "E   ImportError: cannot import X"},
    }
    provider = BuildkiteLogs("tok", http_get=lambda url: responses[url])
    failures = [
        {"name": "gpu-test", "log": "",
         "link": "https://buildkite.com/vllm/omni-ci/builds/2520#j1"},
        {"name": "no-link", "log": "", "link": ""},
    ]
    assert provider.enrich(failures) == 1
    assert "ImportError" in failures[0]["log"]
    assert failures[1]["log"] == ""


def test_buildkite_provider_error_degrades_per_check():
    def boom(url):
        raise OSError("api down")
    provider = BuildkiteLogs("tok", http_get=boom)
    failures = [{"name": "t", "log": "",
                 "link": "https://buildkite.com/o/p/builds/1"}]
    assert provider.enrich(failures) == 0
    assert failures[0]["log"] == ""


def test_github_actions_provider_caches_per_run():
    calls = []

    def gh(args, cwd=None):
        calls.append(args)
        return 0, "FAIL log line"

    provider = GithubActionsLogs(gh)
    failures = [
        {"name": "a", "log": "",
         "link": "https://github.com/o/r/actions/runs/42/job/1"},
        {"name": "b", "log": "",
         "link": "https://github.com/o/r/actions/runs/42/job/2"},
    ]
    assert provider.enrich(failures) == 2
    assert len(calls) == 1                       # one fetch per run id
    assert calls[0][:3] == ["run", "view", "42"]


def test_provider_selection_and_gaps(settings):
    class FakePlugin:
        def __init__(self, provider):
            self.manifest = {"ci": {"provider": provider}}

    provider, gap = provider_for(None, settings)
    assert provider is None and "no ci.provider" in gap
    provider, gap = provider_for(FakePlugin("buildkite"), settings)
    assert provider is None and "BUILDKITE_API_TOKEN" in gap
    settings.buildkite_api_token = "tok"
    provider, gap = provider_for(FakePlugin("buildkite"), settings)
    assert isinstance(provider, BuildkiteLogs) and gap == ""
    provider, gap = provider_for(FakePlugin("github_actions"), settings,
                                 gh_runner=lambda a, cwd=None: (0, ""))
    assert isinstance(provider, GithubActionsLogs)
    provider, gap = provider_for(FakePlugin("jenkins"), settings)
    assert provider is None and "unknown ci.provider" in gap


def test_fetch_ci_records_capability_gap(settings, trace, tmp_path, git_repo,
                                         monkeypatch):
    """Live fetch path with no provider: gap recorded, run continues."""
    from omni_copilot.engine import pr_steps

    monkeypatch.setattr(pr_steps, "_gh", lambda args, cwd=None: (0, json.dumps([
        {"name": "gpu-test", "state": "FAILURE", "bucket": "fail",
         "link": "https://buildkite.com/o/p/builds/1"}])))
    registry = register_builtin_steps(StepRegistry())
    state = {"task_spec": {"pr": 7}, "repo_path": str(git_repo)}
    ctx = StepContext(settings=settings, state=state, params={},
                      run_dir=tmp_path / "run", trace=trace)
    result = asyncio.run(registry.get("pr.fetch_ci_failures").handler(ctx))
    assert result.ok
    gaps = list(trace.events("capability_gap"))
    assert gaps and gaps[0]["capability"] == "ci.provider"


# -- repo_map ---------------------------------------------------------------------

def test_build_index_and_ranked_render(tmp_path):
    pkg = tmp_path / "scheduler"
    pkg.mkdir()
    (pkg / "core.py").write_text(
        "class Scheduler:\n    pass\n\ndef schedule_batch(reqs):\n    pass\n")
    (tmp_path / "unrelated.py").write_text("def helper():\n    pass\n")
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "junk.py").write_text("def hidden(): pass\n")

    index = build_index(tmp_path, "python")
    assert "scheduler/core.py" in index and ".venv/junk.py" not in index

    rmap = RepoMap(tmp_path, "python", cache_dir=tmp_path / ".cache")
    rendered = rmap.render("how does the scheduler batch requests")
    assert "scheduler/core.py" in rendered
    assert "def schedule_batch" in rendered
    assert "unrelated.py" not in rendered        # zero-score tail is dropped

    # cache written and reused
    assert list((tmp_path / ".cache").glob("index-*.json"))
    assert RepoMap(tmp_path, "python",
                   cache_dir=tmp_path / ".cache").render("scheduler")


def test_repo_map_unsupported_language(tmp_path):
    rmap = RepoMap(tmp_path, "cobol")
    assert not rmap.supported
    assert "unsupported" in rmap.render("anything")


def test_repo_map_tool_reaches_agent(settings, trace, tmp_path, git_repo):
    """The repo_map tool is offered to governed agent steps and works."""
    from omni_copilot.engine.agent_runtime import run_agent_step
    from omni_copilot.llm import Block, Reply

    class ToolThenDone:
        available = True

        def __init__(self):
            self.calls = []

        def create(self, *, system, messages, tools=None, model=None,
                   max_tokens=None, on_text=None):
            self.calls.append({"messages": [*messages], "tools": tools})
            if len(self.calls) == 1:
                return Reply(blocks=[Block(type="tool_use", id="t1",
                                           name="repo_map",
                                           input={"query": "mod_a"})])
            return Reply(blocks=[Block(type="text", text=json.dumps({
                "status": "success", "summary": "ok", "findings": [],
                "files_read": [], "files_modified": [], "tests_requested": [],
                "tests_run": [], "assumptions": [], "blockers": [],
                "confidence": "high", "failure_kind": None, "next_action": ""}))])

    (git_repo / "mod_a.py").write_text("def alpha():\n    return 1\n")
    llm = ToolThenDone()
    ctx = StepContext(settings=settings, params={}, run_dir=tmp_path / "run",
                      trace=trace, llm=llm,
                      state={"task_spec": {"repo": "r"},
                             "repo_path": str(git_repo)})
    result, _ = asyncio.run(run_agent_step(
        ctx, step_name="t", purpose="p", evidence={"e": "x"}))
    assert result.ok
    assert any(t["name"] == "repo_map" for t in llm.calls[0]["tools"])
    # the tool result (second round's user message) carries the map
    tool_result = llm.calls[1]["messages"][-1]["content"][0]["content"]
    assert "mod_a.py" in tool_result
