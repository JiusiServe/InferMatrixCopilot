"""Stale verdicts: re-sign, rebuild on current main, or hand to people."""

from __future__ import annotations

from infermatrix_copilot.kb_service import merge
from test_kb_flow import KnowledgeGitHub, _ack, _flow_runtime, _items, _open_pr

HEAD = "d" * 40


class GateGitHub(KnowledgeGitHub):
    """kb-gate statuses with descriptions (the verifier's first problem)."""

    def __init__(self):
        super().__init__()
        self.descriptions: dict[str, str] = {}

    def _answer(self, url):
        if "/commits/" in url and url.endswith("/status"):
            sha = url.split("/commits/")[1].split("/")[0]
            state = self.statuses.get(sha)
            return {"statuses": [{"context": "kb-gate", "state": state,
                                  "description": self.descriptions.get(sha, "")}] if state else []}
        return super()._answer(url)


def _posted(tmp_path):
    rt, lifecycle = _flow_runtime(tmp_path)
    github = GateGitHub()
    github.prs = rt.github.prs
    rt.github = github
    changeset_id, publisher = _open_pr(tmp_path, rt, lifecycle)
    _ack(tmp_path, rt, publisher, kind="open_pr", changeset_id=changeset_id, ok=True, pr=42, head_sha=HEAD)
    rt.github.prs[42] = {"state": "open", "merged": False, "head": {"sha": HEAD}}
    assert merge.advance(rt, lifecycle) == [f"verdict issued {changeset_id}"]
    _ack(tmp_path, rt, publisher, kind="post_verdict", changeset_id=changeset_id, ok=True)
    assert rt.ledger.changeset(changeset_id)["status"] == "verdict_posted"
    return rt, lifecycle, changeset_id, publisher


def _fail(rt, description):
    rt.github.statuses[HEAD] = "failure"
    rt.github.descriptions[HEAD] = description


def test_the_signing_time_is_recorded_and_an_old_verdict_is_resigned(tmp_path):
    rt, lifecycle, changeset_id, _ = _posted(tmp_path)
    signed_at = rt.ledger.changeset(changeset_id)["detail"]["verdict_issued_at"]
    assert signed_at == rt.clock()
    start = rt.clock()
    rt.clock = lambda: start + merge.RESIGN_AFTER + 1
    assert merge.advance(rt, lifecycle) == [f"resign {changeset_id}"]
    assert merge.advance(rt, lifecycle) == [f"verdict issued {changeset_id}"]   # a fresh verdict, same head
    assert len(_items(tmp_path, "post_verdict")) >= 1


def test_an_expired_or_missing_verdict_is_resigned(tmp_path):
    rt, lifecycle, changeset_id, _ = _posted(tmp_path)
    _fail(rt, "no valid signed verdict for PR #42 at dddddddddddd (rejected: verdict is outside its issue window)")
    assert merge.advance(rt, lifecycle) == [f"resign {changeset_id}"]
    assert rt.ledger.changeset(changeset_id)["status"] == "pr_open"


def test_transient_gate_failures_wait(tmp_path):
    rt, lifecycle, changeset_id, _ = _posted(tmp_path)
    _fail(rt, "hold list: hold list is stale (the knowledge service may be down)")
    assert merge.advance(rt, lifecycle) == []
    assert rt.ledger.changeset(changeset_id)["status"] == "verdict_posted"


def test_a_real_problem_goes_to_people_once(tmp_path):
    rt, lifecycle, changeset_id, _ = _posted(tmp_path)
    _fail(rt, "L1 duplicate_rule_id  DEMO-2a")
    assert merge.advance(rt, lifecycle) == [f"gate_failed {changeset_id}"]
    assert rt.ledger.changeset(changeset_id)["status"] == "gate_failed"
    assert rt.ledger.human_queue("demo")
    assert merge.advance(rt, lifecycle) == []


def test_a_context_change_rebuilds_on_current_main_and_replaces_the_pr(tmp_path):
    rt, lifecycle, changeset_id, _ = _posted(tmp_path)
    _fail(rt, "context changed since the verdict was judged: repos/demo/core/_index.md")
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
    _fail(rt, "does not merge cleanly into the current base")
    rt.lease_owner = rt.ledger.acquire_lease("scheduler")
    assert merge.advance(rt, lifecycle) == [f"rebuild_failed {changeset_id}"]
    assert rt.ledger.changeset(changeset_id)["status"] == "rebuild_failed"
    assert rt.ledger.human_queue("demo")


