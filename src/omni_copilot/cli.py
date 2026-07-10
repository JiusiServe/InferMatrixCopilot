"""omni-copilot — conversational CLI (design §3.Y, phases A+B).

REPL + one-shot (-p). NL -> intent -> TaskSpec(s) (echoed; write/push tasks
need confirmation) -> inline plan review for adapted/generated plans ->
planner (reuse > adapt > generate) -> executor. Compound commands ("rebase
pr 12, then review it") become an ordered task queue. Built-ins: /status
/logs /playbooks /resume /quit. Blocked runs exit 3.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

import yaml

from .config import Settings
from .engine.steps import register_builtin_steps
from .engine.executor import Executor
from .engine.planner import Planner, PlanningError, Resolution
from .engine.registry import StepRegistry
from .intent import parse_intents
from .llm import LLM
from .notify import BLOCKED_EXIT, Notifier
from .playbooks.store import PlaybookStore, parse_playbook, playbook_to_doc
from .review.reviewer import run_plan_review
from .run_trace import RunTrace
from .push import PushPolicy
from .task_spec import TaskSpec
from .ui import style


class Copilot:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.llm = LLM(self.settings)
        self.registry = register_builtin_steps(StepRegistry())
        self.store = PlaybookStore(self.settings.playbooks_dir, self.registry)
        self.planner = Planner(self.store, self.registry)
        self.last_run_dir: Path | None = None

    # -- planning ---------------------------------------------------------------
    def resolve(self, spec: TaskSpec) -> Resolution:
        plugin = self._plugin_for(spec.repo)
        capabilities = set(plugin.capabilities) if plugin is not None else set()
        if self._resolve_repo_path(spec.repo):  # REPO_PATHS works plugin-less
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
                          force_confirm: bool = False) -> int | None:
        """Plan-review gate + [y/N] confirm (concision K6). Returns an exit code
        to return, or None to proceed. Confirm fires for confirm_required or a
        review-requiring/explicit plan, unless assume_yes."""
        if not self._plan_review_gate(resolution, spec, assume_yes):
            return BLOCKED_EXIT
        need = force_confirm or spec.confirm_required or resolution.requires_review
        if need and not assume_yes:
            if input(f"{prompt} [y/N] ").strip().lower() not in ("y", "yes"):
                print("aborted.")
                return 1
        return None

    # -- execution -----------------------------------------------------------------
    def run_task(self, spec: TaskSpec, *, assume_yes: bool = False,
                 plan_only: bool = False) -> int:
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

        code = self._gate_and_confirm(resolution, spec, assume_yes)
        if code is not None:
            return code

        run_id = f"run-{time.strftime('%Y%m%d-%H%M%S')}"
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
        from .engine.planner import Resolution

        resolution = Resolution(mode="explicit", playbook=playbook,
                                tier=spec.tier, requires_review=True)
        code = self._gate_and_confirm(
            resolution, spec, assume_yes, force_confirm=True,
            prompt=f"Run {playbook.status} playbook '{name}'?")
        if code is not None:
            return code
        run_id = f"run-{time.strftime('%Y%m%d-%H%M%S')}"
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
        self.last_run_dir = run_dir
        from . import tracing
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
        plugin = self._plugin_for(spec.repo)
        if plugin is not None:
            # repo knowledge from the plugin, not core settings (v2 P0 fix #5)
            state["protected_branches"] = plugin.protected_branches
            if plugin.high_risk_modules:
                state["high_risk_modules"] = plugin.high_risk_modules
        executor = Executor(self.registry, self.settings, run_dir=run_dir,
                            trace=trace, llm=self.llm, notifier=notifier)
        outcome = asyncio.run(executor.run(playbook, state))

        if self.settings.metrics_enabled:
            try:  # metrics are facts about the run; never let them break it
                from .metrics import collect_run_metrics
                m = collect_run_metrics(run_dir, self.settings, outcome.status)
                cost, risk = m["cost"], m["risk"]
                catq = m["catq"]
                print(f"  metrics: usd≈{cost['usd']:.2f} "
                      f"{cost['minutes']:.1f}min S={risk['safety_multiplier']:.2f}"
                      + (f" CATQ={catq:.3f}"
                         + ("*" if m["quality"]["partial"] else "")
                         if catq is not None else "")
                      + f"  ({run_dir / 'metrics.json'})")
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

    def _plugin_for(self, repo: str):
        """The repo's registered plugin, or None (never raises)."""
        try:
            from .plugins.base import PluginRegistry

            return PluginRegistry(self.settings.plugins_dir).resolve(
                name=repo.replace("-", "_"))
        except Exception:
            return None

    def _resolve_repo_path(self, repo: str) -> str:
        """REPO_PATHS first; fall back to the repo's plugin manifest (plugin zero
        declares repo.path), so runs work even without a .env in reach."""
        p = self.settings.repo_path(repo)
        if p:
            return str(p)
        plugin = self._plugin_for(repo)
        if plugin and plugin.repo_path:
            return plugin.repo_path
        return ""

    # -- built-ins ---------------------------------------------------------------
    def status(self) -> str:
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


