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
    combined = rt.github.get(f"/repos/{knowledge_repository()}/commits/{sha}/status")
    for status in combined.get("statuses", []):
        if status.get("context") == "kb-gate":
            return str(status.get("state") or "")
    return ""


def advance(rt, lifecycle) -> list[str]:
    """One pass over this repository's in-flight change sets. Returns events."""
    events: list[str] = []
    if rt.outbox is None:
        return events
    paused = is_paused(rt.ledger, lifecycle.repo)
    queued = rt.ledger.changesets(lifecycle.repo, ("queued",))
    for changeset in rt.ledger.changesets(lifecycle.repo, IN_FLIGHT):
        number = changeset["pr_number"]
        if number is None:
            continue
        pr: dict[str, Any] = _pr_state(rt, int(number))
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
        if changeset["status"] == "pr_open":
            pending = changeset.get("pending_item")
            if pending and pending.get("kind") == "post_verdict" and float(pending["expires_at"]) > rt.clock():
                continue
            envelope = sign_verdict(rt, changeset)
            if issue_once(rt, lifecycle.repo, changeset, "post_verdict", {
                "changeset_id": changeset["id"], "pr": int(number), "head_sha": changeset["head_sha"],
                "comment": f"{VERDICT_MARKER}\n```json\n{json.dumps(envelope, ensure_ascii=False)}\n```\n",
            }):
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

