"""Manual source completion needs real merged admission and the exact active rules."""

from __future__ import annotations

import json

import pytest

from infermatrix_copilot.kb_service import event_settlement as settlement, reconcile
from infermatrix_copilot.kb_service.activate import activate, switch_active
from infermatrix_copilot.kb_service.ledger import LeaseError
from infermatrix_copilot.knowledge_service.signing import SignatureError, verify
from test_kb_intake_gate import PAGE
from test_kb_reconcile_reviewed import world  # noqa: F401


@pytest.fixture(autouse=True)
def settlement_repository(world, monkeypatch):
    monkeypatch.setattr(settlement, "_repository", reconcile._repository)


def _ready(w, *, status="pending", no_rule=False):
    reconcile.apply_plan(w.rt, reconcile.make_plan(w.rt, w.key, **w.options), w.key)
    activate(w.rt, w.sha)
    event = w.rt.ledger.record_event("demo", "merged_pr", "11" if no_rule else "10",
                                    {"source_reference": "PR #11" if no_rule else "PR #10",
                                     "merge_commit_sha": "a" * 40, "body": "immutable upstream evidence"})
    if status != "pending":
        w.rt.ledger.set_event_status(event, status, "original model rejection" if status == "rejected" else "old draft")
    coverage = {"commits": [w.sha], "events": [{"id": event, "outcome": "no_rule" if no_rule else "already_covered",
                "reason": "owner reviewed source; no durable rule" if no_rule else "owner reviewed the cited existing rule",
                "rules": [] if no_rule else [{"path": PAGE, "rule_id": "DEMO-1a"}]}]}
    w.rt.ledger.release_lease(w.rt.lease_owner)
    return event, coverage


@pytest.mark.parametrize("status", ["pending", "rejected", "drafted"])
def test_selected_event_completes_honestly_and_future_events_stay_pending(world, status):
    w = world
    event, coverage = _ready(w, status=status)
    plan = settlement.make_plan(w.rt, w.key, coverage=coverage, **w.options)
    assert w.rt.ledger.event(event)["status"] == status
    future = w.rt.ledger.record_event("demo", "merged_pr", "12", {"merge_commit_sha": "b" * 40})
    receipt = settlement.apply_plan(w.rt, plan, w.key)
    assert settlement.apply_plan(w.rt, plan, w.key) == receipt
    completed = w.rt.ledger.event(event)
    assert completed["status"] == "done"
    assert json.loads(completed["detail"])["outcome"] == "manual_reviewed_merged"
    assert w.rt.ledger.event(future)["status"] == "pending"
    assert reconcile.trusted_commits(w.rt) == {w.sha}  # settlement adds no history trust
    verified = verify(settlement.RECEIPT_PURPOSE, json.loads(receipt.read_text()), w.key.public_key())
    assert verified["events"][0]["source_event"]["status"] == status


def test_no_rule_requires_signed_reason_without_inventing_a_rule(world):
    w = world
    event, coverage = _ready(w, no_rule=True)
    plan = settlement.make_plan(w.rt, w.key, coverage=coverage, **w.options)
    receipt = settlement.apply_plan(w.rt, plan, w.key)
    assert json.loads(w.rt.ledger.event(event)["detail"])["disposition"] == "no_rule"
    assert verify(settlement.RECEIPT_PURPOSE, json.loads(receipt.read_text()), w.key.public_key())["events"][0]["rules"] == []


def test_failed_batches_and_descendants_stop_but_verdicts_and_unrelated_queue_remain(world):
    w = world
    event, coverage = _ready(w)
    with w.rt.ledger.lease() as owner:
        original = w.rt.ledger.new_changeset_id("demo", "intake")
        w.rt.ledger.stage_intake(owner, "demo", original, status="failed", drafted_events=[event],
                                detail={"event_ids": [event], "decision": {"status": "fail"}},
                                verdicts=[{"layer": "gate", "verdict": "fail"}], human_reason="model failed")
        child = w.rt.ledger.new_changeset_id("demo", "refine")
        w.rt.ledger.stage_intake(owner, "demo", child, kind="refine", status="failed", drafted_events=[],
                                detail={"refine_history": [{"changeset": original}], "decision": {"status": "fail"}},
                                verdicts=[{"layer": "gate", "verdict": "fail"}], human_reason="refinement failed")
    w.rt.ledger.enqueue_human("demo", "unrelated task")
    before = w.rt.ledger._conn.execute("SELECT * FROM verdicts").fetchall()
    plan = settlement.make_plan(w.rt, w.key, coverage=coverage, **w.options)
    settlement.apply_plan(w.rt, plan, w.key)
    assert w.rt.ledger.changeset(original)["status"] == "manual_reviewed_merged"
    assert w.rt.ledger.changeset(child)["status"] == "manual_reviewed_merged"
    assert w.rt.ledger.changeset(original)["detail"]["decision"]["status"] == "fail"
    assert w.rt.ledger._conn.execute("SELECT * FROM verdicts").fetchall() == before
    remaining = w.rt.ledger.human_queue()
    assert "unrelated task" in [row["reason"] for row in remaining]
    assert not any(row["changeset_id"] in {original, child} for row in remaining)


