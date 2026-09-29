"""Refused merges: sign again, rebuild on current main, or hand to people."""

from __future__ import annotations

from infermatrix_copilot.kb_service import merge
from test_kb_flow import KnowledgeGitHub, _ack, _flow_runtime, _items, _open_pr

HEAD = "d" * 40


def _posted(tmp_path):
    """A change set whose merge item the publisher's local gate is about to answer."""
    rt, lifecycle = _flow_runtime(tmp_path)
    changeset_id, publisher = _open_pr(tmp_path, rt, lifecycle)
    _ack(tmp_path, rt, publisher, kind="open_pr", changeset_id=changeset_id, ok=True, pr=42, head_sha=HEAD)
    rt.github.prs[42] = {"state": "open", "merged": False, "head": {"sha": HEAD}}
    assert merge.advance(rt, lifecycle) == [f"merge issued {changeset_id}"]
    assert rt.ledger.changeset(changeset_id)["status"] == "merge_requested"
    rt._test = (tmp_path, publisher, changeset_id)
    return rt, lifecycle, changeset_id, publisher


def _fail(rt, problem, *, transient=False):
    """The publisher's local gate refused the merge with this problem."""
    tmp_path, publisher, changeset_id = rt._test
    if transient:
        _ack(tmp_path, rt, publisher, kind="merge", changeset_id=changeset_id, ok=False, error=problem)
    else:
        _ack(tmp_path, rt, publisher, kind="merge", changeset_id=changeset_id, ok=False,
             error=f"local gate: {problem}", problems=[problem])


def test_the_signing_time_is_recorded_with_the_merge_item(tmp_path):
    rt, lifecycle, changeset_id, _ = _posted(tmp_path)
    assert rt.ledger.changeset(changeset_id)["detail"]["verdict_issued_at"] == rt.clock()


def test_transient_refusals_are_signed_again(tmp_path):
    rt, lifecycle, changeset_id, _ = _posted(tmp_path)
    _fail(rt, "main kept moving while PR #42 was checked; retried next round", transient=True)
    assert rt.ledger.changeset(changeset_id)["status"] == "pr_open"
    assert merge.advance(rt, lifecycle) == [f"merge issued {changeset_id}"]   # a fresh verdict, same head
    assert len(_items(tmp_path, "merge")) == 1   # the answered item left the outbox; this is the new one


def test_a_real_problem_goes_to_people_once(tmp_path):
    rt, lifecycle, changeset_id, _ = _posted(tmp_path)
    _fail(rt, "L1 duplicate_rule_id  DEMO-2a")
    assert rt.ledger.changeset(changeset_id)["status"] == "gate_failed"
    assert len(rt.ledger.human_queue("demo")) == 1
    assert merge.advance(rt, lifecycle) == []
    assert _items(tmp_path, "merge") == []       # never retried as is


def test_a_context_change_rebuilds_on_current_main_and_replaces_the_pr(tmp_path):
    rt, lifecycle, changeset_id, _ = _posted(tmp_path)
    _fail(rt, "context changed since the verdict was judged: repos/demo/core/_index.md")
    assert rt.ledger.changeset(changeset_id)["status"] == "rebuild_needed"
    assert merge.advance(rt, lifecycle) == []           # outside the scheduler: no lease, no rebuild
    rt.lease_owner = rt.ledger.acquire_lease("scheduler")
    events = merge.advance(rt, lifecycle)
    assert len(events) == 1 and events[0].startswith(f"rebuilt {changeset_id} as ")
    new_id = events[0].rsplit(" ", 1)[1]
    old, new = rt.ledger.changeset(changeset_id), rt.ledger.changeset(new_id)
    assert old["status"] == "superseding" and new["status"] == "pr_requested"
    assert new["detail"]["operations"] == old["detail"]["operations"]
    assert new["detail"]["base_sha"] == rt.knowledge.main_sha()
    (close,) = _items(tmp_path, "close")
    assert close["body"]["pr"] == 42 and new_id in close["body"]["reason"]
    assert any(item["body"]["changeset_id"] == new_id for item in _items(tmp_path, "open_pr"))
    # the replaced PR stays tracked until GitHub shows it closed
    assert merge.advance(rt, lifecycle) == []
    start = rt.clock()
    rt.clock = lambda: start + 25 * 3600                      # the close item expired unanswered
    merge.advance(rt, lifecycle)
    assert len(_items(tmp_path, "close")) == 2
    rt.github.prs[42] = {"state": "closed", "merged": False, "head": {"sha": HEAD}}
    assert f"superseded {changeset_id}" in merge.advance(rt, lifecycle)
    assert rt.ledger.changeset(changeset_id)["status"] == "superseded"
    assert rt.ledger.changesets("demo", ("closed",)) == []   # not counted as overturned by people


def test_an_interrupted_rebuild_resumes_instead_of_staging_twice(tmp_path):
    rt, lifecycle, changeset_id, _ = _posted(tmp_path)
    rt.lease_owner = rt.ledger.acquire_lease("scheduler")
    old = rt.ledger.changeset(changeset_id)
    real_update = rt.ledger.update_changeset
    calls = {"n": 0}

    def crash_once(cs_id, **fields):
        if cs_id == changeset_id and fields.get("status") == "superseding" and not calls["n"]:
            calls["n"] += 1
            raise RuntimeError("crash after staging the rebuild")
        return real_update(cs_id, **fields)

    rt.ledger.update_changeset = crash_once
    import pytest
    with pytest.raises(RuntimeError):
        merge.rebuild(rt, lifecycle, old, "context changed since the verdict was judged: x")
    rebuilt = rt.ledger.changesets("demo", ("gated", "pr_requested"))
    assert len(rebuilt) == 1
    new_id = merge.rebuild(rt, lifecycle, rt.ledger.changeset(changeset_id), "context changed since ...")
    assert new_id == rebuilt[0]["id"]
    assert len([cs for cs in rt.ledger.changesets("demo", ("gated", "pr_requested")) if cs["kind"] == "rebuild"]) == 1


def test_a_rebuild_that_fails_its_own_gate_leaves_the_pr_to_people(tmp_path):
    from test_kb_intake_gate import ScriptedGateway, _generator_then_judge

    rt, lifecycle, changeset_id, _ = _posted(tmp_path)
    rt.gateway = ScriptedGateway(_generator_then_judge("no"))
    _fail(rt, "context changed since the verdict was judged: repos/demo/core/_index.md")
    rt.lease_owner = rt.ledger.acquire_lease("scheduler")
    assert merge.advance(rt, lifecycle) == [f"rebuild_failed {changeset_id}"]
    assert rt.ledger.changeset(changeset_id)["status"] == "rebuild_failed"
    assert _items(tmp_path, "close") == [] and rt.ledger.human_queue("demo")


def test_a_rule_that_no_longer_applies_goes_to_people(tmp_path):
    rt, lifecycle, changeset_id, _ = _posted(tmp_path)
    detail = rt.ledger.changeset(changeset_id)["detail"]
    detail["operations"] = [{"kind": "edit_same_meaning", "page": "repos/demo/core/rules.md",
                             "rule_id": "DEMO-9z", "section_markdown": "## DEMO-9z — gone\n"}]
    rt.ledger.update_changeset(changeset_id, detail=detail)
    _fail(rt, "the PR does not merge cleanly into the current base")
    rt.lease_owner = rt.ledger.acquire_lease("scheduler")
    assert merge.advance(rt, lifecycle) == [f"rebuild_failed {changeset_id}"]
    assert rt.ledger.changeset(changeset_id)["status"] == "rebuild_failed"
    assert rt.ledger.human_queue("demo")
