"""Durable owner-packet intake: resume, source atomicity and fresh-base gating."""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from types import SimpleNamespace

import pytest

from infermatrix_copilot.kb_service import intake_workflow as workflow
from infermatrix_copilot.kb_service.intake import Draft
from infermatrix_copilot.kb_service.models import ModelUnavailable
from infermatrix_copilot.kb_service.sources import SourceError
from infermatrix_copilot.knowledge_service.ops import KnowledgeOperation, apply_operations
from test_kb_intake_gate import PAGE, ScriptedGateway, _git, _judge_all, _rule, _runtime


@pytest.fixture
def world(tmp_path, monkeypatch):
    rt, lifecycle = _runtime(tmp_path, ScriptedGateway(_judge_all("yes")))
    owner = rt.ledger.acquire_lease("workflow")
    calls, state = [], {"unavailable": None, "reject": None, "empty": False, "collision": False}

    def prepare_event(rt, lifecycle, event, base):
        return {**event["payload"], "source_scope": {"base_branch": event["payload"].get("branch", "main")}}

    def owner_packets(evidence, base, repo_dir, observer):
        return [{**evidence, "owner_page": PAGE, "ordinal": n}
                for n in range(evidence.get("packet_count", 1))]

    helpers = SimpleNamespace(prepare_event=prepare_event, owner_packets=owner_packets,
                              observer_for=lambda rt, lifecycle, evidence: None)
    monkeypatch.setitem(sys.modules, "infermatrix_copilot.kb_service.packets", helpers)

    def draft_changes(**kwargs):
        packet = kwargs["evidence"]
        identity = (kwargs["event_id"], packet["ordinal"])
        calls.append((identity, kwargs["files"]))
        if state["unavailable"] == identity:
            state["unavailable"] = None
            raise ModelUnavailable("temporary quota")
        if state["reject"] == identity:
            return Draft([identity[0]], [], None, rejected=True, attempts=[{"error": "invalid packet"}])
        if state["empty"]:
            draft = Draft([identity[0]], [], None, rationale="all conclusions deliberately dropped")
            draft.conclusion_dispositions = [{"unit": "comment-1", "action": "drop", "reason": "no durable claim"}]
            return draft
        rule_id = "SAME-ID" if state["collision"] else f"PACKET-{identity[0]}-{identity[1]}"
        op = KnowledgeOperation("add", PAGE, rule_id, _rule(rule_id, "PR #11"))
        result = apply_operations(kwargs["files"], [op], release=kwargs["release"], today=kwargs["today"])
        draft = Draft([identity[0]], [op], result, generator="test:generator")
        draft.conclusion_dispositions = [{"unit": "comment-1", "action": "adopt", "rule_id": rule_id}]
        return draft

    monkeypatch.setattr(workflow, "draft_changes", draft_changes)
    return SimpleNamespace(rt=rt, lifecycle=lifecycle, owner=owner, calls=calls, state=state,
                           helpers=helpers, tmp=tmp_path)


def record(world, number, **payload):
    return world.rt.ledger.record_event("demo", "merged_pr", str(number), {
        "source_reference": f"PR #{number}", "title": "upstream change", "body": "RAW-PRIVATE-INPUT",
        "changed_files": ["demo/core/q.py"], "merged_at": "2026-09-28T00:00:00Z",
        "merge_commit_sha": "c" * 40, **payload})


def run(world):
    batch = workflow.prepare_intake(world.rt, world.lifecycle, world.owner)
    if batch:
        workflow.draft_intake(world.rt, world.lifecycle, world.owner, batch)
        return batch, workflow.gate_intake(world.rt, world.lifecycle, world.owner, batch)
    return None, None


def test_packet_checkpoint_resumes_without_redrafting_and_consumes_whole_event(world):
    event = record(world, 11, packet_count=2)
    world.state["unavailable"] = (event, 1)
    batch, cid = run(world)
    assert workflow.batch_path(world.rt, batch).stat().st_mode & 0o777 == 0o600
    assert cid is None
    assert [e["id"] for e in world.rt.ledger.events("demo", "pending")] == [event]
    assert "generator unavailable" in world.rt.ledger.events("demo", "pending")[0]["detail"]
    assert workflow.load_batch(world.rt, batch)["phase"] == "drafting"
    assert workflow.prepare_intake(world.rt, world.lifecycle, world.owner) == batch
    workflow.draft_intake(world.rt, world.lifecycle, world.owner, batch)
    cid = workflow.gate_intake(world.rt, world.lifecycle, world.owner, batch)
    assert [identity for identity, _ in world.calls] == [(event, 0), (event, 1), (event, 1)]
    assert "PACKET-1-0" in world.calls[-1][1][PAGE]  # cumulative successful packet operations
    detail = world.rt.ledger.changeset(cid)["detail"]
    assert detail["event_ids"] == [event] and len(detail["operations"]) == 2
    assert len(detail["conclusion_dispositions"]) == 2
    completed = workflow.load_batch(world.rt, batch)
    assert completed["phase"] == "complete" and "RAW-PRIVATE-INPUT" not in json.dumps(completed)
    assert "RAW-PRIVATE-INPUT" in json.dumps(world.rt.load_changeset_files(cid)["evidence"])