@pytest.mark.parametrize("drift", ["payload", "identity", "status", "created_at"])
def test_source_replacement_or_state_drift_refuses_before_receipt(world, drift):
    w = world
    event, coverage = _ready(w)
    plan = settlement.make_plan(w.rt, w.key, coverage=coverage, **w.options)
    if drift == "payload":
        w.rt.ledger._conn.execute("UPDATE events SET payload=? WHERE id=?", (json.dumps({"merge_commit_sha": "b" * 40}), event))
    elif drift == "identity":
        w.rt.ledger._conn.execute("UPDATE events SET external_id='15' WHERE id=?", (event,))
    elif drift == "created_at":
        w.rt.ledger._conn.execute("UPDATE events SET created_at=created_at+1 WHERE id=?", (event,))
    else:
        w.rt.ledger.set_event_status(event, "rejected", "a newer result")
    with pytest.raises(reconcile.ReconciliationError):
        settlement.apply_plan(w.rt, plan, w.key)
    assert not (w.rt.state_dir / "event-settlements").exists()


@pytest.mark.parametrize("failure", ["missing_rule", "wrong_scope", "no_citation", "no_reason", "no_merge", "failed_check"])
def test_unproven_coverage_cannot_complete_source_events(world, failure):
    w = world
    event, coverage = _ready(w)
    if failure == "missing_rule":
        coverage["events"][0]["rules"][0]["rule_id"] = "MISSING-1"
    elif failure == "wrong_scope":
        coverage["events"][0]["rules"][0]["path"] = "repos/other/rules.md"
    elif failure == "no_citation":
        w.rt.ledger._conn.execute("UPDATE events SET external_id='15' WHERE id=?", (event,))
    elif failure == "no_reason":
        coverage["events"][0]["reason"] = ""
    elif failure == "no_merge":
        coverage["commits"] = [w.base]
    else:
        w.rt.github.checks[0]["conclusion"] = "failure"
    with pytest.raises(reconcile.ReconciliationError):
        settlement.make_plan(w.rt, w.key, coverage=coverage, **w.options)
    assert w.rt.ledger.event(event)["status"] == "pending"


def test_wrong_active_target_and_corrupt_receipts_refuse(world):
    w = world
    event, coverage = _ready(w)
    plan = settlement.make_plan(w.rt, w.key, coverage=coverage, **w.options)
    switch_active(w.rt.state_dir, w.rt.state_dir / "snapshots" / w.base)
    with pytest.raises(reconcile.ReconciliationError, match="exact target"):
        settlement.apply_plan(w.rt, plan, w.key)
    activate(w.rt, w.sha)
    receipt = settlement.apply_plan(w.rt, plan, w.key)
    receipt.write_text("{}")
    with pytest.raises(reconcile.ReconciliationError, match="modified"):
        settlement.apply_plan(w.rt, plan, w.key)


def test_plan_is_not_a_receipt_and_running_scheduler_blocks_apply(world):
    w = world
    _event, coverage = _ready(w)
    plan = settlement.make_plan(w.rt, w.key, coverage=coverage, **w.options)
    directory = w.rt.state_dir / "event-settlements"
    directory.mkdir()
    (directory / f"{reconcile._digest(plan)}.json").write_text(json.dumps(plan))
    with pytest.raises(SignatureError):
        settlement.apply_plan(w.rt, plan, w.key)
    for path in directory.glob("*.json"):
        path.unlink()
    with w.rt.ledger.lease():
        with pytest.raises(LeaseError):
            settlement.apply_plan(w.rt, plan, w.key)


def test_partial_failed_batch_is_refused(world):
    w = world
    event, coverage = _ready(w)
    other = w.rt.ledger.record_event("demo", "merged_pr", "11", {"merge_commit_sha": "b" * 40})
    with w.rt.ledger.lease() as owner:
        w.rt.ledger.stage_intake(owner, "demo", "whole-batch", status="failed", verdicts=[], human_reason="",
                                detail={"event_ids": [event, other]}, drafted_events=[event, other])
    with pytest.raises(ValueError, match="whole existing source batch"):
        settlement.make_plan(w.rt, w.key, coverage=coverage, **w.options)


def test_crash_after_receipt_before_commit_retries_without_another_receipt(world, monkeypatch):
    w = world
    event, coverage = _ready(w)
    plan = settlement.make_plan(w.rt, w.key, coverage=coverage, **w.options)
    real_settle = w.rt.ledger.settle_reviewed_events

    def crash(*_args):
        raise RuntimeError("simulated process exit before ledger commit")

    monkeypatch.setattr(w.rt.ledger, "settle_reviewed_events", crash)
    with pytest.raises(RuntimeError, match="simulated"):
        settlement.apply_plan(w.rt, plan, w.key)
    assert w.rt.ledger.event(event)["status"] == "pending"
    (receipt,) = (w.rt.state_dir / "event-settlements").glob("*.json")
    monkeypatch.setattr(w.rt.ledger, "settle_reviewed_events", real_settle)
    assert settlement.apply_plan(w.rt, plan, w.key) == receipt
    assert w.rt.ledger.event(event)["status"] == "done"


def test_active_snapshot_corruption_and_nonexistent_source_event_refuse(world):
    w = world
    event, coverage = _ready(w)
    coverage["events"][0]["id"] = event + 100
    with pytest.raises(ValueError, match="does not exist"):
        settlement.make_plan(w.rt, w.key, coverage=coverage, **w.options)
    coverage["events"][0]["id"] = event
    plan = settlement.make_plan(w.rt, w.key, coverage=coverage, **w.options)
    page = w.rt.state_dir / "active" / "knowledge" / PAGE
    page.write_text(page.read_text() + "\nunauthorized mutation\n")
    with pytest.raises(RuntimeError, match="snapshot"):
        settlement.apply_plan(w.rt, plan, w.key)
    assert w.rt.ledger.event(event)["status"] == "pending"
