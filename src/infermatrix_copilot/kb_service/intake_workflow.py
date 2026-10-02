"""Durable prepare -> draft -> gate intake, shared by nightly and playbook runs.

Only JSON batch IDs cross step boundaries. Every packet is checkpointed before
the next model call; event consumption and staging remain lease-fenced. Raw
inputs are scrubbed after completion, leaving the canonical changeset audit.
"""

from __future__ import annotations

import hashlib
import json
import uuid

from ..knowledge_service.lifecycle import LifecycleError
from ..knowledge_service.ops import KnowledgeOperation, apply_operations
from ..trace_store import accepted_key, trace_context
from .intake import Draft, draft_changes, merge_drafts, operations_json
from .models import ModelUnavailable
from .outbox import atomic_write_json
from .sources import SourceError


def batch_path(rt, batch_id):
    if not batch_id.startswith("intake-") or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in batch_id):
        raise ValueError("invalid intake batch ID")
    return rt.state_dir / "intake-batches" / f"{batch_id}.json"


def load_batch(rt, batch_id):
    return json.loads(batch_path(rt, batch_id).read_text(encoding="utf-8"))


def _load_for_repo(rt, lifecycle, batch_id):
    batch = load_batch(rt, batch_id)
    if batch["repo"] != lifecycle.repo:
        raise SourceError("intake batch belongs to another repository")
    return batch


def _save(rt, owner, batch):
    rt.ledger.heartbeat(owner)
    with rt.ledger.fenced(owner):
        atomic_write_json(batch_path(rt, batch["id"]), batch, mode=0o600)


def _batches(rt, repo):
    for path in sorted((rt.state_dir / "intake-batches").glob("*.json")):
        batch = json.loads(path.read_text(encoding="utf-8"))
        if batch["repo"] == repo:
            yield batch


def _pending(rt, repo):
    return {e["id"] for e in rt.ledger.events(repo, "pending", limit=1_000_000)}


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _trace(rt, batch, step, **result):
    rt.trace("outcome", context={"repo": batch["repo"], "intake_batch": batch["id"], "step": step},
             result={"outcome": step.replace(".", "_"), "phase": batch["phase"],
                     "event_ids": [e["id"] for e in batch["events"]], **result})


def _finish(rt, owner, batch, changeset=None):
    batch.update(phase="complete", changeset=changeset or "")
    for event in batch["events"]:
        if "packets" in event:
            event["packet_audit"] = [
                {"owner_page": packet.get("owner_page"),
                 "packet_sha256": packet.get("packet_sha256") or _digest({k: v for k, v in packet.items() if k not in ("draft", "packet_sha256")}),
                 "rationale": packet.get("draft", {}).get("rationale", ""),
                 "conclusion_dispositions": packet.get("draft", {}).get("conclusion_dispositions", []),
                 "rejected": packet.get("draft", {}).get("rejected", False),
                 "attempts": packet.get("draft", {}).get("attempts", [])[-3:],
                 "operations": [{**{k: op[k] for k in ("kind", "page", "rule_id", "new_rule_id", "new_page") if k in op},
                                 "sha256": _digest(op)} for op in packet.get("draft", {}).get("operations", [])]}
                for packet in event["packets"]]
        for field in ("payload", "evidence", "packets"):
            event.pop(field, None)
    _save(rt, owner, batch)
    _trace(rt, batch, "intake.complete", changeset=changeset or "")


def _staged(rt, batch):
    for changeset in rt.ledger.changesets_of_kind(batch["repo"], "intake"):
        if changeset["detail"].get("intake_batch") == batch["id"]:
            return changeset["id"]
    return None


