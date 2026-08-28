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
