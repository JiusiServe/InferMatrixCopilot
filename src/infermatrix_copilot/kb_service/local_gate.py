"""The publisher's local gate: the last check before a knowledge PR is merged.

The publisher is the only thing that merges knowledge PRs (design v8). Right
before each merge it verifies, on its own machine and with the Copilot version
it has installed (never code from the PR or from main), the exact tree that
would land: the current tip of ``main`` merged with the PR head.

    verdict signature + binding (repository, PR, head, issue window)
    -> every changed path is a governed page of the item's own repository
    -> the change as applied equals the signed manifest (base independent)
    -> L1 on the change and on the merged tree, block coverage, consistency
       hashes, context-base check (``gate_verifier.verify_change``)
    -> no new tree-level issue on the merged tree

The same checks run once more on the merge commit GitHub actually made
(``post_merge_problems``): ``main`` can move in the seconds between the check
and the merge.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..knowledge_service.gate_verifier import (
    Context, GateError, Git, touches_knowledge, tree_problems, verify_change,
)
from ..knowledge_service.ops import repo_scope
from ..knowledge_service.signing import SignatureError, verify
from ..knowledge_service.verdict import VerdictError, check_binding

GOVERNED_PREFIX = "knowledge/"


class LocalGateError(RuntimeError):
    """The local gate could not run (git or GitHub trouble); retried later."""


def _scope_problems(entries: list[dict], repo: str) -> list[str]:
    """Every changed path must be inside the item's own repository scope."""
    problems = []
    for entry in entries:
        path = entry["path"]
        if not path.startswith(GOVERNED_PREFIX):
            problems.append(f"{path}: outside knowledge/ (split the PR)")
            continue
        try:
            scope = repo_scope(path[len(GOVERNED_PREFIX):])
        except ValueError:
            problems.append(f"{path}: not a governed knowledge page")
            continue
        name = scope.split("/")[-1]
        if name != repo:
            problems.append(f"{path}: belongs to {name}, not to {repo} (one repository per PR)")
    return problems


def check_verdict(envelope: Any, public_key, *, repository: str, pr: int, head_sha: str,
                  now: float) -> dict:
    try:
        verdict = verify("kb-gate-verdict", envelope, public_key)
        check_binding(verdict, repository=repository, pr=pr, head_sha=head_sha, now=now)
    except (SignatureError, VerdictError, KeyError, TypeError, ValueError) as exc:
        raise VerdictError(f"verdict: {exc}") from exc
    if verdict.get("source") != "auto":
        raise VerdictError("only auto verdicts merge (there is no human-approved path)")
    return verdict


def gate(clone: Path, *, repository: str, repo: str, pr: dict, head_sha: str, main_sha: str,
         verdict: dict, public_key, now: float) -> list[str]:
    """Problems with merging ``head_sha`` into ``main_sha`` (empty = pass)."""
    git = Git(clone)
    try:
        base = git.merge_base(main_sha, head_sha)
        entries = git.raw_diff(base, head_sha)
        if not touches_knowledge(entries):
            return ["the PR changes nothing under knowledge/"]
        problems = _scope_problems(entries, repo)
        final = git.merge_tree(main_sha, head_sha)
    except GateError as exc:
        return [str(exc)]
    ctx = Context(git=git, github=None, repository=repository, public_key=public_key,
                  holds_loader=lambda: {}, codeowners=[], now=now)
    problems += verify_change(ctx, pr=pr, head_sha=head_sha, pre=base, post=head_sha, final=final,
                              effective_base=main_sha, stage="local", verdict=verdict, check_holds=False)
    problems += tree_problems(git, main_sha, final)
    return problems


def post_merge_problems(clone: Path, *, repository: str, pr: dict, head_sha: str, merge_sha: str,
                        verdict: dict, public_key, now: float) -> list[str]:
    """The same checks on the merge commit that landed, against its first parent."""
    git = Git(clone)
    try:
        parents = git.parents(merge_sha)
    except GateError as exc:  # not fetched yet, or git trouble: the check could not run
        raise LocalGateError(str(exc)) from exc
    if len(parents) != 2 or parents[1] != head_sha:
        return [f"merge commit {merge_sha[:12]} is not a merge of the verified head"]
    first = parents[0]
    ctx = Context(git=git, github=None, repository=repository, public_key=public_key,
                  holds_loader=lambda: {}, codeowners=[], now=now)
    landed = {**pr, "state": "open"}  # it was open when it merged
    problems = verify_change(ctx, pr=landed, head_sha=head_sha, pre=first, post=merge_sha, final=merge_sha,
                             effective_base=first, stage="local", verdict=verdict, check_holds=False)
    return problems + tree_problems(git, first, merge_sha)
