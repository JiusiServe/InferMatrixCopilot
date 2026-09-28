"""Daily post-merge audit: nothing reaches knowledge/ on main without a record.

The gate constrains every merge path the service knows about; this audit
catches the ones it does not (an admin bypass, a direct push, a merge the
ledger missed). It walks main's first-parent history from the last audited
commit. Every commit whose change (against its first parent) touches
``knowledge/`` must be the recorded merge of a knowledge change set: its SHA
is a change set's merge SHA, or it merges a PR the ledger recorded as merged.
Anything else pauses auto-merge for the repositories it touched (everything,
when it touched knowledge outside a repository scope) and goes to people;
repositories not in auto_merge only get a trace record.

Commits younger than ``GRACE`` wait for the next run: the scheduler records a
merge only when it next looks at the PR, and the audit must not race it.
"""

from __future__ import annotations

import re

from ..knowledge_service.ops import repo_scope

AUDIT_CURSOR = "audit_main_sha"
GRACE = 2 * 3600
_PR_REF = re.compile(r"Merge pull request #(\d+)|\(#(\d+)\)\s*$", re.M)  # reporting only, never proof
_RECORDED = ("merged",)


def _scopes(paths: list[str]) -> set[str]:
    scopes = set()
    for path in paths:
        try:
            scopes.add(repo_scope(path[len("knowledge/"):]).split("/")[-1])
        except Exception:  # noqa: BLE001 - knowledge/tools, top-level pages...
            scopes.add("*")
    return scopes


def _merge_carries_only_the_head(rt, parents: list[str], sha: str, paths: list[str]) -> bool:
    """A merge of a recorded head changed knowledge ONLY as that head did: every
    knowledge path it changed was changed by the PR (merge base..head) and
    holds exactly the head's content. Extra edits in the merge are unrecorded."""
    first, head = parents
    base = rt.knowledge.merge_base(first, head)
    pr_paths = {p for p in rt.knowledge.changed_names(base, head) if p.startswith("knowledge/")}
    if not set(paths) <= pr_paths:
        return False
    return rt.knowledge.blob_ids(sha, paths) == rt.knowledge.blob_ids(head, paths)


def audit_main(rt, pause) -> list[str]:
    """One audit pass; ``pause(scope, reason)`` pauses a repository ("*": all).
    Returns findings (empty when everything that landed was recorded)."""
    main = rt.knowledge.fetch()
    last = rt.ledger.get_cursor("*", AUDIT_CURSOR)
    if not last:
        rt.ledger.set_cursor("*", AUDIT_CURSOR, main)  # first run: the baseline
        return []
    # proof is structural, never a commit message: the commit IS a recorded
    # merge SHA, or it is a two-parent merge of the exact head a merged change
    # set recorded (what the merge queue lands)
    merge_shas, merged_heads = set(), set()
    for lifecycle in rt.registry.values():
        for changeset in rt.ledger.changesets(lifecycle.repo, _RECORDED):
            if changeset.get("merge_sha"):
                merge_shas.add(changeset["merge_sha"])
            if changeset.get("head_sha"):
                merged_heads.add(changeset["head_sha"])
    findings: list[str] = []
    audited = last
    for sha, parents, committed_at, message in rt.knowledge.first_parent_commits(last, main):
        if rt.clock() - committed_at < GRACE:
            break  # too recent to judge: the next run starts here
        audited = sha
        paths = [p for p in rt.knowledge.changed_names(parents[0] if parents else "", sha)
                 if p.startswith("knowledge/")]
        if not paths:
            continue
        refs = [int(a or b) for a, b in _PR_REF.findall(message)]
        if sha in merge_shas or (len(parents) == 2 and parents[1] in merged_heads
                                 and _merge_carries_only_the_head(rt, parents, sha, paths)):
            continue
        scopes = _scopes(paths)
        reason = (f"unrecorded knowledge change {sha[:12]}"
                  f"{' (PR #' + str(refs[0]) + ')' if refs else ' (no PR)'} touching {paths[:3]}")
        auto = [s for s in sorted(scopes) if s == "*" or getattr(rt.registry.get(s), "auto_merge", False)]
        for scope in auto:
            pause(scope, f"daily audit: {reason}")
        rt.trace("outcome", context={"playbook": "kb-audit", "repo": ",".join(sorted(scopes))},
                 result={"outcome": "unrecorded_merge", "sha": sha, "prs": refs, "paths": paths[:20],
                         "paused": auto})
        findings.append(reason)
    rt.ledger.set_cursor("*", AUDIT_CURSOR, audited)
    return findings
