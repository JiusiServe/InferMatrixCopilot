"""The `Copilot` orchestrator: NL-resolved TaskSpec → plan (reuse > adapt >
generate) → plan-review gate → executor, plus the compound-command queue,
resume, and the /status /logs /playbooks built-ins.

This is the orchestration core; the argparse/REPL wiring lives in `entry.py` and
the pure formatters in `utils.py`.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import NamedTuple

import yaml

from ..config import Settings
from ..engine.executor import Executor
from ..engine.planner import Planner, PlanningError, Resolution
from ..engine.registry import StepRegistry
from ..engine.steps import register_builtin_steps
from ..llm import LLM
from ..notify import BLOCKED_EXIT, Notifier
from ..playbooks.store import PlaybookStore, parse_playbook, playbook_to_doc
from ..push import PushPolicy
from ..review.reviewer import run_plan_review
from ..run_trace import RunTrace
from ..task_spec import TaskSpec
from ..ui import style
from .utils import format_metrics_line


class GateOutcome(NamedTuple):
    """Result of the pre-execution gates. `proceed` says whether to run; when
    False, `exit_code` is the process code the caller should return. Read at
    the call site as: ``if not gate.proceed: return gate.exit_code``."""

    proceed: bool
    exit_code: int = 0

    @classmethod
    def go(cls) -> "GateOutcome":
        """Gates passed — run the task."""
        return cls(proceed=True)

    @classmethod
    def stop(cls, exit_code: int) -> "GateOutcome":
        """A gate halted the run — return this exit code."""
        return cls(proceed=False, exit_code=exit_code)


class Copilot:
    """Orchestration core: resolves a TaskSpec to a playbook (reuse > adapt >
    generate), runs it through the plan-review gate + confirmation into the
    Executor, and owns the compound-command queue, resume, and the /status
    /logs /playbooks built-ins. Holds the long-lived collaborators (LLM,
    step registry, playbook store, planner) and tracks `last_run_dir` for the
    built-ins."""

    def __init__(self, settings: Settings | None = None):
        """Wire up the collaborators from `settings` (default `Settings()`):
        the LLM, the built-in step registry, the playbook store rooted at the
        configured dir, and the planner over both. `last_run_dir` starts unset
        and is filled by the first execution."""
        self.settings = settings or Settings()
        self.llm = LLM(self.settings)
        self.registry = register_builtin_steps(StepRegistry())
        self.store = PlaybookStore(self.settings.playbooks_dir, self.registry)
        self.planner = Planner(self.store, self.registry)
        self.last_run_dir: Path | None = None

    # -- planning ---------------------------------------------------------------
    def resolve(self, spec: TaskSpec) -> Resolution:
        """Resolve `spec` to a Resolution via the planner, passing the repo's
        capability set so the planner only reuses playbooks the target supports.
        Capabilities come from the repo's adapter (if any), plus `repo.path` when
        a path is resolvable even without a adapter (REPO_PATHS works adapter-less)."""
        adapter = self._adapter_for(spec.repo)
        capabilities = set(adapter.capabilities) if adapter is not None else set()
        if self._resolve_repo_path(spec.repo):  # REPO_PATHS works adapter-less
            capabilities.add("repo.path")
        return self.planner.resolve(spec, capabilities=capabilities)

    def _plan_review_gate(self, resolution: Resolution, spec: TaskSpec,
                          assume_yes: bool) -> bool:
        """Inline Plan-Review for adapted/generated plans. LLM verdict shown in
        the session; block stops; no reviewer -> the human confirm IS the gate."""
        if not resolution.requires_review:
            return True
        doc = yaml.safe_dump(playbook_to_doc(resolution.playbook), sort_keys=False)
        verdict = run_plan_review(self.llm, playbook_doc=doc, task=spec.describe(),
                                  model=self.settings.reviewer)
        if verdict.verdict == "unavailable":
            print("  ⚠ no reviewer LLM — your confirmation is the plan-review gate")
            return True
        print(f"  plan review: {verdict.verdict}"
              + (f" — {verdict.critiques}" if verdict.critiques else ""))
        if verdict.verdict == "block":
            print("✋ plan blocked by reviewer.")
            return False
        return True  # lgtm, or revise surfaced to the user before their confirm

    def _gate_and_confirm(self, resolution: Resolution, spec: TaskSpec,
                          assume_yes: bool, *, prompt: str = "Proceed?",
                          force_confirm: bool = False) -> GateOutcome:
        """Plan-review gate + [y/N] confirm (concision K6). Returns
        `GateOutcome.go()` to run, or `GateOutcome.stop(code)` to halt with a
        process exit code (BLOCKED_EXIT on a reviewer block, 1 on a user
        abort). Confirm fires for confirm_required or a review-requiring/
        explicit plan, unless assume_yes."""
        if not self._plan_review_gate(resolution, spec, assume_yes):
            return GateOutcome.stop(BLOCKED_EXIT)  # reviewer blocked the plan
        need = force_confirm or spec.confirm_required or resolution.requires_review
        if need and not assume_yes:
            if input(f"{prompt} [y/N] ").strip().lower() not in ("y", "yes"):
                print("aborted.")
                return GateOutcome.stop(1)  # user declined
        return GateOutcome.go()

    # -- execution -----------------------------------------------------------------
    def run_task(self, spec: TaskSpec, *, assume_yes: bool = False,
                 plan_only: bool = False) -> int:
        """Full path for one task: resolve → print plan → gate/confirm →
        persist task.json → execute. Returns a process exit code — 0 done,
        1 failed/aborted, BLOCKED_EXIT when planning fails or a gate blocks.
        `plan_only` prints the resolved plan and returns 0 without running;
        `assume_yes` skips the interactive confirm."""
        try:
            resolution = self.resolve(spec)
        except PlanningError as exc:
            print(style("✋ cannot plan: ", "red", "bold") + str(exc))
            return BLOCKED_EXIT

        print(style("→ task: ", "bold", "cyan") + spec.describe())
        print(style("→ plan: ", "bold", "magenta") + f"{resolution.mode} {resolution.playbook.name}"
              f"@{resolution.playbook.version} ({resolution.playbook.status}) "
              f"steps={[s.step for s in resolution.playbook.steps]}")
        for note in resolution.notes:
            print(f"  · {note}")
        if plan_only:
            return 0

        gate = self._gate_and_confirm(resolution, spec, assume_yes)
        if not gate.proceed:
            return gate.exit_code

        run_id = (f"run-{time.strftime('%Y%m%d-%H%M%S')}"
                  f"-{uuid.uuid4().hex[:6]}")  # unique — same-second runs collided
        run_dir = self.settings.run_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "task.json").write_text(json.dumps({
            "spec": spec.model_dump(), "playbook": playbook_to_doc(resolution.playbook),
        }, indent=2))
        return self._execute(resolution.playbook, spec, run_dir,
                             resolution_mode=resolution.mode, tier=resolution.tier)

    def run_playbook(self, name: str, *, params: dict | None = None,
                     report_only: bool = False, assume_yes: bool = False,
                     plan_only: bool = False) -> int:
        """Explicit playbook override — the only way to execute a CANDIDATE
        (e.g. repo-rebase-native for side-by-side validation). Always treated
        as requiring review + confirmation."""
        playbook = self.store.get(name)
        if playbook is None:
            print(f"✋ no playbook named {name!r} (see /playbooks)")
            return BLOCKED_EXIT
        kind = playbook.task_kinds[0]
        spec = TaskSpec(kind=kind, repo=self.settings.default_repo,
                        report_only=report_only, params=params or {})
        print(style("→ task: ", "bold", "cyan") + spec.describe()
              + style("  [explicit playbook override]", "yellow"))
        print(style("→ plan: ", "bold", "magenta") + f"explicit {playbook.name}@{playbook.version} "
              f"({playbook.status}) steps={[s.step for s in playbook.steps]}")
        if plan_only:
            return 0
        resolution = Resolution(mode="explicit", playbook=playbook,
                                tier=spec.tier, requires_review=True)
        gate = self._gate_and_confirm(
            resolution, spec, assume_yes, force_confirm=True,
            prompt=f"Run {playbook.status} playbook '{name}'?")
        if not gate.proceed:
            return gate.exit_code
        run_id = (f"run-{time.strftime('%Y%m%d-%H%M%S')}"
                  f"-{uuid.uuid4().hex[:6]}")  # unique — same-second runs collided
        run_dir = self.settings.run_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "task.json").write_text(json.dumps({
            "spec": spec.model_dump(), "playbook": playbook_to_doc(playbook),
        }, indent=2))
        return self._execute(playbook, spec, run_dir,
                             resolution_mode="explicit", tier=spec.tier)

    def _execute(self, playbook, spec: TaskSpec, run_dir: Path, *,
                 resolution_mode: str = "resume", tier: str = "?",
                 resuming: bool = False) -> int:
        """Run a resolved `playbook` to completion in `run_dir`: init tracing +
        notifier, seed the shared state (repo path, push policy, protected
        branches / high-risk modules from the adapter when present), drive the
        Executor, then print per-step marks, optional run metrics, and the final
        status. `resuming` seeds the state so steps can pick up where they left
        off. Returns the exit code (0 done, BLOCKED_EXIT blocked, else 1)."""
        self.last_run_dir = run_dir
        from .. import tracing
        tracing.init(run_dir.name, run_dir / "trace.jsonl")
        trace = RunTrace(run_dir / "run_trace.jsonl")
        notifier = Notifier(self.settings, run_dir, trace, run_dir.name)
        trace.record("task", spec=spec.model_dump(), resolution=resolution_mode,
                     playbook=playbook.name, tier=tier)
        state: dict = {
            "task_spec": spec.model_dump(),
            "repo_path": self._resolve_repo_path(spec.repo),
            "push_policy": PushPolicy(),  # steps may replace with a derived policy
            "protected_branches": self.settings.protected_branches,
            "resuming": resuming,
        }
        adapter = self._adapter_for(spec.repo)
        if adapter is not None:
            # repo knowledge from the adapter, not core settings (v2 P0 fix #5)
            state["protected_branches"] = adapter.protected_branches
            if adapter.high_risk_modules:
                state["high_risk_modules"] = adapter.high_risk_modules
        executor = Executor(self.registry, self.settings, run_dir=run_dir,
                            trace=trace, llm=self.llm, notifier=notifier)
        outcome = asyncio.run(executor.run(playbook, state))

        if self.settings.metrics_enabled:
            try:  # metrics are facts about the run; never let them break it
                from ..metrics import collect_run_metrics
                m = collect_run_metrics(run_dir, self.settings, outcome.status)
                print(format_metrics_line(m, run_dir))
            except Exception as exc:
                trace.record("metrics_error", error=f"{type(exc).__name__}: {exc}")

        for step_id, r in outcome.step_results.items():
            mark = style("✓", "green") if r.ok else style("✗", "red", "bold")
            print(f"  {mark} {step_id}: {r.summary}")
        print(f"run {run_dir.name}: {outcome.status}  ({run_dir})")
        if outcome.status == "blocked":
            print(style("  ⚠ ", "yellow", "bold") + f"{outcome.blocked_reason}\n  see {run_dir / 'ESCALATION.md'}")
            return BLOCKED_EXIT
        return 0 if outcome.status == "done" else 1

    def run_queue(self, specs: list[TaskSpec], *, assume_yes: bool = False,
                  plan_only: bool = False) -> int:
        """Ordered task queue for compound commands; stops on failure/blocked."""
        if len(specs) > 1:
            print(f"⧉ queued {len(specs)} tasks:")
            for i, s in enumerate(specs, 1):
                print(f"  {i}. {s.describe()}")
        for i, spec in enumerate(specs, 1):
            if len(specs) > 1:
                print(f"\n── task {i}/{len(specs)} ──")
            code = self.run_task(spec, assume_yes=assume_yes, plan_only=plan_only)
            if code != 0:
                if i < len(specs):
                    print(f"⏸ queue stopped: {len(specs) - i} task(s) not run")
                return code
        return 0

    def resume_last(self) -> int:
        """Re-enter the most recent run at its first incomplete step."""
        runs = sorted(self.settings.run_root.glob("run-*")) \
            if self.settings.run_root.exists() else []
        for run_dir in reversed(runs):
            task_file = run_dir / "task.json"
            if not task_file.exists():
                continue
            saved = json.loads(task_file.read_text())
            spec = TaskSpec(**saved["spec"])
            playbook = parse_playbook(saved["playbook"], str(task_file))
            print(f"↻ resuming {run_dir.name}: {spec.describe()}")
            return self._execute(playbook, spec, run_dir, resuming=True)
        print("no resumable run found")
        return 1

    def _adapter_for(self, repo: str):
        """The repo's registered adapter, or None (never raises)."""
        try:
            from ..adapters.base import AdapterRegistry

            return AdapterRegistry(self.settings.adapters_dir).resolve(
                name=repo.replace("-", "_"))
        except Exception:
            return None

    def _resolve_repo_path(self, repo: str) -> str:
        """REPO_PATHS first; fall back to the repo's adapter manifest (adapter zero
        declares repo.path), so runs work even without a .env in reach."""
        p = self.settings.repo_path(repo)
        if p:
            return str(p)
        adapter = self._adapter_for(repo)
        if adapter and adapter.repo_path:
            return adapter.repo_path
        return ""

    # -- built-ins ---------------------------------------------------------------
    def status(self) -> str:
        """Human-readable status of the current (or most recent) run: completed
        steps from progress.json, plus a rebase-phase line (module/test counts,
        CI result) when rebase_status.json exists. Falls back to the newest
        run-* dir when no run has executed this session."""
        if not self.last_run_dir:
            runs = sorted(self.settings.run_root.glob("run-*")) \
                if self.settings.run_root.exists() else []
            if not runs:
                return "no runs yet"
            self.last_run_dir = runs[-1]
        progress = self.last_run_dir / "progress.json"
        lines = []
        if progress.exists():
            done = list(json.loads(progress.read_text()).get("completed", {}))
            lines.append(f"{self.last_run_dir.name}: completed steps: {done}")
        else:
            lines.append(f"{self.last_run_dir.name}: no progress recorded")
        rebase_status = self.last_run_dir / "rebase_status.json"
        if rebase_status.exists():
            s = json.loads(rebase_status.read_text())
            mods = s.get("modules", {})
            tests = s.get("tests", {})
            lines.append(
                f"  rebase: phase={s.get('phase')} modules(done={mods.get('done', 0)} "
                f"failed={mods.get('failed', 0)}) tests(completed={tests.get('completed', 0)} "
                f"failed={len(tests.get('failed', []))}"
                + (f" current={tests.get('current')}" if tests.get("current") else "")
                + f") ci={s.get('ci_result') or '-'}"
            )
        return "\n".join(lines)

    def logs(self, n: int = 20) -> str:
        """Return the last `n` lines of the current run's run_trace.jsonl, or a
        placeholder string when there is no run / no trace yet."""
        if not self.last_run_dir:
            return "no runs yet"
        tracefile = self.last_run_dir / "run_trace.jsonl"
        if not tracefile.exists():
            return "no trace"
        return "".join(tracefile.read_text().splitlines(keepends=True)[-n:])

    def playbooks(self) -> str:
        """One line per registered playbook (name@version, status, task kinds),
        or "(none)" when the store is empty."""
        return "\n".join(
            f"{p.name}@{p.version} [{p.status}] kinds={p.task_kinds}"
            for p in self.store.all()
        ) or "(none)"
