"""Refine and recheck: a change the gate rejected is never merged; it is refined and judged again."""

from __future__ import annotations

import json

import pytest

from infermatrix_copilot.kb_service import merge
from infermatrix_copilot.kb_service.refine import (
    MAX_REFINES, operation_key, refinement_validator, rejected_operations,
)
from infermatrix_copilot.kb_service.runtime import collect_events, run_intake
from test_kb_flow import _ack, _flow_runtime, _items, _open_pr
from test_kb_intake_gate import PAGE, ScriptedGateway, _judge_all, _rule

HEAD = "d" * 40


class Judges:
    """The generator adds a rule; the judge answers from a script, one verdict per judging round."""

    def __init__(self, verdicts):
        self.verdicts = list(verdicts)   # "yes"/"no" per round of block judging
        self.prompts: list[str] = []

    def __call__(self, role, prompt):
        if role.name == "generator":
            self.prompts.append(prompt)
            op = {"kind": "add", "page": PAGE, "rule_id": "DEMO-2a",
                  "section_markdown": _rule("DEMO-2a", "PR #11")}
            data = {"operations": [op], "rationale": "r"}
            if "gate_feedback" in prompt:
                payload = json.loads(prompt.split("<untrusted_data>\n", 1)[1].split("\n</untrusted_data>", 1)[0])
                if operation_key(op) in payload.get("rejected_operations", []):
                    data["operation_dispositions"] = [
                        {"operation": operation_key(op), "action": "revise", "reason": "correct cited claim",
                         "replacements": [operation_key(op)]}]
            return data
        if '"directory"' in prompt:
            return {"verdict": "consistent", "conflicts": []}
        value = self.verdicts[0] if self.verdicts else "yes"
        answer = _judge_all(value)(role, prompt)
        if value == "no":
            answer["reasons"] = {d: "the claim is not in the evidence" for d in answer["dimensions"]}
        return answer

    def next_round(self):
        if self.verdicts:
            self.verdicts.pop(0)


def _runtime(tmp_path, verdicts):
    rt, lifecycle = _flow_runtime(tmp_path)
    judges = Judges(verdicts)
    rt.gateway = ScriptedGateway(judges)
    rt.lease_owner = rt.ledger.acquire_lease("scheduler")
    return rt, lifecycle, judges


def test_a_rejected_intake_is_refined_with_the_reasons_and_judged_again(tmp_path):
    rt, lifecycle, judges = _runtime(tmp_path, ["no", "yes"])
    collect_events(rt, lifecycle)
    first = run_intake(rt, lifecycle)
    assert rt.ledger.changeset(first)["status"] == "failed"
    judges.next_round()
    events = merge.advance(rt, lifecycle)
    (event,) = [e for e in events if e.startswith("refined")]
    new_id = event.rsplit(" ", 1)[1]
    assert "gate_feedback" in judges.prompts[-1] and "not in the evidence" in judges.prompts[-1]
    old, new = rt.ledger.changeset(first), rt.ledger.changeset(new_id)
    assert old["status"] == "refined" and old["detail"]["refined_as"] == new_id
    assert new["kind"] == "refine" and new["detail"]["refine_round"] == 1
    assert new["status"] == "pr_requested"        # passed the whole gate again, then handed over
    assert merge.advance(rt, lifecycle) == []     # refined once, not again


def test_a_change_still_rejected_after_two_refinements_stays_unmerged_for_people(tmp_path):
    rt, lifecycle, judges = _runtime(tmp_path, ["no"] * (MAX_REFINES + 1))
    collect_events(rt, lifecycle)
    run_intake(rt, lifecycle)
    for _ in range(MAX_REFINES + 1):
        merge.advance(rt, lifecycle)
    exhausted = rt.ledger.changesets("demo", ("refine_exhausted",))
    assert len(exhausted) == 1 and exhausted[0]["detail"]["refine_round"] == MAX_REFINES
    assert len(exhausted[0]["detail"]["refine_history"]) == MAX_REFINES + 1
    (row,) = rt.ledger.human_queue("demo")
    assert f"still rejected after {MAX_REFINES} refinements" in row["reason"] and "round 0" in row["reason"]
    assert not _items(tmp_path, "open_pr") and not _items(tmp_path, "merge")
    calls = len(judges.prompts)
    merge.advance(rt, lifecycle)
    assert len(judges.prompts) == calls          # no more paid generator calls


