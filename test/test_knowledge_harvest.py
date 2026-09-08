"""Guardrails for `pr.harvest_debug_knowledge` — the landed-fix intake drop.

Pinned behavior: the step is a strict no-op without a configured intake dir,
without a real (non-dry-run) push, or without a verified fix; it writes one
JSON record per run keyed by run id; and a write failure is traced and
swallowed — it must never fail a run whose fix already landed."""

import asyncio
import json

import pytest

from infermatrix_copilot.engine.registry import StepRegistry
from infermatrix_copilot.engine.step import StepContext
from infermatrix_copilot.engine.steps import register_builtin_steps


@pytest.fixture()
def registry():
    return register_builtin_steps(StepRegistry())


def _run(registry, settings, trace, tmp_path, state):
    handler = registry.get("pr.harvest_debug_knowledge").handler
    ctx = StepContext(settings=settings, state=state, params={},
                      run_dir=tmp_path / "run-x", trace=trace, llm=None)
    (tmp_path / "run-x").mkdir(exist_ok=True)
    return asyncio.run(handler(ctx))


def _state(*, dry_run=False, verified=True):
    debug_outputs = {
        "root_cause": "import cycle in helper" if verified else "",
        "fix_summary": "moved the import",
        "verification": "pytest test_x passed" if verified else "",
        "files_modified": ["pkg/helper.py"],
    }
    return {
        "task_spec": {"kind": "pr_debug", "repo": "demo", "pr": 42},
        "failure_groups": [{"signature": "ImportError: cycle",
                            "jobs": ["unit"]}],
        "outputs": {
            "debug": debug_outputs,
            "push": {"dry_run": True} if dry_run else {},
        },
    }


def test_disabled_without_intake_dir(registry, settings, trace, tmp_path):
    result = _run(registry, settings, trace, tmp_path, _state())
    assert result.ok
    assert "disabled" in result.summary
    assert not list(tmp_path.glob("intake/*.json"))


def test_dry_run_push_harvests_nothing(registry, settings, trace, tmp_path):
    settings.knowledge_intake_dir = str(tmp_path / "intake")
    result = _run(registry, settings, trace, tmp_path,
                  _state(dry_run=True))
    assert result.ok
    assert "no landed fix" in result.summary
    assert not (tmp_path / "intake").exists()


def test_unverified_fix_is_not_harvested(registry, settings, trace, tmp_path):
    settings.knowledge_intake_dir = str(tmp_path / "intake")
    result = _run(registry, settings, trace, tmp_path,
                  _state(verified=False))
    assert result.ok
    assert "no verified fixes" in result.summary


def test_landed_fix_writes_one_record(registry, settings, trace, tmp_path):
    settings.knowledge_intake_dir = str(tmp_path / "intake")
    settings.repo_full_names = {"demo": "owner/demo"}
    result = _run(registry, settings, trace, tmp_path, _state())
    assert result.ok
    path = tmp_path / "intake" / "run-x.json"
    assert path.is_file()
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["run_id"] == "run-x"
    assert record["repo"] == "owner/demo"  # full identity, not the alias
    assert record["pr"] == 42
    assert record["kind"] == "bugfix_run"
    assert record["groups"][0]["signature"] == "ImportError: cycle"
    assert record["groups"][0]["root_cause"] == "import cycle in helper"
    assert result.outputs["fixes"] == 1
    # No stray temp file left behind by the atomic write.
    assert list((tmp_path / "intake").iterdir()) == [path]


def _capture_gh(monkeypatch, *, code=0, out=None):
    import infermatrix_copilot.engine.steps.pr.debug as debug_module
    calls = []

    def fake_gh(args, cwd=None):
        calls.append(list(args))
        return code, (json.dumps({"html_url": "https://github.com/c/copilot/"
                                  "issues/135#issuecomment-9"})
                      if out is None else out)

    monkeypatch.setattr(debug_module, "_gh", fake_gh)
    return calls


def test_landed_fix_is_posted_to_the_mailbox_issue(
    registry, settings, trace, tmp_path, monkeypatch
):
    settings.knowledge_intake_dir = str(tmp_path / "intake")
    settings.knowledge_intake_issue = "c/copilot#135"
    settings.allow_post = True
    settings.repo_full_names = {"demo": "owner/demo"}
    calls = _capture_gh(monkeypatch)
    result = _run(registry, settings, tmp_path=tmp_path, trace=trace,
                  state=_state())
    assert result.ok and "via drop file and mailbox issue" in result.summary
    assert result.outputs["intake_comment"].endswith("#issuecomment-9")
    assert calls == [["api", "repos/c/copilot/issues/135/comments", "-X", "POST",
                      "-F", f"body=@{tmp_path / 'run-x' / 'knowledge-intake-comment.md'}"]]
    body = (tmp_path / "run-x" / "knowledge-intake-comment.md").read_text(
        encoding="utf-8"
    )
    assert body.startswith("<!-- infermatrix-copilot:bugfix-record:v1 -->\n```json\n")
    posted = json.loads(body.split("```json\n", 1)[1].rsplit("```", 1)[0])
    # The comment carries exactly the record the drop file carries.
    dropped = json.loads((tmp_path / "intake" / "run-x.json").read_text(encoding="utf-8"))
    assert posted == dropped and posted["repo"] == "owner/demo"
    assert list(trace.events("knowledge_intake_published"))


