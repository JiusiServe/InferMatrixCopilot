"""Retrieval acceptance checks actual content rather than merely declared facets."""

import copy
import importlib.util
import json
from pathlib import Path

import pytest
import yaml

from infermatrix_copilot.kb_service.init_stages import _page_frontmatter
from infermatrix_copilot.kb_service.knowledge_coverage import CoveragePolicy, Feature, feature_metadata
from infermatrix_copilot.kb_service.knowledge_depth import build_absence_certificate, depth_page, render_block
from infermatrix_copilot.knowledge_view import KnowledgeViewError

PIN = "a" * 40


@pytest.fixture
def auditor():
    path = Path(__file__).resolve().parents[1] / "eval/knowledge-depth/audit_depth_retrieval.py"
    spec = importlib.util.spec_from_file_location("offline_depth_retrieval", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def world(tmp_path):
    def create(count=2, *, long=False, absent=False):
        root = tmp_path / "repository"
        knowledge = root / "knowledge"
        source = tmp_path / "source"
        (source / "pkg").mkdir(parents=True)
        (source / "pkg/core.py").write_text("def run():\n    return 1\n")
        (source / "docs").mkdir()
        (source / "docs/guide.md").write_text("# Guide\nrun returns one.\n")
        features = tuple(Feature(f"f{i}", f"Feature {i}", "core", ("pkg/core.py",), ("docs/guide.md",),
                                 f"repos/retrievaldemo/components/core/feature-f{i}.md", ("pkg/core.py",))
                         for i in range(count))
        policy = CoveragePolicy(("pkg/",), ("*/tests/*",), (".py",), features,
                                semantic_depth_per_facet_gt=0.90)
        policy_data = {"schema_version": 1, "core": {"roots": ["pkg/"], "exclude": ["*/tests/*"]},
                       "semantic_depth": {"per_facet_gt": 0.90}, "features": [
                           {"id": f.id, "title": f.title, "owner": f.owner, "source_globs": list(f.source_globs),
                            "docs": list(f.docs), "entry_points": list(f.entry_points), "page": f.page} for f in features]}
        adapter = root / "adapters/retrievaldemo"
        adapter.mkdir(parents=True)
        (adapter / "manifest.yaml").write_text(yaml.safe_dump({"knowledge": {"repo_subdir": "repos/retrievaldemo"}}))
        (adapter / "knowledge-coverage.yaml").write_text(yaml.safe_dump(policy_data))
        initial = {"AGENTS.md": "# Knowledge entry\n",
                   "general/review/guides/simplification-audit.md": "# Review guide\n",
                   "repos/retrievaldemo/architecture.md": "# Core owner\n",
                   "repos/retrievaldemo/_routes.yaml": yaml.safe_dump({"schema_version": 1, "owners": [
                       {"owner": "core", "path": "repos/retrievaldemo/architecture.md", "signals": ["feature"],
                        "scope_prefixes": ["pkg/"]}]})}
        for path, text in initial.items():
            target = knowledge / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        for feature in features:
            header = _page_frontmatter(feature.title, kind="architecture", today="2026-10-02", tags=["retrievaldemo"])
            section = {"facet": "api", "title": "Return contract", "interpretation": "fact",
                       "body": "The entry returns one." + (" Explicit contract detail." * 180 if long else ""),
                       "evidence": [{"path": "pkg/core.py", "start": 1, "end": 2}]}
            blocks = [render_block(feature, section, source, "o/retrievaldemo", PIN)]
            if absent:
                section.update(facet="validation", title="Test gap", basis="verified_absent",
                               absence_certificate=build_absence_certificate(source, policy, feature, PIN),
                               body="固定源码树内没有静态关联到该功能的测试入口；动态及外部覆盖仍未知。")
                blocks.append(render_block(feature, section, source, "o/retrievaldemo", PIN, policy=policy))
            for path, body in ((feature.page, header + "Feature overview.\n"),
                               (depth_page(feature), header + "\n\n".join(blocks))):
                target = knowledge / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(feature_metadata(body, feature))
        return root, policy
    return create


def test_all_79_features_have_actual_query_context_without_masking_path_ambiguity(auditor, world):
    root, _ = world(79)
    report = auditor.audit_retrieval(root, "retrievaldemo", PIN, require_depth=True)
    assert not report["problems"]
    assert report["summary"]["total_features"] == 79 and report["summary"]["total_facets"] == 553
    assert len(report["cases"]) == 237
    assert report["summary"]["available_facet_status"] == {"supported": 79, "verified_absent": 0, "unknown": 474}
    for probe in ("description_and_paths", "query_only"):
        summary = report["summary"]["probes"][probe]
        assert summary["feature_hits"] == summary["depth_hits"] == 79
        assert summary["target_feature_injection"]["full"] == 79
    assert report["summary"]["probes"]["paths_only"]["feature_hits"] == 2
    assert all(row["max_documents"] <= 2 and row["max_content_chars"] <= 6000
               for row in report["summary"]["probes"].values())
    assert all(document["content_sha256"] == auditor._hash(document["content"])
               for case in report["cases"] for document in case["documents"])


def test_long_facet_is_partial_injection_and_remains_a_budgeted_followup(auditor, world):
    root, _ = world(1, long=True)
    report = auditor.audit_retrieval(root, "retrievaldemo", PIN, require_depth=True)
    assert not report["problems"]
    assert report["summary"]["available_facet_status"]["supported"] == 1
    for case in report["cases"]:
        assert case["facet_injection"]["api"] == "partial"
        document = case["documents"][0]
        assert document["content_chars"] <= 3000
        assert document["partial"] is True
        assert document["included_facets"] == []
        assert document["included_facet_basis"] == {}
        assert document["available_facets"] == document["not_injected_facets"] == ["api"]
        assert case["followup_read_paths"] == [document["path"]]
    assert report["summary"]["probes"]["query_only"]["target_feature_injection"]["full"] == 0


@pytest.mark.parametrize("content", ["", "Unrelated prose."])
def test_partial_metadata_without_real_section_prose_is_not_depth(auditor, world, monkeypatch, content):
    root, _ = world(1, long=True)
    direct = auditor.direct_review_plan

    def missing_partial_content(*args, **kwargs):
        plan = direct(*args, **kwargs)
        selected = plan["related_knowledge"]["documents"][0]
        assert selected["partial"] and selected["included_facets"] == []
        selected["content"] = content
        plan["related_knowledge"]["content_chars"] = len(content)
        return plan

    monkeypatch.setattr(auditor, "direct_review_plan", missing_partial_content)
    report = auditor.audit_retrieval(root, "retrievaldemo", PIN, require_depth=True)
    assert report["summary"]["probes"]["query_only"]["depth_hits"] == 0
    assert any("feature depth absent from actual Direct context" in p for p in report["problems"])


def test_verified_test_gap_is_visible_without_claiming_tests_passed(auditor, world):
    root, _ = world(1, absent=True)
    report = auditor.audit_retrieval(root, "retrievaldemo", PIN, require_depth=True)
    assert not report["problems"]
    assert report["summary"]["available_facet_status"] == {"supported": 1, "verified_absent": 1, "unknown": 5}
    document = report["cases"][0]["documents"][0]
    assert document["facet_states"]["validation"] == {"status": "verified_absent", "injection": "full",
        "gap_label": "no_statically_associated_test_entry"}
    assert "passing tests" in report["limits"] and "非测试通过证明" in document["content"]


def test_required_depth_does_not_count_an_existing_overview(auditor, world):
    root, policy = world(1)
    (root / "knowledge" / depth_page(policy.features[0])).unlink()
    report = auditor.audit_retrieval(root, "retrievaldemo", PIN, require_depth=True)
    assert report["summary"]["features_with_intact_depth"] == 0
    assert "f0: no intact depth available" in report["problems"]
    assert report["summary"]["probes"]["query_only"]["feature_hits"] == 1
    assert report["summary"]["probes"]["query_only"]["depth_hits"] == 0


def test_snapshot_mutation_during_selection_fails_closed(auditor, world, monkeypatch):
    root, _ = world(1)
    direct = auditor.direct_review_plan

    def mutate_after_selection(*args, **kwargs):
        plan = direct(*args, **kwargs)
        selected = root / "knowledge" / plan["related_knowledge"]["documents"][0]["path"]
        selected.write_text(selected.read_text() + "Edited after freezing.\n")
        return plan

    monkeypatch.setattr(auditor, "direct_review_plan", mutate_after_selection)
    with pytest.raises(KnowledgeViewError, match="does not match manifest"):
        auditor.audit_retrieval(root, "retrievaldemo", PIN)


def test_actual_content_size_is_checked_independently_of_reported_size(auditor, world, monkeypatch):
    root, _ = world(1)
    direct = auditor.direct_review_plan

    def lie_about_size(*args, **kwargs):
        plan = direct(*args, **kwargs)
        plan["related_knowledge"]["documents"][0]["content"] += "z" * 6001
        return plan

    monkeypatch.setattr(auditor, "direct_review_plan", lie_about_size)
    report = auditor.audit_retrieval(root, "retrievaldemo", PIN)
    assert any("actual context violates" in problem for problem in report["problems"])
    assert any("document exceeds" in problem for problem in report["problems"])


def test_source_pin_mismatch_is_a_retrieval_acceptance_failure(auditor, world):
    root, _ = world(1)
    report = auditor.audit_retrieval(root, "retrievaldemo", "b" * 40)
    assert any("another source pin" in problem for problem in report["problems"])


def test_automatic_context_cannot_add_a_document_outside_the_repo_slice(auditor, world, monkeypatch):
    root, _ = world(1)
    direct = auditor.direct_review_plan

    def inject_out_of_scope(*args, **kwargs):
        plan = direct(*args, **kwargs)
        plan["related_knowledge"]["documents"][0]["path"] = "general/review/guides/simplification-audit.md"
        return plan

    monkeypatch.setattr(auditor, "direct_review_plan", inject_out_of_scope)
    report = auditor.audit_retrieval(root, "retrievaldemo", PIN)
    assert any("escaped the selected repository" in problem for problem in report["problems"])


def test_injected_basis_metadata_cannot_disagree_with_actual_facet(auditor, world, monkeypatch):
    root, _ = world(1)
    direct = auditor.direct_review_plan

    def mislabeled_basis(*args, **kwargs):
        plan = direct(*args, **kwargs)
        plan["related_knowledge"]["documents"][0]["included_facet_basis"]["api"] = "verified_absent"
        return plan

    monkeypatch.setattr(auditor, "direct_review_plan", mislabeled_basis)
    report = auditor.audit_retrieval(root, "retrievaldemo", PIN)
    assert any("delivered injected basis differs" in problem for problem in report["problems"])


def test_declared_facet_with_empty_content_is_not_counted_as_depth(auditor, world, monkeypatch):
    root, _ = world(1)
    direct = auditor.direct_review_plan

    def empty_content(*args, **kwargs):
        plan = direct(*args, **kwargs)
        plan["related_knowledge"]["documents"][0]["content"] = ""
        plan["related_knowledge"]["content_chars"] = 0
        return plan

    monkeypatch.setattr(auditor, "direct_review_plan", empty_content)
    report = auditor.audit_retrieval(root, "retrievaldemo", PIN)
    assert report["summary"]["probes"]["query_only"]["depth_hits"] == 0
    assert any("declared injected facet" in problem for problem in report["problems"])


def test_deduplicated_report_replays_exact_actual_context_and_budgets(auditor, world):
    root, _ = world(1)
    report = auditor.audit_retrieval(root, "retrievaldemo", PIN)
    original = copy.deepcopy(report)
    packed = json.loads(auditor.serialize_report(report))
    assert report == original  # Writing evidence must not mutate the audit result.
    assert len(packed["cases"]) == 3
    assert len(packed["content_blobs"]) == 1
    assert len(packed["documents"]) == 2  # Description and path matches retain their distinct metadata.
    assert len(packed["execution_budgets"]) == 1
    assert auditor.expand_report(packed) == original
    assert all("documents" not in case and "execution_budget" not in case for case in packed["cases"])


@pytest.mark.parametrize("corruption", ["body", "metadata", "budget", "reference", "summary"])
def test_deduplicated_report_rejects_changed_or_missing_evidence(auditor, world, corruption):
    root, _ = world(1)
    packed = auditor.pack_report(auditor.audit_retrieval(root, "retrievaldemo", PIN))
    if corruption == "body":
        reference = next(iter(packed["content_blobs"]))
        packed["content_blobs"][reference] += "Changed actual returned text."
    elif corruption == "metadata":
        next(iter(packed["documents"].values()))["included_facets"] = []
    elif corruption == "budget":
        next(iter(packed["execution_budgets"].values()))["knowledge_file_reads"] = 999
    elif corruption == "reference":
        packed["cases"][0]["document_refs"] = ["0" * 64]
    else:
        packed["summary"]["probes"]["query_only"]["depth_hits"] = 999
    with pytest.raises(ValueError, match="hash mismatch|evidence reference|differs from the original audit"):
        auditor.expand_report(packed)
