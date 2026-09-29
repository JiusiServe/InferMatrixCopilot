"""Accepting an unknown knowledge commit instead of reverting it (design v8 §8.3).

``kb accept-unknown <sha>`` is the second way to dispose of a commit that
reached ``knowledge/`` on main without passing the gate: the commit's own
change (its first parent to the commit) is judged by the FULL gate (L1, L2,
consistency, upstream facts, a current judge calibration) as a change set of
kind ``accept``. Only a pass disposes of it: the commit becomes trusted, its
open revert PR is closed, and its queued intake candidate is dropped. Anything
else leaves it undisposed and tells people why.

The CLI only records the request; the scheduler, which holds the ledger lease
for its whole life, judges it on its next tick.
"""

from __future__ import annotations

import json
import re

from .audit import DISPOSED, UNKNOWN, _governed, disposals

ACCEPT = "accept_request:"   # "*" cursors: requests waiting for the scheduler
KIND = "accept"


class AcceptError(ValueError):
    """The request cannot be recorded (no such unknown commit, already disposed...)."""


def resolve(ledger, ref: str) -> str:
    """The full SHA of an open unknown commit from a unique prefix (7+ hex)."""
    if not re.fullmatch(r"[0-9a-f]{7,40}", ref):
        raise AcceptError(f"not a commit SHA: {ref!r}")
    names = [n[len(UNKNOWN):] for n in ledger.cursors_with_prefix("*", UNKNOWN)]
    matches = [sha for sha in names if sha.startswith(ref)]
    if len(matches) != 1:
        raise AcceptError(f"{ref} matches {len(matches)} unknown commits")
    return matches[0]


def request_accept(ledger, ref: str, *, at: float) -> str:
    sha = resolve(ledger, ref)
    disposed = {name[len(DISPOSED):] for name in ledger.cursors_with_prefix("*", DISPOSED)}
    if sha in disposed:
        raise AcceptError(f"{sha[:12]} is already disposed of")
    ledger.set_cursor("*", ACCEPT + sha, json.dumps({"at": at, "state": "requested"}))
    return sha


def accept_pending(rt) -> list[str]:
    """Judge every recorded request (needs the scheduler's lease). Returns events."""
    if not getattr(rt, "lease_owner", None):
        return []
    events = []
    for name, raw in sorted(rt.ledger.cursors_with_prefix("*", ACCEPT).items()):
        request = json.loads(raw)
        if request.get("state") != "requested":
            continue
        sha = name[len(ACCEPT):]
        outcome, detail = _accept(rt, sha)
        rt.ledger.set_cursor("*", name, json.dumps({**request, "state": outcome, "detail": detail,
                                                    "decided_at": rt.clock()}))
        events.append(f"accept {sha[:12]} {outcome}: {detail}")
    return events


