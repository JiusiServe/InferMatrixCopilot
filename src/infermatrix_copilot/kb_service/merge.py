"""The merge flow after a change set is handed to the publisher.

    gated ─publish→ pr_requested ─ack(pr, head)→ pr_open ─sign→ verdict_posted
      ─PR-stage kb-gate success→ queued ─merged→ merged ─activation→ activated

Anything off the happy path goes to people or stops: a rejected publisher
action (``failed``), a head that no longer matches what was signed
(``head_changed`` → human), a PR closed unmerged (``closed``), a paused
repository (``paused``; the pause itself is performed by the publisher through
an always-executable ``pause`` item). At most one knowledge PR per repository
is in the merge queue at a time, which bounds what can land while the
publisher is unavailable.

The service only READS GitHub; every write is an outbox item.
"""

from __future__ import annotations

import json
import os
from typing import Any

from ..knowledge_service.signing import sign
from ..knowledge_service.verdict import build_verdict, manifest_from_files

VERDICT_MARKER = "<!-- kb-gate:verdict:v1 -->"
IN_FLIGHT = ("pr_requested", "pr_open", "verdict_posted", "queued")
# a verdict must first verify within 72 hours: re-sign well before that
RESIGN_AFTER = 48 * 3600
# a queued PR that neither merged nor left the queue by then was dropped by a
# failing merge group (GitHub does not tell us): re-sign and re-enqueue
QUEUE_STALL = 2 * 3600
# kb-gate failures, by what the service can do about them (matched against the
# status description, which is the verifier's first problem)
TRANSIENT_GATE = ("hold list", "paused by the knowledge service", "global pause", "unreachable",
                  "verifier error", "fetched head does not match",
                  "carries kb:hold")  # left by our own pause until the re-signed verdict lifts it
RESIGN_GATE = ("outside its issue window", "no valid signed verdict")
REBUILD_GATE = ("context changed since the verdict", "pages changed since the consistency judgement",
                "does not merge cleanly", "signed patch manifest does not match")
KNOWLEDGE_REPO_ENV = "KB_KNOWLEDGE_REPOSITORY"
DEFAULT_KNOWLEDGE_REPOSITORY = "JiusiServe/InferMatrixCopilot"


def knowledge_repository() -> str:
    return os.environ.get(KNOWLEDGE_REPO_ENV, DEFAULT_KNOWLEDGE_REPOSITORY)


# the transition each outbox item kind drives: (state before, state after)
TRANSITIONS = {
    "open_pr": ("pr_requested", "pr_open"),
    "post_verdict": ("pr_open", "verdict_posted"),
    "enqueue": ("verdict_posted", "queued"),
}


def is_paused(ledger, repo: str) -> bool:
    """A repository is paused when it, or everything (``*``), is paused."""
    return bool(ledger.repo_state(repo)["paused"] or ledger.repo_state("*")["paused"])


def issue_once(rt, repo: str, changeset: dict, kind: str, body: dict) -> bool:
    """Issue ``kind`` for this change set unless the same action is already
    pending and unexpired. The pending item's identity is stored so its ack,
    and only its ack, can advance the change set."""
    pending = changeset.get("pending_item")
    if pending and pending.get("kind") == kind and float(pending.get("expires_at", 0)) > rt.clock():
        return False
    item = rt.outbox.issue(repo, kind, body)
    rt.ledger.update_changeset(changeset["id"], pending_item={
        "id": item.id, "kind": kind, "expires_at": item.expires_at})
    return True