def test_a_pr_the_local_gate_refused_is_replaced_by_a_refined_one(tmp_path):
    rt, lifecycle = _flow_runtime(tmp_path)
    changeset_id, publisher = _open_pr(tmp_path, rt, lifecycle)
    _ack(tmp_path, rt, publisher, kind="open_pr", changeset_id=changeset_id, ok=True, pr=42, head_sha=HEAD)
    rt.github.prs[42] = {"state": "open", "merged": False, "head": {"sha": HEAD}}
    merge.advance(rt, lifecycle)
    _ack(tmp_path, rt, publisher, kind="merge", changeset_id=changeset_id, ok=False,
         error="local gate: L1 dangling_reference repos/demo/x.md DEMO-1a",
         problems=["L1 dangling_reference repos/demo/x.md DEMO-1a"])
    assert rt.ledger.changeset(changeset_id)["status"] == "refine_needed"
    assert rt.ledger.human_queue("demo") == []    # not people yet: refined first
    judges = Judges(["yes"])
    rt.gateway = ScriptedGateway(judges)
    rt.lease_owner = rt.ledger.acquire_lease("scheduler")
    events = merge.advance(rt, lifecycle)
    assert any(e.startswith(f"refined {changeset_id} as ") for e in events)
    assert "dangling_reference" in judges.prompts[-1]
    old = rt.ledger.changeset(changeset_id)
    assert old["status"] == "superseding"
    (close,) = _items(tmp_path, "close")
    assert close["body"]["pr"] == 42
    assert rt.ledger.changeset(old["detail"]["refined_as"])["status"] == "pr_requested"


def test_a_refinement_is_never_staged_twice(tmp_path):
    rt, lifecycle, judges = _runtime(tmp_path, ["no", "yes"])
    collect_events(rt, lifecycle)
    first = run_intake(rt, lifecycle)
    judges.next_round()
    real = rt.ledger.update_changeset
    crashed = {"n": 0}

    def crash_once(cs_id, **fields):
        if cs_id == first and fields.get("status") == "refined" and not crashed["n"]:
            crashed["n"] += 1
            raise RuntimeError("crash after staging the refinement")
        return real(cs_id, **fields)
    rt.ledger.update_changeset = crash_once
    import pytest
    with pytest.raises(RuntimeError):
        merge.advance(rt, lifecycle)
    rt.ledger.update_changeset = real
    merge.advance(rt, lifecycle)
    assert len([cs for cs in rt.ledger.changesets("demo", ("pr_requested", "gated", "failed"))
                if cs["kind"] == "refine"]) == 1


def test_an_external_pr_refused_by_the_local_gate_is_told_why(tmp_path):
    rt, lifecycle = _flow_runtime(tmp_path)
    owner = rt.ledger.acquire_lease("t")
    cs = rt.ledger.new_changeset_id("demo", "external")
    rt.ledger.stage_intake(owner, "demo", cs, kind="external", status="merge_requested", verdicts=[],
                           human_reason="", drafted_events=[], detail={})
    rt.ledger.update_changeset(cs, pr_number=7, head_sha=HEAD, pending_item={"id": "m1", "kind": "merge",
                                                                              "expires_at": rt.clock() + 60})
    merge.apply_acks(rt, [{"item_id": "m1", "kind": "merge", "changeset_id": cs, "ok": False,
                           "error": "local gate: L1 x", "problems": ["L1 x"]}])
    assert rt.ledger.changeset(cs)["status"] == "gate_failed"
    assert rt.ledger.human_queue("demo") == []           # its author is told, and it is checked again daily
    (findings,) = [item["body"] for item in _items(tmp_path, "post_findings")]
    assert findings["pr"] == 7 and "- L1 x" in findings["comment"]
    assert json.dumps(rt.ledger.changeset(cs)["detail"]["gate_problems"]) == '["L1 x"]'


def _failed_intake(tmp_path, verdicts):
    rt, lifecycle, judges = _runtime(tmp_path, verdicts)
    collect_events(rt, lifecycle)
    first = run_intake(rt, lifecycle)
    assert rt.ledger.changeset(first)["status"] == "failed"
    return rt, lifecycle, judges, first


def test_every_piece_of_evidence_reaches_the_refinement(tmp_path):
    rt, lifecycle, judges, first = _failed_intake(tmp_path, ["no"])
    data = rt.load_changeset_files(first)
    data["evidence"] = [{"source_reference": "PR #11", "title": "Bound the queue", "changed_files": ["a.py"]},
                        {"source_reference": "PR #12", "title": "Retry the upload", "changed_files": ["b.py"]}]
    rt.save_changeset_files(first, data)
    merge.advance(rt, lifecycle)
    prompt = judges.prompts[-1]
    assert "Bound the queue" in prompt and "Retry the upload" in prompt and "PR #12" in prompt