def test_a_queued_pr_that_stalls_is_resigned_and_frees_the_queue_slot(tmp_path):
    rt, lifecycle, changeset_id, publisher = _posted(tmp_path)
    rt.github.statuses[HEAD] = "success"
    assert merge.advance(rt, lifecycle) == [f"enqueue issued {changeset_id}"]
    _ack(tmp_path, rt, publisher, kind="enqueue", changeset_id=changeset_id, ok=True)
    assert rt.ledger.changeset(changeset_id)["status"] == "queued"
    start = rt.clock()
    rt.clock = lambda: start + merge.QUEUE_STALL + 1
    assert merge.advance(rt, lifecycle) == [f"requeue {changeset_id}"]
    assert rt.ledger.changeset(changeset_id)["status"] == "queued"   # the slot is held until dequeued
    assert merge.advance(rt, lifecycle) == []                          # the pause item is pending
    (pause,) = _items(tmp_path, "pause")
    assert pause["body"]["pr"] == 42
    _ack(tmp_path, rt, publisher, kind="pause", changeset_id=changeset_id, ok=True)
    assert rt.ledger.changeset(changeset_id)["status"] == "pr_open"
    assert merge.advance(rt, lifecycle) == [f"verdict issued {changeset_id}"]


def test_an_outstanding_enqueue_blocks_re_signing_until_its_ack(tmp_path):
    rt, lifecycle, changeset_id, publisher = _posted(tmp_path)
    rt.github.statuses[HEAD] = "success"
    assert merge.advance(rt, lifecycle) == [f"enqueue issued {changeset_id}"]
    detail = rt.ledger.changeset(changeset_id)["detail"]
    rt.ledger.update_changeset(changeset_id, detail={**detail, "verdict_issued_at": rt.clock() - merge.RESIGN_AFTER - 1})
    _fail(rt, "no valid signed verdict for PR #42")
    assert merge.advance(rt, lifecycle) == []                        # not re-signed under a live enqueue
    assert rt.ledger.changeset(changeset_id)["pending_item"]["kind"] == "enqueue"
    _ack(tmp_path, rt, publisher, kind="enqueue", changeset_id=changeset_id, ok=True)   # a delayed ack
    assert rt.ledger.changeset(changeset_id)["status"] == "queued"
    assert merge.advance(rt, lifecycle) == [f"requeue {changeset_id}"]  # the queued path dequeues first


def test_our_own_hold_label_and_statuses_older_than_the_verdict_never_escalate(tmp_path):
    rt, lifecycle, changeset_id, _ = _posted(tmp_path)
    _fail(rt, "PR #42 carries kb:hold")
    assert merge.advance(rt, lifecycle) == []
    _fail(rt, "L1 duplicate_rule_id  DEMO-2a")

    class Old(GateGitHub):
        def _answer(self, url):
            answer = super()._answer(url)
            for status in answer.get("statuses", []) if isinstance(answer, dict) else []:
                status["updated_at"] = "2020-01-01T00:00:00Z"     # posted before this verdict
            return answer

    old = Old()
    old.prs, old.statuses, old.descriptions = rt.github.prs, rt.github.statuses, rt.github.descriptions
    rt.github = old
    assert merge.advance(rt, lifecycle) == []
    assert rt.ledger.changeset(changeset_id)["status"] == "verdict_posted"


def test_an_outstanding_enqueue_holds_the_single_queue_slot(tmp_path):
    rt, lifecycle, first, publisher = _posted(tmp_path)
    rt.github.statuses[HEAD] = "success"
    assert merge.advance(rt, lifecycle) == [f"enqueue issued {first}"]
    second = rt.ledger.new_changeset_id("demo", "intake")
    rt.ledger.stage_intake(rt.ledger.acquire_lease("t2"), "demo", second, detail={}, status="verdict_posted",
                           kind="intake", verdicts=[], human_reason="", drafted_events=[])
    rt.ledger.update_changeset(second, pr_number=43, head_sha="e" * 40)
    rt.github.prs[43] = {"state": "open", "merged": False, "head": {"sha": "e" * 40}}
    rt.github.statuses["e" * 40] = "success"
    assert merge.advance(rt, lifecycle) == []        # the first's enqueue is still executable
    assert [i["body"]["changeset_id"] for i in _items(tmp_path, "enqueue")] == [first]