def prepare_intake(rt, lifecycle, owner, max_events=10):
    from .packets import observer_for, owner_packets, prepare_event

    batches = list(_batches(rt, lifecycle.repo))
    batch = next((b for b in batches if b["phase"] not in ("complete", "blocked")), None)
    if batch is None:
        candidates = rt.ledger.events(lifecycle.repo, "pending", limit=1_000_000)
        events = candidates[:max_events]
        if not events:
            return None
        try:
            base_sha = rt.knowledge.fetch()
        except SourceError as exc:
            rt.ledger.set_event_statuses(owner, [(e["id"], "pending", f"prepare source unavailable: {exc}") for e in events])
            return None
        payloads = {e["id"]: _digest(e["payload"]) for e in candidates}
        blocked = {e["id"] for b in batches if b["base_sha"] == base_sha for e in b["events"]
                   if (e.get("status") == "rejected_packet" or
                       e.get("status") == "source_unavailable" and e.get("retry_after", 0) > rt.clock())
                   and e.get("payload_sha256") == payloads.get(e["id"])}
        retries = {}
        for prior in batches:
            for event in prior["events"]:
                if event.get("status") == "source_unavailable":
                    retries[event["id"]] = max(retries.get(event["id"], 0), event.get("retry_after", 0))
        # Fresh sources get a turn before expired retries can fill every slot.
        events = sorted((e for e in candidates if e["id"] not in blocked),
                        key=lambda e: retries.get(e["id"], 0))[:max_events]
        if not events:
            return None
        for event in events:
            event["payload_sha256"] = payloads[event["id"]]
        batch = {"id": f"intake-{uuid.uuid4().hex}", "repo": lifecycle.repo, "phase": "preparing",
                 "base_sha": base_sha, "release": rt.release_for(lifecycle.repo), "today": rt.today(),
                 "events": events, "source_branch": None}
        _save(rt, owner, batch)
    staged = _staged(rt, batch)
    if staged:
        _finish(rt, owner, batch, staged)
        return batch["id"]
    if batch["phase"] != "preparing":
        return batch["id"]
    base = rt.knowledge.knowledge_files(batch["base_sha"])
    pending = _pending(rt, lifecycle.repo)
    for event in batch["events"]:
        if event["id"] not in pending:
            event["status"] = "stale"
            continue
        if event.get("evidence") and "packets" in event:
            continue
        try:
            evidence = prepare_event(rt, lifecycle, event, base)
            branch = (evidence.get("source_scope") or {}).get("base_branch", "")
            if batch["source_branch"] is not None and branch != batch["source_branch"]:
                event["status"] = "deferred_branch"
                continue
            event["evidence"] = evidence
            event["evidence_sha256"] = _digest(evidence)
            event["packets"] = owner_packets(evidence, base, lifecycle.knowledge_dir,
                                              observer_for(rt, lifecycle, evidence))
            if not event["packets"]:
                raise SourceError("no owner packet: evidence routing is incomplete")
            if batch["source_branch"] is None:
                batch["source_branch"] = branch
            event["status"] = "prepared"
            event.pop("payload", None)
            _save(rt, owner, batch)
        except SourceError as exc:
            event.update(status="source_unavailable", error=str(exc), retry_after=rt.clock() + 300)
            rt.ledger.set_event_statuses(owner, [(event["id"], "pending", f"prepare source unavailable: {exc}")])
            _save(rt, owner, batch)
            _trace(rt, batch, "intake.prepare", error=str(exc))
    batch["events"] = [e for e in batch["events"] if e.get("status") not in ("stale", "deferred_branch")]
    if not any(e.get("status") == "prepared" for e in batch["events"]):
        _finish(rt, owner, batch)
        return None
    batch["phase"] = "prepared"
    batch.pop("error", None)
    _save(rt, owner, batch)
    _trace(rt, batch, "intake.prepare", branch=batch["source_branch"])
    return batch["id"]


def draft_intake(rt, lifecycle, owner, batch_id):
    from .runtime import draft_key_for_event

    batch = _load_for_repo(rt, lifecycle, batch_id)
    if batch["phase"] in ("complete", "blocked", "drafted"):
        return
    if batch["phase"] not in ("prepared", "drafting"):
        raise SourceError("intake evidence preparation is incomplete")
    staged = _staged(rt, batch)
    if staged:
        _finish(rt, owner, batch, staged)
        return
    base = rt.knowledge.knowledge_files(batch["base_sha"])
    pending = _pending(rt, lifecycle.repo)
    batch["phase"] = "drafting"
    _save(rt, owner, batch)
    for event in batch["events"]:
        if event.get("status") == "source_unavailable":
            continue
        if event["id"] not in pending:
            event["status"] = "stale"
            continue
        preceding = []
        for packet in event["packets"]:
            cached = packet.get("draft")
            if cached is None:
                rt.ledger.heartbeat(owner)
                files = {**base, **apply_operations(base, preceding, release=batch["release"], today=batch["today"]).files}
                key, holder = draft_key_for_event(lifecycle.repo, event["id"]), {}
                try:
                    with trace_context(draft_key=key, _accepted=holder, step="draft", intake_batch=batch_id):
                        draft = draft_changes(repo=lifecycle.repo, repo_dir=lifecycle.knowledge_dir,
                                              event_id=event["id"], evidence=packet, files=files,
                                              gateway=rt.gateway, generator=rt.generator,
                                              release=batch["release"], today=batch["today"])
                except ModelUnavailable as exc:
                    rt.ledger.set_event_statuses(owner, [(event["id"], "pending", f"generator unavailable: {exc}")])
                    batch["error"] = str(exc)
                    _save(rt, owner, batch)
                    _trace(rt, batch, "intake.draft", error=str(exc))
                    return
                packet["draft"] = cached = {"operations": operations_json(draft.operations),
                    "rationale": draft.rationale, "attempts": draft.attempts, "rejected": draft.rejected,
                    "generator": draft.generator, "accepted_key": accepted_key(key, holder) or "",
                    "conclusion_dispositions": getattr(draft, "conclusion_dispositions", [])}
                _save(rt, owner, batch)
            if cached["rejected"]:
                event["status"] = "rejected_packet"
                rt.ledger.set_event_statuses(owner, [(event["id"], "pending", "owner packet rejected after bounded repairs")])
                rt.ledger.enqueue_human(lifecycle.repo, f"intake batch {batch_id}: event {event['id']} owner packet rejected")
                _save(rt, owner, batch)
                _trace(rt, batch, "intake.draft", rejected_event=event["id"])
                break
            preceding.extend(KnowledgeOperation.from_dict(op) for op in cached["operations"])
        if event["status"] != "rejected_packet":
            event["status"] = "drafted"
    batch.update(phase="drafted")
    batch.pop("error", None)
    _save(rt, owner, batch)
    _trace(rt, batch, "intake.draft")


