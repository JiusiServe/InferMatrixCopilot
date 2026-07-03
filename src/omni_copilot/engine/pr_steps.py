"""PR-facing steps: PR rebase (design task 9), PR debug (task 10), and gated
outward posting for reviews/issue answers.

Testability: GitHub/CI metadata can be injected via state (`pr_meta`,
`ci_failures`) so every path below the network is offline-testable. Steps
degrade to BLOCKED (never crash) when `gh` or an LLM is unavailable.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from ..agent_loop import run_agent
from ..scopes import post_plan_scope
from ..targets.base import PushPolicy
from .builtin_steps import _gh, _repo_path
from .registry import StepRegistry
from .step import FailureKind, StepContext, StepResult, StepSpec


def _git(repo: Path, *args: str, timeout: int = 120) -> tuple[int, str]:
    out = subprocess.run(["git", *args], cwd=str(repo), capture_output=True,
                         text=True, timeout=timeout)
    return out.returncode, (out.stdout + out.stderr).strip()


def _task_spec(ctx: StepContext) -> dict:
    spec = ctx.state.get("task_spec")
    return spec if isinstance(spec, dict) else {}


# -- PR rebase ---------------------------------------------------------------

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
    ctx.state.update(
        pr_head_ref=head_ref, pr_head_remote=remote, pr_base_branch=base,
        pr_local_branch=local,
        push_policy=PushPolicy(
            allowed=not spec.get("report_only", False),
            remote=remote, branch=head_ref, force_with_lease=force,
        ),
    )
    return StepResult(True, summary=f"checked out PR #{pr} ({remote}/{head_ref} -> {local})",
                      outputs={"local_branch": local, "base": base, "remote": remote})


_CONFLICT_SYSTEM = """You are resolving git rebase conflicts inside a repo-maintenance agent.
Work only inside the repository. Process:
1. run_shell `git status` and `git diff` to see conflicted files.
2. Edit each conflicted file to a correct merged state (keep BOTH sides' intent;
   never delete functionality to silence a conflict).