def _handle_line(copilot: Copilot, line: str, assume_yes: bool,
                 plan_only: bool) -> int | None:
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
    if line == "/resume":
        return copilot.resume_last()

    results = parse_intents(line, llm=copilot.llm,
                            default_repo=copilot.settings.default_repo,
                            model=copilot.settings.intent)
    unclear = [r for r in results if r.needs_clarification]
    if unclear:
        print(f"? {unclear[0].clarify}")
        return None
    return copilot.run_queue([r.spec for r in results],
                             assume_yes=assume_yes, plan_only=plan_only)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omni-copilot",
                                     description="Conversational repo-maintenance copilot")
    parser.add_argument("-p", "--prompt", help="one-shot natural-language command")
    parser.add_argument("--yes", action="store_true",
                        help="skip confirmation prompts (headless)")
    parser.add_argument("--plan-only", action="store_true",
                        help="resolve and print the plan without executing")
    parser.add_argument("--resume", action="store_true",
                        help="resume the most recent run at its first incomplete step")
    parser.add_argument("--playbook",
                        help="run a specific playbook by name (incl. candidates, "
                             "e.g. repo-rebase-native for validation)")
    parser.add_argument("--report-only", action="store_true",
                        help="with --playbook: read-only variant of the task")
    parser.add_argument("--task-param", action="append", default=[],
                        metavar="KEY=VALUE",
                        help="with --playbook: task param (repeatable), "
                             "e.g. --task-param local_ci_only=true")
    parser.add_argument("--no-chat", action="store_true",
                        help="use the plain command REPL instead of the "
                             "conversational interface")
    args = parser.parse_args(argv)

    copilot = Copilot()

    if args.resume:
        return copilot.resume_last()
    if args.playbook:
        params: dict = {}
        for kv in args.task_param:
            key, _, raw = kv.partition("=")
            value: object = raw
            if raw.lower() in ("true", "false"):
                value = raw.lower() == "true"
            elif raw.isdigit():
                value = int(raw)
            params[key.strip()] = value
        return copilot.run_playbook(args.playbook, params=params,
                                    report_only=args.report_only,
                                    assume_yes=args.yes, plan_only=args.plan_only)
    if args.prompt:
        code = _handle_line(copilot, args.prompt, args.yes, args.plan_only)
        return int(code) if code not in (None, -1) else 0

    # Interactive: conversational chat (Claude-Code-style) when an LLM is
    # configured; plain command REPL otherwise / with --no-chat.
    if copilot.llm.available and not args.no_chat:
        from .chat import chat_repl

        return chat_repl(
            copilot, assume_yes=args.yes,
            handle_builtin=lambda line: _handle_line(copilot, line, args.yes,
                                                     args.plan_only),
        )

    print("omni-copilot — natural-language repo maintenance. "
          "/status /logs /playbooks /resume /quit")
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
