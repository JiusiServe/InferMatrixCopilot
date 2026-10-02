"""Pinned repair localization cannot substitute hints for evidence or truncate spans."""

import json
from types import SimpleNamespace

import pytest

from infermatrix_copilot.kb_service.depth_inputs import DepthContext, load_repair_guidance
from test_kb_depth_shared_index import _write, _index, PIN, POLICY


@pytest.fixture
def world(tmp_path):
    tree = tmp_path / "source"
    _write(tree, "pkg/core.py", "def run():\n    return 17\n")
    _write(tree, "sdks/python/tests/test_core.py", "# setup\n" * 200 + "def test_run():\n    assert run() == 17\n")
    _write(tree, "docs/guide.md", "# Context\n" * 200 + "Run the command.\nExpect the result 17.\n")
    index = _index(tree, ["pkg/core.py"])
    context = DepthContext(tree, ["pkg/core.py"], index=index, pin=PIN, policy_sha256=POLICY, mode="lightweight")
    feature = SimpleNamespace(id="core")
    row = {"feature": "core", "facet": "validation", "priorreason": "wrong same-owner test",
           "bodyproposal": "Untrusted proposal; this is not evidence.",
           "evidence": [{"path": "sdks/python/tests/test_core.py", "start": 201, "end": 202},
                        {"path": "docs/guide.md", "start": 201, "end": 202}]}
    raw = {"schema": "depth-repair-guidance-v1", "pin": PIN, "policy_sha256": POLICY,
           "baseline": "c" * 40, "rows": [row]}
    path = tmp_path / "guidance.json"
    path.write_text(json.dumps(raw))
    return context, feature, raw, path


def test_nested_late_assertions_and_exact_document_steps_are_offered_in_full(world):
    context, feature, _, path = world
    guidance = load_repair_guidance(path, pin=PIN, policy_sha256=POLICY, baseline="c" * 40)
    packet = context.guided(feature, ("validation",), guidance)
    assert packet["files"][0]["text"] == ["201: def test_run():", "202:     assert run() == 17"]
    assert packet["docs"][0]["text"] == ["Run the command.", "Expect the result 17."]
    assert packet["repair_guidance"]["rows"][0]["bodyproposal"] not in "\n".join(packet["files"][0]["text"])
    assert packet["repair_guidance"]["sha256"] == guidance["guidance_sha256"]


@pytest.mark.parametrize("key,value", [("pin", "d" * 40), ("policy_sha256", "d" * 64), ("baseline", "d" * 40)])
def test_guidance_identity_rejects_a_different_source_policy_or_batch(world, key, value):
    _, _, _, path = world
    kwargs = {"pin": PIN, "policy_sha256": POLICY, "baseline": "c" * 40}
    kwargs[key] = value
    with pytest.raises(ValueError, match=key):
        load_repair_guidance(path, **kwargs)


@pytest.mark.parametrize("change", ["duplicate", "unsafe", "boolean", "missing"])
def test_malformed_guidance_cannot_enter_a_model_packet(world, change):
    _, _, raw, path = world
    if change == "duplicate":
        raw["rows"].append(raw["rows"][0])
    elif change == "unsafe":
        raw["rows"][0]["evidence"][0]["path"] = "../private.py"
    elif change == "boolean":
        raw["rows"][0]["evidence"][0]["start"] = True
    else:
        raw["rows"][0]["evidence"] = []
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError):
        load_repair_guidance(path)


def test_missing_facet_and_out_of_range_evidence_remain_errors(world):
    context, feature, raw, path = world
    guidance = load_repair_guidance(path)
    with pytest.raises(ValueError, match="each requested facet"):
        context.guided(feature, ("validation", "flow"), guidance)
    raw["rows"][0]["evidence"][0]["end"] = 203
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="beyond"):
        context.guided(feature, ("validation",), load_repair_guidance(path))


def test_complete_spans_fail_the_budget_instead_of_silently_cutting_assertions(world):
    context, feature, _, path = world
    guidance = load_repair_guidance(path)
    with pytest.raises(ValueError, match="exceed budget"):
        context.guided(feature, ("validation",), guidance, source_limit=10)
    with pytest.raises(ValueError, match="exceed budget"):
        context.guided(feature, ("validation",), guidance, doc_limit=10)


def test_overlapping_ranges_are_merged_without_duplicating_evidence(world):
    context, feature, raw, path = world
    raw["rows"][0]["evidence"].append({"path": "sdks/python/tests/test_core.py", "start": 202, "end": 202})
    path.write_text(json.dumps(raw))
    packet = context.guided(feature, ("validation",), load_repair_guidance(path))
    assert len(packet["files"]) == 1
    assert len(packet["files"][0]["text"]) == 2


def test_guidance_content_edits_change_the_checkpoint_identity(world):
    _, _, raw, path = world
    before = load_repair_guidance(path)["guidance_sha256"]
    raw["rows"][0]["priorreason"] = "Correct different rejected claim"
    path.write_text(json.dumps(raw))
    assert load_repair_guidance(path)["guidance_sha256"] != before


def test_guidance_replaced_after_parent_capture_is_rejected_before_stage_identity(world, monkeypatch):
    from infermatrix_copilot.kb_service.init_knowledge import _Knowledge
    from infermatrix_copilot.kb_service.init_knowledge_depth import _KnowledgeDepth
    from infermatrix_copilot.kb_service.init_support import InitError

    _, _, raw, path = world
    parent_hash = load_repair_guidance(path)["guidance_sha256"]
    raw["rows"][0]["bodyproposal"] = "Replacement input with the same pin, policy and baseline."
    path.write_text(json.dumps(raw))
    monkeypatch.setenv("KB_DEPTH_REPAIR_GUIDANCE", str(path))
    monkeypatch.setenv("KB_DEPTH_REPAIR_GUIDANCE_SHA256", parent_hash)
    monkeypatch.setattr(_Knowledge, "_input_options", lambda _: pytest.fail("replacement reached stage identity"))
    stage = object.__new__(_KnowledgeDepth)
    stage.acceptance_mode = "lightweight"
    stage.depth_index_path = None
    with pytest.raises(InitError, match="campaign's immutable input"):
        stage._input_options()


def test_unchanged_guidance_keeps_the_parent_hash_in_checkpoint_inputs(world, monkeypatch):
    from infermatrix_copilot.kb_service.init_knowledge import _Knowledge
    from infermatrix_copilot.kb_service.init_knowledge_depth import _KnowledgeDepth

    _, _, _, path = world
    parent_hash = load_repair_guidance(path)["guidance_sha256"]
    monkeypatch.setenv("KB_DEPTH_REPAIR_GUIDANCE", str(path))
    monkeypatch.setenv("KB_DEPTH_REPAIR_GUIDANCE_SHA256", parent_hash)
    monkeypatch.setattr(_Knowledge, "_input_options", lambda _: {})
    stage = object.__new__(_KnowledgeDepth)
    stage.acceptance_mode = "lightweight"
    stage.depth_index_path = None
    stage.feature_ids = ("core",)
    assert stage._input_options()["repair_guidance_sha256"] == parent_hash
