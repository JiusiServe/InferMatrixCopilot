"""Read-only observability over the vllm-omni-rebase-agent pipeline.

The parent orchestrator writes `rebase_logs/state.json` (phase marker +
per-module `phase2_progress` + per-test `phase3_progress`) and exits 0/1 with
no notifications. These pure functions turn that into copilot progress events,
typed failure classification, and escalation material. Nothing here writes to
the parent's files.
"""

from __future__ import annotations

import json
import shlex
import shutil
import sys
from pathlib import Path

from ..engine.step import FailureKind

# task params the copilot may forward to the orchestrator CLI — nothing else.
_FLAG_WHITELIST = {
    "local_ci_only": "--local-ci-only",
    "remote_ci_only": "--remote-ci-only",
}


def parse_parent_state(path: str | Path) -> dict | None:
    """Tolerant read: the parent writes non-atomically; partial JSON -> None."""
    p = Path(path)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def summarize_progress(parent_state: dict | None) -> dict:
    if not parent_state:
        return {"phase": "unknown"}
    modules = (parent_state.get("phase2_progress") or {}).get("modules", {})
    counts = {"done": 0, "failed": 0, "running": 0, "skipped": 0}
    for m in modules.values():
        status = (m or {}).get("status", "running")
        counts[status if status in counts else "running"] += 1
    p3 = parent_state.get("phase3_progress") or {}
    return {
        "run_id": parent_state.get("run_id", ""),
        "phase": parent_state.get("phase", "unknown"),
        "modules": counts,
        "tests": {
            "completed": len(p3.get("completed", [])),
            "failed": p3.get("failed", []),
            "skipped": len(p3.get("skipped", [])),
            "current": p3.get("current", ""),
        },
        "ci_result": (parent_state.get("ci") or {}).get("result", ""),
        "main_ci_result": parent_state.get("main_ci_result", ""),
    }


def diff_progress(old: dict, new: dict) -> list[str]:
    """Human-readable change events between two summaries."""
    events: list[str] = []
    if old.get("phase") != new.get("phase"):
        events.append(f"phase: {old.get('phase')} -> {new.get('phase')}")
    om, nm = old.get("modules", {}), new.get("modules", {})
    for key in ("done", "failed"):
        if nm.get(key, 0) > om.get(key, 0):
            events.append(f"modules {key}: {om.get(key, 0)} -> {nm[key]}")
    ot, nt = old.get("tests", {}), new.get("tests", {})
    if nt.get("completed", 0) > ot.get("completed", 0):
        events.append(f"tests completed: {ot.get('completed', 0)} -> {nt['completed']}")
    if len(nt.get("failed", [])) > len(ot.get("failed", [])):
        new_failed = set(map(str, nt.get("failed", []))) - set(map(str, ot.get("failed", [])))
        events.append(f"tests FAILED: {sorted(new_failed)}")
    if nt.get("current") and nt.get("current") != ot.get("current"):
        events.append(f"running test: {nt['current']}")
    for key in ("ci_result", "main_ci_result"):
        if new.get(key) and new.get(key) != old.get(key):
            events.append(f"{key}: {new[key]}")
    return events


def classify_failure(exit_code: int, parent_state: dict | None,
                     *, timed_out: bool = False) -> tuple[FailureKind | None, str]:
    """Map (exit code, state.json) -> typed failure. Returns (None, note) when
    the run actually succeeded despite exit 1 (post-run curator crash)."""
    if timed_out:
        return FailureKind.ESCALATE, "orchestrator timed out"
    if exit_code == 0:
        return None, "completed"
    summary = summarize_progress(parent_state)
    phase = summary.get("phase", "unknown")
    if phase == "done":
        return None, "pipeline reached done; post-run hook failed (non-fatal)"
    if phase in ("unknown", "init", ""):
        return (FailureKind.BLOCKED,
                "orchestrator failed before/at init (environment, dirty branch, "
                "baseline or wheel selection)")
    if summary["modules"]["failed"] > 0:
        return (FailureKind.ESCALATE,
                f"{summary['modules']['failed']} module rebase(s) failed — "
                "conflicts likely need a human")
    if summary["tests"]["failed"]:
        return (FailureKind.TEST_FAILURE,
                f"local tests failed: {summary['tests']['failed'][:5]}")
    if summary.get("ci_result") == "failed":
        return FailureKind.ESCALATE, "Buildkite CI failed after debug retries"
    return FailureKind.ESCALATE, f"orchestrator exited {exit_code} during phase {phase}"


def build_escalation(parent_state: dict | None, agent_root: str | Path) -> dict:
    """Escalation material: compact summary + pointers to the parent's artifacts."""
    root = Path(agent_root)
    latest = root / "rebase_logs" / "latest"
    summary = summarize_progress(parent_state)
    artifacts: list[str] = []
    log_tail = ""
    for name in ("FINAL_SUMMARY.md", "orchestrator.log"):
        p = latest / name
        if p.exists():
            artifacts.append(str(p))
            if name == "orchestrator.log":
                try:
                    log_tail = p.read_text(encoding="utf-8", errors="replace")[-2_000:]
                except OSError:
                    pass
    modules = ((parent_state or {}).get("phase2_progress") or {}).get("modules", {})
    for m, info in modules.items():
        if (info or {}).get("status") == "failed":
            log = latest / "agents" / f"module-{m}.log"
            if log.exists():
                artifacts.append(str(log))
    return {"escalation_summary": {**summary, "log_tail": log_tail},
            "artifacts": artifacts}


def build_command(base_cmd: str, task_params: dict | None,
                  *, resuming: bool = False) -> list[str]:
    """Whitelisted flag passthrough — NL-supplied params can never widen the
    orchestrator's flag surface beyond this list."""
    cmd = shlex.split(base_cmd)
    # console scripts live next to the interpreter; PATH may not include it
    if cmd and "/" not in cmd[0] and shutil.which(cmd[0]) is None:
        sibling = Path(sys.executable).parent / cmd[0]
        if sibling.exists():
            cmd[0] = str(sibling)
    params = task_params or {}
    for key, flag in _FLAG_WHITELIST.items():
        if params.get(key) and flag not in cmd:
            cmd.append(flag)
    idx = params.get("main_ci_idx")
    if isinstance(idx, int) and idx > 0 and "--main-ci-idx" not in cmd:
        cmd += ["--main-ci-idx", str(idx)]
    if resuming and "--resume" not in cmd:
        cmd.append("--resume")
    return cmd
