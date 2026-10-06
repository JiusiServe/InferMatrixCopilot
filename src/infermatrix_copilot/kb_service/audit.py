"""Provenance: nothing reaches knowledge/ on main without passing the gate (design v8).

Without GitHub-side enforcement a person can still merge (or push) a knowledge
change the gate never saw. This module catches it and undoes it. Every
scheduler tick it walks main's first-parent history from the last audited
commit. A commit whose change (against its first parent) touches
``knowledge/`` is one of:

* trusted: it IS a recorded merge of a knowledge change set (the publisher
  merged it after its local gate), or a two-parent merge of a head such a
  change set recorded that carries nothing but that head's knowledge change,
  or the revert that disposed of an unknown commit;
* pending: a merge of a head whose merge item still waits for its receipt;
* disposed: an unknown commit an EXACT revert was merged for;
* unknown: anything else.

An unknown commit pauses automatic merging for the repositories it touched
(everything, when it touched knowledge outside a repository scope), alerts
people, goes back into intake with its diff as evidence, and gets a revert
PR: governed paths restored to the commit's first-parent tree entries (mode
and content), built by the publisher and NEVER merged automatically. If a
path changed again after the commit, or the commit touched non-governed
paths, people revert it by hand.

A revert disposes of unknown commits only if it is exact: it changes exactly
the governed paths they changed, back to exactly the tree entries they had
before the first of them (a revert PR the service opened must also be the
very commit the publisher built). A hand-made revert is recognised the same
way. The pairs are recorded; both commits are then trusted.

No snapshot is activated past a commit that is unknown or still pending:
``provenance_problems`` checks every commit from the active snapshot up to
the exact SHA ``activate()`` is asked for (so ``kb activate`` cannot bypass
it). The trusted list reaches the publisher through the signed control record.
"""

from __future__ import annotations

import json
import re

from ..knowledge_service.ops import repo_scope

AUDIT_CURSOR = "audit_main_sha"
GRACE = 0  # v8: acted on at once; our own merges waiting for a receipt are "pending", not unknown
UNKNOWN = "unknown:"      # "*" cursors: one record per unknown commit
DISPOSED = "disposed:"    # "*" cursors: unknown commit -> the exact revert that disposed of it
TRUSTED = "trusted_merges"  # "*" cursor: the list the control record carries to the publisher
GOVERNED = ("knowledge/repos/", "knowledge/general/")
SUFFIXES = (".md", ".yaml")
_PR_REF = re.compile(r"Merge pull request #(\d+)|\(#(\d+)\)\s*$", re.M)  # reporting only, never proof
_RECORDED = ("merged",)
TRUSTED_KEEP = 500
DIFF_LIMIT = 8 * 1024


def _governed(path: str) -> bool:
    return path.startswith(GOVERNED) and path.endswith(SUFFIXES)


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


def disposals(rt) -> dict[str, str]:
    return {name[len(DISPOSED):]: value for name, value in rt.ledger.cursors_with_prefix("*", DISPOSED).items()}


def _records(rt) -> dict:
    from .reconcile import trusted_commits

    reviewed = trusted_commits(rt)
    merge_shas, merged_heads, pending = set(), set(), set()
    for lifecycle in rt.registry.values():
        for changeset in rt.ledger.changesets(lifecycle.repo, _RECORDED):
            if changeset["kind"] == "revert" and not changeset["detail"].get("exact"):
                continue  # an inexact revert merge is itself unknown
            if changeset.get("merge_sha"):
                merge_shas.add(changeset["merge_sha"])
            if changeset.get("head_sha"):
                merged_heads.add(changeset["head_sha"])
        for changeset in rt.ledger.changesets(lifecycle.repo, ("merge_requested",)):
            if changeset.get("head_sha"):
                pending.add(changeset["head_sha"])
    disposed = disposals(rt)
    return {"merges": merge_shas | reviewed, "reviewed": reviewed, "heads": merged_heads, "pending": pending,
            "disposed": disposed, "disposing": set(disposed.values())}


def _classify(rt, sha: str, parents: list[str], paths: list[str], recs: dict, target: str) -> str:
    """``target``: the commit the history is checked up to. A disposed commit
    is trusted only when the revert that disposed of it is part of that
    history (main rewound to before the revert brings it back)."""
    if not paths:
        return "none"
    if sha in recs["merges"] or sha in recs["disposing"]:
        return "trusted"
    if sha in recs["disposed"]:
        return "trusted" if rt.knowledge.is_ancestor(recs["disposed"][sha], target) else "unknown"
    if len(parents) == 2 and parents[1] in recs["heads"] and _merge_carries_only_the_head(rt, parents, sha, paths):
        return "trusted"
    if len(parents) == 2 and parents[1] in recs["pending"]:
        return "pending"
    return "unknown"


