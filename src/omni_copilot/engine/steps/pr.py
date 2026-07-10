"""PR-facing steps: guarded push, diff/gate fetch, PR rebase (design task 9),
PR debug (task 10), and gated review posting.

Testability: GitHub/CI metadata can be injected via state (`pr_meta`,
`ci_failures`, `diff_text`, `gate_report`) so every path below the network is
offline-testable. Steps degrade to BLOCKED (never crash) when `gh` or an LLM is
unavailable.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict
from pathlib import Path

from ...scopes import post_plan_scope
from ...targets.base import PushPolicy, guard_push
from ..step import FailureKind, StepContext, StepResult, StepSpec
from ._common import gh as _gh
from ._common import git as _git
from ._common import post_step as _post_step
from ._common import register_step
from ._common import repo_path as _repo_path
from ._common import step
from ._common import task_spec as _task_spec


# -- guarded push --------------------------------------------------------------

@step("ci.push", "script", "push",
      "Guarded push (PushPolicy AND protected branches; dry-run default).")
async def _push(ctx: StepContext) -> StepResult:
    repo = _repo_path(ctx)
    raw = ctx.state.get("push_policy")
    policy = raw if isinstance(raw, PushPolicy) else PushPolicy(**(raw or {}))
    protected = ctx.state.get("protected_branches") or ctx.settings.protected_branches
    ctx.trace.record("push_requested", remote=policy.remote, branch=policy.branch)
    decision = guard_push(policy, list(protected))
    if not decision.allowed:
        return StepResult(False, FailureKind.FORBIDDEN, decision.reason)
    if not ctx.settings.allow_push:
        return StepResult(True, summary=f"dry-run (ALLOW_PUSH=0): {' '.join(decision.command)}",
                          outputs={"dry_run": True, "command": list(decision.command)})
    out = subprocess.run(list(decision.command), cwd=str(repo), capture_output=True,
                         text=True, timeout=300)
    if out.returncode != 0:
        return StepResult(False, FailureKind.ESCALATE,
                          f"push failed: {out.stderr[-1_000:]}")
    return StepResult(True, summary=f"pushed {policy.remote} HEAD:{policy.branch}")


# -- read-only fetch steps -----------------------------------------------------

@step("pr.fetch_diff", "deterministic", "read",
      "Fetch a PR diff via gh (read-only).")
async def _pr_fetch_diff(ctx: StepContext) -> StepResult:
    if "diff_text" in ctx.state:  # injected (tests / offline)
        return StepResult(True, summary="diff from state",
                          outputs={"chars": len(ctx.state["diff_text"]),
                                   "state_updates": {"diff_text": ctx.state["diff_text"]}})
    spec = ctx.state.get("task_spec") or {}
    pr = spec.get("pr") if isinstance(spec, dict) else None
    repo = _repo_path(ctx)
    if not pr:
        return StepResult(False, FailureKind.BLOCKED, "no PR number in task spec")
    if repo is None or not repo.exists():
        return StepResult(False, FailureKind.BLOCKED,
                          f"repo checkout not configured (repo_path={repo}) — set "
                          "REPO_PATHS in .env or a plugin repo.path")
    code, out = _gh(["pr", "diff", str(pr)], cwd=repo)
    if code != 0:
        return StepResult(False, FailureKind.BLOCKED, f"gh pr diff failed: {out[:500]}")
    ctx.state["diff_text"] = out
    return StepResult(True, summary=f"fetched PR #{pr} diff ({len(out)} chars)",
                      outputs={"state_updates": {"diff_text": out}})


@step("pr.gate_check", "deterministic", "read",
      "Draft/merge-state/failing-checks gate report (deterministic).")
async def _pr_gate_check(ctx: StepContext) -> StepResult:
    """Deterministic gate check: draft/merge-state/failing checks — the issue
    class the eval showed no diff-only reviewer catches. Non-blocking: the
    findings go into the review context and the report."""
    if "gate_report" in ctx.state:  # injected (tests / offline)
        return StepResult(True, summary="gate report from state",
                          outputs={"state_updates": {"gate_report": ctx.state["gate_report"]}})
    spec = ctx.state.get("task_spec") or {}
    pr = spec.get("pr") if isinstance(spec, dict) else None
    if not pr:
        return StepResult(False, FailureKind.BLOCKED, "no PR number in task spec")
    repo = _repo_path(ctx)
    lines: list[str] = []
    code, out = _gh(["pr", "view", str(pr), "--json",
                     "state,isDraft,mergeable,mergeStateStatus"], cwd=repo)
    if code != 0:
        ctx.state["gate_report"] = "gate check unavailable (gh failed)"
        return StepResult(True, summary="gate check unavailable (gh failed) — "
                                        "continuing without it",
                          outputs={"state_updates":
                                   {"gate_report": ctx.state["gate_report"]}})
    data = json.loads(out or "{}")
    if data.get("isDraft"):
        lines.append("PR is a DRAFT — review findings are provisional.")
    if data.get("mergeable") == "CONFLICTING" or \
            data.get("mergeStateStatus") in ("DIRTY", "BEHIND"):
        lines.append(f"MERGE STATE: {data.get('mergeStateStatus')} / "
                     f"{data.get('mergeable')} — the branch conflicts with or "
                     "trails the base; files may have moved/renamed on main. "
                     "Flag this as a blocking issue.")
    code, out = _gh(["pr", "checks", str(pr), "--json", "name,state,bucket"],
                    cwd=repo)
    if code == 0:
        failing = [c.get("name", "?") for c in json.loads(out or "[]")
                   if c.get("bucket") == "fail"
                   or c.get("state", "").upper() in ("FAILURE", "ERROR")]
        if failing:
            lines.append(f"FAILING CHECKS ({len(failing)}): {failing[:8]} — "
                         "do not re-argue what CI already reports; point at the gate.")
    report = "\n".join(lines) or "gates clean (mergeable, no failing checks)"
    ctx.state["gate_report"] = report
    return StepResult(True, summary=report.splitlines()[0][:120],
                      outputs={"gate_report": report,
                               "state_updates": {"gate_report": report}})


# -- PR rebase -----------------------------------------------------------------

@step("pr.checkout_branch", "deterministic", "read",
      "Checkout PR head (fork-aware); derive PushPolicy.")
async def _pr_checkout(ctx: StepContext) -> StepResult:
    """Fetch PR metadata, add the fork remote if needed, check out a local
    pr-<N>-<head> branch, and derive the PushPolicy for later steps."""
    repo = _repo_path(ctx)
    spec = _task_spec(ctx)
    pr = spec.get("pr")
    if repo is None or not pr:
        return StepResult(False, FailureKind.BLOCKED, "need repo path and PR number")

    meta = ctx.state.get("pr_meta")  # injected in tests / offline
    if meta is None:
        code, out = _gh(["pr", "view", str(pr), "--json",
                         "headRefName,baseRefName,state,isCrossRepository,"
                         "headRepository,headRepositoryOwner"], cwd=repo)
        if code != 0:
            return StepResult(False, FailureKind.BLOCKED, f"gh pr view failed: {out[:400]}")
        meta = json.loads(out)
    if meta.get("state") and meta["state"] != "OPEN":
        return StepResult(False, FailureKind.BLOCKED,
                          f"PR #{pr} is {meta['state']} — nothing to do")

    head_ref = meta["headRefName"]
    base = meta.get("baseRefName") or "main"
    remote = meta.get("remote") or "origin"  # tests may name a local remote
    if meta.get("isCrossRepository") and "remote" not in meta:
        owner = meta["headRepositoryOwner"]["login"]
        name = meta["headRepository"]["name"]
        remote = f"fork-{owner}"
        rc, remotes = _git(repo, "remote")
        if remote not in remotes.split():
            _git(repo, "remote", "add", remote, f"https://github.com/{owner}/{name}.git")

    rc, out = _git(repo, "fetch", remote, head_ref)
    if rc != 0:
        return StepResult(False, FailureKind.BLOCKED, f"fetch {remote}/{head_ref} failed: {out[:400]}")
    local = f"pr-{pr}-{head_ref}".replace("/", "-")
    rc, out = _git(repo, "checkout", "-B", local, "FETCH_HEAD")
    if rc != 0:
        return StepResult(False, FailureKind.BLOCKED, f"checkout failed: {out[:400]}")

    force = bool(ctx.params.get("force_push", False))
    policy = PushPolicy(
        allowed=not spec.get("report_only", False),
        remote=remote, branch=head_ref, force_with_lease=force,
    )
    ctx.state.update(
        pr_head_ref=head_ref, pr_head_remote=remote, pr_base_branch=base,
        pr_local_branch=local, push_policy=policy,
    )
    return StepResult(True, summary=f"checked out PR #{pr} ({remote}/{head_ref} -> {local})",
                      outputs={"local_branch": local, "base": base, "remote": remote,
                               # push_policy serialized JSON-simple; ci.push
                               # rehydrates dicts back into a PushPolicy
                               "state_updates": {
                                   "pr_head_ref": head_ref, "pr_head_remote": remote,
                                   "pr_base_branch": base, "pr_local_branch": local,
                                   "push_policy": asdict(policy),
                               }})


_CONFLICT_GUIDANCE = """You are resolving git rebase conflicts. Work only inside the repository.
Process:
1. run_shell `git status` and `git diff` to see conflicted files.
2. Edit each conflicted file to a correct merged state (keep BOTH sides' intent;
   never delete functionality to silence a conflict).
