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


def test_write_failure_is_swallowed(registry, settings, trace, tmp_path):
    blocker = tmp_path / "intake"
    blocker.write_text("a file where the directory should be")
    settings.knowledge_intake_dir = str(blocker)
    result = _run(registry, settings, trace, tmp_path, _state())
    assert result.ok  # the landed fix must never be failed by the drop
    assert "intake drop failed" in result.summary
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
