"""Lightweight review keeps pinned evidence and confidence labels explicit."""

import json
import re
from dataclasses import replace
from types import SimpleNamespace

import pytest
import yaml

from infermatrix_copilot.kb_service.depth_judge import review_facets
from infermatrix_copilot.kb_service.init_budget import Budget
from infermatrix_copilot.kb_service.knowledge_coverage import load_policy
from infermatrix_copilot.kb_service.knowledge_depth import (
    FACETS, VALIDATION_KINDS, audit_depth, depth_acceptance_mode, depth_page, digest,
    render_block, validate_draft, verified_blocks,
)
from infermatrix_copilot.kb_service.models import ModelReply, ModelRole, ModelUnavailable
from test_kb_depth_completion_proofs import PIN, _page, _policy, _replace_proof, _section, _source


def proof(block):
    return json.loads(re.search(r"<!-- kb:depth-proof (.*?) -->", block, re.S)[1])


def api():
    return {"facet": "api", "title": "Input contract",
            "body": "run takes a value and returns the increment from helper.", "interpretation": "fact",
            "evidence": [{"path": "pkg/core.py", "start": 1, "end": 4}]}


def light(feature, section, tree):
    if section["facet"] == "validation" and "validation_kind" not in section:
        section = {**section, "validation_kind": "automated_runtime"}
    return render_block(feature, section, tree, "o/demo", PIN, acceptance_mode="lightweight")


@pytest.mark.parametrize("mode", [None, True, 1, "", "mixed", [], {}])
def test_unknown_acceptance_mode_fails_closed(mode):
    with pytest.raises(ValueError, match="acceptance_mode"):
        depth_acceptance_mode({"acceptance_mode": mode})
    with pytest.raises(ValueError, match="acceptance_mode"):
        validate_draft({"sections": []}, acceptance_mode=mode)


def test_default_strict_render_preserves_actual_legacy_fixture_bytes(tmp_path):
    _source(tmp_path)
    feature = _policy().features[0]
    block = render_block(feature, api(), tmp_path, "o/demo", PIN)
    # Frozen b4d2a769 renderer output, rather than recomputing expected metadata.
    assert digest(block) == "f9e9281e584f8b6ec6e56d7211582e37a6d35ef9f38498451587b9099a07e177"
    assert "acceptance_mode" not in proof(block)
    assert depth_acceptance_mode(proof(block)) == "strict"
    assert block == render_block(feature, api(), tmp_path, "o/demo", PIN, acceptance_mode="strict")


def test_lightweight_flow_has_pinned_citations_without_semantic_trace(tmp_path, monkeypatch):
    _source(tmp_path)
    section = {**_section("flow"), "trace": [{"bogus": "unresolved dynamic dispatch"}]}
    validate_draft({"sections": [section]}, acceptance_mode="lightweight")
    monkeypatch.setattr("infermatrix_copilot.kb_service.knowledge_depth.verify_trace",
                        lambda *a, **k: pytest.fail("lightweight must not run semantic call proof"))
    block = light(_policy().features[0], section, tmp_path)
    assert proof(block)["trace"] == []
    assert proof(block)["acceptance_mode"] == "lightweight"
    assert "调用路径：" not in block
    blocks, problems = verified_blocks(_page([block]), _policy().features[0], tmp_path, PIN)
    assert not problems and blocks == {"flow": block}


@pytest.mark.parametrize("basis", ["verified_absent", "unknown"])
def test_lightweight_never_generates_or_accepts_absence_certificates(tmp_path, monkeypatch, basis):
    _source(tmp_path)
    section = {**_section("validation"), "basis": basis, "absence_certificate": {"forged": True}}
    monkeypatch.setattr("infermatrix_copilot.kb_service.knowledge_depth.build_absence_certificate",
                        lambda *a, **k: pytest.fail("no lightweight absence detector call"))
    with pytest.raises(ValueError, match="absence"):
        validate_draft({"sections": [section]}, acceptance_mode="lightweight")
    with pytest.raises(ValueError, match="absence"):
        light(_policy().features[0], section, tmp_path)


