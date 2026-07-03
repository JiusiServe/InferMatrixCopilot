"""omni-copilot — conversational CLI (design §3.Y).

REPL + one-shot (-p). NL -> intent -> TaskSpec (echoed; write/push tasks need
confirmation) -> planner (reuse > adapt > generate) -> executor. Built-ins:
/status /logs /playbooks /quit. Blocked runs exit 3.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

from .config import Settings
from .engine.builtin_steps import register_builtin_steps
from .engine.executor import Executor
from .engine.planner import Planner, PlanningError, Resolution
from .engine.registry import StepRegistry
from .intent import parse_intent
from .llm import LLM
from .notify import BLOCKED_EXIT, Notifier
from .playbooks.store import PlaybookStore
from .run_trace import RunTrace
from .targets.base import PushPolicy
from .task_spec import TaskSpec


class Copilot:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.llm = LLM(self.settings)
        self.registry = register_builtin_steps(StepRegistry())
        self.store = PlaybookStore(self.settings.playbooks_dir, self.registry)
        self.planner = Planner(self.store, self.registry)
        self.last_run_dir: Path | None = None

    # -- dispatch --------------------------------------------------------------
    def resolve(self, spec: TaskSpec) -> Resolution:
        return self.planner.resolve(spec)

    def run_task(self, spec: TaskSpec, *, assume_yes: bool = False,
                 plan_only: bool = False) -> int:
        try:
            resolution = self.resolve(spec)
        except PlanningError as exc:
            print(f"✋ cannot plan: {exc}")
            return BLOCKED_EXIT

        print(f"→ task: {spec.describe()}")
        print(f"→ plan: {resolution.mode} {resolution.playbook.name}"
              f"@{resolution.playbook.version} ({resolution.playbook.status}) "
              f"steps={[s.step for s in resolution.playbook.steps]}")
        for note in resolution.notes:
            print(f"  · {note}")
        if plan_only:
            return 0

        if (spec.confirm_required or resolution.requires_review) and not assume_yes:
            answer = input("Proceed? [y/N] ").strip().lower()
            if answer not in ("y", "yes"):
                print("aborted.")
                return 1

        run_id = f"run-{time.strftime('%Y%m%d-%H%M%S')}"
        run_dir = self.settings.run_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        self.last_run_dir = run_dir
        trace = RunTrace(run_dir / "run_trace.jsonl")
        notifier = Notifier(self.settings, run_dir, trace, run_id)
        trace.record("task", spec=spec.model_dump(), resolution=resolution.mode,
                     playbook=resolution.playbook.name, tier=resolution.tier)

        state: dict = {
            "task_spec": spec.model_dump(),
            "repo_path": str(self.settings.repo_path(spec.repo) or ""),
            "push_policy": PushPolicy(),  # pushes stay disallowed unless a target enables them
            "protected_branches": self.settings.protected_branches,
        }
        executor = Executor(self.registry, self.settings, run_dir=run_dir,
                            trace=trace, llm=self.llm, notifier=notifier)
        outcome = asyncio.run(executor.run(resolution.playbook, state))

        for step_id, r in outcome.step_results.items():
            mark = "✓" if r.ok else "✗"
            print(f"  {mark} {step_id}: {r.summary}")
        print(f"run {run_id}: {outcome.status}  ({run_dir})")
        if outcome.status == "blocked":
            print(f"  ⚠ {outcome.blocked_reason}\n  see {run_dir / 'ESCALATION.md'}")
            return BLOCKED_EXIT
        return 0 if outcome.status == "done" else 1

    # -- built-ins ---------------------------------------------------------------
    def status(self) -> str:
        if not self.last_run_dir:
            runs = sorted(self.settings.run_root.glob("run-*")) if self.settings.run_root.exists() else []
            if not runs:
                return "no runs yet"
            self.last_run_dir = runs[-1]
        progress = self.last_run_dir / "progress.json"
        if progress.exists():
            done = list(json.loads(progress.read_text()).get("completed", {}))
            return f"{self.last_run_dir.name}: completed steps: {done}"
        return f"{self.last_run_dir.name}: no progress recorded"

    def logs(self, n: int = 20) -> str:
        if not self.last_run_dir:
            return "no runs yet"
        tracefile = self.last_run_dir / "run_trace.jsonl"
        if not tracefile.exists():
            return "no trace"
        return "".join(tracefile.read_text().splitlines(keepends=True)[-n:])

    def playbooks(self) -> str:
        return "\n".join(
            f"{p.name}@{p.version} [{p.status}] kinds={p.task_kinds}"
            for p in self.store.all()
        ) or "(none)"


def _handle_line(copilot: Copilot, line: str, assume_yes: bool, plan_only: bool) -> int | None:
    line = line.strip()
    if not line:
        return None
    if line in ("/quit", "/exit", "exit", "quit"):
        return -1
    if line == "/status":
        print(copilot.status())
        return None
    if line.startswith("/logs"):
        parts = line.split()
        print(copilot.logs(int(parts[1]) if len(parts) > 1 else 20))
        return None
    if line == "/playbooks":
        print(copilot.playbooks())
        return None
    result = parse_intent(line, llm=copilot.llm,
                          default_repo=copilot.settings.default_repo,
                          model=copilot.settings.intent)
    if result.needs_clarification:
        print(f"? {result.clarify}")
        return None
    return copilot.run_task(result.spec, assume_yes=assume_yes, plan_only=plan_only)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omni-copilot",
                                     description="Conversational repo-maintenance copilot")
    parser.add_argument("-p", "--prompt", help="one-shot natural-language command")
    parser.add_argument("--yes", action="store_true",
                        help="skip confirmation prompts (headless)")
    parser.add_argument("--plan-only", action="store_true",
                        help="resolve and print the plan without executing")
    args = parser.parse_args(argv)

    copilot = Copilot()

    if args.prompt:
        code = _handle_line(copilot, args.prompt, args.yes, args.plan_only)
        return int(code) if code not in (None, -1) else 0

    print("omni-copilot — natural-language repo maintenance. /status /logs /playbooks /quit")
    while True:
        try:
            line = input("copilot> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        code = _handle_line(copilot, line, args.yes, args.plan_only)
        if code == -1:
            return 0


if __name__ == "__main__":
    sys.exit(main())
