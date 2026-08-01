"""repo-rebase v3 steps — thin, governed wrappers over `rebase_engine`
(assembly PR; the playbook is CANDIDATE until the validation gate).

Every handler is substate-first (durable, run-stamped), publishes consumed
keys via `state_updates`, and fails typed — the transition-table terminal
rows are enforced by `rebase.v3_finalize` (all-steps-ok + substate failures
⇒ BLOCKED, the reused needs-human exit 3; it runs AFTER the report step so
RUN_REPORT always exists when the run terminates needs-human)."""

from __future__ import annotations

import asyncio
import shlex
import weakref
from pathlib import Path
from typing import Mapping

import yaml

from ...rebase_engine import test_loop as tl
from ...rebase_engine import wheel as wheel_mod
from ...rebase_engine.modes import MODES, MUTATING_MODES, mode_state_flags
from ...rebase_engine.phase1_steps import Phase1Config, run_commit_assignment
from ...rebase_engine.push_gate import evaluate_push_gate
from ...rebase_engine.substate import Substate
from ...rebase_engine.test_manifest import ManifestSpec, build_manifest
from ...rebase_engine.testing_env import scrubbed_agent_env
from ...scopes import PathScope, ToolScope
from ..step import FailureKind, StepContext, StepResult
from ._common import require_repo, step


def _task_params(ctx: StepContext) -> dict:
    spec = ctx.state.get("task_spec") or {}
    return (spec.get("params") if isinstance(spec, dict) else {}) or {}


def _adapter_manifest(ctx: StepContext) -> dict | StepResult:
    repo = (ctx.state.get("task_spec") or {}).get("repo", "")
    path = Path(ctx.settings.adapters_dir) / repo.replace("-", "_") / \
        "manifest.yaml"
    if not path.is_file():
        return StepResult(False, FailureKind.BLOCKED,
                          f"no adapter manifest for {repo!r} — the v3 "
                          "pipeline is adapter-data driven")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _substate(ctx: StepContext) -> Substate:
    return Substate(ctx.run_dir, ctx.state.get("run_id")
                    or ctx.run_dir.name)


def _parse_env_pairs(env_str: str) -> dict[str, str]:
    """The manifest job's `env` field ("K=V K2=V2", from stripped `export`
    lines) as a dict for `TestJob.env` — dropping a job's declared env would
    change what the test actually exercises."""
    out: dict[str, str] = {}
    try:
        parts = shlex.split(env_str or "")
    except ValueError:
        parts = (env_str or "").split()
    for part in parts:
        if "=" in part:
            k, v = part.split("=", 1)
            if k:
                out[k] = v
    return out


def manifest_job_to_test_job(j: Mapping):
    """THE production conversion from a built-manifest job dict to the
    runner's `TestJob` — one authority, used by the v3 test loop and pinned
    by the tier-3 shell-golden parity suite (a test-local re-implementation
    would let the two drift apart unnoticed)."""
    from ...testing.runner import TestJob
    return TestJob(key=j["slug"], command=j["command"],
                   timeout_sec=j["timeout_sec"], min_gpus=j["min_gpus"],
                   env=_parse_env_pairs(j.get("env", "")),
                   setup=j.get("setup", ""))


def _tier_client(ctx: StepContext):
    """The run's agent backend via `Settings.tier_target` — the ONLY place a
    tier's model may pair with an endpoint and credential. Returns
    `(client, target)` or a BLOCKED StepResult (with a `capability_gap`
    trace) when no credential is configured for the resolved tier."""
    from ...config import TierNotConfiguredError
    mode = (ctx.state.get("task_spec") or {}).get("mode", "eco")
    try:
        target = ctx.settings.tier_target(mode)
    except TierNotConfiguredError as exc:
        return StepResult(False, FailureKind.BLOCKED, str(exc))
    if not target.api_key:
        ctx.trace.record("capability_gap", capability="rebase.module_agent",
                         detail=f"no API key for tier target {target.source} "
                                "— rebase agents cannot run")
        return StepResult(False, FailureKind.BLOCKED,
                          "rebase agents need a configured Anthropic-"
                          "compatible backend for the resolved tier")
    from anthropic import AsyncAnthropic
    kwargs: dict = {"api_key": target.api_key}
    if target.base_url:
        kwargs["base_url"] = target.base_url
    return AsyncAnthropic(**kwargs), target


def _target_venv(manifest: dict) -> str:
    """The TARGET repo's virtualenv from adapter data (env-expanded).
    Empty = not configured."""
    from ...adapters.base import expand_path
    return expand_path((manifest.get("repo") or {}).get("venv", ""))


def _target_test_env(ctx: StepContext, manifest: dict,
                     *, pythonpath_prepend: str | None = None) -> dict:
    """The env for TARGET-repo subprocesses (tests, precommit, wheel
    installs): inherit-plus-overlay with the target venv on PATH, the
    host's CUDA selection, and HF_HOME — raw manifest commands like
    `pytest ...` must resolve inside the target repo's runtime, never the
    copilot's own virtualenv."""
    import os
    from ...testing.env_plan import build_subprocess_env
    venv = _target_venv(manifest)
    return build_subprocess_env(
        venv=Path(venv) if venv else None,
        cuda_visible_devices=os.environ.get("CUDA_VISIBLE_DEVICES"),
        hf_home=os.environ.get("HF_HOME"),
        pythonpath_prepend=pythonpath_prepend)


def _agent_shell_env(ctx: StepContext, manifest: dict, repo_root: str,
                     adapter_dir: Path, *, gpu_mutex: bool = True) -> dict:
    """The env for AGENT shells (`run_shell` + everything it spawns): the
    PR1 credential scrub over the process env, then the TARGET runtime
    overlay (venv PATH/VIRTUAL_ENV, host CUDA selection, HF_HOME) and the
    `imx-omni-pytest` contract variables — without IMX_TARGET_REPO/
    IMX_LOG_DIR the mandated pytest wrapper exits immediately, and without
    the venv overlay agent verification runs against the copilot's own
    environment."""
    import os
    from ...testing.env_plan import build_subprocess_env
    venv = _target_venv(manifest)
    # HF token only on the manifest's EXPLICIT opt-in (Rev 8 §4:
    # validation.requires_hf_token — gated-model verification needs it;
    # every other adapter keeps the token scrubbed)
    keep_hf = bool((manifest.get("validation") or {})
                   .get("requires_hf_token"))
    env = build_subprocess_env(
        base=scrubbed_agent_env(keep_hf_token=keep_hf),
        venv=Path(venv) if venv else None,
        cuda_visible_devices=os.environ.get("CUDA_VISIBLE_DEVICES"),
        hf_home=os.environ.get("HF_HOME"))
    env["IMX_TARGET_REPO"] = str(repo_root)
    env["IMX_LOG_DIR"] = str(ctx.run_dir)
    env["IMX_ADAPTER_REBASE"] = str(adapter_dir / "rebase")
    if gpu_mutex:
        # Phase-2 module agents serialize every wrapper invocation on the
        # GPU lock (parent contract)
        env["IMX_GPU_MUTEX"] = "1"
    return env


