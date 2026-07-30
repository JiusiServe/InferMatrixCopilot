import asyncio
import json
import subprocess
from pathlib import Path

import pytest

from infermatrix_copilot.engine.steps import register_builtin_steps
from infermatrix_copilot.engine.steps.pr import extract_signature
from infermatrix_copilot.engine.registry import StepRegistry
from infermatrix_copilot.engine.step import FailureKind, StepContext
from infermatrix_copilot.push import PushPolicy


def _git(repo: Path, *args: str) -> str:
    out = subprocess.run(["git", *args], cwd=repo, check=True,
                         capture_output=True, text=True)
    return out.stdout.strip()


@pytest.fixture()
def pr_repos(tmp_path):
    """origin repo with main + a 'feature' PR branch, and a working clone."""
    origin = tmp_path / "origin"
    origin.mkdir()
    _git(origin, "init", "-q", "-b", "main")
    _git(origin, "config", "user.email", "t@e.c")
    _git(origin, "config", "user.name", "t")
    (origin / "core.py").write_text("x = 1\n")
    (origin / "docs.md").write_text("# docs\n")
    _git(origin, "add", ".")
    _git(origin, "commit", "-q", "-m", "base")
    _git(origin, "checkout", "-q", "-b", "feature")
    (origin / "feature.py").write_text("f = 1\n")
    _git(origin, "add", ".")
    _git(origin, "commit", "-q", "-m", "pr change")
    _git(origin, "checkout", "-q", "main")

    work = tmp_path / "work"
    subprocess.run(["git", "clone", "-q", str(origin), str(work)], check=True,
                   capture_output=True)
    _git(work, "config", "user.email", "t@e.c")
    _git(work, "config", "user.name", "t")
    return origin, work


def _ctx(settings, trace, tmp_path, state, params=None, llm=None):
    return StepContext(settings=settings, state=state, params=params or {},
                       run_dir=tmp_path / "rundir", trace=trace, llm=llm)


@pytest.fixture()
def registry():
    return register_builtin_steps(StepRegistry())


def test_checkout_sets_branch_and_push_policy(registry, settings, trace, tmp_path, pr_repos):
    _, work = pr_repos
    state = {"repo_path": str(work), "task_spec": {"pr": 7},
             "pr_meta": {"headRefName": "feature", "baseRefName": "main",
                         "remote": "origin"}}
    step = registry.get("pr.checkout_branch")
    result = asyncio.run(step.handler(_ctx(settings, trace, tmp_path, state,
                                           params={"force_push": True})))
    assert result.ok, result.summary
    assert _git(work, "branch", "--show-current") == "pr-7-feature"
    policy = state["push_policy"]
    assert isinstance(policy, PushPolicy)
    assert policy.allowed and policy.branch == "feature" and policy.force_with_lease


def test_checkout_report_only_disallows_push(registry, settings, trace, tmp_path, pr_repos):
    _, work = pr_repos
    state = {"repo_path": str(work), "task_spec": {"pr": 7, "report_only": True},
             "pr_meta": {"headRefName": "feature", "remote": "origin"}}
    step = registry.get("pr.checkout_branch")
    assert asyncio.run(step.handler(_ctx(settings, trace, tmp_path, state))).ok
    assert state["push_policy"].allowed is False


def test_clean_rebase_and_analyze(registry, settings, trace, tmp_path, pr_repos):
    origin, work = pr_repos
    # advance origin main with a NON-conflicting commit
    (origin / "other.py").write_text("o = 1\n")
    _git(origin, "add", ".")
    _git(origin, "commit", "-q", "-m", "main moves on")

    state = {"repo_path": str(work), "task_spec": {"pr": 7},
             "pr_meta": {"headRefName": "feature", "remote": "origin"}}
    for name in ("pr.checkout_branch", "pr.rebase_onto_base", "pr.analyze_diff"):
        result = asyncio.run(registry.get(name).handler(
            _ctx(settings, trace, tmp_path, state)))
        assert result.ok, f"{name}: {result.summary}"
    # rebased on top of new main: both files reachable
    assert (work / "other.py").exists() and (work / "feature.py").exists()
    analyze = state["affected_modules"]
    assert analyze == ["root"]  # feature.py at top level, no adapter in sandbox
    assert state["primary_files"] == ["*feature.py"]