def apply_acks(rt, acks: list[dict]) -> None:
    """Advance change sets from the publisher's signed acks. An ack applies
    only to the pending item it answers and only from the matching state: a
    late ack for a superseded duplicate, or one arriving after the change set
    moved on, changes nothing."""
    for ack in acks:
        changeset_id = str(ack.get("changeset_id") or "")
        if not changeset_id or "invalid" in ack:
            continue
        try:
            changeset = rt.ledger.changeset(changeset_id)
        except KeyError:
            continue
        kind = ack.get("kind")
        if kind == "pause":
            # under the publication lock that `kb resume` also holds, so a resume
            # cannot slip between reading the pause state and recording the ack
            with rt.outbox.publication_lock():
                current = rt.ledger.changeset(changeset_id)
                if not ack.get("ok") or current["status"] not in ("pr_open", "verdict_posted", "queued"):
                    continue
                if is_paused(rt.ledger, current["repo"]):
                    rt.ledger.update_changeset(changeset_id, status="paused", pending_item=None)
                else:
                    # resumed before this (late) pause landed: the PR is now
                    # dequeued and draft, so re-sign and re-enqueue it
                    rt.ledger.update_changeset(changeset_id, status="pr_open", pending_item=None)
            continue
        pending = changeset.get("pending_item") or {}
        if kind not in TRANSITIONS or pending.get("id") != ack.get("item_id"):
            continue
        before, after = TRANSITIONS[kind]
        if changeset["status"] != before:
            continue
        if not ack.get("ok"):
            rt.ledger.update_changeset(changeset_id, status="failed", pending_item=None)
            rt.ledger.enqueue_human(changeset["repo"], f"publisher refused {kind}: {ack.get('error', '')}",
                                    changeset_id)
            continue
        fields = {"status": after, "pending_item": None}
        if kind == "open_pr":
            fields.update(pr_number=int(ack["pr"]), head_sha=str(ack["head_sha"]),
                          branch=str(ack.get("branch", "")))
        elif kind == "enqueue":
            fields["detail"] = {**changeset["detail"], "queued_at": rt.clock()}
        rt.ledger.update_changeset(changeset_id, **fields)


def sign_verdict(rt, changeset: dict) -> dict:
    """The signed kb-gate verdict for this change set's PR at its recorded head."""
    detail = changeset["detail"]
    data = rt.load_changeset_files(changeset["id"])
    base = rt.knowledge.knowledge_files(detail["base_sha"])
    head = {**base, **data["files"]}
    for rel in data.get("deleted", []):
        head.pop(rel, None)
    touched = set(data["files"]) | set(data.get("deleted", []))
    manifest = manifest_from_files({k: v for k, v in base.items() if k in touched},
                                   {k: v for k, v in head.items() if k in touched})
    decision = detail["decision"]
    blocks = [{k: b[k] for k in ("block_id", "kind", "path", "rule_id", "op", "sha256", "verdict", "model")}
              for b in decision["blocks"]]
    consistency = [{"owner_dir": c["owner_dir"], "verdict": c["verdict"], "pages": c["pages"]}
                   for c in decision["consistency"]]
    verdict = build_verdict(
        repository=knowledge_repository(), pr=int(changeset["pr_number"]), head_sha=changeset["head_sha"],
        context_base_sha=detail["base_sha"], manifest=manifest, blocks=blocks, consistency=consistency,
        release=detail["release"], upstream={}, facts=[],
        models={"generator": detail["generator"], "judge": detail["judge"]},
        issued_at=rt.clock(),
    )
    return sign("kb-gate-verdict", verdict, rt.outbox._key)


def _pr_state(rt, number: int) -> dict:
    return rt.github.get(f"/repos/{knowledge_repository()}/pulls/{number}")


def _gate_status(rt, sha: str) -> str:
    return _gate(rt, sha)[0]


def _gate(rt, sha: str, *, since: float = 0.0) -> tuple[str, str]:
    """(state, description) of the latest kb-gate status on ``sha``; a status
    posted before ``since`` (the current verdict) is not about it: ("", "")."""
    combined = rt.github.get(f"/repos/{knowledge_repository()}/commits/{sha}/status")
    for status in combined.get("statuses", []):
        if status.get("context") == "kb-gate":
            posted = _epoch(status.get("updated_at") or status.get("created_at"))
            if since and posted and posted < since:
                return "", ""
            return str(status.get("state") or ""), str(status.get("description") or "")
    return "", ""


def _epoch(value) -> float:
    if not value:
        return 0.0
    import datetime as dt

    try:
        return dt.datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def _enqueue_outstanding(rt, changeset: dict) -> bool:
    """A signed enqueue that the publisher may still execute (unexpired)."""
    pending = changeset.get("pending_item") or {}
    return pending.get("kind") == "enqueue" and float(pending.get("expires_at", 0)) > rt.clock()