def _build_backends(ctx: StepContext, manifest: dict, repo: str, target):
    """The PRODUCTION `RebaseBackends`: plan review on the run's resolved
    tier backend, pytest/reproduce/precommit through the PR1 runner in the
    TARGET env, and the knowledge tools on the copilot stores (agents may
    only propose skills — governance preserved). Replaces the fail-closed
    `_unwired` defaults for live module/debug agents; an unavailable
    collaborator still answers with an explicit error dict, never a
    silent success. All handlers are SYNC (tool dispatch is synchronous
    inside the agent loop) — the reviewer uses its own sync client."""
    from ...memory import SkillStore
    from ...memory.debug_memory import DebugMemory
    from ...rebase_engine.plan_review import review_plan
    from ...rebase_engine.rebase_tools import RebaseBackends
    from ...testing.runner import TestJob, TestRunner
    repo_name = (ctx.state.get("task_spec") or {}).get("repo", "")
    reviewer_model = getattr(ctx.settings, "rebase_reviewer_model", "") \
        or target.model

    def request_plan_review(**kw) -> dict:
        from anthropic import Anthropic
        ckw: dict = {"api_key": target.api_key}
        if target.base_url:
            ckw["base_url"] = target.base_url
        return review_plan(
            Anthropic(**ckw), reviewer_model,
            plan_json_path=str(kw.get("plan_json_path", "")),
            plan_md_path=str(kw.get("plan_md_path", "") or ""),
            kind=str(kw.get("kind", "rebase")))

    def _run_tests(kw: Mapping, key: str) -> dict:
        paths = kw.get("test_paths") or []
        if isinstance(paths, str):
            paths = paths.split()
        if not paths:
            return {"error": "test_paths is required"}
        markers = str(kw.get("markers", "") or "")
        cmd = "python -m pytest " + " ".join(str(p) for p in paths)
        if markers:
            cmd += f" -m '{markers}'"
        runner = TestRunner(repo_root=Path(repo),
                            tests_dir=ctx.run_dir / "tests",
                            gpu_lock_dir=ctx.run_dir / "gpu_lock")
        outcome = runner.run(
            TestJob(key=f"{key}_{abs(hash(cmd)) % 10 ** 8}", command=cmd,
                    timeout_sec=float(kw.get("timeout") or 1800),
                    min_gpus=0, gpu_lock=True),
            _target_test_env(ctx, manifest))
        tail = ""
        try:
            if outcome.log_file and Path(outcome.log_file).is_file():
                tail = "\n".join(Path(outcome.log_file)
                                 .read_text(encoding="utf-8",
                                            errors="replace")
                                 .splitlines()[-120:])
        except OSError:
            pass
        return {"exit_code": outcome.rc, "passed": outcome.rc == 0,
                "timed_out": outcome.timed_out, "output": tail,
                "log_file": outcome.log_file}

    def run_pytest(**kw) -> dict:
        return _run_tests(kw, "agent_pytest")

    def reproduce(**kw) -> dict:
        return _run_tests(kw, "agent_repro")

    def run_precommit(**kw) -> dict:
        pc = (manifest.get("rebase") or {}).get("precommit") or {}
        command = str(pc.get("command") or "")
        if not command:
            return {"error": "no precommit command declared in the adapter "
                             "manifest"}
        files = kw.get("files") or []
        if isinstance(files, str):
            files = files.split()
        if files:
            # `--all-files` and `--files` are mutually exclusive — a
            # file-scoped call must drop the manifest command's all-files
            # sweep or pre-commit refuses to run at all
            import re as _re
            command = _re.sub(r"\s(?:--all-files|-a)\b", "", command)
            command += " --files " + " ".join(str(f) for f in files)
        runner = TestRunner(repo_root=Path(repo),
                            tests_dir=ctx.run_dir / "tests",
                            gpu_lock_dir=ctx.run_dir / "gpu_lock")
        outcome = runner.run(
            TestJob(key="agent_precommit", command=command,
                    timeout_sec=float(pc.get("timeout_sec") or 600),
                    min_gpus=0, gpu_lock=False),
            _target_test_env(ctx, manifest))
        return {"exit_code": outcome.rc, "passed": outcome.rc == 0,
                "log_file": outcome.log_file}

    def _memory() -> DebugMemory:
        return DebugMemory(ctx.settings.memory_db)

    def search_debug_memory(**kw) -> dict:
        query = " ".join(str(kw.get(k, "") or "")
                         for k in ("keyword", "module", "tags")).strip()
        if not query:
            return {"results": []}
        try:
            return {"results": _memory().search(
                query, k=int(kw.get("max_results") or 5), repo=repo_name)}
        except Exception as exc:  # noqa: BLE001 - store trouble is a result
            return {"error": f"debug memory unavailable: {exc}"}

    def record_debug_memory(**kw) -> dict:
        try:
            entry_id = _memory().record(
                repo=repo_name, module=str(kw.get("module", "")),
                run_id=str(ctx.state.get("run_id", "")),
                symptom=str(kw.get("symptom", "")),
                root_cause=str(kw.get("root_cause", "")),
                fix_summary=str(kw.get("fix", "")),
                files=[f.strip() for f in
                       str(kw.get("files", "")).split(",") if f.strip()],
                verification="recorded by rebase agent"
                             + (f" (key={kw.get('key')})"
                                if kw.get("key") else ""))
            return {"ok": True, "id": entry_id}
        except Exception as exc:  # noqa: BLE001
            return {"error": f"debug memory write failed: {exc}"}

    # seed skills live in the (runtime-READ-ONLY) adapter tree; agent
    # proposals land in the RUNTIME state dir — writing candidates into
    # the checked-in adapter source would dirty it and bypass the module
    # scope's writable wall (Rev 8 §1.1 seed/runtime split)
    seed_skills_dir = Path(ctx.settings.adapters_dir) \
        / repo_name.replace("-", "_") / "skills"
    runtime_skills_dir = Path(ctx.settings.memory_db).parent / "state" \
        / repo_name / "skills_runtime"

    def search_skills(**kw) -> dict:
        query = str(kw.get("keyword", "") or "")
        module_q = str(kw.get("module", "") or "")
        k = int(kw.get("max_results") or 3)
        # retrieval = a REAL seed ∪ runtime union: runtime (learned, newer)
        # first, then seed entries it doesn't override — a full seed page
        # can never starve distinct runtime skills out of the result
        merged: dict[str, object] = {}
        for store_dir in (runtime_skills_dir, seed_skills_dir):
            for s in SkillStore(store_dir).find(query=query,
                                                module=module_q, k=k):
                merged.setdefault(s.name, s)
        return {"skills": [{"name": s.name, "description": s.description}
                           for s in list(merged.values())[:k]]}

    def skill_manage(**kw) -> dict:
        action = str(kw.get("action", ""))
        if action not in ("create", "propose", "update", "save"):
            return {"error": f"unsupported skill action {action!r} — "
                             "agents may only propose"}
        try:
            # governance: agents PROPOSE candidates; promotion to a real
            # SKILL.md is a curator/human action (read-wide/write-narrow)
            SkillStore(runtime_skills_dir).propose(
                name=str(kw.get("name", "")),
                description=str(kw.get("description", "")),
                body=str(kw.get("body", "")))
            return {"ok": True, "proposed": str(kw.get("name", "")),
                    "note": "recorded as a CANDIDATE — human promotion "
                            "required"}
        except Exception as exc:  # noqa: BLE001
            return {"error": f"skill proposal failed: {exc}"}

    return RebaseBackends(
        search_debug_memory=search_debug_memory,
        record_debug_memory=record_debug_memory,
        skill_manage=skill_manage, search_skills=search_skills,
        request_plan_review=request_plan_review,
        run_pytest=run_pytest, reproduce=reproduce,
        run_precommit=run_precommit)


def _module_scope(repo_root: str, module: str, manifest: dict,
                  run_dir: Path | None = None) -> ToolScope:
    """C5 path governance for one module agent: the repo tree (plus the
    run's own artifact dir — the plan gate REQUIRES the agent to write its
    decision under `<run_dir>/plans/`) is the hard writable wall; the
    module's manifest `local_paths` plus the plan dir are its primary files
    — writes elsewhere execute but are RECORDED out-of-scope. An UNKNOWN
    module (e.g. a debug agent for an unassigned job) gets a never-matching
    repo primary, so every one of its repo writes is recorded rather than
    silently in-scope."""
    root = Path(repo_root).resolve()
    local = tuple(((manifest.get("modules") or {}).get(module) or {})
                  .get("local_paths") or ())
    writable = [f"{root.as_posix()}/*"]
    primary = [f"{(root / p).as_posix()}*" for p in local] \
        or ["/__imx_no_primary__/*"]
    if run_dir is not None:
        rd = Path(run_dir).resolve().as_posix()
        writable.append(f"{rd}/*")
        primary.append(f"{rd}/plans/*")
    return ToolScope(
        name=f"rebase-module:{module}",
        allowed_tools=frozenset(),  # extras bypass the builtin allowlist;
                                    # enforcement here is the path scope
        path_scope=PathScope(writable=tuple(writable),
                             primary=tuple(primary)),
        root=str(root))


