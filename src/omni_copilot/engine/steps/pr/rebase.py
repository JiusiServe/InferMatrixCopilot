"""PR rebase steps: check out the PR head (fork-aware) and derive the
PushPolicy, rebase onto the latest base (conflicts → a governed agent step, or
abort+escalate when no LLM), map the changed files to modules, and run the
per-module advisory verification.

The fail-closed gate is `review.patch_gate` before push; `agent.verify_module`
here is advisory only.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from ....push import PushPolicy
from ....scopes import post_plan_scope
from ...step import FailureKind, StepContext, StepResult
from .._common import no_llm_gap, published, step
from .._common import gh as _gh
from .._common import git as _git
from .._common import repo_path as _repo_path
from .._common import task_spec as _task_spec


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
        from ...agent_runtime import run_agent_step

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
        from ....plugins.base import PluginRegistry
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
    return published(f"{len(changed)} files across modules {modules}",
                     changed_files=changed, modules=modules,
                     state={"affected_modules": modules, "touched_modules": modules,
                            "primary_files": ctx.state["primary_files"]})


@step("agent.verify_module", "validation", "read",
      "Per-module rebase-damage check — plain-LLM advisory validation, NOT a "
      "governed agent step (gate is patch review).")
async def _verify_module(ctx: StepContext) -> StepResult:
    """Read-only per-module sanity check of the rebased diff. Advisory: the
    fail-closed gate is review.patch_gate before push."""
    module = ctx.item or "all"
    if ctx.llm is None or not ctx.llm.available:
        return no_llm_gap(ctx, "agent.verify_module",
                          "advisory verification skipped; patch gate before push "
                          "remains fail-closed",
                          summary=f"{module}: verification skipped (no LLM); patch "
                                  "gate before push remains fail-closed")
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