def _resign(rt, changeset: dict, why: str) -> None:
    """Back to pr_open: the next pass signs a fresh verdict for the same head."""
    rt.ledger.update_changeset(changeset["id"], status="pr_open", pending_item=None)
    _outcome(rt, changeset, "resigned", reason=why)


REBUILD_MARK = "rebuild of "


def _rebuild_of(rt, repo: str, old_id: str) -> str | None:
    """A change set already staged as the rebuild of ``old_id`` (its evidence
    carries the mark, written atomically with the staging), so an interrupted
    rebuild is resumed instead of staged twice."""
    for candidate in rt.ledger.changesets(repo, ("gated", "failed", "human", *IN_FLIGHT)):
        if candidate["kind"] != "rebuild":
            continue
        try:
            evidence = rt.load_changeset_files(candidate["id"]).get("evidence") or []
        except (OSError, ValueError):
            continue
        if any(str(item.get("source_reference") or "") == REBUILD_MARK + old_id for item in evidence):
            return candidate["id"]
    return None


def rebuild(rt, lifecycle, changeset: dict, why: str) -> str | None:
    """Rebuild a change set whose verdict can no longer verify on the current
    base (context pages moved, or the PR no longer applies): re-apply its
    operations to current main and gate them again. Only a rebuild that passes
    the gate replaces the PR; the old one then waits in ``superseding`` until
    its close is observed. Anything else goes to people with the old PR left
    open. Needs the scheduler's lease; returns the new change set id or None."""
    from ..knowledge_service.lifecycle import LifecycleError
    from ..knowledge_service.ops import KnowledgeOperation, apply_operations
    from .runtime import gate_and_stage, publish

    owner = getattr(rt, "lease_owner", None)
    if not owner:
        return None

    def to_people(reason: str) -> None:
        rt.ledger.update_changeset(changeset["id"], status="rebuild_failed")
        rt.ledger.enqueue_human(lifecycle.repo, reason, changeset["id"])

    detail = changeset["detail"]
    raw = detail.get("operations") or []
    if not raw:  # a mechanical change set (index fixes): nothing to re-apply
        to_people(f"kb-gate failed ({why}); no operations to rebuild")
        return None
    new_id = _rebuild_of(rt, lifecycle.repo, changeset["id"])
    if new_id is None:
        base_sha = rt.knowledge.fetch()
        base = rt.knowledge.knowledge_files(base_sha)
        external = rt.knowledge.external_texts(base_sha)
        operations = [KnowledgeOperation.from_dict(item) for item in raw]
        try:
            result = apply_operations(base, operations, release=detail["release"], today=rt.today())
        except LifecycleError as exc:
            to_people(f"cannot rebuild on current main: {exc}")
            return None
        evidence = [*(rt.load_changeset_files(changeset["id"]).get("evidence") or []),
                    {"source_reference": REBUILD_MARK + changeset["id"], "title": why}]
        new_id = gate_and_stage(rt, lifecycle, owner, kind="rebuild", base=base, base_sha=base_sha,
                                external=external, operations=operations, result=result,
                                evidence=evidence, event_ids=[], release=detail["release"],
                                draft_keys=[])
    staged = rt.ledger.changeset(new_id)
    if staged["status"] not in ("gated", *IN_FLIGHT):
        # the rebuild itself did not pass the gate: nothing replaces the PR
        to_people(f"rebuild {new_id} on current main did not pass the gate ({staged['status']})")
        return None
    rt.ledger.update_changeset(changeset["id"], status="superseding",
                               detail={**detail, "rebuilt_as": new_id, "superseded_because": why})
    _outcome(rt, changeset, "superseded", reason=why, replaced_by=new_id)
    _request_close(rt, lifecycle.repo, rt.ledger.changeset(changeset["id"]))
    publish(rt, lifecycle, new_id)
    return new_id


def _request_close(rt, repo: str, changeset: dict) -> None:
    issue_once(rt, repo, changeset, "close", {
        "changeset_id": changeset["id"], "pr": int(changeset["pr_number"]),
        "reason": (f"Superseded by change set {changeset['detail'].get('rebuilt_as')}, rebuilt on "
                   f"current main ({changeset['detail'].get('superseded_because', '')}).")})