# same-checkout module agents must never run concurrently — the executor's
# foreach fan-out gathers items, but every module mutates the SAME target
# tree (the parent runs wave members sequentially). Locks are LOOP-scoped:
# keyed WEAKLY by the running loop object (the runtime-registry pattern —
# id() reuse on a dead loop's address can NOT resurrect its lock) with a
# per-loop run-dir map; a collected loop drops its whole entry.
_MODULE_SERIAL: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, dict]" \
    = weakref.WeakKeyDictionary()


def _serial_lock(run_dir) -> asyncio.Lock:
    loop = asyncio.get_running_loop()
    per_loop = _MODULE_SERIAL.setdefault(loop, {})
    return per_loop.setdefault(str(run_dir), asyncio.Lock())


def _drop_serial_lock(run_dir) -> None:
    """Completed-run cleanup (called by the lock finalizer): drop the run's
    serialization entry from every live loop's map."""
    for per_loop in list(_MODULE_SERIAL.values()):
        per_loop.pop(str(run_dir), None)


# run dirs whose scratch teardown finalizer is registered in THIS process —
# a resumed run that ADOPTS an existing scratch must re-register teardown or
# the "disposable" checkout survives its run
_SCRATCH_REGISTERED: set[str] = set()


def _register_scratch_teardown(ctx: StepContext, scratch: Path) -> None:
    key = str(ctx.run_dir)
    if key in _SCRATCH_REGISTERED:
        return
    _SCRATCH_REGISTERED.add(key)
    from ..lifecycle import register_finalizer

    async def _teardown_scratch(_outcome, _path=scratch, _key=key) -> None:
        import shutil
        shutil.rmtree(_path, ignore_errors=True)
        _SCRATCH_REGISTERED.discard(_key)

    register_finalizer(ctx.run_dir, _teardown_scratch)