def _knowledge_paths(rt, sha: str, parents: list[str]) -> list[str]:
    return [p for p in rt.knowledge.changed_names(parents[0] if parents else "", sha) if p.startswith("knowledge/")]


def open_unknown(rt) -> list[str]:
    """Unknown commits not disposed of yet."""
    disposed = disposals(rt)
    from .reconcile import trusted_commits
    reviewed = trusted_commits(rt)
    return sorted(name[len(UNKNOWN):] for name in rt.ledger.cursors_with_prefix("*", UNKNOWN)
                  if name[len(UNKNOWN):] not in disposed and name[len(UNKNOWN):] not in reviewed)


def provenance_problems(rt, sha: str) -> list[str]:
    """Why ``sha`` may not be activated (empty: every knowledge commit from the
    active snapshot up to it is trusted). The very first activation has no
    trusted baseline and is allowed."""
    active = rt.ledger.active_snapshot()
    if not active or active == sha:
        return []
    if not rt.knowledge.is_ancestor(active, sha):
        return [f"{sha[:12]} does not descend from the active snapshot {active[:12]}"]
    recs = _records(rt)
    problems = []
    for commit, parents, _at, _message in rt.knowledge.first_parent_commits(active, sha):
        kind = _classify(rt, commit, parents, _knowledge_paths(rt, commit, parents), recs, sha)
        if kind in ("unknown", "pending"):
            problems.append(f"{commit[:12]} is {kind}")
    return problems


def publish_trusted(rt) -> None:
    """What the publisher may treat as trusted on main (control record)."""
    recs = _records(rt)
    # Supervised trust is never cached: control publication verifies its
    # durable receipts directly, so removal/corruption cannot renew stale trust.
    trusted = sorted((recs["merges"] - recs["reviewed"]) | set(recs["disposed"]) | recs["disposing"])[-TRUSTED_KEEP:]
    rt.ledger.set_cursor("*", TRUSTED, json.dumps(trusted))


def audit_main(rt, pause) -> list[str]:
    """One pass; ``pause(scope, reason)`` pauses a repository ("*": all).
    Returns findings (empty when everything that landed was trusted)."""
    main = rt.knowledge.fetch()
    last = rt.ledger.get_cursor("*", AUDIT_CURSOR)
    if not last:
        rt.ledger.set_cursor("*", AUDIT_CURSOR, main)  # first run: the baseline
        publish_trusted(rt)
        return []
    findings: list[str] = []
    audited = last
    for sha, parents, committed_at, message in rt.knowledge.first_parent_commits(last, main):
        if rt.clock() - committed_at < GRACE:
            break
        paths = _knowledge_paths(rt, sha, parents)
        kind = _classify(rt, sha, parents, paths, _records(rt), main)
        if kind == "pending":
            break  # our own merge; its receipt records it next tick: look again then
        audited = sha
        if kind in ("none", "trusted") or rt.ledger.get_cursor("*", UNKNOWN + sha):
            continue
        if _dispose_by_revert(rt, sha, parents, paths):
            continue  # an exact revert (by hand, or of a PR merged around the service)
        findings.append(_unknown(rt, pause, sha, parents, message, paths, main))
    rt.ledger.set_cursor("*", AUDIT_CURSOR, audited)
    _issue_pending_reverts(rt, main)
    publish_trusted(rt)
    return findings