def test_a_rebuild_keeps_the_refine_limit(tmp_path):
    rt, lifecycle, judges, first = _failed_intake(tmp_path, ["no"])
    detail = rt.ledger.changeset(first)["detail"]
    rt.ledger.update_changeset(first, status="rebuild_needed", pr_number=42, head_sha=HEAD, detail={
        **detail, "refine_round": MAX_REFINES, "refine_history": [{"changeset": "a", "reasons": ["x"]},
                                                                  {"changeset": "b", "reasons": ["y"]}]})
    new_id = merge.rebuild(rt, lifecycle, rt.ledger.changeset(first), "context changed since ...")
    assert new_id is None                                   # the rebuild was rejected by its own gate
    (rebuilt,) = [cs for cs in rt.ledger.changesets_of_kind("demo", "rebuild")]
    assert rebuilt["detail"]["refine_round"] == MAX_REFINES  # the lineage carried over
    calls = len(judges.prompts)
    merge.advance(rt, lifecycle)
    assert rt.ledger.changeset(rebuilt["id"])["status"] == "refine_exhausted"   # no third refinement
    assert len(judges.prompts) == calls


def test_a_refinement_staged_before_a_crash_is_found_in_any_status(tmp_path):
    from infermatrix_copilot.kb_service.refine import REFINE_MARK

    rt, lifecycle, judges, first = _failed_intake(tmp_path, ["no"])
    staged = rt.ledger.new_changeset_id("demo", "refine")
    rt.save_changeset_files(staged, {"base_sha": "x", "files": {}, "deleted": [],
                                     "evidence": [{"source_reference": REFINE_MARK + first}]})
    rt.ledger.stage_intake(rt.lease_owner, "demo", staged, kind="refine", status="companion_pending",
                           verdicts=[], human_reason="", drafted_events=[], detail={})
    calls = len(judges.prompts)
    merge.advance(rt, lifecycle)
    assert len(judges.prompts) == calls                     # not drafted again
    assert rt.ledger.changeset(first)["detail"]["refined_as"] == staged


def test_a_refinement_may_carry_as_many_operations_as_the_change_set(tmp_path):
    rt, lifecycle, judges, first = _failed_intake(tmp_path, ["no"])
    data = rt.load_changeset_files(first)
    data["evidence"] = [{"source_reference": f"PR #{n}", "title": f"event {n}"} for n in (11, 12)]
    rt.save_changeset_files(first, data)
    many = [{"kind": "add", "page": PAGE, "rule_id": f"DEMO-{n}a", "section_markdown": _rule(f"DEMO-{n}a", "PR #11")}
            for n in range(3, 10)]                         # 7 operations: more than one event may carry

    class Many(Judges):
        def __call__(self, role, prompt):
            if role.name == "generator" and "gate_feedback" in prompt:
                self.prompts.append(prompt)
                return {"operations": many, "rationale": "r", "operation_dispositions": [
                    {"operation": PAGE + "::DEMO-2a", "action": "revise", "reason": "split corrected conclusions",
                     "replacements": [operation_key(op) for op in many]}]}
            return super().__call__(role, prompt)
    judges = Many(["yes"])
    rt.gateway = ScriptedGateway(judges)
    events = merge.advance(rt, lifecycle)
    (event,) = [e for e in events if e.startswith(f"refined {first} as ")]
    refined = rt.ledger.changeset(event.rsplit(" ", 1)[1])
    assert len(refined["detail"]["operations"]) == 7


def _operation(rule_id):
    return {"kind": "add", "page": PAGE, "rule_id": rule_id,
            "section_markdown": _rule(rule_id, "PR #11")}