def _ensure_upstream_scratch(ctx: StepContext) -> str | StepResult:
    """The per-run DISPOSABLE upstream checkout (Rev 8 §4 risk reduction):
    wheel selection resets/checks out the tree and agent `run_shell` can
    mutate it, so those operations get a `git clone --shared` scratch of
    the canonical upstream, torn down by a lifecycle finalizer. Returns
    the scratch path — re-cloning on resume if a prior teardown removed
    it, and RE-REGISTERING teardown when a resumed process merely adopts
    a surviving scratch; BLOCKED when no canonical upstream is known or
    the clone fails."""
    import subprocess
    scratch = Path(ctx.state.get("upstream_path", "") or "")
    origin = ctx.state.get("upstream_origin_path", "")
    # only a path INSIDE the run dir counts as an existing scratch — a
    # canonical path in `upstream_path` (older state, manual seeding) must
    # never be adopted as the mutable tree
    if str(scratch).startswith(str(ctx.run_dir)) \
            and (scratch / ".git").exists():
        _register_scratch_teardown(ctx, scratch)
        return str(scratch)
    if not origin:
        return StepResult(False, FailureKind.BLOCKED,
                          "no canonical upstream recorded — prelude gap")
    scratch = ctx.run_dir / "upstream_scratch"
    if not (scratch / ".git").exists():
        r = subprocess.run(["git", "clone", "--shared", "--no-checkout",
                            str(origin), str(scratch)],
                           capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            return StepResult(False, FailureKind.BLOCKED,
                              "upstream scratch clone failed: "
                              + r.stderr.strip()[:300])
        subprocess.run(["git", "-C", str(scratch), "checkout", "--detach",
                        "HEAD"], capture_output=True, text=True,
                       timeout=300)
        ctx.trace.record("upstream_scratch_created", path=str(scratch))
    _register_scratch_teardown(ctx, scratch)
    ctx.state["upstream_path"] = str(scratch)
    return str(scratch)


# process-local registry of HELD checkout flocks, keyed by run dir. The
# prelude acquires them on a fresh run — but a `--resume` replays completed
# steps from the checkpoint WITHOUT executing them, so every mutating step
# re-ensures the locks through here (idempotent within the process; a new
# process acquires fresh flocks).
_HELD_LOCKS: dict[str, list] = {}


def _ensure_checkout_locks(ctx: StepContext, manifest: dict,
                           mode: str) -> StepResult | None:
    """Acquire (once per process per run) the shared checkout flocks for a
    mutating mode and register their lifecycle-finalizer release. Returns a
    BLOCKED StepResult on contention, None when held/not needed."""
    if mode not in MUTATING_MODES:
        return None
    key = str(ctx.run_dir)
    if _HELD_LOCKS.get(key):
        return None
    repo = require_repo(ctx)
    if isinstance(repo, StepResult):
        return repo
    from ...rebase_engine.runctx import CheckoutLock
    rb = manifest.get("rebase") or {}
    locks = [CheckoutLock(Path(repo), rb.get("lock_name", "checkout"))]
    # the CANONICAL upstream is what external users contend on — the
    # per-run scratch clone inside run_dir needs no shared lock
    upstream = ctx.state.get("upstream_origin_path", "")
    if upstream and mode == "full":
        locks.append(CheckoutLock(Path(upstream), "upstream"))
    held: list = []
    for lock in locks:
        if not lock.acquire(blocking=False):
            for h in held:
                h.release()
            return StepResult(False, FailureKind.BLOCKED,
                              f"another run holds {lock.path} — an "
                              "external or archival run is active on this "
                              "checkout")
        held.append(lock)
    _HELD_LOCKS[key] = held
    from ..lifecycle import register_finalizer

    async def _release_locks(_outcome, _key=key) -> None:
        for h in _HELD_LOCKS.pop(_key, []):
            h.release()
        _drop_serial_lock(_key)

    register_finalizer(ctx.run_dir, _release_locks)
    ctx.trace.record("checkout_locks_acquired",
                     paths=[str(lk.path) for lk in held])
    return None


@step("rebase.v3_prelude", "deterministic", "read",
      "Validate mode + adapter data; init runtime, locks, and mode flags.")
async def _v3_prelude(ctx: StepContext) -> StepResult:
    """Publishes the `mode_*` flags every later `when:` gate uses (Rev 8
    §2.1 — the mode was already resolved and written back by
    `resolve_effective_mode` before confirmation; an absent/unknown value
    here is a hard failure, not a default). For mutating modes it also
    initializes the run's world: the shared checkout flocks (released by a
    lifecycle finalizer on EVERY exit path), `upstream_path`, and the
    `last_rebase_upstream_commit` baseline (Rev 8 §3.4 — without these
    every full run would block at the wheel step and mutation paths would
    race external checkout users)."""
    mode = _task_params(ctx).get("rebase_mode", "")
    if mode not in MODES:
        return StepResult(False, FailureKind.BLOCKED,
                          f"rebase_mode missing/unknown ({mode!r}) — "
                          "resolve_effective_mode did not run; refuse to "
                          "guess permissions")
    manifest = _adapter_manifest(ctx)
    if isinstance(manifest, StepResult):
        return manifest
    if manifest.get("status") != "active":
        return StepResult(False, FailureKind.BLOCKED,
                          "adapter is not active — v3 refuses inactive "
                          "adapters")

    # transition-table row 3 (Rev 8 §3.1): a run that ends blocked at ANY
    # later step still owes RUN_REPORT — the report step never runs on the
    # blocked path, so a lifecycle finalizer augments the artifacts
    # (never upgrades the outcome). Registered before anything can block.
    from ..lifecycle import register_finalizer
    sub = _substate(ctx)

    async def _terminal_report(outcome, _run_dir=ctx.run_dir, _sub=sub,
                               _mode=mode) -> None:
        path = _run_dir / "RUN_REPORT.md"
        if path.exists():
            return
        status = getattr(outcome, "status", None) or "aborted"
        data = _sub.read()
        mods = data.get("modules") or {}
        pipeline = ((data.get("tests") or {}).get("pipeline")) or {}
        path.write_text(
            "# Run report (terminal — written by the run finalizer)\n\n"
            f"- status: {status}\n"
            f"- rebase_mode: {_mode}\n"
            f"- substate phase: {data.get('phase', '')}\n"
            f"- modules: "
            f"{sum(1 for m in mods.values() if (m or {}).get('status') == 'done')}"
            f" done / {len(mods)} total\n"
            f"- tests: {pipeline.get('passed', 0)} passed, "
            f"{pipeline.get('failed', 0)} failed\n\n"
            "The run terminated before the report step; see ESCALATION.md / "
            "DIAGNOSTICS.md and run_trace.jsonl for the failure detail.\n",
            encoding="utf-8")

    register_finalizer(ctx.run_dir, _terminal_report)

    updates: dict = {}
    from ...adapters.base import expand_path
    upstream = ctx.state.get("upstream_origin_path", "") \
        or ctx.state.get("upstream_path", "") or expand_path(
        (manifest.get("upstream") or {}).get("repo_path", ""))
    if upstream:
        updates["upstream_origin_path"] = upstream
        ctx.state.setdefault("upstream_origin_path", upstream)
    baseline = _task_params(ctx).get("last_rebase_commit", "") \
        or ctx.state.get("last_rebase_upstream_commit", "")
    if baseline:
        updates["last_rebase_upstream_commit"] = baseline
    if mode == "full":
        if not upstream:
            return StepResult(False, FailureKind.BLOCKED,
                              "full mode needs the upstream checkout — set "
                              "the manifest upstream.repo_path (env var "
                              "unset?)")
        if not baseline:
            return StepResult(False, FailureKind.BLOCKED,
                              "full mode needs the last-rebase baseline — "
                              "pass --task-param last_rebase_commit=<sha>")

    # §2.2 preconditions for the prepared-tree modes: they operate on a tree
    # whose pin step already ran — refuse one that was never prepared, and
    # (remote_ci) refuse to push without the upstream-commit signal
    if mode in ("local_ci", "remote_ci"):
        repo = require_repo(ctx)
        if isinstance(repo, StepResult):
            return repo
        pin_data = ((manifest.get("rebase") or {}).get("wheel") or {}) \
            .get("pin")
        if not pin_data:
            return StepResult(False, FailureKind.BLOCKED,
                              f"{mode} needs the manifest wheel.pin spec — "
                              "cannot verify the prepared tree")
        if not wheel_mod.pin_present(Path(repo),
                                     wheel_mod.PinSpec.from_manifest(
                                         pin_data)):
            return StepResult(False, FailureKind.BLOCKED,
                              f"{mode} operates on a PREPARED tree, but the "
                              "CI Dockerfile carries no wheel pin — run "
                              "full mode (or pin) first")
    if mode == "remote_ci":
        upstream_commit = _task_params(ctx).get("upstream_commit", "") \
            or ctx.state.get("upstream_commit", "") \
            or (sub.read().get("upstream_commit") or "")
        if not upstream_commit:
            return StepResult(False, FailureKind.BLOCKED,
                              "remote_ci needs the upstream-commit signal "
                              "(--task-param upstream_commit=<sha>, or a "
                              "resumed run's substate) — refusing to push "
                              "an unprepared branch")
        updates["upstream_commit"] = upstream_commit

    if mode in MUTATING_MODES:
        blocked = _ensure_checkout_locks(ctx, manifest, mode)
        if blocked is not None:
            return blocked
    if mode == "full":
        # per-run DISPOSABLE upstream (Rev 8 §4): wheel checkout/reset and
        # agent shells mutate the SCRATCH clone, never the canonical tree
        scratch = _ensure_upstream_scratch(ctx)
        if isinstance(scratch, StepResult):
            return scratch
        updates["upstream_path"] = scratch

    sub.update({"phase": "init", **{k: v for k, v in
                                    mode_state_flags(mode).items()}})
    return StepResult(True, summary=f"mode={mode}",
                      outputs={"state_updates": {
                          **mode_state_flags(mode), **updates,
                          "run_id": sub.run_id}})


@step("rebase.v3_guard", "deterministic", "write_workspace",
      "Locked clean-tree gate: checkout flocks first, adapter guard policy.")
async def _v3_guard(ctx: StepContext) -> StepResult:
    """The pipeline's FIRST mutator: `workspace.guard_clean_rebase` can
    abort stale git operations and discard artifacts, so checkout
    exclusion must exist BEFORE it acts — including on a resume that
    replays the completed prelude and starts here. Also injects the
    adapter's guard policy (manifest `rebase.guard`), which the generic
    step reads only from its params — without this the adapter's
    `discard_untracked_patterns` was dead configuration."""
    manifest = _adapter_manifest(ctx)
    if isinstance(manifest, StepResult):
        return manifest
    blocked = _ensure_checkout_locks(
        ctx, manifest, _task_params(ctx).get("rebase_mode", ""))
    if blocked is not None:
        return blocked
    from .workspace import _guard_clean_rebase
    guard_cfg = dict((manifest.get("rebase") or {}).get("guard") or {})
    guard_cfg.setdefault("abort_stale_state", True)
    # the shared checkout flock we JUST took lives under <repo>/locks/ —
    # it must not read as dirt, and must never be discarded while held
    guard_cfg.setdefault("ignore_untracked_prefixes", ["locks/"])
    inner = StepContext(settings=ctx.settings, state=ctx.state,
                        params={**guard_cfg, **ctx.params},
                        run_dir=ctx.run_dir, trace=ctx.trace,
                        llm=ctx.llm, item=ctx.item)
    return await _guard_clean_rebase(inner)


@step("rebase.v3_scan", "deterministic", "read",
      "Report-only scan: manifest + drift preview, stores untouched.")
async def _v3_scan(ctx: StepContext) -> StepResult:
    repo = require_repo(ctx)
    if isinstance(repo, StepResult):
        return repo
    manifest = _adapter_manifest(ctx)
    if isinstance(manifest, StepResult):
        return manifest
    spec = ManifestSpec.from_manifest(manifest)
    built = build_manifest(Path(repo), spec)
    out = ctx.run_dir / "test_manifest.json"
    import json
    out.write_text(json.dumps(built.to_dict(), indent=1), encoding="utf-8")
    summary = (f"{len(built.jobs)} CI jobs, "
               f"{len(built.changes)} test changes")
    if built.dropped:
        summary += (f"; {len(built.dropped)} labeled step(s) with no "
                    "runnable command DROPPED (structural in a test run)")
        ctx.trace.record("manifest_steps_dropped", labels=built.dropped)
    return StepResult(True, summary=summary,
                      outputs={"state_updates": {
                          "manifest_jobs": len(built.jobs)}})


@step("rebase.v3_wheel", "deterministic", "write_workspace",
      "Pick the wheel commit and pin the CI Dockerfile.")
async def _v3_wheel(ctx: StepContext) -> StepResult:
    repo = require_repo(ctx)
    if isinstance(repo, StepResult):
        return repo
    manifest = _adapter_manifest(ctx)
    if isinstance(manifest, StepResult):
        return manifest
    blocked = _ensure_checkout_locks(
        ctx, manifest, _task_params(ctx).get("rebase_mode", ""))
    if blocked is not None:
        return blocked
    rb = manifest.get("rebase") or {}
    wheel_spec = wheel_mod.WheelSpec.from_manifest(rb["wheel"])
    pin = wheel_mod.PinSpec.from_manifest(rb["wheel"]["pin"])
    upstream = _ensure_upstream_scratch(ctx)
    if isinstance(upstream, StepResult):
        return upstream
    venv = _target_venv(manifest)
    if not venv:
        return StepResult(False, FailureKind.BLOCKED,
                          "the target repo venv is not configured (manifest "
                          "repo.venv / its env var) — refusing to install "
                          "the wheel into the copilot's own environment")
    import subprocess
    pre_head = subprocess.run(
        ["git", "-C", upstream, "rev-parse", "HEAD"],
        capture_output=True, text=True, timeout=30).stdout.strip()
    branch = (manifest.get("upstream") or {}).get("target_branch") \
        or (manifest.get("repo") or {}).get("default_branch", "main")
    try:
        found = wheel_mod.pick_wheel_commit(
            Path(upstream), branch, wheel_spec,
            probe=wheel_mod.make_arch_probe(wheel_spec),
            baseline=ctx.state.get("last_rebase_upstream_commit", ""),
            force_commit=_task_params(ctx).get("force_upstream_commit", ""))
        wheel_mod.pin_dockerfile(Path(repo), found, pin)
        # the selection contract ends with the package INSTALLED at the
        # picked commit in the TARGET venv — otherwise stale extensions or
        # a different installed version drive every later module check
        installed = wheel_mod.ensure_wheel_installed(
            Path(upstream), found, wheel_spec,
            python=str(Path(venv) / "bin" / "python"),
            install_log=ctx.run_dir / "wheel_install.log",
            import_check_log=ctx.run_dir / "wheel_import_check.log",
            pre_checkout_head=pre_head)
    except wheel_mod.WheelPickError as exc:
        return StepResult(False, FailureKind.BLOCKED, str(exc))
    except wheel_mod.PinError as exc:
        return StepResult(False, FailureKind.BLOCKED, str(exc))
    except wheel_mod.WheelInstallError as exc:
        return StepResult(False, FailureKind.BLOCKED, str(exc))
    _substate(ctx).set_field("upstream_commit", found)
    return StepResult(True,
                      summary=f"wheel commit {found[:12]} "
                              + ("(reinstalled)" if installed
                                 else "(install healthy, skipped)"),
                      outputs={"state_updates": {"upstream_commit": found}})


@step("rebase.v3_assign", "deterministic", "read",
      "Classify upstream commits into modules; publish the wave lists.")
async def _v3_assign(ctx: StepContext) -> StepResult:
    manifest = _adapter_manifest(ctx)
    if isinstance(manifest, StepResult):
        return manifest
    upstream = _ensure_upstream_scratch(ctx)
    if isinstance(upstream, StepResult):
        return upstream
    baseline = ctx.state.get("last_rebase_upstream_commit", "")
    if not baseline:
        return StepResult(False, FailureKind.BLOCKED,
                          "last-rebase baseline not in state")
    cfg = Phase1Config(
        upstream_repo=Path(upstream), target_repo=Path("."),
        log_dir=ctx.run_dir, baseline_commit=baseline,
        base_class_watch_paths=tuple((manifest.get("rebase") or {})
                                     .get("base_class_watch_paths") or ()))
    modules = manifest.get("modules") or {}
    # PATH SYNC before assignment (parent 35_sync_module_paths): after an
    # upstream rename, `git log -- <missing-path>` yields no commits and
    # the module would be SILENTLY marked skippable — retarget the static
    # upstream_paths against the live tree first (existence-filtered,
    # never-empty)
    from ...rebase_engine.path_sync import sync_path_map
    module_paths = {
        m: tuple(paths) for m, paths in sync_path_map(
            Path(upstream),
            {m: list((s or {}).get("upstream_paths") or ())
             for m, s in modules.items()}).items()}
    dropped = {m: sorted(set((modules[m] or {}).get("upstream_paths") or ())
                         - set(module_paths[m])) for m in modules}
    dropped = {m: d for m, d in dropped.items() if d}
    if dropped:
        ctx.trace.record("upstream_path_sync_dropped", dropped=dropped)
    from ...rebase_engine.assign import AssignError
    try:
        result = run_commit_assignment(cfg, module_paths, _substate(ctx))
    except AssignError as exc:
        return StepResult(False, FailureKind.BLOCKED, str(exc))
    active = [m for m, s in result.skip.items() if not s]
    # wave ordering is a dependency contract (manifest `wave`, parent
    # parity): wave 1 runs first; the wave gate empties wave 2 on failure
    wave1 = [m for m in modules if m in active
             and int((modules[m] or {}).get("wave") or 2) == 1]
    wave2 = [m for m in modules if m in active and m not in wave1]
    return StepResult(True,
                      summary=f"{result.total_commits} commits over "
                              f"{len(active)} active modules "
                              f"(wave1={len(wave1)}, wave2={len(wave2)})",
                      outputs={"state_updates": {
                          "active_modules": active,
                          "wave1_modules": wave1,
                          "wave2_modules": wave2}})


@step("rebase.v3_wave_gate", "deterministic", "read",
      "Wave gate: a wave-1 failure empties wave 2 (or ESCALATEs on halt).")
async def _v3_wave_gate(ctx: StepContext) -> StepResult:
    """Rev 8 §2.2: the gate ALWAYS runs between the waves. Any wave-1
    module failure empties `wave2_modules` (dependents must not build on a
    broken base); `halt_on_module_failure=true` escalates instead."""
    sub = _substate(ctx)
    data = sub.read()
    wave1 = ctx.state.get("wave1_modules") or []
    failed = [m for m in wave1
              if ((data.get("modules") or {}).get(m) or {})
              .get("status") == "failed"]
    if not failed:
        return StepResult(True, summary="wave 1 clean; wave 2 proceeds")
    if _task_params(ctx).get("halt_on_module_failure"):
        return StepResult(False, FailureKind.ESCALATE,
                          "halt_on_module_failure: wave-1 module(s) failed: "
                          + ", ".join(failed))
    ctx.trace.record("wave_gate", failed_wave1=failed, wave2_emptied=True)
    return StepResult(True,
                      summary=f"wave-1 failure(s) ({', '.join(failed)}) — "
                              "wave 2 emptied",
                      outputs={"state_updates": {"wave2_modules": []}})


async def _run_debug_agent(ctx: StepContext, manifest: dict, module: str,
                           slug: str, traceback_text: str) -> str:
    """One regression-debug agent attempt for a failing test's module —
    the configured state-injected backend the loop's `debug_fn` invokes.
    Returns "done" when the agent claims completion (the caller re-runs the
    test; only a green re-run counts as fixed), "not_done" when the agent
    honestly gave up, or "error:<detail>" when the DEBUG MACHINERY itself
    failed (structural, per the §2.3 taxonomy — agent dispatch failures are
    never ordinary test failures)."""
    client = _tier_client(ctx)
    if isinstance(client, StepResult):
        return "error:debug backend unavailable"
    client, target = client
    from ...rebase_engine.agent_loop import run_agent_loop
    from ...rebase_engine.prompt_builder import (ModulePromptData,
                                                 build_debug_prompt)
    from ...rebase_engine.rebase_tools import (RebasePaths,
                                               build_rebase_tools,
                                               load_tool_schemas)
    repo_name = (ctx.state.get("task_spec") or {}).get("repo", "")
    adapter_dir = Path(ctx.settings.adapters_dir) / repo_name.replace("-", "_")
    data = ModulePromptData.load(adapter_dir / "rebase")
    defs = load_tool_schemas(adapter_dir / "rebase" / "tool_schemas.json")
    repo_root = ctx.state.get("repo_path", "")
    paths = RebasePaths(omni_path=repo_root,
                        vllm_path=ctx.state.get("upstream_path", ""),
                        env=_agent_shell_env(ctx, manifest, repo_root,
                                             adapter_dir))
    tools = build_rebase_tools(
        defs, paths, _build_backends(ctx, manifest, repo_root, target))
    prompt = build_debug_prompt(module or slug, traceback_text,
                                data.debug_prompt_template, slug)
    agent_log = ctx.run_dir / "agents" / f"debug-{slug}.log"
    agent_log.parent.mkdir(parents=True, exist_ok=True)
    ctx.trace.record("debug_attempt", slug=slug, module=module,
                     model=target.model)
    try:
        result = await run_agent_loop(
            client, prompt, model=target.model, tool_defs=defs,
            extra_tools=tools,
            scope=_module_scope(repo_root, module, manifest,
                                run_dir=ctx.run_dir),
            trace=ctx.trace, require_plan_review=False,
            model_aliases=ctx.settings.model_aliases,
            model_mismatch_policy=ctx.settings.model_mismatch_policy,
            agent_log=str(agent_log))
    except Exception as exc:  # noqa: BLE001 - a debug crash is STRUCTURAL
        ctx.trace.record("debug_attempt_error", slug=slug, error=str(exc))
        return f"error:debug agent crashed: {exc}"
    if result.get("done"):
        return "done"
    # done=False from the loop is ALWAYS machinery/budget (fatal auth,
    # stream error, model mismatch, truncation abort, max turns) — an agent
    # that finishes, even unsuccessfully, returns done=True. Structural.
    return "error:agent loop did not complete: " \
           + (result.get("text") or "")[:200]


@step("rebase.v3_test_loop", "script", "write_workspace",
      "The local test loop: run, baseline-compare, debug regressions.")
async def _v3_test_loop(ctx: StepContext) -> StepResult:
    """Runs the manifest jobs through the PR1 runner with main-baseline
    comparison. Local-loop contract (parent parity): nightly-sourced jobs
    are excluded; job env pairs reach the child; the baseline run prepends
    the worktree to PYTHONPATH so main's files execute against main's code;
    timeouts/watchdog kills are recorded as INFRASTRUCTURE failures
    (structural for the push gate, never assertion pass-through); an empty
    manifest marks `manifest_empty` instead of vacuously passing. The
    regression DEBUG agent runs on the tier backend — absent one,
    regressions are recorded as failures with a declared `capability_gap`
    (fail closed, never silently skipped)."""
    repo = require_repo(ctx)
    if isinstance(repo, StepResult):
        return repo
    manifest = _adapter_manifest(ctx)
    if isinstance(manifest, StepResult):
        return manifest
    blocked = _ensure_checkout_locks(
        ctx, manifest, _task_params(ctx).get("rebase_mode", ""))
    if blocked is not None:
        return blocked
    spec = ManifestSpec.from_manifest(manifest)
    built = build_manifest(Path(repo), spec)
    sub = _substate(ctx)

    jobs = built.to_dict()["jobs"]
    local_jobs = [j for j in jobs if j.get("source") != "nightly"]
    if len(local_jobs) < len(jobs):
        ctx.trace.record("nightly_jobs_excluded",
                         count=len(jobs) - len(local_jobs))
    # labeled steps the builder DROPPED for lack of a runnable command are
    # STRUCTURAL on every path — including the all-dropped one, where the
    # generic manifest_empty block must still carry the labels
    dropped_infra = [f"step '{label}': no runnable command"
                     for label in built.dropped]
    if dropped_infra:
        ctx.trace.record("manifest_steps_dropped", labels=built.dropped)
    if not local_jobs:
        # zero runnable jobs is corrupt/empty manifest territory — the push
        # gate must block, not sail through a vacuous "0 failed"
        sub.update({"manifest_empty": True,
                    "tests": {"pipeline": {"passed": 0, "failed": 0,
                                           "failed_tests": [],
                                           "skipped": 0},
                              "infra_failures": dropped_infra}})
        return StepResult(True,
                          summary="no runnable local jobs — manifest_empty "
                                  "set (push gate blocks)"
                                  + (f"; {len(dropped_infra)} dropped "
                                     "step(s) recorded"
                                     if dropped_infra else ""),
                          outputs={"state_updates": {"phase3_failed": []}})

    import os
    from ...testing.runner import TestJob, TestRunner
    from ...testing.watchdog import WatchdogPatterns
    if not _target_venv(manifest):
        return StepResult(False, FailureKind.BLOCKED,
                          "the target repo venv is not configured (manifest "
                          "repo.venv / its env var) — raw manifest commands "
                          "would execute against the copilot's own "
                          "environment")
    rb = manifest.get("rebase") or {}
    adapter_dir = Path(ctx.settings.adapters_dir) / \
        ((ctx.state.get("task_spec") or {}).get("repo", "")).replace("-", "_")
    pat_file = adapter_dir / "testing" / "watchdog_patterns.yaml"
    patterns = WatchdogPatterns.from_yaml(pat_file) \
        if pat_file.is_file() else None

    def notify_download(key: str, repo_id: str) -> None:
        ctx.trace.record("model_download_expected", job=key, repo=repo_id)

    runner = TestRunner(
        repo_root=Path(repo), tests_dir=ctx.run_dir / "tests",
        patterns=patterns, gpu_lock_dir=ctx.run_dir / "gpu_lock",
        artifact_globs=list((rb.get("testing") or {})
                            .get("artifact_globs") or []),
        cuda_visible_devices=os.environ.get("CUDA_VISIBLE_DEVICES", ""),
        notify_download=notify_download)
    jobs_by_slug = {j["slug"]: j for j in local_jobs}

    def _job(slug: str) -> TestJob:
        return manifest_job_to_test_job(jobs_by_slug[slug])

    def _to_result(outcome) -> tl.TestRunResult:
        infra = "timeout" if outcome.timed_out else \
            ("watchdog kill" if outcome.watchdog_triggered else "")
        return tl.TestRunResult(rc=outcome.rc, skipped=outcome.skipped,
                                skip_reason=outcome.skip_reason,
                                output=outcome.log_file, infra=infra)

    def run_fn(slug: str) -> tl.TestRunResult:
        # a non-RUNNABLE command (empty or comment-only) must NEVER read as
        # a pass — bash exits 0 on both (the parent's §10 false-pass
        # mechanism, DRIFT_TRIAGE #4); the builder already drops such
        # steps, so one arriving here is corruption and classifies
        # STRUCTURAL
        from ...rebase_engine.test_manifest import is_runnable_command
        if not is_runnable_command(jobs_by_slug[slug].get("command", "")):
            return tl.TestRunResult(rc=1, infra="no runnable command")
        # tests INHERIT the process env (Rev 8 §6: inherit-plus-overlay;
        # the credential scrub applies to agent shells only) with the
        # TARGET venv + CUDA + HF_HOME overlay — raw manifest commands
        # must resolve inside the target repo's runtime, never ours
        return _to_result(runner.run(_job(slug),
                                     _target_test_env(ctx, manifest)))

    worktree_path = ctx.run_dir / "main_worktree"

    def baseline_fn(slug: str) -> tl.TestRunResult | None:
        wt = tl.ensure_main_worktree(Path(repo), worktree_path)
        if wt is None:
            return None
        wt_runner = TestRunner(
            repo_root=wt, tests_dir=ctx.run_dir / "tests",
            patterns=patterns, gpu_lock_dir=ctx.run_dir / "gpu_lock",
            cuda_visible_devices=runner.cuda,
            notify_download=notify_download)
        # main's files must import main's code: prepend the worktree so the
        # baseline never executes against rebase dependencies (parent's
        # baseline PYTHONPATH override) — same TARGET env otherwise; infra
        # outcomes propagate (a baseline timeout must never read as "fails
        # on main too")
        env = _target_test_env(ctx, manifest, pythonpath_prepend=str(wt))
        return _to_result(wt_runner.run(_job(slug), env, baseline=True))

    async def debug_fn(slug: str, label: str, rc: int,
                       output: str) -> bool | str:
        tier = _tier_client(ctx)
        if isinstance(tier, StepResult):
            ctx.trace.record("capability_gap",
                             capability="rebase.debug_agent",
                             detail=f"no agent backend; {slug} regression "
                                    "recorded as a structural failure")
            return "debug backend unavailable (capability_gap)"
        traceback_text = ""
        try:
            log_path = Path(output)
            if log_path.is_file():
                traceback_text = "\n".join(
                    log_path.read_text(encoding="utf-8",
                                       errors="replace")
                    .splitlines()[-200:])
        except OSError:
            pass
        # attempt-scoped snapshot (parent parity): a rejected/unverified
        # debug patch must NOT stay in the tree — assertion failures pass
        # the push gate by default, so leftover edits would eventually be
        # committed and pushed
        snap, untracked = tl.snapshot_worktree(Path(repo))
        verdict = await _run_debug_agent(
            ctx, manifest, jobs_by_slug[slug].get("module", ""), slug,
            traceback_text or f"{label} failed with rc={rc}")
        if verdict.startswith("error:"):
            tl.restore_worktree(Path(repo), snap, untracked)
            return f"debug agent failed: {verdict[6:]}"
        rerun = run_fn(slug)             # only a green re-run counts
        if rerun.infra:
            tl.restore_worktree(Path(repo), snap, untracked)
            return f"post-debug re-run {rerun.infra}"
        if rerun.skipped:
            tl.restore_worktree(Path(repo), snap, untracked)
            return "post-debug re-run skipped (unverifiable fix)"
        if rerun.rc != 0:
            tl.restore_worktree(Path(repo), snap, untracked)
            return False
        return True

    result = await tl.run_test_loop(
        local_jobs, substate=sub, run_fn=run_fn,
        baseline_fn=baseline_fn, debug_fn=debug_fn,
        visible_gpus=len([d for d in runner.cuda.split(",") if d.strip()
                          and not d.strip().startswith("-")]))
    tl.remove_main_worktree(Path(repo), worktree_path)
    infra = result["infra_failures"] + dropped_infra
    sub.update({"tests": {
        "pipeline": {
            "passed": result["passed"], "failed": result["failed"],
            "failed_tests": result["failed_tests"],
            "skipped": len(result["skipped_tests"])},
        "infra_failures": infra}})
    return StepResult(True,
                      summary=f"{result['passed']} passed, "
                              f"{result['failed']} failed "
                              f"({len(infra)} infra), "
                              f"{len(result['skipped_tests'])} skipped",
                      outputs={"state_updates": {
                          "phase3_failed": result["failed_tests"]}})


def _halt_on_phase3(ctx: StepContext, sub: Substate) -> StepResult | None:
    """`halt_on_phase3_failures=true`: the operator explicitly asked the run
    to STOP at the end of phase 3 (loop + precommit — precommit still runs)
    instead of proceeding toward push/remote CI with failures aboard.
    ESCALATE (needs-human, exit 3) when any phase-3 failure exists."""
    if not _task_params(ctx).get("halt_on_phase3_failures"):
        return None
    data = sub.read()
    tests = data.get("tests") or {}
    problems: list[str] = []
    problems.extend((tests.get("pipeline") or {}).get("failed_tests") or [])
    problems.extend(tests.get("infra_failures") or [])
    if ((tests.get("precommit") or {}).get("result")) == "failed":
        problems.append("precommit red")
    if not problems:
        return None
    return StepResult(False, FailureKind.ESCALATE,
                      "halt_on_phase3_failures: "
                      f"{len(problems)} phase-3 failure(s) — halting "
                      "before any push/CI: " + "; ".join(problems[:5]))


@step("rebase.v3_precommit", "script", "write_workspace",
      "Phase-3.2 precommit workflow: run, retry once, record in substate.")
async def _v3_precommit(ctx: StepContext) -> StepResult:
    """The parent's Phase 3.2 (always runs after the local test loop): the
    adapter-declared precommit command, with one retry — auto-fix hooks
    (formatters, end-of-file fixers) often pass on the second run. The
    result is SUBSTATE DATA: `tests.precommit.result` is what the push gate
    reads ("failed" is a structural block, §2.3), so the step itself
    returns ok either way. write_workspace risk: hooks auto-fix files in
    place. An adapter with no declared precommit records `not_declared`
    (data-driven — never invented, never silently green-as-passed)."""
    repo = require_repo(ctx)
    if isinstance(repo, StepResult):
        return repo
    manifest = _adapter_manifest(ctx)
    if isinstance(manifest, StepResult):
        return manifest
    blocked = _ensure_checkout_locks(
        ctx, manifest, _task_params(ctx).get("rebase_mode", ""))
    if blocked is not None:
        return blocked
    sub = _substate(ctx)
    pc = (manifest.get("rebase") or {}).get("precommit") or {}
    command = str(pc.get("command") or "")
    if not command:
        ctx.trace.record("capability_gap", capability="rebase.precommit",
                         detail="no precommit command declared in the "
                                "adapter manifest")
        sub.update({"tests": {"precommit": {"result": "not_declared",
                                            "attempt": 0}}})
        halted = _halt_on_phase3(ctx, sub)
        if halted is not None:
            return halted
        return StepResult(True, summary="precommit: not declared (recorded)")

    from ...testing.runner import TestJob, TestRunner
    runner = TestRunner(repo_root=Path(repo),
                        tests_dir=ctx.run_dir / "tests",
                        gpu_lock_dir=ctx.run_dir / "gpu_lock")
    job = TestJob(key="__precommit__", command=command,
                  timeout_sec=float(pc.get("timeout_sec") or 600),
                  min_gpus=0, gpu_lock=False)
    outcome = runner.run(job, _target_test_env(ctx, manifest))
    attempt = 0
    if outcome.rc != 0 and pc.get("retry_once", True):
        # parity: many hooks fix files in place; a second run then passes.
        # NO `git add -A` here (parent-documented: indiscriminate staging is
        # how stray artifacts ended up in rebase commits)
        attempt = 1
        outcome = runner.run(job, _target_test_env(ctx, manifest))
    passed = outcome.rc == 0 and not outcome.timed_out
    sub.update({"tests": {"precommit": {
        "result": "passed" if passed else "failed",
        "attempt": attempt, "last_log": outcome.log_file or None}}})
    halted = _halt_on_phase3(ctx, sub)
    if halted is not None:
        return halted
    return StepResult(True,
                      summary="precommit "
                              + ("passed" if passed else
                                 f"FAILED (rc={outcome.rc}; push gate "
                                 "blocks)"))


@step("rebase.v3_push_gate", "deterministic", "read",
      "Fail-closed push gate: structural failures block; assertions flag.")
async def _v3_push_gate(ctx: StepContext) -> StepResult:
    from ...rebase_engine.modes import ModeConflictError
    sub = _substate(ctx)
    try:
        decision = evaluate_push_gate(sub.read(), _task_params(ctx))
    except ModeConflictError as exc:
        return StepResult(False, FailureKind.BLOCKED, str(exc))
    if not decision.allowed:
        return StepResult(False, FailureKind.FORBIDDEN,
                          "push gate: " + "; ".join(decision.reasons))
    summary = "push gate open"
    if decision.flagged:
        summary += f" ({len(decision.flagged)} flagged test failure(s))"
    if decision.reasons:
        # "explicit and logged" (Rev 8 §2.3): a push_with_failures override
        # must be UNMISTAKABLE in the trace and report — never
        # indistinguishable from a genuinely clean gate
        ctx.trace.record("push_gate_override",
                         reasons=list(decision.reasons))
        summary += (f"; OVERRIDDEN structural failure(s): "
                    + "; ".join(decision.reasons))
    return StepResult(True, summary=summary,
                      outputs={"state_updates": {
                          "push_gate_flagged": list(decision.flagged),
                          "push_gate_overrides": list(decision.reasons)}})


@step("rebase.v3_finalize", "deterministic", "read",
      "Transition-table terminal row: substate failures ⇒ needs-human.")
async def _v3_finalize(ctx: StepContext) -> StepResult:
    """Rev 8 §3.1 row 2: all steps ok but substate carries failed
    modules/tests ⇒ the run terminates needs-human via the REUSED blocked /
    exit-3 semantics (Decision 4 — no new exit code). Runs AFTER the report
    step, so RUN_REPORT exists and the BLOCKED outcome only adds the
    ESCALATION artifact. The finalizer never upgrades a failure into
    success; substate `phase` records the honest terminal name."""
    sub = _substate(ctx)
    data = sub.read()
    failures: list[str] = []
    for module, spec in (data.get("modules") or {}).items():
        if (spec or {}).get("status") == "failed":
            failures.append(f"module {module}")
    tests = data.get("tests") or {}
    failed_tests = ((tests.get("pipeline") or {}).get("failed_tests")) or []
    failures.extend(f"test {t}" for t in failed_tests)
    failures.extend(f"infra {i}" for i in tests.get("infra_failures") or [])
    if ((tests.get("precommit") or {}).get("result")) == "failed":
        failures.append("precommit red")
    if data.get("manifest_empty"):
        failures.append("manifest empty")
    sub.update({"phase": "needs_human" if failures else "done"})
    if failures:
        return StepResult(False, FailureKind.BLOCKED,
                          "completed with failures needing a human: "
                          + "; ".join(failures[:10]))
    return StepResult(True, summary="substate clean; phase=done")


@step("rebase.v3_module_rebase", "script", "write_workspace",
      "One module's rebase agent (foreach over the wave lists).")
async def _v3_module_rebase(ctx: StepContext) -> StepResult:
    """The PR4a/PR4b assembly: golden-parity prompt → gated loop → substate
    outcome, per module via foreach fan-out. Fan-out siblings SERIALIZE on a
    per-run lock (they all mutate the same checkout; the parent runs wave
    members sequentially). Requires the tier-resolved backend; absent one
    this BLOCKS with a declared capability_gap (never a silent skip). Module
    failures are substate data (the wave gate and the finalize row consume
    them), so the step itself returns ok."""
    module = str(ctx.item or "")
    if not module:
        return StepResult(False, FailureKind.BLOCKED,
                          "v3_module_rebase needs a foreach module item")
    # substate-first idempotency (crash-window contract): a module whose
    # durable status is already terminal-done short-circuits on re-entry —
    # a crash between the substate write and the executor checkpoint must
    # never run the agent (and apply its edits) twice
    sub = _substate(ctx)
    prior = ((sub.read().get("modules") or {}).get(module)) or {}
    if prior.get("status") in ("done", "skipped"):
        return StepResult(True,
                          summary=f"{module}: already {prior['status']} "
                                  "(substate short-circuit)",
                          outputs={"state_updates": {
                              f"module_{module}_status": prior["status"]}})
    manifest = _adapter_manifest(ctx)
    if isinstance(manifest, StepResult):
        return manifest
    blocked = _ensure_checkout_locks(
        ctx, manifest, _task_params(ctx).get("rebase_mode", ""))
    if blocked is not None:
        return blocked
    client = _tier_client(ctx)
    if isinstance(client, StepResult):
        return client
    client, target = client
    from ...rebase_engine.hooks import load_hooks
    from ...rebase_engine.module_rebase import ModuleRunConfig, rebase_module
    from ...rebase_engine.prompt_builder import ModulePromptData
    from ...rebase_engine.rebase_tools import (RebasePaths,
                                               build_rebase_tools,
                                               load_tool_schemas)
    repo_name = (ctx.state.get("task_spec") or {}).get("repo", "")
    adapter_dir = Path(ctx.settings.adapters_dir) / repo_name.replace("-", "_")
    data = ModulePromptData.load(adapter_dir / "rebase")
    defs = load_tool_schemas(adapter_dir / "rebase" / "tool_schemas.json")
    repo_root = ctx.state.get("repo_path", "")
    paths = RebasePaths(omni_path=repo_root,
                        vllm_path=ctx.state.get("upstream_path", ""),
                        env=_agent_shell_env(ctx, manifest, repo_root,
                                             adapter_dir))
    tools = build_rebase_tools(
        defs, paths, _build_backends(ctx, manifest, repo_root, target))
    hooks = load_hooks(adapter_dir, manifest)
    # the LIVE test plan (authoritative CI obligations + upstream test
    # changes) goes into the module prompt — reuse the scan artifact when
    # present, else build fresh
    test_plan: dict | None = None
    try:
        import json as _json
        plan_file = ctx.run_dir / "test_manifest.json"
        if plan_file.is_file():
            plans = (_json.loads(plan_file.read_text(encoding="utf-8"))
                     .get("module_plans") or {})
            raw = plans.get(module)
            if raw:
                test_plan = {"ci_tests": raw.get("ci_tests") or [],
                             "upstream_changes":
                                 raw.get("upstream_changes") or [],
                             "omni_specific":
                                 raw.get("omni_specific") or []}
        else:
            built = build_manifest(Path(repo_root),
                                   ManifestSpec.from_manifest(manifest))
            plan_file.write_text(_json.dumps(built.to_dict(), indent=1),
                                 encoding="utf-8")
            mp = built.for_module(module)
            test_plan = {"ci_tests": [j.slug for j in mp.ci_tests],
                         "upstream_changes": [
                             {"path": c.path, "type": c.change_type,
                              "new_path": c.new_path}
                             for c in mp.upstream_changes],
                         "omni_specific": mp.omni_specific_tests}
    except Exception:  # noqa: BLE001 - plan enrichment is best-effort
        ctx.trace.record("module_test_plan_unavailable", module=module)
    import os
    config = ModuleRunConfig(
        vllm_path=paths.vllm_path, omni_path=paths.omni_path,
        script_dir=str(adapter_dir / "rebase"), model=target.model,
        log_dir=str(ctx.run_dir),
        last_rebase_vllm_commit=ctx.state.get("last_rebase_upstream_commit",
                                              ""),
        # the prompt's CUDA/HF facts must describe THIS host, not the
        # dataclass defaults
        cuda_devices=os.environ.get("CUDA_VISIBLE_DEVICES", "0,1"),
        hf_home=os.environ.get("HF_HOME", "/model"),
        model_aliases=ctx.settings.model_aliases,
        model_mismatch_policy=ctx.settings.model_mismatch_policy)
    async with _serial_lock(ctx.run_dir):
        outcome = await rebase_module(
            module, client=client, config=config,
            prompt_data=data, tool_defs=defs, extra_tools=tools,
            substate=sub, hooks=hooks,
            scope=_module_scope(repo_root, module, manifest,
                                run_dir=ctx.run_dir),
            module_test_plan=test_plan,
            trace=ctx.trace)
    return StepResult(True,
                      summary=f"{module}: {outcome['status']} "
                              f"(debug_attempts={outcome['debug_attempts']})",
                      outputs={"state_updates": {
                          f"module_{module}_status": outcome["status"]}})


@step("rebase.v3_ci", "script", "push",
      "Remote CI: push, guarded build creation, monitored to terminal.")
async def _v3_ci(ctx: StepContext) -> StepResult:
    """remote_ci/full phase 4: commit-and-push through the PR3 cluster (C4
    double gate inside), then a guarded op-recorded build monitored to a
    terminal state. Requires the CI provider client — absent a token this
    BLOCKS with a declared capability_gap."""
    manifest = _adapter_manifest(ctx)
    if not isinstance(manifest, StepResult):
        blocked = _ensure_checkout_locks(
            ctx, manifest, _task_params(ctx).get("rebase_mode", ""))
        if blocked is not None:
            return blocked
    if not getattr(ctx.settings, "buildkite_api_token", ""):
        ctx.trace.record("capability_gap", capability="ci.provider_client",
                         detail="no CI token — remote CI cannot run")
        return StepResult(False, FailureKind.BLOCKED,
                          "remote CI needs a provider token; run local_ci "
                          "instead")
    return StepResult(False, FailureKind.BLOCKED,
                      "the provider HTTP client lands with the live-run "
                      "wiring (EXT1/PR6 preflight); use local_ci until then")