def test_prepare_groups_only_the_first_source_branch(world):
    first = record(world, 11, branch="beta")
    deferred = record(world, 12, branch="main")
    third = record(world, 13, branch="beta")
    batch, cid = run(world)
    assert world.rt.ledger.changeset(cid)["detail"]["event_ids"] == [first, third]
    assert [e["id"] for e in world.rt.ledger.events("demo", "pending")] == [deferred]
    assert workflow.load_batch(world.rt, batch)["source_branch"] == "beta"
    _, second = run(world)
    assert world.rt.ledger.changeset(second)["detail"]["event_ids"] == [deferred]


def test_crash_after_staging_recovers_one_changeset_and_scrubs_batch(world, monkeypatch):
    record(world, 11)
    batch = workflow.prepare_intake(world.rt, world.lifecycle, world.owner)
    workflow.draft_intake(world.rt, world.lifecycle, world.owner, batch)
    real_save = workflow._save

    def crash(rt, owner, data):
        if data["phase"] == "complete":
            raise RuntimeError("crash after gate transaction")
        return real_save(rt, owner, data)

    monkeypatch.setattr(workflow, "_save", crash)
    with pytest.raises(RuntimeError):
        workflow.gate_intake(world.rt, world.lifecycle, world.owner, batch)
    (staged,) = world.rt.ledger.changesets_of_kind("demo", "intake")
    monkeypatch.setattr(workflow, "_save", real_save)
    assert workflow.prepare_intake(world.rt, world.lifecycle, world.owner) == batch
    assert workflow.gate_intake(world.rt, world.lifecycle, world.owner, batch) == staged["id"]
    assert len(world.rt.ledger.changesets_of_kind("demo", "intake")) == 1
    assert len(world.calls) == 1
    assert "evidence" not in workflow.load_batch(world.rt, batch)["events"][0]


def test_cross_event_id_collision_leaves_conflicting_source_pending(world):
    first, second = record(world, 11), record(world, 12)
    world.state["collision"] = True
    _, cid = run(world)
    assert world.rt.ledger.changeset(cid)["detail"]["event_ids"] == [first]
    (pending,) = world.rt.ledger.events("demo", "pending")
    assert pending["id"] == second and "conflict" in pending["detail"]
    _, retried = run(world)
    assert world.rt.ledger.changeset(retried)["detail"]["event_ids"] == [second]


def test_cached_operations_are_gated_on_current_main_not_preparation_base(world):
    record(world, 11)
    batch = workflow.prepare_intake(world.rt, world.lifecycle, world.owner)
    old = workflow.load_batch(world.rt, batch)["base_sha"]
    workflow.draft_intake(world.rt, world.lifecycle, world.owner, batch)
    origin = world.tmp / "origin"
    (origin / "README.md").write_text("main advanced\n")
    _git(origin, "add", "README.md")
    _git(origin, "-c", "user.name=t", "-c", "user.email=t@e", "commit", "-q", "-m", "advance main")
    current = _git(origin, "rev-parse", "HEAD").strip()
    cid = workflow.gate_intake(world.rt, world.lifecycle, world.owner, batch)
    assert world.rt.ledger.changeset(cid)["detail"]["base_sha"] == current != old
    assert len(world.calls) == 1


def test_rejected_packet_holds_only_its_source_and_retries_after_base_change(world):
    failed = record(world, 11, packet_count=2)
    good = record(world, 12)
    world.state["reject"] = (failed, 1)
    batch, cid = run(world)
    assert world.rt.ledger.changeset(cid)["detail"]["event_ids"] == [good]
    assert world.rt.ledger.events("demo", "pending")[0]["id"] == failed
    assert world.rt.ledger.human_queue("demo")
    rejected_audit = workflow.load_batch(world.rt, batch)["events"][0]["packet_audit"][1]
    assert rejected_audit["rejected"] and rejected_audit["attempts"] == [{"error": "invalid packet"}]
    assert run(world) == (None, None)  # bounded same-source review hold
    origin = world.tmp / "origin"
    (origin / "README.md").write_text("retry with changed knowledge base\n")
    _git(origin, "add", "README.md")
    _git(origin, "-c", "user.name=t", "-c", "user.email=t@e", "commit", "-q", "-m", "retry context")
    world.state["reject"] = None
    _, recovered = run(world)
    assert world.rt.ledger.changeset(recovered)["detail"]["event_ids"] == [failed]