def test_mailbox_post_failure_is_swallowed(
    registry, settings, trace, tmp_path, monkeypatch
):
    settings.knowledge_intake_dir = str(tmp_path / "intake")
    settings.knowledge_intake_issue = "c/copilot#135"
    settings.allow_post = True
    _capture_gh(monkeypatch, code=1, out="HTTP 403: locked")
    result = _run(registry, settings, tmp_path=tmp_path, trace=trace,
                  state=_state())
    assert result.ok  # the landed fix and its drop file are not undone
    assert (tmp_path / "intake" / "run-x.json").is_file()
    assert "via drop file" in result.summary
    assert result.outputs["intake_publish_error"] == "HTTP 403: locked"
    assert "intake_comment" not in result.outputs
    assert list(trace.events("knowledge_intake_publish_failed"))


def test_mailbox_publisher_exception_is_swallowed(
    registry, settings, trace, tmp_path, monkeypatch
):
    import subprocess

    import infermatrix_copilot.engine.steps.pr.debug as debug_module

    def hanging_gh(args, cwd=None):
        raise subprocess.TimeoutExpired(cmd=["gh", *args], timeout=120)

    monkeypatch.setattr(debug_module, "_gh", hanging_gh)
    settings.knowledge_intake_dir = str(tmp_path / "intake")
    settings.knowledge_intake_issue = "c/copilot#135"
    settings.allow_post = True
    result = _run(registry, settings, tmp_path=tmp_path, trace=trace,
                  state=_state())
    assert result.ok and "via drop file" in result.summary
    assert result.outputs["intake_publish_error"].startswith("TimeoutExpired")
    assert list(trace.events("knowledge_intake_publish_failed"))


def test_mailbox_post_is_dry_run_without_allow_post(
    registry, settings, trace, tmp_path, monkeypatch
):
    """Invariant 5: an outward write needs the env flag too."""
    settings.knowledge_intake_dir = str(tmp_path / "intake")
    settings.knowledge_intake_issue = "c/copilot#135"
    settings.allow_post = False
    calls = _capture_gh(monkeypatch)
    result = _run(registry, settings, tmp_path=tmp_path, trace=trace,
                  state=_state())
    assert result.ok and calls == []
    assert "via drop file" in result.summary
    assert result.outputs["intake_publish_skipped"].startswith("ALLOW_POST=0")
    assert list(trace.events("knowledge_intake_publish_skipped"))


def test_mailbox_is_off_without_configuration(
    registry, settings, trace, tmp_path, monkeypatch
):
    settings.knowledge_intake_dir = str(tmp_path / "intake")
    calls = _capture_gh(monkeypatch)
    result = _run(registry, settings, tmp_path=tmp_path, trace=trace,
                  state=_state())
    assert result.ok and calls == []
    assert "intake_comment" not in result.outputs


def test_mailbox_only_configuration_posts_without_a_drop_dir(
    registry, settings, trace, tmp_path, monkeypatch
):
    """The production shape: no local consumer, only the mailbox."""
    settings.knowledge_intake_issue = "c/copilot#135"
    settings.allow_post = True
    calls = _capture_gh(monkeypatch)
    result = _run(registry, settings, tmp_path=tmp_path, trace=trace,
                  state=_state())
    assert result.ok and "via mailbox issue" in result.summary
    assert len(calls) == 1 and "intake_comment" in result.outputs
    assert "intake_path" not in result.outputs
    assert not (tmp_path / "intake").exists()


def test_drop_failure_does_not_suppress_the_mailbox(
    registry, settings, trace, tmp_path, monkeypatch
):
    blocker = tmp_path / "intake"
    blocker.write_text("a file where the directory should be")
    settings.knowledge_intake_dir = str(blocker)
    settings.knowledge_intake_issue = "c/copilot#135"
    settings.allow_post = True
    calls = _capture_gh(monkeypatch)
    result = _run(registry, settings, tmp_path=tmp_path, trace=trace,
                  state=_state())
    assert result.ok and "via mailbox issue" in result.summary
    assert "intake_error" in result.outputs and "intake_comment" in result.outputs
    assert len(calls) == 1


def test_write_failure_is_swallowed(registry, settings, trace, tmp_path):
    blocker = tmp_path / "intake"
    blocker.write_text("a file where the directory should be")
    settings.knowledge_intake_dir = str(blocker)
    result = _run(registry, settings, trace, tmp_path, _state())
    assert result.ok  # the landed fix must never be failed by the drop
    assert "intake delivery failed" in result.summary
    assert "intake_error" in result.outputs