def test_conflict_without_llm_aborts_and_escalates(registry, settings, trace,
                                                   tmp_path, pr_repos):
    origin, work = pr_repos
    # conflicting change on main touching the same line as a new feature commit
    (origin / "core.py").write_text("x = 2\n")
    _git(origin, "add", ".")
    _git(origin, "commit", "-q", "-m", "main edits core")
    _git(origin, "checkout", "-q", "feature")
    (origin / "core.py").write_text("x = 3\n")
    _git(origin, "add", ".")
    _git(origin, "commit", "-q", "-m", "feature edits core")
    _git(origin, "checkout", "-q", "main")

    state = {"repo_path": str(work), "task_spec": {"pr": 7},
             "pr_meta": {"headRefName": "feature", "remote": "origin"}}
    assert asyncio.run(registry.get("pr.checkout_branch").handler(
        _ctx(settings, trace, tmp_path, state))).ok
    result = asyncio.run(registry.get("pr.rebase_onto_base").handler(
        _ctx(settings, trace, tmp_path, state)))
    assert not result.ok and result.failure is FailureKind.ESCALATE
    assert "core.py" in result.outputs["conflicts"]
    # rebase aborted -> workspace clean, no rebase in progress
    assert _git(work, "status", "--porcelain") == ""
    assert not (work / ".git" / "rebase-merge").exists()
    assert list(trace.events("rebase_conflict"))


def test_extract_signature_prefers_root_cause_over_symptom():
    log = (
        "collecting...\n"
        "E   ImportError: cannot import name 'SchedulerOutput'\n"
        "... later the engine dies ...\n"
        "APIConnectionError: Connection refused\n"
    )
    assert "ImportError" in extract_signature(log)
    assert extract_signature("") == "unknown failure"


def test_group_failures_and_cap(registry, settings, trace, tmp_path):
    failures = [
        {"name": "gpu-test-1", "log": "E   ImportError: cannot import name 'X'"},
        {"name": "gpu-test-2", "log": "blah\nE   ImportError: cannot import name 'X'"},
        {"name": "cpu-test", "log": "AssertionError: bad output"},
    ]
    state = {"ci_failures": failures, "task_spec": {"pr": 7}}
    result = asyncio.run(registry.get("pr.group_failures").handler(
        _ctx(settings, trace, tmp_path, state)))
    assert result.ok
    groups = state["failure_groups"]
    assert len(groups) == 2
    assert sorted(len(g["jobs"]) for g in groups) == [1, 2]

    settings.pr_debug_max_groups = 1
    result = asyncio.run(registry.get("pr.group_failures").handler(
        _ctx(settings, trace, tmp_path, dict(state))))
    assert not result.ok and result.failure is FailureKind.ESCALATE
    assert "safety cap" in result.summary


def test_debug_group_blocked_without_llm(registry, settings, trace, tmp_path):
    state = {"repo_path": "/tmp", "task_spec": {"pr": 7}}
    ctx = _ctx(settings, trace, tmp_path, state)
    ctx.item = {"signature": "E ImportError", "jobs": ["j1"]}
    result = asyncio.run(registry.get("agent.debug_group").handler(ctx))
    assert not result.ok and result.failure is FailureKind.BLOCKED


def test_post_review_gating(registry, settings, trace, tmp_path):
    step = registry.get("pr.post_review")
    # post flag not set -> no-op
    state = {
        "review_text": "looks fine\n\n**Verdict:** COMMENT",
        "review_summary": "looks fine\n\n**Verdict:** COMMENT",
        "review_comments": [],
        "task_spec": {"pr": 7, "post": False},
        "pr_state": "OPEN",
    }
    result = asyncio.run(step.handler(_ctx(settings, trace, tmp_path, state)))
    assert result.ok and "not posting" in result.summary
    # post flag set but ALLOW_POST=0 -> dry-run
    state["task_spec"]["post"] = True
    result = asyncio.run(step.handler(_ctx(settings, trace, tmp_path, state)))
    assert result.ok and result.outputs.get("dry_run") is True
    assert result.outputs["payload"]["event"] == "COMMENT"


_REVIEW_DIFF = """\
diff --git a/a.py b/a.py
index 1111111..2222222 100644
--- a/a.py
+++ b/a.py
@@ -9,3 +9,4 @@
 context
-old
+new
 tail
+added
"""


