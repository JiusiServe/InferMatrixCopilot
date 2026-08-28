"""The `Copilot` orchestrator: NL-resolved TaskSpec → plan (reuse > adapt >
generate) → plan-review gate → executor, plus the compound-command queue,
resume, and the /status /logs /playbooks built-ins.

This is the orchestration core; the argparse/REPL wiring lives in `entry.py` and
the pure formatters in `utils.py`.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import NamedTuple

import yaml

from ..config import Settings, TierNotConfiguredError
from ..engine.executor import Executor
from ..engine.lifecycle import RunLock, RunLockHeld, run_guarded
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


def _mode_review_context(playbook, spec) -> str:
    """Plan-review context for MODE-AWARE playbooks: the reviewer sees the
    raw yaml's FULL step list, but the `when:` gates resolve against the
    ALREADY-RESOLVED mode (`resolve_effective_mode` runs before the review
    gate) — without this context a report-only plan looks like it runs its
    write/push steps and gets spuriously blocked. The active-step set is
    the same mechanical truth the executor computes, never prose."""
    if not getattr(playbook, "mode_aware", False):
        return ""
    mode = str((getattr(spec, "params", None) or {})
               .get("rebase_mode", "") or "")
    if not mode:
        return ""
    from ..engine.executor import _eval_when
    from ..rebase_engine.modes import mode_state_flags

    flags = {"task_spec": {}, **mode_state_flags(mode)}
    active = [s.get("id", s.get("step", "?"))
              for s in playbook_to_doc(playbook).get("steps", [])
              if "when" not in s or _eval_when(s["when"], flags)]
    repo = str(getattr(spec, "repo", "") or "")
    repo_line = (f"\nTarget repo (authoritative): {repo!r} — bound at "
                 "runtime from the TaskSpec; the yaml `repos:` list is a "
                 "planner RECALL FILTER where empty means repo-neutral, "
                 "never untargeted." if repo else "")
    return (f"\n\nResolved mode context (authoritative): "
            f"rebase_mode={mode}. Under this mode the `when:` gates run "
            f"ONLY these steps: {active}. Every other listed step is "
            "statically gated OFF for this run — judge the plan for THIS "
            "mode's step set."
            + repo_line +
            "\nWrite/push governance (authoritative): the mode's own "
            "push/CI steps are governed at runtime by the push-gate "
            "ruling, guard_push, and the ALLOW_PUSH env double-gate — "
            "the task tier does not forbid steps this mode activates.")


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
        # provider-registry seam: a real llm.LLM under backend "api"
        # (byte-identical), a HarnessLLM adapter under a harness backend
        from ..providers import llm_for

        self.llm = llm_for(self.settings)
        self.registry = register_builtin_steps(StepRegistry())
        self.store = PlaybookStore(self.settings.playbooks_dir, self.registry)
        self.planner = Planner(self.store, self.registry)
        self.last_run_dir: Path | None = None
        # why the last execution stopped, when it stopped blocked — read by
        # `_execute_reserved_locked`, which owns the terminal run_status write
        self.last_blocked_reason: str = ""

    # -- planning ---------------------------------------------------------------
    def resolve(self, spec: TaskSpec) -> Resolution:
        """Resolve `spec` to a Resolution via the planner, passing the repo's
        capability set so the planner only reuses playbooks the target supports.
        Capabilities come from the repo's adapter (if any), plus `repo.path` when
        a path is resolvable even without a adapter (REPO_PATHS works adapter-less)."""
        # Only genuine adapter ABSENCE takes the unknown-capabilities
        # compatibility path — a malformed/unreadable KNOWN adapter must fail
        # closed here, not fail open into capabilities=None and recall a
        # playbook whose requirements were never established.
        from ..adapters.base import AdapterError, AdapterNotFound, AdapterRegistry
        adapter_name = spec.repo.replace("-", "_")
        try:
            adapter = AdapterRegistry(self.settings.adapters_dir).resolve(
                name=adapter_name)
        except AdapterNotFound:
            # the registry resolves by DECLARED manifest name and skips
            # manifest-less directories — so "not found" alone does not
            # prove absence. Only a genuinely absent directory is the
            # v1-compatible path; an existing directory that failed to
            # load/resolve (deleted manifest, wrong name:) fails closed.
            if (Path(self.settings.adapters_dir) / adapter_name).exists():
                raise AdapterError(
                    f"adapter directory {adapter_name!r} exists but did not "
                    "load/resolve (missing manifest.yaml or mismatched "
                    "name:) — refusing to plan with unknown capabilities")
            adapter = None                # absence: v1-compatible
        except FileNotFoundError:
            adapter = None                # no adapters directory at all
        if adapter is None:
            # No adapter means capabilities are UNKNOWN, not zero — the
            # store's requires-filter (now covering exact-repo playbooks too)
            # skips on None, keeping adapter-less setups v1-compatible
            # instead of silently dropping every playbook with a `requires:`.
            if self._repo_path_for(spec):
                return self.planner.resolve(spec, capabilities=None)
            return self.planner.resolve(spec, capabilities=set())
        capabilities = set(adapter.capabilities)
        if self._repo_path_for(spec):  # REPO_PATHS works adapter-less
            capabilities.add("repo.path")
        return self.planner.resolve(spec, capabilities=capabilities)

    def _plan_review_gate(self, resolution: Resolution, spec: TaskSpec,
                          assume_yes: bool) -> bool:
        """Inline Plan-Review for adapted/generated plans. LLM verdict shown in
        the session; block stops. A non-`lgtm` verdict is only ever *surfaced*
        — the human `[y/N]` is what actually gates it — so when `--yes` removes
        that human, the same verdict must stop the run instead
        (`ReviewVerdict.passing`, SPEC C6: only `lgtm` passes)."""
        if not resolution.requires_review:
            return True
        doc = yaml.safe_dump(playbook_to_doc(resolution.playbook), sort_keys=False)
        task_text = spec.describe() + _mode_review_context(
            resolution.playbook, spec)
        verdict = run_plan_review(self.llm, playbook_doc=doc,
                                  task=task_text,
                                  model=self.settings.reviewer)
        if verdict.verdict != "unavailable":
            print(f"  plan review: {verdict.verdict}"
                  + (f" — {verdict.critiques}" if verdict.critiques else ""))
        if verdict.verdict == "block":
            print("✋ plan blocked by reviewer.")
            return False
        if verdict.passing:
            return True
        # Everything below is non-passing: `revise`, or `unavailable`. Both used
        # to return True on the strength of a confirmation that `--yes` had
        # already deleted, so an unattended run executed an unvetted plan on an
        # unread verdict. Measured on the release matrix: an unparseable review
        # let three of four backends run a pr-rebase plan through to its push
        # gate, while the one backend whose reviewer parsed cleanly BLOCKED the
        # very same plan.
        if assume_yes:
            reason = ("no reviewer LLM" if verdict.verdict == "unavailable"
                      else f"plan review returned {verdict.verdict}")
            print(f"✋ {reason} and --yes leaves no human to gate it — blocked.")
            return False
        if verdict.verdict == "unavailable":
            print("  ⚠ no reviewer LLM — your confirmation is the plan-review gate")
        return True  # revise/unavailable, surfaced to the user before their confirm

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
        # tier preflight (plan v2): backend availability is DEPLOYMENT state,
        # so it is enforced here at resolution — before the echo, the gate,
        # and the run dir — never discovered as a BLOCKED step minutes in.
        try:
            tier_target = self.settings.tier_target(spec.mode)
        except TierNotConfiguredError as exc:
            print(style("✋ cannot run: ", "red", "bold") + str(exc))
            return BLOCKED_EXIT

        # Mode governance (Rev 8 §2.1): for mode-aware playbooks the ONE
        # authority is params.rebase_mode, resolved + WRITTEN BACK before the
        # plan echo and the confirmation gate (spec.report_only reflects the
        # canonical mode, so every TaskSpec-derived consumer sees one truth).
        # The locked delegating playbook does not declare mode_aware and is
        # untouched — byte-identical behavior.
        if getattr(resolution.playbook, "mode_aware", False):
            from ..rebase_engine.modes import (ModeConflictError,
                                               resolve_effective_mode)
            try:
                resolve_effective_mode(spec)
            except ModeConflictError as exc:
                print(style("✋ blocked: ", "red", "bold") + str(exc))
                return BLOCKED_EXIT

        print(style("→ task: ", "bold", "cyan") + spec.describe())
        print(style("→ plan: ", "bold", "magenta") + f"{resolution.mode} {resolution.playbook.name}"
              f"@{resolution.playbook.version} ({resolution.playbook.status}) "
              f"steps={[s.step for s in resolution.playbook.steps]}")
        for note in resolution.notes:
            print(f"  · {note}")
        print(style("→ path: ", "bold", "cyan")
              + f"{spec.mode} · agent-model={tier_target.model}"
                f" @ {tier_target.host}")
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
            "invocation_id": os.environ.get("IMX_INVOCATION_ID", ""),
        }, indent=2))
        return self._execute(resolution.playbook, spec, run_dir,
                             resolution_mode=resolution.mode, tier=resolution.tier)

    def run_playbook(self, name: str, *, params: dict | None = None,
                     report_only: bool = False, assume_yes: bool = False,
                     plan_only: bool = False) -> int:
        """Explicit playbook override — the only way to execute a CANDIDATE
        (candidates stay planner-invisible). Always treated as requiring
        review + confirmation."""
        playbook = self.store.get(name)
        if playbook is None:
            print(f"✋ no playbook named {name!r} (see /playbooks)")
            return BLOCKED_EXIT
        kind = playbook.task_kinds[0]
        # lift target params into first-class spec fields so the explicit
        # playbook path can address a PR/issue/repo like every other surface
        params = dict(params or {})
        pr = params.pop("pr", None)
        issue = params.pop("issue", None)
        repo = str(params.pop("repo", "") or self.settings.default_repo)
        try:
            pr = int(pr) if pr is not None else None
            issue = int(issue) if issue is not None else None
        except (TypeError, ValueError):
            print("✋ pr/issue task params must be integers")
            return BLOCKED_EXIT
        if repo not in (self.settings.repo_paths or {repo: ""}):
            print(f"✋ unknown repo alias {repo!r} "
                  f"(known: {', '.join(sorted(self.settings.repo_paths or {}))})")
            return BLOCKED_EXIT
        spec = TaskSpec(kind=kind, repo=repo, pr=pr, issue=issue,
                        report_only=report_only, params=params)
        from ..intent import validate_spec
        err = validate_spec(spec)
        if err:
            print(f"✋ {err} (pass e.g. --task-param pr=5134)")
            return BLOCKED_EXIT
        # mode governance applies to explicit invocations too — the ONLY
        # way to run the candidate v3/v1 playbooks today (Rev 8 §2.1)
        if getattr(playbook, "mode_aware", False):
            from ..rebase_engine.modes import (ModeConflictError,
                                               resolve_effective_mode)
            try:
                resolve_effective_mode(spec)
            except ModeConflictError as exc:
                print(style("✋ blocked: ", "red", "bold") + str(exc))
                return BLOCKED_EXIT
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
            "invocation_id": os.environ.get("IMX_INVOCATION_ID", ""),
        }, indent=2))
        return self._execute(playbook, spec, run_dir,
                             resolution_mode="explicit", tier=spec.tier)

    def _execute(self, playbook, spec: TaskSpec, run_dir: Path, *,
                 resolution_mode: str = "resume", tier: str = "?",
                 resuming: bool = False, held_lock: RunLock | None = None) -> int:
        """Run a resolved `playbook` to completion in `run_dir`: init tracing +
        notifier, seed the shared state (repo path, push policy, protected
        branches / high-risk modules from the adapter when present), drive the
        Executor, then print per-step marks, optional run metrics, and the final
        status. `resuming` seeds the state so steps can pick up where they left
        off. Returns the exit code (0 done, BLOCKED_EXIT blocked, else 1), and
        records `last_blocked_reason` for the reserved-run caller, which has only
        the code but owns the terminal `run_status.json` write."""
        self.last_run_dir = run_dir
        self.last_blocked_reason = ""
        lock = held_lock
        if lock is None:
            try:
                # First, before any trace/status write: a losing concurrent
                # invocation (second --resume) must leave the active run's
                # artifacts completely untouched. execute_reserved holds the
                # lock across its whole lifecycle and passes it in instead.
                lock = RunLock(run_dir).acquire()
            except RunLockHeld as exc:
                print(style("✋ ", "red", "bold") + str(exc))
                return BLOCKED_EXIT
        # Per-repo knowledge lock, SHARED, held for the run's lifetime:
        # never contends with other runs; it exists so the knowledge
        # migration's EXCLUSIVE acquire can prove no potential store
        # writer is alive (and so no run starts mid-migration).
        knowledge_lock = None
        if spec.repo:
            from ..memory.paths import (KnowledgeLockHeld,
                                        KnowledgePaths,
                                        KnowledgeRunLock,
                                        KnowledgeStateError)
            try:
                knowledge_lock = KnowledgeRunLock(
                    KnowledgePaths.resolve(self.settings, spec.repo)
                    .knowledge_run_lock).acquire_shared()
            except (KnowledgeLockHeld, KnowledgeStateError) as exc:
                # BOTH refusals take the terminal protocol: an invalid
                # activation marker (KnowledgeStateError) must exit
                # blocked/3 with the run lock RELEASED, never escape as
                # a traceback that leaves the lock held in a long-lived
                # process (PR-boundary F4)
                if held_lock is None:
                    lock.release()
                print(style("✋ ", "red", "bold") + str(exc))
                return BLOCKED_EXIT
        try:
            from .. import tracing
            tracing.init(run_dir.name, run_dir / "trace.jsonl")
            # Stamp the workflow into the span file itself, so a trace lifted out of
            # its run directory still says which playbook and task produced it.
            tracing.run_meta(playbook=f"{playbook.name}@{playbook.version}",
                             task_kind=spec.kind, repo=spec.repo, tier=tier,
                             mode=spec.mode, resolution=resolution_mode,
                             report_only=spec.report_only, post=spec.post,
                             resuming=resuming, params=spec.params)
            trace = RunTrace(run_dir / "run_trace.jsonl")
            notifier = Notifier(self.settings, run_dir, trace, run_dir.name)
            trace.record("task", spec=spec.model_dump(), resolution=resolution_mode,
                         playbook=playbook.name, tier=tier)
            state: dict = {
                "task_spec": spec.model_dump(),
                "repo_path": self._repo_path_for(spec),
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
            # run_guarded finalizes inside the event loop: playbooks that
            # register run finalizers (lifecycle.register_finalizer) get
            # teardown on every exit path. Nothing registered == no-op.
            outcome = asyncio.run(
                run_guarded(executor.run(playbook, state), run_dir))

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
                self.last_blocked_reason = str(outcome.blocked_reason or "")
                print(style("  ⚠ ", "yellow", "bold") + f"{outcome.blocked_reason}\n  see {run_dir / 'ESCALATION.md'}")
                return BLOCKED_EXIT
            return 0 if outcome.status == "done" else 1
        finally:
            if knowledge_lock is not None:
                knowledge_lock.release()
            if held_lock is None:
                lock.release()

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
            saved = json.loads(task_file.read_text(encoding="utf-8"))
            spec = TaskSpec(**saved["spec"])
            playbook = parse_playbook(saved["playbook"], str(task_file))
            try:  # tier preflight holds on re-entry too (deployment state
                # may have changed since the run was created)
                self.settings.tier_target(spec.mode)
            except TierNotConfiguredError as exc:
                print(style("✋ cannot resume: ", "red", "bold") + str(exc))
                return BLOCKED_EXIT
            print(f"↻ resuming {run_dir.name}: {spec.describe()}")
            return self._execute(playbook, spec, run_dir, resuming=True)
        print("no resumable run found")
        return 1

    # -- MCP surface (reserve + child execute) --------------------------------
    # These support the start/poll MCP server (mcp_server.py). The CLI path
    # (run_task/run_playbook) is deliberately untouched: it still gates BEFORE
    # creating a run dir, so an aborted plan leaves no directory. Reservation
    # (dir before plan) is an MCP-only shape whose blocked/failed outcome is a
    # terminal poll record, not litter.
    _RUN_ID_RE = re.compile(r"^run-\d{8}-\d{6}-[0-9a-f]{6}$")

    @staticmethod
    def _new_run_id() -> str:
        """A fresh unique run id (`run-<ts>-<uuid6>`; same format the CLI uses)."""
        return f"run-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"

    def _contained_run_dir(self, run_id: str, *, must_exist: bool = True) -> Path:
        """Validate `run_id` and resolve it to a directory strictly contained
        under `run_root` — rejecting path traversal from an untrusted MCP arg.
        Raises ValueError on a bad pattern, an escape, or (unless
        `must_exist=False`) a missing run.

        `must_exist=False` is for the poll path, which must distinguish a
        well-formed id whose run this server has never heard of — answered as
        `state: unknown` so a client can tell "lost" from "still running" — from
        a malformed or escaping id, which stays an error."""
        if not self._RUN_ID_RE.match(run_id or ""):
            raise ValueError(f"invalid run_id: {run_id!r}")
        root = self.settings.run_root.resolve()
        run_dir = (self.settings.run_root / run_id).resolve()
        if run_dir.parent != root:
            raise ValueError(f"run_id escapes run_root: {run_id!r}")
        if must_exist and not run_dir.exists():
            raise ValueError(f"no such run: {run_id!r}")
        return run_dir

    def reserve_run(self, spec: TaskSpec, *, owner_server_id: str,
                    owner_server_pid: int) -> str:
        """MCP-only: reserve a run and return its id **without** planning or
        executing (no LLM), so the tool call returns in ms and the caller polls.
        Persists `request.json` (0600) + an initial `queued` `run_status.json`
        stamped with the owning server; planning happens later in the child.

        A `repo_path` on the spec is authorized and canonicalized HERE, so the
        persisted request names one immutable checkout for the life of the run.
        The child re-authorizes it anyway — `request.json` is untrusted — but
        freezing it at reservation is what stops two concurrent per-call repos
        from racing through shared settings, which is how the deleted
        `configure_strict_repo` worked."""
        from .. import run_status as rs
        from ..mcp_policy import authorize_repo_path

        if spec.repo_path:
            spec = spec.model_copy(update={"repo_path": authorize_repo_path(
                spec.repo, spec.repo_path, self.settings)})
        run_id = self._new_run_id()
        run_dir = self.settings.run_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        req = run_dir / "request.json"
        req.write_text(json.dumps(spec.model_dump(), indent=2), encoding="utf-8")
        try:  # least-privilege perms; advisory only against same-user tampering
            os.chmod(req, 0o600)
        except OSError:
            pass
        rs.init_queued(run_dir, run_id=run_id, owner_server_id=owner_server_id,
                       owner_server_pid=owner_server_pid)
        return run_id

    def execute_reserved(self, run_id: str) -> int:
        """MCP-only child entry (subprocess, stdout -> console.log). Writes its
        own pid FIRST (single-writer invariant), **re-enforces** the read-only
        MCP policy on the persisted request (request.json is untrusted — a host
        could have rewritten it), plans, then executes, driving
        `run_status.json` planning -> running -> terminal. Returns the exit code."""
        from ..mcp_policy import enforce_mcp_policy

        return self._execute_reserved(run_id, enforce_mcp_policy)

    def execute_strict_reserved(self, run_id: str) -> int:
        """Execute a reserved Strict review using the previous Eco workflow."""
        from ..mcp_policy import enforce_strict_review_policy

        return self._execute_reserved(run_id, enforce_strict_review_policy)

    def _execute_reserved(self, run_id: str, policy) -> int:
        """Shared reserved-run executor with an authoritative child policy."""
        run_dir = self._contained_run_dir(run_id)
        try:
            # Lock the whole reserved-run lifecycle before the first status
            # write: a duplicate child must not overwrite child_pid, flip
            # run_status.json through PLANNING, or mark the active run
            # BLOCKED while the winning process is still executing.
            lock = RunLock(run_dir).acquire()
        except RunLockHeld as exc:
            print(style("✋ ", "red", "bold") + str(exc))
            return BLOCKED_EXIT
        try:
            return self._execute_reserved_locked(run_dir, lock, policy)
        finally:
            lock.release()

    def _execute_reserved_locked(self, run_dir: Path, lock: RunLock,
                                 policy) -> int:
        """The body of `_execute_reserved`, run while holding the run lock."""
        from .. import run_status as rs
        from ..mcp_policy import PolicyError

        rs.mark_child_started(run_dir, child_pid=os.getpid(), state=rs.PLANNING)
        try:
            raw = json.loads((run_dir / "request.json").read_text(encoding="utf-8"))
            spec = policy(
                raw, allowed_repos=self.settings.mcp_allowed_repos,
                settings=self.settings)
        except (PolicyError, OSError, json.JSONDecodeError, ValueError) as exc:
            rs.mark(run_dir, rs.FAILED, note=f"policy/request rejected: {exc}")
            return 1
        try:
            resolution = self.resolve(spec)
        except PlanningError as exc:
            rs.mark(run_dir, rs.BLOCKED, note=f"cannot plan: {exc}")
            return BLOCKED_EXIT
        try:  # tier preflight is re-enforced in the MCP child (authoritative)
            self.settings.tier_target(spec.mode)
        except TierNotConfiguredError as exc:
            rs.mark(run_dir, rs.BLOCKED, note=f"cannot run: {exc}")
            return BLOCKED_EXIT
        (run_dir / "task.json").write_text(json.dumps({
            "spec": spec.model_dump(),
            "playbook": playbook_to_doc(resolution.playbook),
        }, indent=2))
        rs.mark(run_dir, rs.RUNNING)
        try:
            code = self._execute(resolution.playbook, spec, run_dir,
                                 resolution_mode=resolution.mode, tier=resolution.tier,
                                 held_lock=lock)
        except Exception as exc:  # a crash still leaves a terminal record
            rs.mark(run_dir, rs.FAILED, note=f"{type(exc).__name__}: {exc}")
            raise
        # Carry WHY it stopped into the terminal record. An MCP client only ever
        # sees `run_status.json`, and a bare `blocked` with no note gives it
        # nothing to distinguish a stale-head refusal from a missing tier or a
        # failed checkout — the reason was previously printed to the child's
        # console and discarded.
        rs.mark(run_dir, {0: rs.DONE, BLOCKED_EXIT: rs.BLOCKED}.get(code, rs.FAILED),
                note=self.last_blocked_reason if code == BLOCKED_EXIT else "")
        return code

    def _adapter_for(self, repo: str):
        """The repo's registered adapter, or None (never raises)."""
        try:
            from ..adapters.base import AdapterRegistry

            return AdapterRegistry(self.settings.adapters_dir).resolve(
                name=repo.replace("-", "_"))
        except Exception:
            return None

    def _repo_path_for(self, spec: TaskSpec) -> str:
        """The checkout THIS spec runs against: its frozen `repo_path` first,
        else the ambient resolution by alias.

        Every place a run learns its checkout must agree. Resolution derives the
        `repo.path` capability from this, and `_execute` seeds `state` from it:
        with an explicit path but no ambient `REPO_PATHS` and no adapter
        `repo.path`, an alias-only lookup would drop the capability and fail to
        resolve a playbook that requires it — while a perfectly valid checkout
        sat in the spec. With both configured and differing, planning would
        evaluate one checkout and execution would run against another."""
        return spec.repo_path or self._resolve_repo_path(spec.repo)

    def _resolve_repo_path(self, repo: str) -> str:
        """REPO_PATHS first; fall back to the repo's adapter manifest (adapter zero
        declares repo.path), so runs work even without a .env in reach.

        Alias-only: callers that hold a TaskSpec want `_repo_path_for`, which
        honors a frozen per-run path."""
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
            done = list(json.loads(progress.read_text(encoding="utf-8")).get("completed", {}))
            lines.append(f"{self.last_run_dir.name}: completed steps: {done}")
        else:
            lines.append(f"{self.last_run_dir.name}: no progress recorded")
        rebase_status = self.last_run_dir / "rebase_status.json"
        if rebase_status.exists():
            s = json.loads(rebase_status.read_text(encoding="utf-8"))
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
        return "".join(tracefile.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)[-n:])

    def playbooks(self) -> str:
        """One line per registered playbook (name@version, status, task kinds),
        or "(none)" when the store is empty."""
        return "\n".join(
            f"{p.name}@{p.version} [{p.status}] kinds={p.task_kinds}"
            for p in self.store.all()
        ) or "(none)"