@pytest.mark.parametrize("kind", VALIDATION_KINDS)
def test_validation_categories_are_explicit_and_manual_steps_are_unexecuted(tmp_path, kind):
    _source(tmp_path)
    feature = _policy().features[0]
    if kind == "documented_manual":
        (tmp_path / "docs/guide.md").write_text("# Manual check\nCall run(1); expect the returned value to equal 2.\n")
        evidence = {"path": "docs/guide.md", "start": 1, "end": 2}
        body = "The project guide describes calling run(1) and expecting 2; this batch did not execute that check."
    else:
        (tmp_path / "tests").mkdir()
        symbol = "helper" if kind == "helper_unit" else "run"
        content = ("from pathlib import Path\ndef test_source_contract():\n    assert 'return helper(value)' in Path('pkg/core.py').read_text()\n"
                   if kind == "automated_source_text" else "from pkg.core import " + symbol
                   + "\ndef test_increment():\n    assert " + symbol + "(1) == 2\n")
        (tmp_path / "tests/test_increment.py").write_text(content)
        evidence = {"path": "tests/test_increment.py", "start": 1, "end": 3}
        body = "The test entry asserts the increment contract; the test was not executed in this batch."
    section = {**_section("validation"), "validation_kind": kind,
               "body": body, "evidence": [evidence]}
    validate_draft({"sections": [section]}, acceptance_mode="lightweight")
    block = light(feature, section, tmp_path)
    assert proof(block)["validation_kind"] == kind
    if kind == "documented_manual":
        assert "文档中的人工验收步骤（本轮未执行）" in block
    report = audit_depth({depth_page(feature): _page([block])}, tmp_path, _policy(), PIN)
    assert report["recognized_facets"] == 1
    assert report["validation_kind_counts"][kind] == 1
    assert report["features"][feature.id]["validation_kinds"] == {"validation": kind}


def test_lightweight_validation_without_kind_is_invalid(tmp_path):
    _source(tmp_path)
    with pytest.raises(ValueError, match="validation_kind"):
        validate_draft({"sections": [_section("validation")]}, acceptance_mode="lightweight")
    with pytest.raises(ValueError, match="validation_kind"):
        render_block(_policy().features[0], _section("validation"), tmp_path, "o/demo", PIN,
                     acceptance_mode="lightweight")


@pytest.mark.parametrize("kind", [None, False, "manual", [], {}])
def test_invalid_validation_kind_is_a_section_error(tmp_path, kind):
    _source(tmp_path)
    with pytest.raises(ValueError, match="validation_kind"):
        validate_draft({"sections": [{**_section("validation"), "validation_kind": kind}]},
                       acceptance_mode="lightweight")


def test_manual_disclosure_cannot_be_removed_by_rehashing_a_block(tmp_path):
    _source(tmp_path)
    feature = _policy().features[0]
    block = light(feature, {**_section("validation"), "validation_kind": "documented_manual"}, tmp_path)
    body = re.search(r"sha256=([0-9a-f]{64}) -->\n(.*?)\n<!-- /kb:depth -->", block, re.S)
    changed = body[2].replace("文档中的人工验收步骤（本轮未执行）：\n\n", "")
    bad = block.replace(body[2], changed).replace(body[1], digest(changed))
    blocks, problems = verified_blocks(_page([bad]), feature, tmp_path, PIN)
    assert not blocks and any("not executed" in problem for problem in problems)


@pytest.mark.parametrize("mode", ["strict", "lightweight"])
def test_changed_source_or_document_hash_is_rejected_in_both_modes(tmp_path, mode):
    _source(tmp_path)
    feature = _policy().features[0]
    section = {**api(), "evidence": [{"path": "docs/guide.md", "start": 1, "end": 2}]}
    block = render_block(feature, section, tmp_path, "o/demo", PIN, acceptance_mode=mode)
    (tmp_path / "docs/guide.md").write_text("# Changed guide\nThe documented behavior changed.\n")
    blocks, problems = verified_blocks(_page([block]), feature, tmp_path, PIN)
    assert not blocks and any("evidence changed" in problem for problem in problems)


@pytest.mark.parametrize("count,met", [(71, False), (72, True)])
def test_mixed_79_feature_gate_counts_each_slot_once_and_strict_cannot_use_light(tmp_path, count, met):
    _source(tmp_path)
    policy = replace(_policy(79), semantic_depth_acceptance_mode="lightweight")
    head = {}
    for i, feature in enumerate(policy.features):
        blocks = [render_block(feature, {**_section(facet), **({"validation_kind": "automated_runtime"}
                               if facet == "validation" and i % 3 != 0 else {})}, tmp_path, "o/demo", PIN,
                               acceptance_mode="strict" if i % 3 == 0 else "lightweight")
                  for j, facet in enumerate(FACETS) if (i + j * 11) % 79 < count]
        head[depth_page(feature)] = _page(blocks)
    report = audit_depth(head, tmp_path, policy, PIN)
    assert report["total_facets"] == 553
    assert report["recognized_facets"] == count * 7
    assert report["recognized_facets"] == report["strict_recognized_facets"] + report["lightweight_recognized_facets"]
    assert report["target_met"] is met
    assert all(row["strict_recognized"] + row["lightweight_recognized"] + row["unknown"] == 79
               for row in report["facet_counts"].values())
    strict = audit_depth(head, tmp_path, replace(policy, semantic_depth_acceptance_mode="strict"), PIN)
    assert not strict["target_met"]
    assert strict["recognized_facets"] == report["recognized_facets"]
    assert strict["eligible_recognized_facets"] == strict["strict_recognized_facets"]


