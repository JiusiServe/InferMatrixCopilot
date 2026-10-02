"""Regression coverage for the replacement/voice failure in nightly extraction."""

from __future__ import annotations

import json

import pytest

from infermatrix_copilot.kb_service.gate import changes_between, run_gate
from infermatrix_copilot.knowledge_service.ops import KnowledgeOperation as Op, apply_operations
from test_kb_intake_gate import JUDGE, PAGE, ScriptedGateway, _judge_all, _rule, _tree


def _payload(prompt):
    return json.loads(prompt.split("<untrusted_data>\n", 1)[1].rsplit("\n</untrusted_data>", 1)[0])


def _crowded_tree():
    base = _tree()
    base[PAGE] += "\n".join(_rule(f"UNRELATED-{n:02d}") for n in range(40))
    return base


def _run(base, operations, answer, **kwargs):
    head = {**base, **apply_operations(base, operations, release="v1", today="2026-10-02").files}
    evidence = [{"source_reference": "PR #11", "quoted_predecessor": "Reject every voice value."}]
    gateway = ScriptedGateway(answer)
    decision = run_gate(base=base, head=head, changes=changes_between(base, head), external_texts={},
                        evidence=evidence, gateway=gateway, judge=JUDGE, release="v1",
                        repo_dir="repos/demo", **kwargs)
    return decision, [_payload(prompt) for _, prompt in gateway.calls]


@pytest.mark.parametrize("target", ["repos/demo/core/rules-speech.md", "repos/demo/speech/rules.md"])
def test_replacement_successor_is_complete_even_outside_the_neighbour_cap_or_owner(target):
    base = _crowded_tree()
    base[target] = base[PAGE].split("## ", 1)[0]
    directory = target.rsplit("/", 1)[0]
    base[f"{directory}/_index.md"] = f"# rules\n\n- [speech]({target.rsplit('/', 1)[1]})\n"
    successor = (_rule("SPEECH-CAPABILITIES", "PR #11", "voice 的空值和 default 是占位")
                 + "\n".join(f"- 约束 {n}。" for n in range(12))
                 + "\n- 禁止：把真实 speaker 名当作 default 占位。\n")
    replace = Op("replace", PAGE, "DEMO-1a", successor, new_rule_id="SPEECH-CAPABILITIES",
                 new_page=target, evidence="PR #11")
    seen = []

    def answer(role, prompt):
        data = _payload(prompt)
        if data.get("change", {}).get("op") == "supersede":
            seen.append(data)
            context = data["replacement_context"]
            assert context["predecessor"]["before"]["status"] == "active"
            assert context["predecessor"]["after"]["status"] == "retired"
            assert context["successor"]["before"] is None
            assert context["successor"]["after"]["page"] == target
            assert context["successor"]["after"]["status"] == "active"
            assert "真实 speaker 名" in context["successor"]["after"]["text"]
            assert len(data["surrounding_rules"]) == 30
            assert data["evidence"][0]["quoted_predecessor"] == "Reject every voice value."
            assert "default 是占位" not in data["change"]["before"]
        return _judge_all("yes")(role, prompt)

    decision, prompts = _run(base, [replace], answer)
    assert decision.status == "pass", decision.reasons
    assert len(seen) == 1
    successor_judgment = next(p for p in prompts if p.get("change", {}).get("rule_id") == "SPEECH-CAPABILITIES")
    assert successor_judgment["replacement_context"] == seen[0]["replacement_context"]
    assert "DEMO-1a" not in {r["rule_id"] for p in prompts for r in p.get("surrounding_rules", [])}


def test_changed_and_relevant_active_rules_precede_unrelated_rules_and_keep_changed_constraints():
    base = _crowded_tree()
    relevant = "repos/demo/core/rules-z-voice.md"
    base[relevant] = base[PAGE].split("## ", 1)[0] + _rule("VOICE-EXISTING", claim="voice default 占位")
    changed = (_rule("VOICE-CHANGED", "PR #11", "speech_request 的 voice 是占位")
               + "\n".join(f"- 约束 {n}。" for n in range(12)) + "\n- 禁止：later constraint。\n")
    operations = [Op("add", PAGE, "VOICE-NEW", _rule("VOICE-NEW", "PR #11", "voice default 占位")),
                  Op("add", relevant, "VOICE-CHANGED", changed),
                  Op("retire", PAGE, "UNRELATED-00", reason="incorrect", evidence="PR #11")]
    decision, prompts = _run(base, operations, _judge_all("yes"))
    assert decision.status == "pass", decision.reasons
    data = next(p for p in prompts if p.get("change", {}).get("rule_id") == "VOICE-NEW")
    neighbours = data["surrounding_rules"]
    assert neighbours[0]["rule_id"] == "VOICE-CHANGED" and neighbours[0]["changed"]
    assert "later constraint" in neighbours[0]["text"]
    assert neighbours[1]["rule_id"] == "VOICE-EXISTING" and not neighbours[1]["changed"]
    assert "UNRELATED-00" not in {r["rule_id"] for r in neighbours}
    assert len(neighbours) == 30


@pytest.mark.parametrize("verdict,protected,expected", [
    ("no", (), "fail"), ("unsure", (), "human"), ("yes", ("DEMO-1a",), "human"),
])
def test_complete_replacement_context_still_requires_the_judge_and_protection_gate(verdict, protected, expected):
    replacement = Op("replace", PAGE, "DEMO-1a", _rule("DEMO-NEW", "PR #11"),
                     new_rule_id="DEMO-NEW", evidence="PR #11")
    decision, prompts = _run(_crowded_tree(), [replacement], _judge_all(verdict), protected_rules=protected)
    assert decision.status == expected
    retirement = next(p for p in prompts if p.get("change", {}).get("op") == "supersede")
    assert retirement["dimensions_to_answer"] == ["deletion_justified"]
    successor = next(p for p in prompts if p.get("change", {}).get("op") == "add")
    assert successor["dimensions_to_answer"] == ["faithful", "non_contradictory", "actionable"]


def test_oversized_relevant_evidence_goes_to_review_without_a_judge_call():
    from infermatrix_copilot.kb_service.evidence import for_rule
    from infermatrix_copilot.knowledge_service.ops import KnowledgeOperation, apply_operations
    from infermatrix_copilot.kb_service.gate import changes_between, run_gate

    base = _tree()
    head = {**base, **apply_operations(base, [KnowledgeOperation(
        "add", PAGE, "DEMO-2a", _rule("DEMO-2a", "PR #11"))],
        release="v1", today="2026-10-02").files}
    gateway = ScriptedGateway(_judge_all("yes"))

    def evidence_for(text, evidence):
        return for_rule(text, evidence, None)

    evidence = [{"source_reference": "PR #11", "threads": [
        {"id": 1, "body": "queue " + "x" * 50000},
        {"id": 2, "in_reply_to_id": 1, "body": "withdrawn after inspection"}]}]

    decision = run_gate(base=base, head=head, changes=changes_between(base, head),
                        external_texts={}, evidence=evidence, gateway=gateway, judge=JUDGE, release="v1",
                        repo_dir="repos/demo", evidence_for=evidence_for)
    assert decision.status == "human"
    assert "relevant threads chronology exceeds" in decision.blocks[0].reasons["evidence"]
    assert "sha256=" in decision.blocks[0].reasons["evidence"]
    assert all('"directory"' in prompt for _role, prompt in gateway.calls)