def _accept(rt, sha: str) -> tuple[str, str]:
    from .gate import run_gate
    from .runtime import calibration_current

    raw = rt.ledger.get_cursor("*", UNKNOWN + sha)
    if raw is None:
        return "refused", "not an unknown commit"
    record = json.loads(raw)
    if record.get("state") == "accepting":  # passed; interrupted before its cleanup finished
        return _finish(rt, sha, record)
    if sha in disposals(rt):
        return "done", "already disposed of"
    paths, parents, scopes = record.get("paths") or [], record.get("parents") or [], record.get("scopes") or []
    lifecycle = rt.registry.get(scopes[0]) if len(scopes) == 1 else None

    def refuse(why: str) -> tuple[str, str]:
        rt.ledger.enqueue_human(lifecycle.repo if lifecycle else next(iter(rt.registry)),
                                f"accept-unknown {sha[:12]} refused: {why}")
        return "refused", why

    if lifecycle is None or not lifecycle.enabled or not lifecycle.publishes:
        return refuse(f"it touches {scopes}: only a change inside one enabled, public repository can be accepted")
    if not parents or any(not _governed(p) for p in paths):
        return refuse("it touches paths the gate does not govern (or is a root commit): revert it by hand")
    revert = record.get("revert_changeset")
    if revert and rt.ledger.changeset(revert)["status"] == "pr_requested":
        return "requested", "its revert PR is being opened; judged again next tick"
    if not calibration_current(rt, lifecycle):
        return refuse("the judge calibration is missing or outdated")
    first = parents[0]
    base, head = rt.knowledge.knowledge_files(first), rt.knowledge.knowledge_files(sha)
    changes = [_change(e) for e in rt.knowledge.raw_manifest(first, sha)]
    decision = run_gate(base=base, head=head, changes=changes, external_texts=rt.knowledge.external_texts(sha),
                        evidence=[{"source_reference": f"commit {sha}", "title": record.get("reason", ""),
                                   "body": rt.knowledge.diff_text(first, sha, paths)[:8000]}],
                        gateway=rt.gateway, judge=rt.judge, release=rt.release_for(lifecycle.repo),
                        repo_dir=lifecycle.knowledge_dir, protected_rules=lifecycle.protected_rules,
                        retire_ratio=lifecycle.retire_ratio, max_files=lifecycle.max_files,
                        facts=rt.upstream_facts(lifecycle))
    from .external import _lifecycle_bookkeeping

    changeset_id = rt.ledger.new_changeset_id(lifecycle.repo, KIND)
    rt.save_changeset_files(changeset_id, {"base_sha": first, "files": {}, "deleted": [], "evidence": []})
    passed = decision.status == "pass"
    rt.ledger.stage_intake(rt.lease_owner, lifecycle.repo, changeset_id, kind=KIND,
                           status="accepted" if passed else "failed", verdicts=[], human_reason="",
                           drafted_events=[], detail={
                               "accepts": sha, "base_sha": first, "operations": [], "judge": rt.judge.label(),
                               "decision": decision.to_dict(), "release": rt.release_for(lifecycle.repo),
                               # what L1 found it retiring/purging (as for external PRs): the
                               # retirement ledger drives the next release's purge
                               **_lifecycle_bookkeeping(decision.l1, head)})
    rt.trace("decision", context={"repo": lifecycle.repo, "changeset_id": changeset_id, "playbook": "kb-audit",
                                  "step": "accept-unknown"},
             result={"status": decision.status, "sha": sha, "reasons": decision.reasons})
    if not passed:
        return refuse(f"the gate did not pass it ({decision.status}): " + "; ".join(decision.reasons)[:400])
    # recorded first, disposed of last: an interrupted cleanup is finished by
    # the next tick (without judging again), never skipped
    record = {**record, "state": "accepting", "accepted_by": changeset_id, "repo": lifecycle.repo}
    rt.ledger.set_cursor("*", UNKNOWN + sha, json.dumps(record))
    return _finish(rt, sha, record)


def _finish(rt, sha: str, record: dict) -> tuple[str, str]:
    """Idempotent: record its retirements, drop the candidate, close the revert
    PR, then dispose."""
    from .merge import _request_close, record_retirements

    changeset_id, repo = record["accepted_by"], record["repo"]
    record_retirements(rt, rt.ledger.changeset(changeset_id))   # upserts: safe to repeat
    event = rt.ledger.event_by_external_id(repo, "unrecorded", sha)
    if event is not None and event["status"] == "pending":
        rt.ledger.set_event_status(event["id"], "superseded", f"accepted as {changeset_id}")
    revert = record.get("revert_changeset")
    if revert:
        pending = rt.ledger.changeset(revert)
        if pending["status"] == "revert_open":
            rt.ledger.update_changeset(revert, status="superseding", detail={
                **pending["detail"], "rebuilt_as": changeset_id,
                "superseded_because": f"{sha[:12]} was accepted through the gate"})
            _request_close(rt, repo, rt.ledger.changeset(revert))
    # the commit disposes of itself: trusted wherever it is part of the history
    rt.ledger.set_cursor("*", DISPOSED + sha, sha)
    rt.ledger.set_cursor("*", UNKNOWN + sha, json.dumps({**record, "state": "accepted"}))
    return "accepted", f"passed the gate as {changeset_id}; run `kb resume --repo {repo}` to resume merging"


def _change(entry: dict):
    from ..knowledge_service.l1 import Change

    status = entry["status"] if entry["status"] in "AMD" else "M"
    return Change(entry["path"], status, entry["old_mode"], entry["new_mode"])