def test_one_dimension_below_target_still_fails_with_large_mixed_total(tmp_path):
    _source(tmp_path)
    policy = replace(_policy(79), semantic_depth_acceptance_mode="lightweight")
    head = {depth_page(f): _page([light(f, _section(facet), tmp_path) for facet in FACETS
                                if facet != "flow" or i < 71]) for i, f in enumerate(policy.features)}
    report = audit_depth(head, tmp_path, policy, PIN)
    assert report["recognized_facets"] > 504 and not report["target_met"]
    assert report["facet_counts"]["flow"]["recognized"] == 71


def test_duplicate_modes_do_not_create_two_rows_and_other_facets_survive(tmp_path):
    _source(tmp_path)
    policy = _policy()
    f = policy.features[0]
    strict = render_block(f, _section("flow"), tmp_path, "o/demo", PIN)
    report = audit_depth({depth_page(f): _page([strict, light(f, _section("flow"), tmp_path), light(f, api(), tmp_path)])},
                         tmp_path, policy, PIN)
    assert report["recognized_facets"] == 1
    assert report["features"][f.id]["recognized_facets"] == ["api"]
    assert any("duplicate" in p for p in report["problems"])


def approval(feature, block, **metadata):
    return {"feature": feature.id, "facet": "api", "page": depth_page(feature), "pin": PIN,
            "block_sha256": digest(block), "dimensions": {k: "yes" for k in
            ("faithful", "non_contradictory", "does_not_weaken")},
            "native_trace_id": "native-review", "native_reply_sha256": "b" * 64, **metadata}


@pytest.mark.parametrize("metadata,accepted", [({}, False), ({"acceptance_mode": "strict"}, False),
    ({"acceptance_mode": "lightweight"}, True), ({"acceptance_modes": {"api": "lightweight"}}, True),
    ({"acceptance_mode": "strict", "acceptance_modes": {"api": "lightweight"}}, False)])
def test_lightweight_receipt_must_bind_its_mode(tmp_path, metadata, accepted):
    _source(tmp_path)
    policy = _policy()
    f = policy.features[0]
    block = light(f, api(), tmp_path)
    report = audit_depth({depth_page(f): _page([block])}, tmp_path, policy, PIN,
                         approvals=[approval(f, block, **metadata)])
    assert report["recognized_facets"] == int(accepted)
    assert bool(report["approval_binding_problems"]) is not accepted


@pytest.mark.parametrize("metadata,accepted", [({}, False), ({"validation_kind": "automated_runtime"}, False),
    ({"validation_kind": "documented_manual"}, True),
    ({"validation_kinds": {"validation": "documented_manual"}}, True)])
def test_validation_approval_binds_its_evidence_category(tmp_path, metadata, accepted):
    _source(tmp_path)
    policy = _policy()
    f = policy.features[0]
    block = light(f, {**_section("validation"), "validation_kind": "documented_manual"}, tmp_path)
    row = {**approval(f, block, acceptance_mode="lightweight"), "facet": "validation", **metadata}
    report = audit_depth({depth_page(f): _page([block])}, tmp_path, policy, PIN, approvals=[row])
    assert report["recognized_facets"] == int(accepted)
    assert bool(report["approval_binding_problems"]) is not accepted


def test_policy_acceptance_mode_is_optional_and_explicit():
    f = _policy().features[0]
    data = {"schema_version": 1, "core": {"roots": ["pkg/"], "exclude": ["*/tests/*"]},
            "semantic_depth": {"per_facet_gt": .90}, "features": [
                {"id": f.id, "title": f.title, "owner": f.owner, "source_globs": list(f.source_globs),
                 "docs": list(f.docs), "page": f.page}]}
    assert load_policy(yaml.safe_dump(data), "repos/demo").semantic_depth_acceptance_mode == "strict"
    data["semantic_depth"]["acceptance_mode"] = "lightweight"
    assert load_policy(yaml.safe_dump(data), "repos/demo").semantic_depth_acceptance_mode == "lightweight"
    data["semantic_depth"]["acceptance_mode"] = "mixed"
    with pytest.raises(ValueError, match="acceptance_mode"):
        load_policy(yaml.safe_dump(data), "repos/demo")