def gate_intake(rt, lifecycle, owner, batch_id):
    from .runtime import gate_and_stage

    batch = _load_for_repo(rt, lifecycle, batch_id)
    if batch["phase"] == "complete":
        return batch.get("changeset") or None
    staged = _staged(rt, batch)
    if staged:
        _finish(rt, owner, batch, staged)
        return staged
    if batch["phase"] != "drafted":
        return None
    try:
        base_sha = rt.knowledge.fetch()
        base = rt.knowledge.knowledge_files(base_sha)
        external = rt.knowledge.external_texts(base_sha)
    except SourceError as exc:
        _trace(rt, batch, "intake.gate", error=str(exc))
        return None
    pending = _pending(rt, lifecycle.repo)
    drafts = []
    for event in batch["events"]:
        if event.get("status") in ("rejected_packet", "source_unavailable"):
            continue
        if event["id"] not in pending:
            event["status"] = "stale"
            continue
        packets = [p["draft"] for p in event["packets"]]
        operations = [KnowledgeOperation.from_dict(op) for p in packets for op in p["operations"]]
        drafts.append(Draft([event["id"]], operations, None,
                            generator=", ".join(dict.fromkeys(p["generator"] for p in packets))))
    operations, result, kept, conflicting = merge_drafts(base, drafts, release=batch["release"], today=batch["today"])
    kept_ids = {i for d in kept for i in d.event_ids}
    conflicting_ids = {i for d in conflicting for i in d.event_ids}
    updates = [(d.event_ids[0], "done", "no rules: all owner packets intentionally dropped") for d in drafts if d.empty]
    updates.extend((i, "pending", "cached operations conflict with current knowledge tree") for i in conflicting_ids)
    rt.ledger.set_event_statuses(owner, updates)
    for event in batch["events"]:
        if event.get("status") in ("rejected_packet", "source_unavailable"):
            continue
        if event["id"] in conflicting_ids:
            event["status"] = "conflicting"
        elif event["id"] in kept_ids:
            event["status"] = "staged"
        elif event["id"] in pending:
            event["status"] = "no_rules"
    changeset = None
    if operations and result:
        evidence = []
        for event in batch["events"]:
            if event["id"] in kept_ids:
                item = {**event["evidence"], "diffs": {path: patch for p in event["packets"] for path, patch in p.get("diffs", {}).items()}}
                if item["diffs"] and all(path in item["diffs"] for path in item.get("changed_files", [])):
                    item.pop("diff", None)
                evidence.append(item)
        keys = [p["draft"]["accepted_key"] for e in batch["events"] if e["id"] in kept_ids
                for p in e["packets"] if p["draft"]["accepted_key"]]
        changeset = gate_and_stage(rt, lifecycle, owner, kind="intake", base=base, base_sha=base_sha,
            external=external, operations=operations, result=result, evidence=evidence,
            event_ids=sorted(kept_ids), release=batch["release"], draft_keys=keys,
            extra_detail={"intake_batch": batch_id, "source_event_ids": sorted(kept_ids),
                          "conclusion_dispositions": [
                              {"event_id": e["id"], "owner_page": p.get("owner_page"), "dispositions": p["draft"].get("conclusion_dispositions", [])}
                              for e in batch["events"] if e["id"] in kept_ids for p in e["packets"]],
                          "generator": ", ".join(dict.fromkeys(d.generator for d in kept))})
    _finish(rt, owner, batch, changeset)
    return changeset