def advance(rt, lifecycle) -> list[str]:
    """One pass over this repository's in-flight change sets. Returns events."""
    events: list[str] = []
    if rt.outbox is None:
        return events
    paused = is_paused(rt.ledger, lifecycle.repo)
    # the one queue slot per repository is taken by a queued PR AND by any PR
    # whose signed enqueue is still executable (not yet acked)
    queued = rt.ledger.changesets(lifecycle.repo, ("queued",)) + [
        cs for cs in rt.ledger.changesets(lifecycle.repo, ("verdict_posted",)) if _enqueue_outstanding(rt, cs)]
    for changeset in rt.ledger.changesets(lifecycle.repo, (*IN_FLIGHT, "superseding")):
        number = changeset["pr_number"]
        if number is None:
            continue
        pr: dict[str, Any] = _pr_state(rt, int(number))
        if changeset["status"] == "superseding":
            # the replaced PR stays tracked until GitHub shows it closed; the
            # close item is re-issued whenever the previous one expired
            if pr.get("state") == "closed" or pr.get("merged"):
                rt.ledger.update_changeset(changeset["id"], status="superseded", pending_item=None)
                events.append(f"superseded {changeset['id']}")
            else:
                _request_close(rt, lifecycle.repo, changeset)
            continue
        if pr.get("merged"):
            rt.ledger.update_changeset(changeset["id"], status="merged",
                                       merge_sha=str(pr.get("merge_commit_sha") or ""))
            record_retirements(rt, changeset)
            _outcome(rt, changeset, "merged", merge_sha=str(pr.get("merge_commit_sha") or ""))
            events.append(f"merged {changeset['id']}")
            continue
        if pr.get("state") == "closed":
            rt.ledger.update_changeset(changeset["id"], status="closed")
            _outcome(rt, changeset, "closed_unmerged")  # overturned by people: a negative label
            events.append(f"closed {changeset['id']}")
            continue
        head = str((pr.get("head") or {}).get("sha") or "")
        if head != changeset["head_sha"]:
            _outcome(rt, changeset, "head_changed", head_sha=head)
            rt.ledger.update_changeset(changeset["id"], status="head_changed")
            rt.ledger.enqueue_human(lifecycle.repo, f"PR #{number} head changed after signing", changeset["id"])
            events.append(f"head_changed {changeset['id']}")
            continue
        if paused:
            continue  # the pause itself is issued by `kb pause` / breakers
        signed_at = float(changeset["detail"].get("verdict_issued_at") or 0)
        stale_verdict = bool(signed_at) and rt.clock() - signed_at > RESIGN_AFTER
        queued_at = float(changeset["detail"].get("queued_at") or 0)
        if changeset["status"] == "queued" and (
                stale_verdict or (queued_at and rt.clock() - queued_at > QUEUE_STALL)):
            # never free the queue slot on a timer: dequeue (+ draft) first; the
            # pause ack returns it to pr_open, then it is re-signed and re-queued
            if issue_once(rt, lifecycle.repo, changeset, "pause", {
                    "changeset_id": changeset["id"], "pr": int(number),
                    "reason": "re-signing: the verdict is ageing or the PR stalled in the merge queue"}):
                events.append(f"requeue {changeset['id']}")
            continue
        if changeset["status"] == "verdict_posted" and _enqueue_outstanding(rt, changeset):
            continue  # its ack decides: queued (then the queued path applies) or refused
        if changeset["status"] == "verdict_posted" and stale_verdict:
            _resign(rt, changeset, "verdict close to its issue window")
            events.append(f"resign {changeset['id']}")
            continue
        if changeset["status"] == "verdict_posted":
            state, description = _gate(rt, changeset["head_sha"], since=signed_at)
            if state == "failure" and not any(m in description for m in TRANSIENT_GATE):
                if any(m in description for m in RESIGN_GATE):
                    _resign(rt, changeset, description)
                    events.append(f"resign {changeset['id']}")
                elif any(m in description for m in REBUILD_GATE):
                    if not getattr(rt, "lease_owner", None):
                        continue  # only the scheduler (holding the lease) rebuilds
                    new_id = rebuild(rt, lifecycle, changeset, description)
                    events.append(f"rebuilt {changeset['id']} as {new_id}" if new_id
                                  else f"rebuild_failed {changeset['id']}")
                else:  # a real problem with the change itself: people decide
                    rt.ledger.update_changeset(changeset["id"], status="gate_failed")
                    rt.ledger.enqueue_human(lifecycle.repo, f"kb-gate failed: {description}", changeset["id"])
                    events.append(f"gate_failed {changeset['id']}")
                continue
        if changeset["status"] == "pr_open":
            pending = changeset.get("pending_item")
            if pending and pending.get("kind") == "post_verdict" and float(pending["expires_at"]) > rt.clock():
                continue
            envelope = sign_verdict(rt, changeset)
            if issue_once(rt, lifecycle.repo, changeset, "post_verdict", {
                "changeset_id": changeset["id"], "pr": int(number), "head_sha": changeset["head_sha"],
                "comment": f"{VERDICT_MARKER}\n```json\n{json.dumps(envelope, ensure_ascii=False)}\n```\n",
            }):
                current = rt.ledger.changeset(changeset["id"])
                rt.ledger.update_changeset(changeset["id"], detail={
                    **current["detail"], "verdict_issued_at": envelope["payload"]["issued_at"]})
                events.append(f"verdict issued {changeset['id']}")
        elif changeset["status"] == "verdict_posted" and not queued:
            if _gate_status(rt, changeset["head_sha"]) == "success":
                if issue_once(rt, lifecycle.repo, changeset, "enqueue", {
                        "changeset_id": changeset["id"], "pr": int(number), "head_sha": changeset["head_sha"]}):
                    events.append(f"enqueue issued {changeset['id']}")
                queued = [changeset]  # at most one queued knowledge PR per repository
    return events