3. run_shell `git add -A` then `git -c core.editor=true rebase --continue`.
4. Repeat until `git status` shows no rebase in progress.
Set status=success only when the rebase has fully completed; otherwise
status=blocked with the reason."""


@step("pr.rebase_onto_base", "agent", "write_workspace",
      "git rebase onto latest base; conflicts -> governed agent step "
      "(unified runtime) or abort+escalate.")
async def _pr_rebase_onto_base(ctx: StepContext) -> StepResult:
    repo = _repo_path(ctx)
    base = ctx.state.get("pr_base_branch", "main")
    base_remote = ctx.params.get("base_remote", "origin")
    rc, out = _git(repo, "fetch", base_remote, base)
    if rc != 0:
        return StepResult(False, FailureKind.BLOCKED, f"fetch {base_remote}/{base} failed: {out[:400]}")
    rc, base_sha = _git(repo, "rev-parse", "FETCH_HEAD")
    ctx.state["rebase_base_sha"] = base_sha

    rc, out = _git(repo, "rebase", "FETCH_HEAD")
    if rc == 0:
        return StepResult(True, summary=f"rebased onto {base_remote}/{base} cleanly",
                          outputs={"state_updates": {"rebase_base_sha": base_sha}})

    _, conflicts = _git(repo, "diff", "--name-only", "--diff-filter=U")
    conflict_files = conflicts.splitlines()
    ctx.trace.record("rebase_conflict", files=conflict_files)

    if ctx.llm is not None and ctx.llm.available:
        from ..agent_runtime import run_agent_step

        result, output = await run_agent_step(
            ctx, step_name="pr.rebase_conflicts",
            purpose=f"Resolve the rebase conflicts onto {base_remote}/{base} "
                    "and complete the rebase.",
            guidance=_CONFLICT_GUIDANCE,
            expected="status=success only when the rebase fully completed",
            evidence={"conflict_files": "\n".join(conflict_files),
                      "repo_note": f"Repo: {repo}. All shell commands must run "
                                   f"with cwd={repo}."},
            output_extension={"resolution_summary":
                              "how each conflict was resolved"},
            scope=post_plan_scope(repo),  # write the workspace; run_shell allowed
            max_iters=ctx.settings.max_agent_iters,
        )
        in_progress = (Path(repo) / ".git" / "rebase-merge").exists() or \
                      (Path(repo) / ".git" / "rebase-apply").exists()
        if result.ok and not in_progress:
            outputs = {**result.outputs}
            outputs.setdefault("state_updates", {})["rebase_base_sha"] = base_sha
            return StepResult(True, summary=f"conflicts resolved by agent "
                                            f"({len(conflict_files)} files): "
                                            f"{output.get('resolution_summary', '')[:150]}",
                              changed_files=conflict_files, outputs=outputs)
        _git(repo, "rebase", "--abort")
        return StepResult(False, FailureKind.ESCALATE,
                          f"agent could not resolve conflicts: {result.summary[:300]}",
                          outputs={"conflicts": conflict_files})

    _git(repo, "rebase", "--abort")
    return StepResult(False, FailureKind.ESCALATE,
                      f"rebase conflicts in {conflict_files} (no LLM to resolve; aborted, "
                      "workspace restored)", outputs={"conflicts": conflict_files})


@step("pr.analyze_diff", "deterministic", "read",
      "Changed files -> affected modules (plugin map).")
async def _pr_analyze_diff(ctx: StepContext) -> StepResult:
    repo = _repo_path(ctx)
    base_sha = ctx.state.get("rebase_base_sha", "HEAD~1")
    rc, out = _git(repo, "diff", "--numstat", f"{base_sha}..HEAD")
    changed: list[str] = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            changed.append(parts[2])

    # module mapping: plugin first, top-level dir fallback
    plugin = None
    try:
        from ...plugins.base import PluginRegistry
        plugin = PluginRegistry(ctx.settings.plugins_dir).resolve(
            repo_path=str(repo)) if repo else None
    except Exception:
        plugin = None
    modules: list[str] = []
    for path in changed:
        mod = plugin.module_for_path(path) if plugin else None
        mod = mod or (path.split("/")[0] if "/" in path else "root")
        if mod not in modules:
            modules.append(mod)

    ctx.state["affected_modules"] = modules
    ctx.state["touched_modules"] = modules
    ctx.state["primary_files"] = [f"*{c}" for c in changed]
    return StepResult(True, summary=f"{len(changed)} files across modules {modules}",
                      outputs={"changed_files": changed, "modules": modules,
                               "state_updates": {
                                   "affected_modules": modules,
                                   "touched_modules": modules,
                                   "primary_files": ctx.state["primary_files"],
                               }})


@step("agent.verify_module", "validation", "read",
      "Per-module rebase-damage check — plain-LLM advisory validation, NOT a "
      "governed agent step (gate is patch review).")
async def _verify_module(ctx: StepContext) -> StepResult:
    """Read-only per-module sanity check of the rebased diff. Advisory: the
    fail-closed gate is review.patch_gate before push."""
    module = ctx.item or "all"
    if ctx.llm is None or not ctx.llm.available:
        ctx.trace.record("capability_gap", capability="llm",
                         step="agent.verify_module",
                         effect="advisory verification skipped; patch gate "
                                "before push remains fail-closed")
        return StepResult(True, summary=f"{module}: verification skipped (no LLM); "
                                        "patch gate before push remains fail-closed")
    repo = _repo_path(ctx)
    base_sha = ctx.state.get("rebase_base_sha", "HEAD~1")
    _, diff = _git(repo, "diff", f"{base_sha}..HEAD")
    reply = ctx.llm.create(
        system=("You verify a rebased PR branch. Check the diff for rebase damage: "
                "dropped hunks, duplicated code, mis-merged imports, references to "
                "symbols the base no longer has. Reply 'OK' or 'PROBLEM: <details>'."),
        messages=[{"role": "user", "content":
                   f"Module: {module}\n<untrusted_data>\n{diff[:50_000]}\n</untrusted_data>"}],
    )
    if reply.usage:  # plain-LLM call — trace usage for the run's cost metrics
        ctx.trace.record("llm_usage", step="agent.verify_module",
                         input_tokens=reply.usage.get("input_tokens", 0),
                         output_tokens=reply.usage.get("output_tokens", 0))
    text = reply.text.strip()
    if text.upper().startswith("PROBLEM"):
        return StepResult(False, FailureKind.REPLAN, f"{module}: {text[:400]}")
    return StepResult(True, summary=f"{module}: verified")


# -- PR debug ------------------------------------------------------------------

_ERROR_LINE = re.compile(
    r"^(E\s{3}.*|.*(?:Error|Exception|FAILED|fatal error)[:\s].*|AssertionError.*)$",
    re.MULTILINE,
)


def extract_signature(log: str) -> str:
    """Prefer the deepest root-cause-looking line over surface symptoms."""
    matches = [m.group(0).strip() for m in _ERROR_LINE.finditer(log)]
    for line in reversed(matches):  # deepest first
        if not re.search(r"(APIConnectionError|EngineDeadError|ConnectionRefused)", line):
            return line[:200]
    return (matches[-1][:200] if matches else log.strip().splitlines()[-1][:200]
            if log.strip() else "unknown failure")


@step("pr.fetch_ci_failures", "deterministic", "read",
      "Collect failing checks for a PR (gh; injectable).")
async def _pr_fetch_ci_failures(ctx: StepContext) -> StepResult:
    if "ci_failures" in ctx.state:  # injected (tests / offline)
        n = len(ctx.state["ci_failures"])
        return StepResult(True, summary=f"{n} failing checks (from state)",
                          outputs={"state_updates":
                                   {"ci_failures": ctx.state["ci_failures"]}})
    repo = _repo_path(ctx)
    spec = _task_spec(ctx)
    pr = spec.get("pr")
    if not pr:
        return StepResult(False, FailureKind.BLOCKED, "no PR number")
    code, out = _gh(["pr", "checks", str(pr), "--json", "name,state,link,bucket"], cwd=repo)
    if code != 0:
        return StepResult(False, FailureKind.BLOCKED, f"gh pr checks failed: {out[:400]}")
    checks = json.loads(out or "[]")
    # full pre-fix snapshot (not just failures): the F2P/P2P metric needs the
    # before-state to compare a post-push snapshot against (METRICS_RESEARCH §2)
    snapshot = {c.get("name", "?"): (c.get("bucket") or c.get("state", ""))
                for c in checks}
    ctx.state["ci_check_snapshot"] = snapshot
    ctx.trace.record("ci_check_snapshot", when="pre_fix", checks=snapshot)
    failing = [c for c in checks if c.get("bucket") == "fail"
               or c.get("state", "").upper() in ("FAILURE", "ERROR")]
    ctx.state["ci_failures"] = [
        {"name": c.get("name", "?"), "log": "", "link": c.get("link", "")} for c in failing
    ]
    enriched = _enrich_ci_logs(ctx, repo)
    return StepResult(True, summary=f"{len(failing)}/{len(checks)} checks failing"
                                    + (f", {enriched} log(s) fetched"
                                       if enriched else ""),
                      outputs={"failing": [c.get("name") for c in failing],
                               "state_updates": {
                                   "ci_failures": ctx.state["ci_failures"],
                                   "ci_check_snapshot": snapshot,
                               }})


def _enrich_ci_logs(ctx: StepContext, repo: Path | None) -> int:
    """Fetch real failure logs via the profile-selected CI provider.
    Best-effort: a missing provider is a recorded capability gap (pr-debug
    degrades to name grouping), never a failure."""
    failures = ctx.state.get("ci_failures") or []
    if not failures:
        return 0
    from ...ci.providers import provider_for
    from ..agent_runtime import _resolve_plugin

    provider, gap = provider_for(_resolve_plugin(ctx), ctx.settings,
                                 gh_runner=lambda args, cwd=None:
                                 _gh(args, cwd=cwd or repo))
    if provider is None:
        ctx.trace.record("capability_gap", capability="ci.provider",
                         step="pr.fetch_ci_failures", reason=gap,
                         effect="no CI logs; failures grouped by check name")
        return 0
    enriched = provider.enrich(failures)
    ctx.trace.record("ci_logs_enriched", provider=type(provider).__name__,
                     enriched=enriched, total=len(failures))
    return enriched


@step("pr.group_failures", "deterministic", "read",
      "Bucket failures by root-cause signature; hard cap escalates.")
async def _pr_group_failures(ctx: StepContext) -> StepResult:
    from ...ci.normalize import normalize_signature

    failures = ctx.state.get("ci_failures", [])
    groups: dict[str, dict] = {}
    for f in failures:
        sig = extract_signature(f.get("log", "")) if f.get("log") else f.get("name", "unknown")
        sig = normalize_signature(sig)  # same failure ≠ new failure per run
        g = groups.setdefault(sig, {"signature": sig, "jobs": [], "log_excerpt": ""})
        g["jobs"].append(f.get("name", "?"))
        if f.get("log") and not g["log_excerpt"]:
            g["log_excerpt"] = f["log"][-4_000:]
    group_list = list(groups.values())
    max_groups = ctx.settings.pr_debug_max_groups
    if len(group_list) > max_groups:
        return StepResult(False, FailureKind.ESCALATE,
                          f"{len(group_list)} distinct failure groups exceeds the "
                          f"safety cap of {max_groups} — this PR needs a human",
                          outputs={"signatures": [g["signature"] for g in group_list]})
    ctx.state["failure_groups"] = group_list
    return StepResult(True, summary=f"{len(failures)} failures -> {len(group_list)} root-cause groups",
                      outputs={"signatures": [g["signature"] for g in group_list],
                               "state_updates": {"failure_groups": group_list}})


_DEBUG_GUIDANCE = """You are debugging one grouped CI failure in a repo checkout.
Fix the ROOT CAUSE, not the symptom. Process: reproduce/inspect with read_file,
grep and run_shell; make the minimal correct edit; verify (run the relevant
test if possible, record it in tests_run); then run_shell
`git add -A && git commit -m "fix: <signature>"`.
status=success only after the fix is committed; otherwise status=failed with
failure_kind=escalate and an honest root_cause of what you found."""


@step("agent.debug_group", "agent", "write_workspace",
      "Fix one failure group's root cause; commits the fix.")
async def _pr_debug_group(ctx: StepContext) -> StepResult:
    group = ctx.item or {}
    sig = group.get("signature", "unknown")
    repo = _repo_path(ctx)
    if repo is None:
        return StepResult(False, FailureKind.BLOCKED, "no repo path")
    from ..agent_runtime import run_agent_step

    result, output = await run_agent_step(
        ctx, step_name="agent.debug_group",
        purpose=f"Fix the root cause of the grouped CI failure: {sig}",
        guidance=_DEBUG_GUIDANCE,
        expected="root_cause + fix_summary + verification; fix committed",
        evidence={"failure_signature": sig,
                  "failing_jobs": str(group.get("jobs")),
                  "ci_log_excerpt": group.get("log_excerpt", "(no log)"),
                  "repo_note": f"Repo: {repo}; all shell commands with cwd={repo}."},
        output_extension={"root_cause": "the actual root cause found",
                          "fix_summary": "what was changed",
                          "verification": "how the fix was verified"},
        scope=post_plan_scope(repo),
        max_iters=ctx.settings.max_agent_iters,
    )
    if result.ok:
        result.summary = (f"'{sig}': {output.get('fix_summary', '')[:150]} "
                          f"(verified: {output.get('verification', '?')[:80]})")
    else:
        result.summary = f"'{sig}': {result.summary[:250]}"
    return result


# -- gated review posting ------------------------------------------------------

register_step(StepSpec(
    "pr.post_review", "script", "push",
    _post_step("review_text",
               lambda spec, body: ["pr", "comment", str(spec.get("pr")),
                                    "--body", body],
               "PR review comment"),
    "Post the review as a PR comment (explicit post flag + ALLOW_POST)."))