def test_refinement_preserves_process_and_jev_learning_and_source_trace(tmp_path):
    """The live four-PR batch lost process/Jev rules while repairing browser rules."""
    from infermatrix_copilot.trace_store import TraceStore

    rt, lifecycle, judges, first = _failed_intake(tmp_path, ["no"])
    original = rt.ledger.changeset(first)["detail"]
    operations = [_operation(r) for r in ("DEMO-2a", "PROCESS-LEASE", "JEV-CONFIG")]
    rt.ledger.update_changeset(first, detail={**original, "operations": operations,
                                           "event_ids": [71, 72, 73], "source_event_ids": [71, 72, 73]})
    rt.traces = TraceStore(tmp_path / "trace")
    judges.next_round()
    merge.advance(rt, lifecycle)
    refined = rt.ledger.changeset(rt.ledger.changeset(first)["detail"]["refined_as"])
    assert {op["rule_id"] for op in refined["detail"]["operations"]} == {
        "DEMO-2a", "PROCESS-LEASE", "JEV-CONFIG"}
    assert refined["detail"]["event_ids"] == []
    assert refined["detail"]["source_event_ids"] == [71, 72, 73]
    dispositions = refined["detail"]["operation_dispositions"]
    assert {d["operation"] for d in dispositions if d["action"] == "keep"} == {
        PAGE + "::PROCESS-LEASE", PAGE + "::JEV-CONFIG"}
    # Full gate judges inherited operations too; no previous pass is reused.
    assert {b["rule_id"] for b in refined["detail"]["decision"]["blocks"]} == {
        "DEMO-2a", "PROCESS-LEASE", "JEV-CONFIG"}
    (trace,) = [r for r in rt.traces.query(kind="outcome") if r["result"].get("action") == "refinement"]
    assert trace["context"]["source_event_ids"] == [71, 72, 73]
    assert trace["result"]["operation_dispositions"] == dispositions


def test_refinement_requires_explicit_dispositions_and_allows_justified_failed_drop():
    previous = [_operation("BAD-CLAIM"), _operation("PROCESS-LEASE"), _operation("JEV-CONFIG")]
    bad = operation_key(previous[0])
    audit = {}
    validate = refinement_validator(previous, {bad}, audit)
    with pytest.raises(ValueError, match="missing explicit disposition"):
        validate({"operations": []})
    with pytest.raises(ValueError, match="missing explicit disposition"):
        validate({"operations": previous[1:]})
    data = {"operations": [], "operation_dispositions": [
        {"operation": bad, "action": "drop", "reason": "PR #11 shows the assertion was not implemented"}]}
    validate(data)
    assert data["operations"] == previous[1:]
    assert audit["operation_dispositions"][0]["action"] == "drop"
    with pytest.raises(ValueError, match="unrejected operation"):
        validate({"operations": [], "operation_dispositions": [
            data["operation_dispositions"][0],
            {"operation": operation_key(previous[1]), "action": "drop", "reason": "shorten the answer"}]})


def test_refinement_collision_rename_and_semantic_replacement_have_explicit_mapping():
    previous = [_operation("DUPLICATE-ID")]
    replacement = {"kind": "replace", "page": PAGE, "rule_id": "SERV-5j", "new_rule_id": "SPEECH-CAPABILITIES",
                   "section_markdown": _rule("SPEECH-CAPABILITIES"), "evidence": "PR #11"}
    renamed = _operation("FRESH-ID")
    data = {"operations": [renamed, replacement], "operation_dispositions": [
        {"operation": operation_key(previous[0]), "action": "revise", "reason": "fresh ID and supersede old meaning",
         "replacements": [operation_key(renamed), operation_key(replacement)]}]}
    refinement_validator(previous, {operation_key(previous[0])}, {})(data)
    assert data["operations"] == [renamed, replacement]


def test_refinement_gate_failure_scope_preserves_other_owners():
    process, browser, generation = [_operation(r) for r in ("PROCESS-LEASE", "JEV-CONFIG", "GEN-NATIVE")]
    browser["page"] = "repos/demo/browser/rules.md"
    generation["page"] = "repos/demo/generation/rules.md"
    detail = {"decision": {"blocks": [{"rule_id": "GEN-NATIVE", "verdict": "fail"}],
                           "consistency": [{"owner_dir": "repos/demo/browser", "verdict": "conflict"}],
                           "l1_issues": []}}
    assert rejected_operations([process, browser, generation], detail) == {
        operation_key(browser), operation_key(generation)}