def _finding(path, line, severity="major", text="fix this"):
    return {
        "file": path,
        "line": line,
        "severity": severity,
        "comment": text,
        "evidence": "verified against the hunk",
    }


def test_review_payload_validates_diff_lines_and_preserves_fallbacks():
    from infermatrix_copilot.engine.steps.pr.publish import _review_payload

    state = {
        "diff_text": _REVIEW_DIFF,
        "review_comments": [
            _finding("a.py", 10),
            _finding("a.py", 99, "minor", "stale line"),
            _finding("missing.py", 1, "minor", "wrong path"),
        ],
        "review_summary": "summary\n\n**Verdict:** REQUEST CHANGES",
        "review_text": "full\n\n**Verdict:** REQUEST CHANGES",
        "pr_state": "OPEN",
        "pr_head_sha": "a" * 40,
    }
    payload, downgraded = _review_payload(state)

    assert payload["event"] == "REQUEST_CHANGES"
    assert payload["commit_id"] == "a" * 40
    assert payload["comments"] == [{
        "path": "a.py",
        "line": 10,
        "side": "RIGHT",
        "body": "**[major]** fix this\n\nEvidence: verified against the hunk",
    }]
    assert downgraded == 2
    assert "a.py:99" in payload["body"]
    assert "missing.py:1" in payload["body"]


def test_review_payload_downgrades_all_comments_when_head_changed():
    from infermatrix_copilot.engine.steps.pr.publish import _review_payload

    state = {
        "diff_text": _REVIEW_DIFF,
        "review_comments": [_finding("a.py", 10)],
        "review_summary": "summary\n\n**Verdict:** REQUEST CHANGES",
        "pr_state": "OPEN",
        "pr_head_sha": "a" * 40,
    }
    payload, downgraded = _review_payload(state, current_head="b" * 40)

    assert payload["comments"] == []
    assert payload["commit_id"] == "b" * 40
    assert downgraded == 1
    assert "PR head changed after review" in payload["body"]


@pytest.mark.parametrize(
    ("comments", "pr_state", "review_text", "event"),
    [
        ([_finding("a.py", 10, "major")], "OPEN", "", "REQUEST_CHANGES"),
        ([_finding("a.py", 10, "minor")], "OPEN", "", "COMMENT"),
        ([], "OPEN", "**Verdict:** APPROVE", "APPROVE"),
        ([_finding("a.py", 10, "major")], "MERGED", "", "COMMENT"),
    ],
)
def test_review_event_mapping(comments, pr_state, review_text, event):
    from infermatrix_copilot.engine.steps.pr.publish import _event_for_review

    assert _event_for_review(comments, pr_state, review_text) == event


def test_post_review_submits_one_review_with_inline_comments(
        registry, settings, trace, tmp_path, monkeypatch):
    from infermatrix_copilot.engine.steps.pr import publish

    settings.allow_post = True
    state = {
        "repo_path": str(tmp_path),
        "task_spec": {"pr": 7, "post": True},
        "diff_text": _REVIEW_DIFF,
        "review_comments": [
            _finding("a.py", 10),
            _finding("a.py", 99, "minor", "stale line"),
        ],
        "review_summary": "summary\n\n**Verdict:** REQUEST CHANGES",
        "review_text": "full\n\n**Verdict:** REQUEST CHANGES",
        "pr_state": "OPEN",
        "pr_head_sha": "b" * 40,
    }
    captured = {}
    monkeypatch.setattr(
        publish, "_repo_full_name", lambda ctx, repo: "owner/repo")

    def fake_gh(args, cwd=None):
        if args[:2] == ["pr", "view"]:
            return 0, json.dumps({"commits": [{"oid": "b" * 40}]})
        captured["args"] = args
        captured["cwd"] = cwd
        payload_path = Path(args[args.index("--input") + 1])
        captured["payload"] = json.loads(payload_path.read_text(encoding="utf-8"))
        return 0, json.dumps({"html_url": "https://github.com/owner/repo/pull/7#review"})

    monkeypatch.setattr(publish, "_gh", fake_gh)
    result = asyncio.run(registry.get("pr.post_review").handler(
        _ctx(settings, trace, tmp_path, state)))

    assert result.ok, result.summary
    assert captured["args"][:3] == ["api", "--method", "POST"]
    assert captured["args"][3] == "repos/owner/repo/pulls/7/reviews"
    assert len(captured["payload"]["comments"]) == 1
    assert result.outputs["inline"] == 1
    assert result.outputs["downgraded"] == 1
    assert result.outputs["event"] == "REQUEST_CHANGES"
    assert result.outputs["url"].endswith("#review")