def _executor_env(settings, trace, tmp_path, calls=None):
    """A real Executor over the real registry plus two stand-ins for the
    debug/push steps' externals — the e2e boundary is the process edge
    (agent LLM, git push), not the engine."""
    from infermatrix_copilot.engine import Executor, StepResult, StepSpec
    from infermatrix_copilot.notify import Notifier

    registry = register_builtin_steps(StepRegistry())

    async def debug_sim(ctx):
        if calls is not None:
            calls.append("debug")
        return StepResult(
            True, summary="fixed",
            outputs={"root_cause": "flaky fixture reuse",
                     "fix_summary": "isolated the fixture",
                     "verification": "pytest -k fixture passed",
                     "files_modified": ["tests/conftest.py"],
                     "state_updates": {
                         "failure_groups": [{"signature": "FixtureError",
                                             "jobs": ["unit"]}]}})

    async def push_sim(ctx):
        return StepResult(True, summary="pushed", outputs={})

    registry.register(StepSpec("test.debug_sim", "deterministic", "read",
                               debug_sim))
    registry.register(StepSpec("test.push_sim", "deterministic", "read",
                               push_sim))
    run_dir = tmp_path / "run-e2e"
    notifier = Notifier(settings, run_dir, trace, "run-e2e")
    executor = Executor(registry, settings, run_dir=run_dir, trace=trace,
                        notifier=notifier)
    return executor


def _harvest_playbook(*, include_harvest=True):
    from infermatrix_copilot.playbooks.store import Playbook, PlaybookStep

    steps = [PlaybookStep("debug", "test.debug_sim"),
             PlaybookStep("push", "test.push_sim")]
    if include_harvest:
        steps.append(PlaybookStep("harvest", "pr.harvest_debug_knowledge"))
    return Playbook(name="e2e-debug", version=1, status="active",
                    task_kinds=["pr_debug"], repos=[], steps=steps)


def test_e2e_executor_runs_harvest_after_push(settings, trace, tmp_path):
    """Whole-pipeline path: the executor's own outputs map (not hand-built
    state) feeds the harvest step, and the drop lands with the checkpoint
    contract intact."""
    settings.knowledge_intake_dir = str(tmp_path / "intake")
    settings.repo_full_names = {"demo": "owner/demo"}
    executor = _executor_env(settings, trace, tmp_path)
    outcome = asyncio.run(executor.run(
        _harvest_playbook(),
        {"task_spec": {"kind": "pr_debug", "repo": "demo", "pr": 42}},
    ))
    assert outcome.status == "done"
    drops = list((tmp_path / "intake").glob("*.json"))
    assert len(drops) == 1
    record = json.loads(drops[0].read_text(encoding="utf-8"))
    assert record["repo"] == "owner/demo"
    assert record["groups"][0]["root_cause"] == "flaky fixture reuse"
    assert record["run_id"] == "run-e2e"


def test_e2e_resume_restores_outputs_for_harvest(settings, trace, tmp_path):
    """Crash-before-harvest then --resume: the harvest step consumes the
    executor-restored outputs map from progress.json, so a resumed run
    still drops the record (invariant #2's restore path, exercised end to
    end rather than with hand-built state)."""
    settings.knowledge_intake_dir = str(tmp_path / "intake")
    settings.repo_full_names = {"demo": "owner/demo"}
    calls = []
    executor = _executor_env(settings, trace, tmp_path, calls)
    state = {"task_spec": {"kind": "pr_debug", "repo": "demo", "pr": 42}}
    # Phase 1: the run completes debug+push, then "crashes" before harvest
    # (the step simply is not in this playbook revision).
    outcome = asyncio.run(executor.run(
        _harvest_playbook(include_harvest=False), dict(state)))
    assert outcome.status == "done"
    assert calls == ["debug"]
    assert not (tmp_path / "intake").exists()
    # Phase 2: resume over the same run dir with FRESH state — completed
    # steps short-circuit from the checkpoint and only harvest executes.
    executor2 = _executor_env(settings, trace, tmp_path, calls)
    outcome = asyncio.run(executor2.run(
        _harvest_playbook(), dict(state)))
    assert outcome.status == "done"
    assert calls == ["debug"]  # the checkpoint replayed; no re-execution
    drops = list((tmp_path / "intake").glob("*.json"))
    assert len(drops) == 1
    record = json.loads(drops[0].read_text(encoding="utf-8"))
    assert record["groups"][0]["root_cause"] == "flaky fixture reuse"


def test_playbook_wires_the_harvest_after_push(settings):
    import yaml
    from pathlib import Path

    playbook = yaml.safe_load(
        (Path(__file__).resolve().parents[1] / "playbooks" /
         "pr-debug.yaml").read_text(encoding="utf-8")
    )
    ids = [step["id"] for step in playbook["steps"]]
    assert ids.index("harvest") == ids.index("push") + 1
    harvest = next(s for s in playbook["steps"] if s["id"] == "harvest")
    assert harvest["step"] == "pr.harvest_debug_knowledge"
    assert harvest["when"] == "not report_only"