@pytest.mark.parametrize("claim,citation", [
    ("`pkg/removed.py`", "PR #10"),
    ("`pkg/queue.py::Queue.removed`", "PR #10"),
    ("`pkg/queue.py::Queue.put`", "PR #99"),
])
def test_false_required_facts_can_be_refined_without_changing_valid_learning(claim, citation):
    from infermatrix_copilot.kb_service.gate import changes_between, run_gate
    from infermatrix_copilot.kb_service.intake import draft_changes
    from infermatrix_copilot.knowledge_service.ops import KnowledgeOperation, apply_operations
    from test_kb_intake_gate import GEN, JUDGE, _tree
    from test_kb_upstream_facts import FakeUpstream

    base, observer = _tree(), FakeUpstream()
    valid = "`pkg/queue.py::Queue.put`"
    bad, good = _operation("BAD-CLAIM"), _operation("GOOD-CLAIM")
    bad["section_markdown"] = _rule("BAD-CLAIM", citation, claim=claim)
    good["section_markdown"] = _rule("GOOD-CLAIM", "PR #10", claim=valid)
    previous = [bad, good]

    def gate(operations):
        result = apply_operations(base, [KnowledgeOperation.from_dict(op) for op in operations],
                                  release="v1", today="2026-10-02")
        head = {**base, **result.files}
        return run_gate(base=base, head=head, changes=changes_between(base, head), external_texts={},
                        evidence=[], gateway=ScriptedGateway(_judge_all("yes")), judge=JUDGE,
                        release="v1", repo_dir="repos/demo", facts=observer)

    failed = gate(previous)
    assert failed.status == "fail" and failed.blocks == []
    rejected = rejected_operations(previous, {"decision": failed.to_dict()})
    assert rejected == {operation_key(bad)}
    revised = {**bad, "section_markdown": _rule("BAD-CLAIM", "PR #10", claim=valid)}
    answer = {"operations": [revised], "operation_dispositions": [
        {"operation": operation_key(bad), "action": "revise", "reason": "correct the observed false fact",
         "replacements": [operation_key(revised)]}]}
    draft = draft_changes(repo="demo", repo_dir="repos/demo", event_id=0, evidence={}, files=base,
                          gateway=ScriptedGateway(lambda role, prompt: answer), generator=GEN,
                          release="v1", today="2026-10-02",
                          reply_validator=refinement_validator(previous, rejected, {}))
    normalized = [op.to_dict() for op in draft.operations]
    assert not draft.rejected and normalized == [revised, good]
    assert gate(normalized).status == "pass"


def test_only_false_required_retirement_evidence_implicates_the_retirement():
    retirement = {"kind": "retire", "page": PAGE, "rule_id": "DEMO-1a",
                  "reason": "incorrect", "evidence": "PR #99"}
    untouched = _operation("GOOD-CLAIM")
    untouched["section_markdown"] = _rule("GOOD-CLAIM", "PR #10", claim="`pkg/removed.py`")
    facts = [{"kind": "pr", "pr": 99, "merged": False, "must_hold": True},
             {"kind": "path", "path": "pkg/removed.py", "exists": False, "must_hold": False}]
    assert rejected_operations([retirement, untouched], {"decision": {"facts": facts}}) == {
        operation_key(retirement)}


@pytest.mark.parametrize("collision", ["BAD-CLAIM", "BAD-CLAIM-NESTED"])
def test_pathless_l1_collisions_implicate_exact_rule_ids_including_nested_rules(collision):
    bad, good = _operation("BAD-CLAIM"), _operation("BAD-CLAIM-X")
    bad["section_markdown"] += "\n### BAD-CLAIM-NESTED — nested contract\n\n- preserve this contract.\n"
    decision = {"l1_issues": [{"code": "duplicate_rule_id", "path": "", "detail": collision}]}
    assert rejected_operations([bad, good], {"decision": decision}) == {operation_key(bad)}


def test_source_events_and_inherited_operations_survive_both_refinement_rounds(tmp_path):
    rt, lifecycle, judges, first = _failed_intake(tmp_path, ["no"])
    detail = rt.ledger.changeset(first)["detail"]
    rt.ledger.update_changeset(first, detail={**detail, "event_ids": [71, 72], "source_event_ids": [71, 72],
                                           "operations": [_operation("DEMO-2a"), _operation("PROCESS-LEASE")]})

    class Selective(Judges):
        def __call__(self, role, prompt):
            if role.name == "judge" and '"directory"' not in prompt:
                payload = json.loads(prompt.split("<untrusted_data>\n", 1)[1].split("\n</untrusted_data>", 1)[0])
                if payload["change"]["rule_id"] == "PROCESS-LEASE":
                    return _judge_all("yes")(role, prompt)
            return super().__call__(role, prompt)

    judges = Selective(["no", "yes"])
    rt.gateway = ScriptedGateway(judges)
    merge.advance(rt, lifecycle)
    middle = rt.ledger.changeset(rt.ledger.changeset(first)["detail"]["refined_as"])
    assert middle["status"] == "failed"
    judges.next_round()
    merge.advance(rt, lifecycle)
    final = rt.ledger.changeset(rt.ledger.changeset(middle["id"])["detail"]["refined_as"])
    assert final["detail"]["refine_round"] == MAX_REFINES
    assert final["detail"]["source_event_ids"] == [71, 72]
    assert {op["rule_id"] for op in final["detail"]["operations"]} == {"DEMO-2a", "PROCESS-LEASE"}


