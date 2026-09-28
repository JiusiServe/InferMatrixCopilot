"""Run a knowledge playbook for one repository through the standard executor
(checkpointed run directory, RunTrace, typed failures)."""

from __future__ import annotations

import asyncio
import time
import uuid
from pathlib import Path


def run_playbook(settings, name: str, repo: str, *, state_dir: Path, params: dict | None = None):
    from ..engine.executor import Executor
    from ..engine.registry import StepRegistry
    from ..engine.steps import register_builtin_steps
    from ..playbooks.store import PlaybookStore
    from ..run_trace import RunTrace
    from ..sdk._resources import resource_dir

    from ..engine.steps import knowledge as knowledge_steps

    registry = register_builtin_steps(StepRegistry())
    # the steps build their runtime from THIS state directory (never by
    # mutating the process environment)
    knowledge_steps.use_state_dir(state_dir)
    store = PlaybookStore(resource_dir("playbooks"), registry)
    playbook = store.get(name)
    if playbook is None or not name.startswith("kb-"):
        raise ValueError(f"unknown knowledge playbook: {name}")
    for spec in playbook.steps:
        spec.params = {**(spec.params or {}), "repo": repo, **(params or {})}
    run_dir = state_dir / "runs" / f"{name}-{repo}-{time.strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:6]}"
    run_dir.mkdir(parents=True, exist_ok=True)
    trace = RunTrace(run_dir / "run_trace.jsonl")
    executor = Executor(registry, settings, run_dir=run_dir, trace=trace)
    return asyncio.run(executor.run(playbook, {"kb_repo": repo})), run_dir
