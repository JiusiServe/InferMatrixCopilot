"""Repo-rebase delegation step (wrap-don't-rewrite): the locked repo-rebase
playbook runs the existing 5-phase orchestrator here rather than reimplementing
it. Monitored: per-phase/per-module progress is streamed from the parent's
state.json into the RunTrace, failures classified into escalation material.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..step import FailureKind, StepContext, StepResult
from ._common import step


@step("rebase.run_external", "script", "write_workspace",
      "Delegate to the existing 5-phase rebase orchestrator (locked pipeline).")
async def _run_external_rebase(ctx: StepContext) -> StepResult:
    import asyncio as _asyncio

    from ...rebase.monitor import (build_command, build_escalation,
                                   classify_failure, diff_progress,
                                   parse_parent_state, summarize_progress)

    spec = ctx.state.get("task_spec") or {}
    task_params = (spec.get("params") if isinstance(spec, dict) else {}) or {}
    resuming = bool(ctx.state.get("resuming"))
    cmd = build_command(ctx.params.get("command") or ctx.settings.rebase_orchestrator_cmd,
                        task_params, resuming=resuming)
    state_file = Path(ctx.params.get("state_file")
                      or ctx.settings.rebase_agent_root / "rebase_logs" / "state.json")
    poll = float(ctx.params.get("poll_interval") or ctx.settings.rebase_poll_interval)
    timeout = float(ctx.params.get("timeout", 6 * 3600))
    ctx.trace.record("external_command", command=cmd)

    pre = parse_parent_state(state_file)
    if pre and pre.get("phase") not in ("", "done", None) and not resuming:
        ctx.trace.record("rebase_preexisting_state", phase=pre.get("phase"),
                         run_id=pre.get("run_id"))

    ctx.run_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = ctx.run_dir / "orchestrator_stdout.log"
    stderr_path = ctx.run_dir / "orchestrator_stderr.log"
    status_path = ctx.run_dir / "rebase_status.json"
    timed_out = False
    with stdout_path.open("ab") as out_f, stderr_path.open("ab") as err_f:
        try:
            proc = await _asyncio.create_subprocess_exec(*cmd, stdout=out_f, stderr=err_f)
        except FileNotFoundError:
            return StepResult(False, FailureKind.BLOCKED,
                              f"orchestrator not found: {cmd[0]!r} — is "
                              "vllm-omni-rebase-agent installed?")
        last = summarize_progress(parse_parent_state(state_file))
        loop = _asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while proc.returncode is None:
            try:
                await _asyncio.wait_for(proc.wait(), timeout=min(poll, 5.0))
                break
            except _asyncio.TimeoutError:
                pass
            if loop.time() > deadline:
                proc.terminate()
                try:
                    await _asyncio.wait_for(proc.wait(), timeout=30)
                except _asyncio.TimeoutError:
                    proc.kill()
                timed_out = True
                break
            current = summarize_progress(parse_parent_state(state_file))
            events = diff_progress(last, current)
            if events:
                ctx.trace.record("rebase_progress", events=events,
                                 phase=current.get("phase"))
                status_path.write_text(json.dumps(current, indent=2))
                last = current

    final_state = parse_parent_state(state_file)
    rc_early = proc.returncode if proc.returncode is not None else 1
    if rc_early != 0 and final_state == pre:
        # state.json never changed during THIS invocation — whatever it says
        # belongs to a previous run; don't let a stale phase=done mask a crash
        final_state = None
    final = summarize_progress(final_state)
    status_path.write_text(json.dumps(final, indent=2))
    tail = ""
    for p in (stderr_path, stdout_path):
        try:
            tail = tail or p.read_text(encoding="utf-8", errors="replace")[-3_000:].strip()
        except OSError:
            pass

    rc = proc.returncode if proc.returncode is not None else 1
    kind, note = classify_failure(rc, final_state, timed_out=timed_out)
    if kind is None:
        summary = f"external rebase pipeline completed ({note}; phase={final.get('phase')})"
        return StepResult(True, summary=summary,
                          outputs={"rebase_status": final, "tail": tail})
    esc = build_escalation(final_state, ctx.settings.rebase_agent_root)
    return StepResult(False, kind, f"{note} (exit {rc})",
                      outputs={**esc, "rebase_status": final, "tail": tail})
