"""One resumable coordinator for CLI, playbook and the weekly scheduler."""
from __future__ import annotations
import json
import time
from pathlib import Path

from ..trace_store import file_lock
from .artifacts import atomic_json

def run(settings, store, *, workflow="all", repo="", post=False, now=None, llm=None, sandbox=None):
    from .cycle import run_cycle, ledger_dir_for
    from . import experiments, evolution
    if not settings.improve_enabled or not settings.improve_evolve_enabled:
        return {"state": "disabled", "reason": "improvement kill switch"}
    now = time.time() if now is None else now
    root = ledger_dir_for(settings)
    root.mkdir(parents=True, exist_ok=True)
    with file_lock(root / "coordinator.lock", blocking=False) as held:
        if not held: return {"state": "deferred", "reason": "cycle coordinator locked"}
        path = root / "coordinator.json"
        state = json.loads(path.read_text()) if path.exists() else {}
        from .budget import iso_week
        if state.get("state") == "complete":
            if iso_week(state["at"]) == iso_week(now):
                # Same weekly cycle: keep completed paid phases, refresh
                # candidate/adoption/publication state only.
                state["stages"].pop("evolve", None)
            else: state = {}
        if not state:
            state = {"state": "running", "at": now, "stages": {}}
            atomic_json(path, state)
        if "lint" not in state["stages"]:
            state["stages"]["lint"] = run_cycle(store, settings, root, now=state["at"])
            atomic_json(path, state)
        # Previously registered experiments always have priority over a new candidate.
        pending = [e for e in experiments.list_experiments(root) if e.state in ("registered", "running")]
        attempted = {r["id"] for r in state["stages"].get("experiments", [])}
        if "experiments" not in state["stages"] or any(e.experiment_id not in attempted for e in pending):
            completed = list(state["stages"].get("experiments", []))
            for exp in pending:
                if exp.experiment_id in attempted: continue
                try:
                    result = experiments.run(store, settings, root, exp.experiment_id, judge_llm=llm, sandbox=sandbox)
                    completed.append({"id": result.experiment_id, "state": result.state})
                except Exception as exc:
                    completed.append({"id": exp.experiment_id, "error": str(exc)})
            state["stages"]["experiments"] = completed
            atomic_json(path, state)
        forensic_key = "forensics" if workflow == "all" and not repo else f"forensics:{workflow}:{repo}"
        if forensic_key not in state["stages"]:
            # Reuse the actual playbook handler; expose the original lint window.
            from ..engine.step import StepContext
            from ..engine.steps.improve import _forensics
            from ..run_trace import RunTrace
            from ..llm import LLM
            import asyncio
            report = state["stages"]["lint"]
            ctx = StepContext(settings.model_copy(update={"trace_store_root": str(store.root)}), {"improve_cycle": report}, {"workflow": "" if workflow == "all" else workflow, "repo": repo}, root / "coordinator-run",
                              RunTrace(root / "coordinator-trace.jsonl"), llm or LLM(settings))
            ctx.run_dir.mkdir(parents=True, exist_ok=True)
            # Persist before a paid phase; an interrupted invocation is recorded
            # as interrupted on restart and never submitted twice.
            state["stages"][forensic_key] = {"ok": False, "summary": "forensics-interrupted; no paid-call replay"}
            atomic_json(path, state)
            from ..trace_store import bind_store, trace_context
            from .enroll import declarations_for
            from .fingerprint import compute
            decl = declarations_for(settings).get("workflow-improve.improve.forensics")
            fingerprint, manifest = compute(decl, settings, state={"improve_item": "cycle"}) if decl else ("", {})
            context = {"playbook": "workflow-improve", "step": "improve.forensics", "workflow": "workflow-improve.improve.forensics", "item": "cycle", "unit_id": f"cycle-{state['at']}:{forensic_key}", "fingerprint": fingerprint}
            with bind_store(store), trace_context(**context):
                result = asyncio.run(_forensics(ctx))
                store.append("decision", result={"type": "step_result", "ok": result.ok, "summary": result.summary}, inputs={"fingerprint_manifest": json.dumps(manifest)}, outputs={"forensics": json.dumps(result.outputs, default=str)})
            state["stages"][forensic_key] = {"ok": result.ok, "outputs": result.outputs, "summary": result.summary}
            atomic_json(path, state)
        if "evolve" not in state["stages"]:
            state["stages"]["evolve"] = evolution.run(settings, store, workflow=workflow, repo=repo, post=post, llm=llm, sandbox=sandbox, now=now)
            atomic_json(path, state)
        state["state"] = "complete"
        state["units"] = state["stages"]["lint"].get("units", 0)
        state["proposals_opened"] = state["stages"]["lint"].get("proposals_opened", [])
        atomic_json(path, state)
        return state