class Gateway:
    def __init__(self, data):
        self.data, self.calls, self.payload = data, 0, None

    def call_json(self, role, **kwargs):
        self.calls += 1
        self.payload = json.loads(re.search(r"<untrusted_data>\s*(.*?)\s*</untrusted_data>", kwargs["prompt"], re.S)[1])
        try:
            kwargs["validate"](self.data)
        except ValueError as exc:
            raise ModelUnavailable(str(exc)) from exc
        return ModelReply(role, self.data, json.dumps(self.data), role.model, {}, .01)


def yes(**changes):
    return {"dimensions": {k: "yes" for k in ("faithful", "non_contradictory", "does_not_weaken")},
            "reason": "The pinned lines support the claim.", **changes}


@pytest.mark.parametrize("bad", [None, {}, {"dimensions": {"faithful": "yes"}, "reason": "partial"}])
def test_bad_lightweight_facet_does_not_discard_an_independently_valid_facet(tmp_path, bad):
    _source(tmp_path)
    f = _policy().features[0]
    blocks = {"api": light(f, api(), tmp_path), "validation": light(f, _section("validation"), tmp_path)}
    data = {"facets": {"api": yes()}}
    if bad is not None:
        data["facets"]["validation"] = bad
    gateway = Gateway(data)
    rt = SimpleNamespace(gateway=gateway, judge=ModelRole.parse("judge", "codex:fixture"))
    result = review_facets(rt, Budget(1), SimpleNamespace(judge_call_usd=.5), feature=f.id, pin=PIN,
                           blocks=blocks, existing={}, evidence=[], acceptance_modes={k: "lightweight" for k in blocks})
    assert gateway.calls == 1
    assert result["facets"]["api"]["verdict"] == "pass"
    assert result["facets"]["validation"]["verdict"] == "unjudged"
    assert result["acceptance_modes"] == gateway.payload["acceptance_modes"] == {k: "lightweight" for k in blocks}
    assert result["validation_kinds"] == gateway.payload["validation_kinds"] == {"validation": "automated_runtime"}


def test_model_cannot_override_no_dimension_with_forged_pass(tmp_path):
    _source(tmp_path)
    f = _policy().features[0]
    result_data = yes(verdict="pass")
    result_data["dimensions"]["faithful"] = "no"
    gateway = Gateway({"facets": {"api": result_data}})
    rt = SimpleNamespace(gateway=gateway, judge=ModelRole.parse("judge", "codex:fixture"))
    result = review_facets(rt, Budget(1), SimpleNamespace(judge_call_usd=.5), feature=f.id, pin=PIN,
                           blocks={"api": light(f, api(), tmp_path)}, existing={}, evidence=[])
    assert result["facets"]["api"]["verdict"] == "fail"


def test_reviewer_mode_cannot_differ_from_stored_block(tmp_path):
    _source(tmp_path)
    f = _policy().features[0]
    gateway = Gateway({"facets": {"api": yes()}})
    rt = SimpleNamespace(gateway=gateway, judge=ModelRole.parse("judge", "codex:fixture"))
    with pytest.raises(ValueError, match="acceptance_modes"):
        review_facets(rt, Budget(1), SimpleNamespace(judge_call_usd=.5), feature=f.id, pin=PIN,
                      blocks={"api": light(f, api(), tmp_path)}, existing={}, evidence=[],
                      acceptance_modes={"api": "strict"})
    assert not gateway.calls


def test_reviewer_rejects_invalid_stored_validation_category_before_dispatch(tmp_path):
    _source(tmp_path)
    f = _policy().features[0]
    block = light(f, _section("validation"), tmp_path)
    block = _replace_proof(block, lambda data: data.update(validation_kind="untested_guarantee"))
    gateway = Gateway({"facets": {"validation": yes()}})
    rt = SimpleNamespace(gateway=gateway, judge=ModelRole.parse("judge", "codex:fixture"))
    with pytest.raises(ValueError, match="validation_kind"):
        review_facets(rt, Budget(1), SimpleNamespace(judge_call_usd=.5), feature=f.id, pin=PIN,
                      blocks={"validation": block}, existing={}, evidence=[])
    assert not gateway.calls