def test_source_error_remains_pending_then_retries_and_foreign_batch_is_refused(world):
    event = record(world, 11)
    original = world.helpers.prepare_event
    world.helpers.prepare_event = lambda *args: (_ for _ in ()).throw(SourceError("incomplete discussion"))
    assert workflow.prepare_intake(world.rt, world.lifecycle, world.owner) is None
    assert "incomplete discussion" in world.rt.ledger.events("demo", "pending")[0]["detail"]
    world.helpers.prepare_event = original
    assert workflow.prepare_intake(world.rt, world.lifecycle, world.owner) is None
    recovered_at = world.rt.clock() + 301
    world.rt.clock = lambda: recovered_at
    batch = workflow.prepare_intake(world.rt, world.lifecycle, world.owner)
    foreign = replace(world.lifecycle, repo="foreign", knowledge_dir="repos/foreign")
    with pytest.raises(SourceError, match="another repository"):
        workflow.draft_intake(world.rt, foreign, world.owner, batch)
    with pytest.raises(SourceError, match="another repository"):
        workflow.gate_intake(world.rt, foreign, world.owner, batch)
    workflow.draft_intake(world.rt, world.lifecycle, world.owner, batch)
    assert workflow.gate_intake(world.rt, world.lifecycle, world.owner, batch)
    assert world.rt.ledger.events("demo", "drafted")[0]["id"] == event


def test_stale_event_is_never_reset_or_staged_by_cached_batch(world):
    event = record(world, 11)
    batch = workflow.prepare_intake(world.rt, world.lifecycle, world.owner)
    world.rt.ledger.set_event_statuses(world.owner, [(event, "drafted", "another changeset")])
    workflow.draft_intake(world.rt, world.lifecycle, world.owner, batch)
    assert workflow.gate_intake(world.rt, world.lifecycle, world.owner, batch) is None
    assert world.rt.ledger.events("demo", "drafted")[0]["detail"] == "another changeset"
    assert not world.calls and not world.rt.ledger.changesets_of_kind("demo", "intake")


def test_intentional_empty_learning_retains_per_unit_reasons_after_raw_cleanup(world):
    event = record(world, 11, packet_count=2)
    world.state["empty"] = True
    batch, cid = run(world)
    assert cid is None and world.rt.ledger.events("demo", "done")[0]["id"] == event
    compact = workflow.load_batch(world.rt, batch)
    assert "RAW-PRIVATE-INPUT" not in json.dumps(compact)
    audit = compact["events"][0]["packet_audit"]
    assert len(audit) == 2 and all(p["rationale"] for p in audit)
    assert all(p["conclusion_dispositions"] == [{"unit": "comment-1", "action": "drop", "reason": "no durable claim"}]
               for p in audit)


def test_changed_base_collision_defers_whole_event_without_consuming_earlier_packet(world):
    event = record(world, 11, packet_count=2)
    batch = workflow.prepare_intake(world.rt, world.lifecycle, world.owner)
    workflow.draft_intake(world.rt, world.lifecycle, world.owner, batch)
    origin = world.tmp / "origin"
    target = origin / "knowledge" / PAGE
    target.write_text(target.read_text() + "\n" + _rule(f"PACKET-{event}-1"))
    _git(origin, "add", "knowledge")
    _git(origin, "-c", "user.name=t", "-c", "user.email=t@e", "commit", "-q", "-m", "reserve candidate ID")
    assert workflow.gate_intake(world.rt, world.lifecycle, world.owner, batch) is None
    assert world.rt.ledger.events("demo", "pending")[0]["id"] == event
    assert not world.rt.ledger.changesets_of_kind("demo", "intake")
    audit = workflow.load_batch(world.rt, batch)["events"][0]
    assert audit["status"] == "conflicting" and len(audit["packet_audit"]) == 2


def test_gate_canonical_evidence_reuses_prepared_patches_and_source_digest(world):
    record(world, 11, diff="RAW-FULL-DIFF", source_sha256="original-source-digest")
    original = world.helpers.owner_packets

    def packets(*args):
        result = original(*args)
        for packet in result:
            packet["diffs"] = {"demo/core/q.py": "complete prepared per-file patch"}
            packet["packet_sha256"] = "a" * 64
        return result

    world.helpers.owner_packets = packets
    batch, cid = run(world)
    (evidence,) = world.rt.load_changeset_files(cid)["evidence"]
    assert evidence["source_sha256"] == "original-source-digest"
    assert evidence["diffs"] == {"demo/core/q.py": "complete prepared per-file patch"}
    assert "diff" not in evidence
    assert workflow.load_batch(world.rt, batch)["events"][0]["packet_audit"][0]["packet_sha256"] == "a" * 64