def test_post_review_api_failure_escalates_with_payload(
        registry, settings, trace, tmp_path, monkeypatch):
    from infermatrix_copilot.engine.steps.pr import publish

    settings.allow_post = True
    state = {
        "repo_path": str(tmp_path),
        "task_spec": {"pr": 7, "post": True},
        "diff_text": _REVIEW_DIFF,
        "review_comments": [_finding("a.py", 10)],
        "review_summary": "summary\n\n**Verdict:** REQUEST CHANGES",
        "review_text": "full\n\n**Verdict:** REQUEST CHANGES",
        "pr_state": "OPEN",
    }
    monkeypatch.setattr(
        publish, "_repo_full_name", lambda ctx, repo: "owner/repo")

    def fake_gh(args, cwd=None):
        if args[:2] == ["pr", "view"]:
            return 0, json.dumps({"commits": [{"oid": "c" * 40}]})
        return 1, "HTTP 422 stale line"

    monkeypatch.setattr(publish, "_gh", fake_gh)

    result = asyncio.run(registry.get("pr.post_review").handler(
        _ctx(settings, trace, tmp_path, state)))

    assert not result.ok and result.failure is FailureKind.ESCALATE
    assert "422" in result.summary
    assert Path(result.outputs["artifacts"][0]).is_file()


def test_worktree_at_creates_and_reuses(git_repo, tmp_path):
    """_worktree_at pins a detached worktree at a sha, reuses a matching one,
    and swaps a stale one; failures return (False, why) instead of raising."""
    import subprocess

    from infermatrix_copilot.engine.steps.pr.fetch import _worktree_at

    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=git_repo,
                         capture_output=True, text=True).stdout.strip()
    dest = tmp_path / "wt"
    ok, detail = _worktree_at(git_repo, sha, dest)
    assert ok and "created" in detail and (dest / "mod_a.py").exists()
    ok, detail = _worktree_at(git_repo, sha, dest)
    assert ok and "reused" in detail
    ok, detail = _worktree_at(git_repo, "0" * 40, dest)
    assert not ok and "failed" in detail


def test_fetch_diff_pins_pr_time_checkout(settings, trace, tmp_path, git_repo,
                                          monkeypatch):
    """pr.fetch_diff publishes repo_path pinned to the PR head (injected sha in
    tests) plus a checkout_note; the worktree lands under ~/.infermatrix-copilot."""
    import asyncio
    import subprocess

    from infermatrix_copilot.engine.registry import StepRegistry
    from infermatrix_copilot.engine.step import StepContext
    from infermatrix_copilot.engine.steps import register_builtin_steps
    from infermatrix_copilot.engine.steps.pr import fetch as fetch_mod
    from infermatrix_copilot.run_trace import RunTrace

    monkeypatch.setattr(fetch_mod, "_gh",
                        lambda args, cwd=None: (0, "diff --git a/x b/x"))
    monkeypatch.setattr(fetch_mod.Path, "home", staticmethod(lambda: tmp_path))
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=git_repo,
                         capture_output=True, text=True).stdout.strip()
    registry = register_builtin_steps(StepRegistry())
    settings.repo_paths = {"vllm-omni": str(git_repo)}
    state = {"task_spec": {"kind": "pr_review", "pr": 7, "repo": "vllm-omni"},
             "repo_path": str(git_repo), "pr_head_sha": sha}
    ctx = StepContext(settings=settings, state=state, params={},
                      run_dir=tmp_path / "run", trace=RunTrace(tmp_path / "t.jsonl"),
                      llm=None)
    result = asyncio.run(registry.get("pr.fetch_diff").handler(ctx))
    assert result.ok, result.summary
    upd = result.outputs["state_updates"]
    assert "PR-TIME TREE" in upd["checkout_note"]
    assert upd["pr_head_sha"] == sha
    assert upd["repo_path"].endswith("-pr7")
    assert (tmp_path / ".infermatrix-copilot" / "worktrees").exists()
