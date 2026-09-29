"""`kb accept-unknown`: an unknown knowledge commit judged through the gate instead of reverted."""

from __future__ import annotations

import json

import pytest

from infermatrix_copilot.kb_service import merge
from infermatrix_copilot.kb_service.accept import ACCEPT, AcceptError, accept_pending, request_accept
from infermatrix_copilot.kb_service.audit import DISPOSED, UNKNOWN, audit_main, open_unknown, provenance_problems
from infermatrix_copilot.knowledge_service.ops import KnowledgeOperation as Op, apply_operations
from test_kb_audit import _land, _setup
from test_kb_flow import _items
from test_kb_intake_gate import PAGE, ScriptedGateway, _calibrate, _judge_all, _rule
from test_kb_provenance import _open_revert


def _sneak_rule(origin):
    """A reasonable rule pushed straight to main, around the gate."""
    page = origin / "knowledge" / PAGE
    before = page.read_text()
    after = apply_operations({PAGE: before}, [Op("add", PAGE, "DEMO-2a", _rule("DEMO-2a", "PR #11"))],
                             release="v1", today="2026-09-29").files[PAGE]
    return _land(origin, f"knowledge/{PAGE}", after, "add a rule directly"), before


def _unknown(tmp_path, *, judge="yes"):
    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    rt.gateway = ScriptedGateway(_judge_all(judge))
    _calibrate(tmp_path, rt, lifecycle)
    sha, before = _sneak_rule(origin)
    audit_main(rt, scheduler._pause)
    assert open_unknown(rt) == [sha]
    return rt, rt.registry["demo"], scheduler, origin, sha, before


def _state(rt, sha):
    return json.loads(rt.ledger.get_cursor("*", ACCEPT + sha))


def test_an_accepted_commit_is_disposed_of_and_its_revert_closed(tmp_path):
    rt, lifecycle, scheduler, origin, sha, before = _unknown(tmp_path)
    assert request_accept(rt.ledger, sha[:10], at=rt.clock()) == sha
    (event,) = accept_pending(rt)
    assert "requested" in event and _state(rt, sha)["state"] == "requested"   # its revert PR is being opened
    revert_id, _head = _open_revert(rt, origin, sha, before)
    (event,) = accept_pending(rt)
    assert f"accept {sha[:12]} accepted" in event and "kb resume --repo demo" in event
    assert rt.ledger.get_cursor("*", DISPOSED + sha) == sha and open_unknown(rt) == []
    (accepted,) = rt.ledger.changesets_of_kind("demo", "accept")
    assert accepted["status"] == "accepted" and accepted["detail"]["accepts"] == sha
    assert accepted["detail"]["decision"]["status"] == "pass"
    revert = rt.ledger.changeset(revert_id)
    assert revert["status"] == "superseding"
    assert [i["body"]["pr"] for i in _items(tmp_path, "close")] == [90]
    assert rt.ledger.events("demo", "pending") == []                         # the candidate is dropped
    assert provenance_problems(rt, rt.knowledge.fetch()) == []               # activation may pass it now
    assert audit_main(rt, scheduler._pause) == []
    assert accept_pending(rt) == []                                          # decided once


def test_a_commit_the_gate_rejects_stays_unknown(tmp_path):
    rt, lifecycle, scheduler, origin, sha, before = _unknown(tmp_path, judge="no")
    _open_revert(rt, origin, sha, before)
    request_accept(rt.ledger, sha, at=rt.clock())
    (event,) = accept_pending(rt)
    assert "refused" in event and "the gate did not pass it (fail)" in event
    assert open_unknown(rt) == [sha] and rt.ledger.get_cursor("*", DISPOSED + sha) is None
    assert any("accept-unknown" in row["reason"] for row in rt.ledger.human_queue("demo"))
    (rejected,) = rt.ledger.changesets_of_kind("demo", "accept")
    assert rejected["status"] == "failed"
    assert rt.ledger.changesets_of_kind("demo", "revert")[0]["status"] == "revert_open"   # the revert stays


def test_no_acceptance_without_a_current_judge_calibration(tmp_path):
    rt, lifecycle, scheduler, origin, sha, before = _unknown(tmp_path)
    _open_revert(rt, origin, sha, before)
    _calibrate(tmp_path, rt, lifecycle, passed=False)
    request_accept(rt.ledger, sha, at=rt.clock())
    (event,) = accept_pending(rt)
    assert "calibration" in event and open_unknown(rt) == [sha]
    assert rt.ledger.changesets_of_kind("demo", "accept") == []              # nothing was judged


def test_a_change_outside_the_governed_pages_cannot_be_accepted(tmp_path):
    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    _calibrate(tmp_path, rt, lifecycle)
    sha = _land(origin, "knowledge/repos/demo/tools/x.py", "print(1)\n", "a script, directly")
    audit_main(rt, scheduler._pause)
    request_accept(rt.ledger, sha, at=rt.clock())
    (event,) = accept_pending(rt)
    assert "does not govern" in event and open_unknown(rt) == [sha]