def test_large_multi_pr_refinement_uses_bounded_failed_context_and_preserves_canonical_audit(tmp_path):
    from infermatrix_copilot.kb_service.packets import MAX_PACKET_BYTES

    rt, lifecycle, judges, first = _failed_intake(tmp_path, ["no"])
    original = rt.ledger.changeset(first)["detail"]
    operations = [_operation(r) for r in ("DEMO-2a", "PROCESS-LEASE", "JEV-CONFIG")]
    rt.ledger.update_changeset(first, detail={**original, "operations": operations})
    data = rt.load_changeset_files(first)
    canonical = [{"source_reference": f"PR #{n}", "title": f"Source title {n}",
                  "body": "UNRELATED-RAW-CONTENT " * 10_000, "changed_files": [f"pkg/{n}.py"],
                  "merged_at": "2026-10-01T00:00:00Z", "merge_commit_sha": "c" * 40,
                  "diffs": {f"pkg/{n}.py": "+long patch\n" * 5_000}}
                 for n in range(11, 21)]
    data["evidence"] = canonical
    rt.save_changeset_files(first, data)
    judges.next_round()
    merge.advance(rt, lifecycle)
    prompt = judges.prompts[-1]
    assert len(prompt.encode()) <= MAX_PACKET_BYTES
    assert "UNRELATED-RAW-CONTENT" not in prompt
    payload = json.loads(prompt.split("<untrusted_data>\n", 1)[1].split("\n</untrusted_data>", 1)[0])
    assert "body" not in payload and len(payload["evidence"]) == 1
    assert payload["source_catalog"][-1]["title"] == "Source title 20"
    refined = rt.ledger.changeset(rt.ledger.changeset(first)["detail"]["refined_as"])
    assert {op["rule_id"] for op in refined["detail"]["operations"]} == {"DEMO-2a", "PROCESS-LEASE", "JEV-CONFIG"}
    assert rt.load_changeset_files(refined["id"])["evidence"][:-1] == canonical


@pytest.mark.parametrize("problem", ["oversized-discussion", "oversized-prompt", "unavailable-observer"])
def test_unbounded_or_unavailable_refinement_context_escalates_before_generator(tmp_path, monkeypatch, problem):
    from infermatrix_copilot.kb_service import packets
    from infermatrix_copilot.knowledge_service.facts import FactsError

    rt, lifecycle, judges, first = _failed_intake(tmp_path, ["no"])
    before_calls = len(judges.prompts)
    if problem == "oversized-discussion":
        data = rt.load_changeset_files(first)
        data["evidence"][0]["threads"] = [{"id": 1, "body": "queue " * 10_000}]
        rt.save_changeset_files(first, data)
    elif problem == "oversized-prompt":
        detail = rt.ledger.changeset(first)["detail"]
        op = {**detail["operations"][0], "section_markdown": "massive rule " * 30_000}
        rt.ledger.update_changeset(first, detail={**detail, "operations": [op]})
    else:
        def unavailable(*args):
            raise FactsError("branch mirror unavailable")
        monkeypatch.setattr(packets, "observer_for", unavailable)
    merge.advance(rt, lifecycle)
    assert len(judges.prompts) == before_calls
    assert rt.ledger.changeset(first)["status"] == "refine_exhausted"
    assert not [cs for cs in rt.ledger.changesets_of_kind("demo", "refine")]
    (queue,) = rt.ledger.human_queue("demo")
    assert "refinement" in queue["reason"]
    assert "no truncated refinement" in queue["reason"] if problem == "oversized-prompt" else "context unavailable" in queue["reason"]


def test_duplicate_original_operation_identity_is_explicitly_refused():
    from infermatrix_copilot.knowledge_service.lifecycle import LifecycleError

    first = {"kind": "edit_same_meaning", "page": PAGE, "rule_id": "DEMO-1a",
             "section_markdown": _rule("DEMO-1a")}
    second = {**first, "section_markdown": _rule("DEMO-1a", claim="different rewording")}
    with pytest.raises(LifecycleError, match="not unique; explicit consolidation"):
        refinement_validator([first, second], set(), {})