def _dispose_by_revert(rt, sha: str, parents: list[str], paths: list[str]) -> list[str]:
    """Whether ``sha`` completes the revert of open unknown commits. The set
    is every open unknown commit sharing a knowledge path with ``sha``, and,
    transitively, with those (a partial revert made earlier is itself one of
    them). It is disposed of when ``sha`` changes only paths of the set and,
    after it, EVERY path the set touched (governed or not) holds exactly the
    tree entry it had before the earliest commit of the set: together they
    changed nothing. Returns the commits disposed of."""
    import functools

    if not paths or not parents:
        return []
    records = {u: json.loads(rt.ledger.get_cursor("*", UNKNOWN + u) or "{}") for u in open_unknown(rt)}
    # history order (ancestors first): the earliest commit's pre-image wins
    in_order = sorted(records, key=functools.cmp_to_key(
        lambda a, b: -1 if rt.knowledge.is_ancestor(a, b) else (1 if rt.knowledge.is_ancestor(b, a) else 0)))
    targets, touched = [], set(paths)
    grew = True
    while grew:
        grew = False
        for unknown in in_order:
            if unknown not in targets and set(records[unknown].get("pre") or {}) & touched:
                targets.append(unknown)
                touched |= set(records[unknown].get("pre") or {})
                grew = True
    if not targets:
        return []
    covered: dict[str, str] = {}
    for unknown in in_order:
        if unknown in targets:
            for path, entry in (records[unknown].get("pre") or {}).items():
                covered.setdefault(path, entry)
    if not set(paths) <= set(covered) or rt.knowledge.blob_ids(sha, list(covered)) != covered:
        return []
    for unknown in targets:
        rt.ledger.set_cursor("*", DISPOSED + unknown, sha)
    return targets


def _unknown(rt, pause, sha: str, parents: list[str], message: str, paths: list[str], main: str) -> str:
    refs = [int(a or b) for a, b in _PR_REF.findall(message)]
    scopes = _scopes(paths)
    reason = (f"unrecorded knowledge change {sha[:12]}"
              f"{' (PR #' + str(refs[0]) + ')' if refs else ' (no PR)'} touching {paths[:3]}")
    auto = [s for s in sorted(scopes) if s == "*" or getattr(rt.registry.get(s), "auto_merge", False)]
    for scope in auto:
        pause(scope, f"provenance: {reason}; nothing is activated until it is reverted")
    # the COMPLETE path list and every path's entry before the commit: a
    # revert is exact only if it restores all of them (reports stay short)
    record = {"scopes": sorted(scopes), "paths": paths, "prs": refs, "paused": auto, "state": "open",
              "parents": parents, "reason": reason, "at": rt.clock(),
              "pre": rt.knowledge.blob_ids(parents[0], paths) if parents else {}}
    revert_repo = next((s for s in auto if s != "*"), None)
    lifecycle = rt.registry.get(revert_repo) if revert_repo else None
    # a revert PR and a candidate both publish the commit's paths and content:
    # only when EVERY repository scope it touches may publish
    public = all(s == "*" or (rt.registry.get(s) is not None and rt.registry[s].publishes) for s in scopes)
    if lifecycle is not None and lifecycle.publishes and public:
        record.update(repo=lifecycle.repo, state="revert_pending")
        # its content goes back through the gate as a candidate of its own
        rt.ledger.record_event(lifecycle.repo, "unrecorded", sha, {
            "source_reference": f"commit {sha}", "title": message.splitlines()[0] if message else sha,
            "body": message[:3000], "changed_files": paths[:50],
            "diff_excerpt": rt.knowledge.diff_text(parents[0] if parents else "", sha, paths)[:DIFF_LIMIT]})
    else:
        record["state"] = "people"
        rt.ledger.enqueue_human(revert_repo or next(iter(rt.registry)), f"{reason}: revert it by hand")
    rt.ledger.set_cursor("*", UNKNOWN + sha, json.dumps(record))
    rt.trace("outcome", context={"playbook": "kb-audit", "repo": ",".join(sorted(scopes))},
             result={"outcome": "unrecorded_merge", "sha": sha, "prs": refs, "paths": paths[:20], "paused": auto})
    return reason


def _issue_pending_reverts(rt, main: str) -> None:
    """Revert PRs for unknown commits that do not have one yet (staging needs
    the scheduler's lease; without it they wait for the next pass)."""
    if not getattr(rt, "lease_owner", None):
        return
    disposed = disposals(rt)
    remaining = set(open_unknown(rt))
    for name, raw in sorted(rt.ledger.cursors_with_prefix("*", UNKNOWN).items(),
                            key=lambda item: json.loads(item[1]).get("at", 0)):
        record = json.loads(raw)
        sha = name[len(UNKNOWN):]
        lifecycle = rt.registry.get(record.get("repo") or "")
        if record.get("state") != "revert_pending" or lifecycle is None or sha in disposed or sha not in remaining:
            continue
        record.update(_issue_revert(rt, lifecycle, sha, record, main))
        rt.ledger.set_cursor("*", name, json.dumps(record))


