"""Stage 1: monitored delegation to the external rebase orchestrator."""

import asyncio
import json
import sys

from omni_copilot.engine.steps import register_builtin_steps
from omni_copilot.engine.registry import StepRegistry
from omni_copilot.engine.step import FailureKind, StepContext
from omni_copilot.rebase.monitor import (
    build_command,
    build_escalation,
    classify_failure,
    diff_progress,
    parse_parent_state,
    summarize_progress,
)

STATE = {
    "run_id": "rebase-20260703-010101",
    "phase": "local_testing",
    "phase2_progress": {"run_id": "rebase-20260703-010101", "modules": {
        "worker_runner": {"status": "done", "exit_code": 0},
        "scheduler": {"status": "failed", "exit_code": 1},
        "platform": {"status": "running"},
    }},
    "phase3_progress": {"completed": ["t1", "t2"], "failed": ["t3"],
                        "skipped": [], "current": "t4"},
    "ci": {"result": ""},
    "main_ci_result": "passed",
}


def test_parse_parent_state_tolerant(tmp_path):
    assert parse_parent_state(tmp_path / "missing.json") is None
    bad = tmp_path / "bad.json"
    bad.write_text("{ partial")
    assert parse_parent_state(bad) is None
    good = tmp_path / "good.json"
    good.write_text(json.dumps(STATE))
    assert parse_parent_state(good)["phase"] == "local_testing"


def test_summarize_and_diff():
    s = summarize_progress(STATE)
    assert s["phase"] == "local_testing"
    assert s["modules"] == {"done": 1, "failed": 1, "running": 1, "skipped": 0}
    assert s["tests"]["completed"] == 2 and s["tests"]["failed"] == ["t3"]
    assert s["main_ci_result"] == "passed"

    later = json.loads(json.dumps(STATE))
    later["phase"] = "ci_e2e"
    later["phase2_progress"]["modules"]["platform"] = {"status": "done"}
    later["phase3_progress"]["completed"].append("t4")
    later["phase3_progress"]["failed"].append("t5")
    events = diff_progress(s, summarize_progress(later))
    joined = " | ".join(events)
    assert "phase: local_testing -> ci_e2e" in joined
    assert "modules done: 1 -> 2" in joined and "t5" in joined


def test_classify_failure_table():
    assert classify_failure(0, STATE)[0] is None
    assert classify_failure(1, None)[0] is FailureKind.BLOCKED       # died pre-init
    assert classify_failure(1, {"phase": "init"})[0] is FailureKind.BLOCKED
    assert classify_failure(1, STATE)[0] is FailureKind.ESCALATE     # failed module
    tests_only = {"phase": "local_testing",
                  "phase3_progress": {"failed": ["t3"], "completed": []}}
    assert classify_failure(1, tests_only)[0] is FailureKind.TEST_FAILURE
    ci = {"phase": "ci_e2e", "ci": {"result": "failed"}}
    assert classify_failure(1, ci)[0] is FailureKind.ESCALATE
    kind, note = classify_failure(1, {"phase": "done"})
    assert kind is None and "non-fatal" in note                       # curator crash
    assert classify_failure(1, STATE, timed_out=True)[0] is FailureKind.ESCALATE


def test_build_command_whitelist():
    base = "omni-rebase-orchestrator --dry-run"
    cmd = build_command(base, {})
    # cmd[0] may be resolved to the venv's bin dir when PATH lacks it
    assert cmd[0].rsplit("/", 1)[-1] == "omni-rebase-orchestrator"
    assert cmd[1:] == ["--dry-run"]
    cmd = build_command(base, {"local_ci_only": True, "main_ci_idx": 42,
                               "evil_flag": True, "command": "rm -rf /"},
                        resuming=True)
    assert cmd[1:] == ["--dry-run", "--local-ci-only",
                       "--main-ci-idx", "42", "--resume"]
    assert "rm" not in " ".join(cmd) and "evil" not in " ".join(cmd)


def test_build_escalation_collects_artifacts(tmp_path):
    latest = tmp_path / "rebase_logs" / "latest"
    (latest / "agents").mkdir(parents=True)
    (latest / "FINAL_SUMMARY.md").write_text("# summary")
    (latest / "orchestrator.log").write_text("line1\nline2\n")
    (latest / "agents" / "module-scheduler.log").write_text("conflict details")
    esc = build_escalation(STATE, tmp_path)
    names = [a.rsplit("/", 1)[-1] for a in esc["artifacts"]]
    assert "FINAL_SUMMARY.md" in names and "module-scheduler.log" in names
    assert "line2" in esc["escalation_summary"]["log_tail"]