def test_requests_are_validated_when_recorded(tmp_path):
    rt, lifecycle, scheduler, origin, sha, before = _unknown(tmp_path)
    with pytest.raises(AcceptError, match="not a commit SHA"):
        request_accept(rt.ledger, "HEAD", at=0)
    with pytest.raises(AcceptError, match="matches 0 unknown commits"):
        request_accept(rt.ledger, "0" * 40, at=0)
    rt.ledger.set_cursor("*", DISPOSED + sha, "f" * 40)
    with pytest.raises(AcceptError, match="already disposed"):
        request_accept(rt.ledger, sha, at=0)
    assert rt.ledger.get_cursor("*", UNKNOWN + sha)                          # the record itself is untouched


def test_without_the_lease_nothing_is_judged(tmp_path):
    rt, lifecycle, scheduler, origin, sha, before = _unknown(tmp_path)
    request_accept(rt.ledger, sha, at=rt.clock())
    rt.lease_owner = None
    assert accept_pending(rt) == [] and _state(rt, sha)["state"] == "requested"


def test_kb_status_lists_open_unknown_commits_with_their_request(tmp_path, monkeypatch, capsys):
    from infermatrix_copilot.kb_service.cli import _unknown_status

    rt, lifecycle, scheduler, origin, sha, before = _unknown(tmp_path)
    request_accept(rt.ledger, sha, at=1.0)
    status = _unknown_status(rt.ledger)
    assert status[sha]["state"] == "reverting" and status[sha]["accept"]["state"] == "requested"
    rt.ledger.set_cursor("*", DISPOSED + sha, sha)
    assert _unknown_status(rt.ledger) == {}
    assert merge.is_paused(rt.ledger, "demo")                                # resuming stays a person's call


def test_an_interrupted_acceptance_is_finished_without_judging_again(tmp_path):
    rt, lifecycle, scheduler, origin, sha, before = _unknown(tmp_path)
    revert_id, _head = _open_revert(rt, origin, sha, before)
    request_accept(rt.ledger, sha, at=rt.clock())
    real = rt.ledger.update_changeset

    def crash(changeset_id, **fields):
        if changeset_id == revert_id:
            raise RuntimeError("the process died here")
        return real(changeset_id, **fields)
    rt.ledger.update_changeset = crash
    with pytest.raises(RuntimeError):
        accept_pending(rt)
    rt.ledger.update_changeset = real
    assert rt.ledger.get_cursor("*", DISPOSED + sha) is None                 # not disposed of half-way
    calls = len(rt.gateway.calls)
    (event,) = accept_pending(rt)
    assert "accepted" in event and len(rt.gateway.calls) == calls           # finished, not judged again
    assert rt.ledger.changeset(revert_id)["status"] == "superseding"
    assert rt.ledger.get_cursor("*", DISPOSED + sha) == sha
    assert len(rt.ledger.changesets_of_kind("demo", "accept")) == 1


def test_the_candidate_is_dropped_however_many_events_wait(tmp_path):
    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    rt.gateway = ScriptedGateway(_judge_all("yes"))
    _calibrate(tmp_path, rt, lifecycle)
    for n in range(1001):
        rt.ledger.record_event("demo", "merged_pr", str(n), {})
    sha, before = _sneak_rule(origin)
    audit_main(rt, scheduler._pause)
    _open_revert(rt, origin, sha, before)
    request_accept(rt.ledger, sha, at=rt.clock())
    accept_pending(rt)
    assert rt.ledger.event_by_external_id("demo", "unrecorded", sha)["status"] == "superseded"


def test_an_accepted_retirement_becomes_purgeable_next_release(tmp_path):
    from dataclasses import replace

    rt, lifecycle, scheduler, origin = _setup(tmp_path)
    rt.gateway = ScriptedGateway(_judge_all("yes"))
    rt.release_label = lambda repo: "v1"
    _calibrate(tmp_path, rt, lifecycle)
    rt.registry["demo"] = replace(rt.registry["demo"], retire_ratio=1.0)
    _land(origin, "skills/x.md", "no citations here\n", "drop the citation")   # else it needs a companion
    before = (origin / "knowledge" / PAGE).read_text()
    retired = apply_operations({PAGE: before}, [Op("retire", PAGE, "DEMO-1a", reason="upstream-removed",
                                                   evidence="PR #13")], release="v1", today="2026-09-29").files[PAGE]
    sha = _land(origin, f"knowledge/{PAGE}", retired, "retire a rule directly")
    audit_main(rt, scheduler._pause)
    _open_revert(rt, origin, sha, before)
    request_accept(rt.ledger, sha, at=rt.clock())
    (event,) = accept_pending(rt)
    assert "accepted" in event, event
    assert [r["rule_id"] for r in rt.ledger.purge_eligible("demo", "v2")] == ["DEMO-1a"]