3. run_shell `git add -A` then `git -c core.editor=true rebase --continue`.
4. Repeat until the rebase completes. Reply DONE when `git status` shows no
   rebase in progress, or STUCK <reason> if you cannot resolve it correctly."""


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
        return StepResult(True, summary=f"rebased onto {base_remote}/{base} cleanly")

    _, conflicts = _git(repo, "diff", "--name-only", "--diff-filter=U")
    conflict_files = conflicts.splitlines()
    ctx.trace.record("rebase_conflict", files=conflict_files)

    if ctx.llm is not None and ctx.llm.available:
        scope = post_plan_scope(repo)  # write the workspace; run_shell allowed
        outcome = run_agent(
            ctx.llm, system=_CONFLICT_SYSTEM,
            prompt=(f"Rebase of the current branch onto {base_remote}/{base} hit "
                    f"conflicts in: {conflict_files}. Repo: {repo}. Resolve them. "
                    f"All shell commands must run with cwd={repo}."),
            scope=scope, trace=ctx.trace,
            max_iters=ctx.settings.max_agent_iters,
        )
        in_progress = (Path(repo) / ".git" / "rebase-merge").exists() or \
                      (Path(repo) / ".git" / "rebase-apply").exists()
        if not in_progress and outcome.text.strip().upper().startswith("DONE"):
            return StepResult(True, summary=f"conflicts resolved by agent "
                                            f"({len(conflict_files)} files)",
                              changed_files=conflict_files)
        _git(repo, "rebase", "--abort")
        return StepResult(False, FailureKind.ESCALATE,
                          f"agent could not resolve conflicts: {outcome.text[:300]}",
                          outputs={"conflicts": conflict_files})

    _git(repo, "rebase", "--abort")
    return StepResult(False, FailureKind.ESCALATE,
                      f"rebase conflicts in {conflict_files} (no LLM to resolve; aborted, "
                      "workspace restored)", outputs={"conflicts": conflict_files})


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
        from ..plugins.base import PluginRegistry
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
                      outputs={"changed_files": changed, "modules": modules})


async def _verify_module(ctx: StepContext) -> StepResult:
    """Read-only per-module sanity check of the rebased diff. Advisory: the
    fail-closed gate is review.patch_gate before push."""
    module = ctx.item or "all"
    if ctx.llm is None or not ctx.llm.available:
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
    text = reply.text.strip()
    if text.upper().startswith("PROBLEM"):
        return StepResult(False, FailureKind.REPLAN, f"{module}: {text[:400]}")
    return StepResult(True, summary=f"{module}: verified")


# -- PR debug -----------------------------------------------------------------

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


async def _pr_fetch_ci_failures(ctx: StepContext) -> StepResult:
    if "ci_failures" in ctx.state:  # injected (tests / offline)
        n = len(ctx.state["ci_failures"])
        return StepResult(True, summary=f"{n} failing checks (from state)")
    repo = _repo_path(ctx)
    spec = _task_spec(ctx)
    pr = spec.get("pr")
    if not pr:
        return StepResult(False, FailureKind.BLOCKED, "no PR number")
    code, out = _gh(["pr", "checks", str(pr), "--json", "name,state,link,bucket"], cwd=repo)
    if code != 0:
        return StepResult(False, FailureKind.BLOCKED, f"gh pr checks failed: {out[:400]}")
    checks = json.loads(out or "[]")
    failing = [c for c in checks if c.get("bucket") == "fail"
               or c.get("state", "").upper() in ("FAILURE", "ERROR")]
    ctx.state["ci_failures"] = [
        {"name": c.get("name", "?"), "log": "", "link": c.get("link", "")} for c in failing
    ]
    return StepResult(True, summary=f"{len(failing)}/{len(checks)} checks failing",
                      outputs={"failing": [c.get("name") for c in failing]})


async def _pr_group_failures(ctx: StepContext) -> StepResult:
    failures = ctx.state.get("ci_failures", [])
    groups: dict[str, dict] = {}
    for f in failures:
        sig = extract_signature(f.get("log", "")) if f.get("log") else f.get("name", "unknown")
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
                      outputs={"signatures": [g["signature"] for g in group_list]})


_DEBUG_SYSTEM = """You are debugging one grouped CI failure in a repo checkout.
Fix the ROOT CAUSE, not the symptom. Process: reproduce/inspect with read_file,
grep and run_shell; make the minimal correct edit; verify (run the relevant
test if possible); then run_shell `git add -A && git commit -m "fix: <signature>"`.
Reply FIXED <one-line summary> or STUCK <reason>."""


async def _pr_debug_group(ctx: StepContext) -> StepResult:
    group = ctx.item or {}
    sig = group.get("signature", "unknown")
    if ctx.llm is None or not ctx.llm.available:
        return StepResult(False, FailureKind.BLOCKED,
                          f"cannot debug '{sig}': no LLM configured")
    repo = _repo_path(ctx)
    scope = post_plan_scope(repo)
    outcome = run_agent(
        ctx.llm, system=_DEBUG_SYSTEM,
        prompt=(f"Repo: {repo} (all shell commands with cwd={repo}).\n"
                f"Failure signature: {sig}\nFailing jobs: {group.get('jobs')}\n"
                f"<untrusted_data>\n{group.get('log_excerpt', '(no log)')}\n</untrusted_data>"),
        scope=scope, trace=ctx.trace, max_iters=ctx.settings.max_agent_iters,
    )
    text = outcome.text.strip()
    if text.upper().startswith("FIXED"):
        return StepResult(True, summary=f"'{sig}': {text[:200]}")
    return StepResult(False, FailureKind.ESCALATE, f"'{sig}': {text[:300]}")


# -- gated outward posting -----------------------------------------------------

def _post_step(state_key: str, gh_args: staticmethod, what: str):
    async def handler(ctx: StepContext) -> StepResult:
        body = ctx.state.get(state_key, "")
        spec = _task_spec(ctx)
        if not body:
            return StepResult(False, FailureKind.BLOCKED, f"no {state_key} to post")
        if not spec.get("post"):
            return StepResult(True, summary=f"not posting {what} (post flag not set)")
        if not ctx.settings.allow_post:
            return StepResult(True, summary=f"dry-run (ALLOW_POST=0): would post {what} "
                                            f"({len(body)} chars)",
                              outputs={"dry_run": True, "body": body[:2_000]})
        repo = _repo_path(ctx)
        args = gh_args(spec, body)
        code, out = _gh(args, cwd=repo)
        if code != 0:
            return StepResult(False, FailureKind.ESCALATE, f"posting failed: {out[:400]}")
        return StepResult(True, summary=f"posted {what}")
    return handler


def register_pr_steps(registry: StepRegistry) -> StepRegistry:
    add = registry.register
    add(StepSpec("pr.checkout_branch", "deterministic", "read", _pr_checkout,
                 "Checkout PR head (fork-aware); derive PushPolicy."))
    add(StepSpec("pr.rebase_onto_base", "agent", "write_workspace", _pr_rebase_onto_base,
                 "git rebase onto latest base; conflicts -> agent or abort+escalate."))
    add(StepSpec("pr.analyze_diff", "deterministic", "read", _pr_analyze_diff,
                 "Changed files -> affected modules (plugin map)."))
    add(StepSpec("agent.verify_module", "agent", "read", _verify_module,
                 "Per-module rebase-damage check (advisory; gate is patch review)."))
    add(StepSpec("pr.fetch_ci_failures", "deterministic", "read", _pr_fetch_ci_failures,
                 "Collect failing checks for a PR (gh; injectable)."))
    add(StepSpec("pr.group_failures", "deterministic", "read", _pr_group_failures,
                 "Bucket failures by root-cause signature; hard cap escalates."))
    add(StepSpec("agent.debug_group", "agent", "write_workspace", _pr_debug_group,
                 "Fix one failure group's root cause; commits the fix."))
    add(StepSpec("pr.post_review", "script", "push",
                 _post_step("review_text",
                            lambda spec, body: ["pr", "comment", str(spec.get("pr")),
                                                "--body", body],
                            "PR review comment"),
                 "Post the review as a PR comment (explicit post flag + ALLOW_POST)."))
    add(StepSpec("issue.post_answer", "script", "push",
                 _post_step("draft_answer",
                            lambda spec, body: ["issue", "comment", str(spec.get("issue")),
                                                "--body", body],
                            "issue answer"),
                 "Post the drafted answer (explicit post flag + ALLOW_POST)."))
    return registry