def _fake_orchestrator(tmp_path, state_file, exit_code=0, sleep=0.0):
    """A tiny script standing in for omni-rebase-orchestrator."""
    script = tmp_path / "fake_orch.py"
    script.write_text(f"""
import json, sys, time
state = {json.dumps(STATE)}
state["phase"] = "module_rebase"
open({str(state_file)!r}, "w").write(json.dumps(state))
time.sleep({sleep})
state["phase"] = "done" if {exit_code} == 0 else "local_testing"
open({str(state_file)!r}, "w").write(json.dumps(state))
print("orchestrator output line")
sys.exit({exit_code})
""")
    return f"{sys.executable} {script}"


def _run_step(settings, trace, tmp_path, params, state=None):
    registry = register_builtin_steps(StepRegistry())
    ctx = StepContext(settings=settings, state=state or {}, params=params,
                      run_dir=tmp_path / "rundir", trace=trace)
    return asyncio.run(registry.get("rebase.run_external").handler(ctx))


def test_monitored_run_success(settings, trace, tmp_path):
    state_file = tmp_path / "state.json"
    cmd = _fake_orchestrator(tmp_path, state_file, exit_code=0, sleep=1.5)
    result = _run_step(settings, trace, tmp_path,
                       {"command": cmd, "state_file": str(state_file),
                        "poll_interval": 0.2})
    assert result.ok, result.summary
    assert result.outputs["rebase_status"]["phase"] == "done"
    assert "orchestrator output line" in result.outputs["tail"]
    assert (tmp_path / "rundir" / "rebase_status.json").exists()
    assert (tmp_path / "rundir" / "orchestrator_stdout.log").exists()
    assert list(trace.events("rebase_progress"))  # progress streamed mid-run


def test_monitored_run_failure_classified_with_escalation(settings, trace, tmp_path):
    state_file = tmp_path / "state.json"
    # the fake writes a failed-module state then exits 1
    cmd = _fake_orchestrator(tmp_path, state_file, exit_code=1)
    result = _run_step(settings, trace, tmp_path,
                       {"command": cmd, "state_file": str(state_file),
                        "poll_interval": 0.2})
    assert not result.ok and result.failure is FailureKind.ESCALATE
    assert "module rebase(s) failed" in result.summary
    assert "escalation_summary" in result.outputs


def test_stale_done_state_does_not_mask_a_crash(settings, trace, tmp_path):
    # a previous run left phase=done; this invocation crashes without touching it
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({"run_id": "rebase-old", "phase": "done"}))
    result = _run_step(settings, trace, tmp_path,
                       {"command": "false", "state_file": str(state_file)})
    assert not result.ok and result.failure is FailureKind.BLOCKED


def test_missing_orchestrator_blocks(settings, trace, tmp_path):
    result = _run_step(settings, trace, tmp_path,
                       {"command": "definitely-not-a-real-binary-xyz"})
    assert not result.ok and result.failure is FailureKind.BLOCKED


def test_timeout_escalates(settings, trace, tmp_path):
    state_file = tmp_path / "state.json"
    cmd = _fake_orchestrator(tmp_path, state_file, exit_code=0, sleep=30)
    result = _run_step(settings, trace, tmp_path,
                       {"command": cmd, "state_file": str(state_file),
                        "poll_interval": 0.2, "timeout": 1.0})
    assert not result.ok and result.failure is FailureKind.ESCALATE
    assert "timed out" in result.summary


def test_resume_flag_from_state(settings, trace, tmp_path):
    state_file = tmp_path / "state.json"
    script = tmp_path / "echo_args.py"
    script.write_text("import sys; print(' '.join(sys.argv[1:]))")
    result = _run_step(settings, trace, tmp_path,
                       {"command": f"{sys.executable} {script}",
                        "state_file": str(state_file)},
                       state={"resuming": True})
    # exit 0 + no state file -> success; --resume must be in the recorded command
    event = next(trace.events("external_command"))
    assert "--resume" in event["command"]
    assert "--resume" in result.outputs["tail"]