def test_unavailable_source_does_not_starve_healthy_events_and_retries_after_backoff(world):
    unavailable, healthy = record(world, 11), record(world, 12)
    original = world.helpers.prepare_event

    def flaky(rt, lifecycle, event, base):
        if event["id"] == unavailable:
            raise SourceError("temporary incomplete GitHub response")
        return original(rt, lifecycle, event, base)

    world.helpers.prepare_event = flaky
    batch, cid = run(world)
    assert world.rt.ledger.changeset(cid)["detail"]["event_ids"] == [healthy]
    assert [identity[0] for identity, _ in world.calls] == [healthy]
    (pending,) = world.rt.ledger.events("demo", "pending")
    assert pending["id"] == unavailable and "GitHub" in pending["detail"]
    failed = workflow.load_batch(world.rt, batch)["events"][0]
    assert failed["status"] == "source_unavailable" and failed["retry_after"] == world.rt.clock() + 300
    assert failed["error"] == "temporary incomplete GitHub response"
    assert "evidence" not in failed and "payload" not in failed
    assert run(world) == (None, None)
    world.helpers.prepare_event = original
    recovered_at = world.rt.clock() + 301
    world.rt.clock = lambda: recovered_at
    _, recovered = run(world)
    assert world.rt.ledger.changeset(recovered)["detail"]["event_ids"] == [unavailable]


def test_checkpoint_cannot_overwrite_new_holder_after_heartbeat_takeover(world, monkeypatch):
    from infermatrix_copilot.kb_service.ledger import Ledger, LeaseError
    from infermatrix_copilot.kb_service.outbox import atomic_write_json

    record(world, 11)
    batch_id = workflow.prepare_intake(world.rt, world.lifecycle, world.owner)
    stale = workflow.load_batch(world.rt, batch_id)
    current = {**stale, "phase": "complete", "changeset": "new-holder-result"}
    heartbeat = world.rt.ledger.heartbeat

    def takeover(owner):
        heartbeat(owner)
        usurper = Ledger(world.rt.ledger.path, clock=lambda: 1e12)
        new_owner = usurper.acquire_lease("new-holder", ttl=600)
        with usurper.fenced(new_owner):
            atomic_write_json(workflow.batch_path(world.rt, batch_id), current, mode=0o600)
        usurper.close()

    monkeypatch.setattr(world.rt.ledger, "heartbeat", takeover)
    with pytest.raises(LeaseError, match="lost"):
        workflow._save(world.rt, world.owner, stale)
    assert workflow.load_batch(world.rt, batch_id) == current


def test_failed_branch_packet_does_not_pin_batch_and_starve_a_healthy_branch(world):
    unavailable = record(world, 11, branch="beta")
    healthy = record(world, 12, branch="main")
    original = world.helpers.owner_packets

    def owner_packets(evidence, *args):
        if evidence["source_scope"]["base_branch"] == "beta":
            raise SourceError("beta PR mirror is unavailable")
        return original(evidence, *args)

    world.helpers.owner_packets = owner_packets
    batch, cid = run(world)
    assert world.rt.ledger.changeset(cid)["detail"]["event_ids"] == [healthy]
    assert workflow.load_batch(world.rt, batch)["source_branch"] == "main"
    assert world.rt.ledger.events("demo", "pending")[0]["id"] == unavailable
    # Even when the next scheduler tick exceeds backoff, beta cannot starve main.
    later = world.rt.clock() + 901
    world.rt.clock = lambda: later
    next_healthy = record(world, 13, branch="main")
    _, next_cid = run(world)
    assert world.rt.ledger.changeset(next_cid)["detail"]["event_ids"] == [next_healthy]


def test_expired_source_retry_cannot_fill_every_event_slot_before_fresh_work(world):
    unavailable = record(world, 11, branch="beta")
    healthy = record(world, 12, branch="main")
    original = world.helpers.prepare_event

    def prepare_event(rt, lifecycle, event, base):
        if event["id"] == unavailable:
            raise SourceError("unavailable old source")
        return original(rt, lifecycle, event, base)

    world.helpers.prepare_event = prepare_event
    assert workflow.prepare_intake(world.rt, world.lifecycle, world.owner, max_events=1) is None
    later = world.rt.clock() + 901
    world.rt.clock = lambda: later
    batch = workflow.prepare_intake(world.rt, world.lifecycle, world.owner, max_events=1)
    assert [e["id"] for e in workflow.load_batch(world.rt, batch)["events"]] == [healthy]
    workflow.draft_intake(world.rt, world.lifecycle, world.owner, batch)
    cid = workflow.gate_intake(world.rt, world.lifecycle, world.owner, batch)
    assert world.rt.ledger.changeset(cid)["detail"]["event_ids"] == [healthy]
    assert world.rt.ledger.events("demo", "pending")[0]["id"] == unavailable