def _rule_ids(changeset: dict) -> list[str]:
    return sorted({op.get("new_rule_id") or op["rule_id"] for op in changeset["detail"].get("operations", [])
                   if op.get("new_rule_id") or op.get("rule_id")})


def _outcome(rt, changeset: dict, outcome: str, **result) -> None:
    """What finally happened to a change set: the gold label its decision is scored against."""
    trace = getattr(rt, "trace", None)
    if trace is not None:
        trace("outcome", context={"repo": changeset["repo"], "changeset_id": changeset["id"],
                                  "pr": changeset.get("pr_number"), "rule_ids": _rule_ids(changeset)},
              result={"outcome": outcome, **result})


def record_retirements(rt, changeset: dict) -> None:
    release = changeset["detail"].get("release", "")
    for op in changeset["detail"].get("operations", []):
        if op["kind"] in ("retire", "replace"):
            rt.ledger.record_retirement(changeset["repo"], op["rule_id"], op["page"], release)
            trace = getattr(rt, "trace", None)
            if trace is not None:  # the rule's earlier admission now has a later-retired label
                trace("outcome", context={"repo": changeset["repo"], "changeset_id": changeset["id"],
                                          "rule_ids": [op["rule_id"]]},
                      result={"outcome": "rule_retired", "rule_id": op["rule_id"], "release": release,
                              "reason": op.get("reason", "")})
        elif op["kind"] == "purge":
            rt.ledger.mark_purged(changeset["repo"], op["rule_id"])


def pause_open_prs(ledger, outbox, repo: str, reason: str) -> int:
    """Issue always-executable pause items (dequeue + draft) for every open
    knowledge PR of ``repo``; they are marked paused once the publisher acks."""
    count = 0
    if outbox is None:
        return count
    for changeset in ledger.changesets(repo, ("pr_open", "verdict_posted", "queued")):
        if changeset["pr_number"] is None:
            continue
        outbox.issue(repo, "pause", {"changeset_id": changeset["id"], "pr": int(changeset["pr_number"]),
                                     "reason": reason})
        count += 1
    return count


def resume_paused_prs(ledger, repo: str) -> int:
    """After ``kb resume``: paused knowledge PRs go back to ``pr_open``. The
    resumed repository has a NEW generation, so the next pass signs a fresh
    verdict for the PR's current head and re-enqueues (the publisher's enqueue
    marks the draft PR ready first); a head that moved goes to people."""
    count = 0
    for changeset in ledger.changesets(repo, ("paused",)):
        if changeset["pr_number"] is None:
            continue
        ledger.update_changeset(changeset["id"], status="pr_open", pending_item=None)
        count += 1
    return count