def _issue_revert(rt, lifecycle, sha: str, record: dict, main: str) -> dict:
    """A revert PR restoring every governed path to its tree entry before the
    commit. Refused (people) when a path is not governed or changed again."""
    from .merge import issue_once

    reason, paths, parents = record["reason"], record["paths"], record.get("parents") or []
    first = parents[0] if parents else ""
    other = [p for p in paths if not _governed(p)]
    if other or not first:
        rt.ledger.enqueue_human(lifecycle.repo, f"{reason}: it touches {other[:3] or 'a root commit'}, "
                                "which the service does not revert; revert it by hand")
        return {"state": "people"}
    landed, now = rt.knowledge.blob_ids(sha, paths), rt.knowledge.blob_ids(main, paths)
    moved = [p for p in paths if landed[p] != now[p]]
    if moved:
        rt.ledger.enqueue_human(lifecycle.repo, f"{reason}: a revert would conflict ({moved[:3]} changed again "
                                "since); revert it by hand (an exact revert unblocks it)")
        return {"state": "conflict", "moved": moved}
    pre = record["pre"]
    if any(entry and not entry.startswith("100644 blob ") for entry in pre.values()):
        rt.ledger.enqueue_human(lifecycle.repo, f"{reason}: a path had a non-regular mode before it; revert it by hand")
        return {"state": "people"}
    files = {p: rt.knowledge.show(first, p) for p, entry in pre.items() if entry}
    deleted = [p for p, entry in pre.items() if not entry]
    changeset_id = rt.ledger.new_changeset_id(lifecycle.repo, "revert")
    rel = lambda p: p[len("knowledge/"):]  # noqa: E731
    rt.save_changeset_files(changeset_id, {"base_sha": main, "files": {rel(p): t for p, t in files.items()},
                                           "deleted": [rel(p) for p in deleted],
                                           "evidence": [{"source_reference": f"commit {sha}", "title": reason}]})
    rt.ledger.stage_intake(rt.lease_owner, lifecycle.repo, changeset_id, kind="revert", status="pr_requested",
                           verdicts=[], human_reason=f"{reason}: review and merge revert PR (changeset {changeset_id})",
                           drafted_events=[], detail={"reverts": sha, "expected": pre, "operations": []})
    issue_once(rt, lifecycle.repo, rt.ledger.changeset(changeset_id), "open_revert_pr", {
        "changeset_id": changeset_id, "base_sha": main, "branch": f"kb/revert/{sha[:12]}",
        "files": files, "deleted": deleted,
        "title": f"knowledge: revert {sha[:12]} (merged without passing the knowledge gate)",
        "body": (f"{reason}.\n\nThis revert restores the governed knowledge pages to their content before "
                 f"`{sha}`. It is never merged automatically: merge it to dispose of the unrecorded change "
                 "(auto-merge then resumes after `kb resume`), or close it and decide otherwise. The reverted "
                 "content has been queued as a new knowledge candidate and goes through the gate.")})
    return {"state": "reverting", "revert_changeset": changeset_id}


def settle_revert(rt, changeset: dict, pr: dict) -> bool:
    """A revert PR was merged: record the disposal only if it is exact (the
    very commit the publisher built, merged with nothing else on governed
    paths, every path back to its tree entry, mode included)."""
    rt.knowledge.fetch()  # the merge commit may be newer than our clone
    merge_sha = str(pr.get("merge_commit_sha") or "")
    detail = changeset["detail"]
    expected: dict[str, str] = detail.get("expected") or {}
    exact = False
    if merge_sha and str((pr.get("head") or {}).get("sha") or "") == changeset.get("head_sha"):
        parents = rt.knowledge.parents(merge_sha)
        if parents:
            changed = {p for p in rt.knowledge.changed_names(parents[0], merge_sha) if p.startswith("knowledge/")}
            exact = changed == set(expected) and rt.knowledge.blob_ids(merge_sha, list(expected)) == expected
    rt.ledger.update_changeset(changeset["id"], status="merged", merge_sha=merge_sha or None,
                               detail={**detail, "exact": exact})
    if exact:
        rt.ledger.set_cursor("*", DISPOSED + detail["reverts"], merge_sha)
    else:
        rt.ledger.enqueue_human(changeset["repo"], (
            f"revert PR #{changeset['pr_number']} for {detail['reverts'][:12]} was merged but is not the exact "
            "revert (modified or with other knowledge changes): the change stays undisposed"), changeset["id"])
    return exact
