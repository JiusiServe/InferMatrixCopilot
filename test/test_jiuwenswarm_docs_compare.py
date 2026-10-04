"""Author-doc comparison must not enrich its own experimental baseline."""
from copy import deepcopy
from types import SimpleNamespace
import subprocess

import yaml

import pytest

from eval.jiuwenswarm_docs_compare import (
    DEPTH_FACETS, audit_inventory, body_lines, digest, feature_packet,
    original_document, paragraphs, prepare, source_references, validate_mapping, wrap_original,
)
from infermatrix_copilot.knowledge_docs import KnowledgeDocs
from infermatrix_copilot.knowledge_service.lifecycle import Page
import eval.jiuwenswarm_docs_compare as comparison


PIN = "a" * 40
SOURCE = "jiuwenswarm/runtime/service.py"


@pytest.mark.parametrize("path", [
    ".doc_project_maintainer/project/flows/example.md", "docs/zh/智能体.md",
    "jiuwenswarm/server/runtime/skill/skilldev/DESIGN.md",
    "jiuwenswarm/symphony/retrieval/algorithm.md", "sdks/README.md",
    "jiuwenbox/tests/system_tests/TEST_GUIDE.md", "tests/ui_e2e/SKILL.md",
    "jiuwenswarm/channels/web/AGENTS.md",
])
def test_first_party_author_docs(path):
    assert original_document(path)


@pytest.mark.parametrize("path", [
    ".doc_project_maintainer/project/source-symbol-inventory.json",
    "jiuwenswarm/resources/agent/workspace/USER.md",
    "jiuwenswarm/agents/harness/code/rails/sdd/design_rail/skills/example/SKILL.md",
    "jiuwenswarm/channels/web/frontend/public/third-party/tool/README.md",
    "jiuwenswarm/channels/web/frontend/src/features/trajectory/PROVENANCE.md",
    "docs/generated/README.md",
])
def test_no_machine_inventory_prompt_or_third_party_docs(path):
    assert not original_document(path)


def test_wrapper_keeps_original_words_and_actual_budget(tmp_path):
    raw = "---\nstatus: partial\n---\n# Original API\n\nThe original author says cancellation belongs to this session.\n"
    feature = SimpleNamespace(docs=("docs/api.md",), entry_points=(SOURCE,), source_globs=(SOURCE,))
    wrapped = wrap_original(raw, "docs/api.md", PIN, [feature], set())
    parsed = Page.parse(wrapped)
    assert wrapped[len(parsed.frontmatter):] == raw
    assert parsed.frontmatter_data()["original_sha256"] == digest(raw)
    assert "kb:depth" not in wrapped
    target = tmp_path / "repos/jiuwenswarm/docs/api.md"
    target.parent.mkdir(parents=True)
    target.write_text(wrapped)
    selected = KnowledgeDocs(tmp_path, "repos/jiuwenswarm").related([SOURCE])
    assert selected["documents"][0]["content"] == raw.strip()
    assert selected["content_chars"] == len(raw.strip())


def test_common_reference_metric_ignores_inventory_but_keeps_explanations():
    machine = (f"<!-- kb:file path={SOURCE} pin={PIN} sha256={'b' * 64} -->\n"
               f"The implementation owns {SOURCE} and otherwise has sufficiently long generated prose.\n<!-- /kb:file -->")
    text = (f"---\nsources: [{SOURCE}]\n---\n# Inventory\n\n- `{SOURCE}`\n\n"
            + machine + "\n\nThe session registry owns execution identities and keeps late cleanup from deleting a newer "
            "generation. Cancellation wakes the producer and awaits cleanup instead of leaving the consumer blocked.\n\n"
            f"来源：[{SOURCE}](https://github.com/openJiuwen-ai/jiuwenswarm/blob/{PIN}/{SOURCE}#L1-L20)\n")
    refs, spans = source_references(text, [SOURCE, "jiuwenswarm/unused.py"])
    assert refs == {SOURCE}
    assert len(spans) == 1
    assert spans[0]["start"] > 8
    assert source_references(machine, [SOURCE]) == (set(), [])
    assert source_references(f"# Paths\n\n| path |\n| `{SOURCE}` |", [SOURCE]) == (set(), [])


def test_inventory_deduplicates_symbol_details_and_retains_expired_status():
    primary = "---\nsymbol: Example.run\nsource: jiuwenswarm/example.py\naudit:\n  status: audit_expired\n---\n# Example.run\n"
    detail = "---\nsymbol: Example.run\nsource: jiuwenswarm/example.py\n---\n# behavior\n"
    audit = audit_inventory({".doc_project_maintainer/code/example.py/Example.run.md": primary,
                            ".doc_project_maintainer/code/example.py/Example.run/actual-behavior.md": detail}, [])
    assert audit["documents"] == 2
    assert audit["unique_symbol_cards"] == 1
    assert audit["symbol_card_audit_statuses"] == {"audit_expired": 1}


def test_author_symbol_source_and_flow_directory_keep_original_routing(tmp_path):
    raw = f"---\nsource: {SOURCE}\ndirectories: [jiuwenswarm/runtime]\n---\n# Symbol\n\nOriginal behavior.\n"
    wrapped = wrap_original(raw, ".doc_project_maintainer/code/symbol.md", PIN, [], set(), tracked={SOURCE})
    meta = Page.parse(wrapped).frontmatter_data()
    assert SOURCE in meta["entry_points"]
    assert "jiuwenswarm/runtime/**" in meta["source_globs"]
    target = tmp_path / "repos/jiuwenswarm/symbol.md"
    target.parent.mkdir(parents=True)
    target.write_text(wrapped)
    selected = KnowledgeDocs(tmp_path, "repos/jiuwenswarm").related([SOURCE])
    assert selected["status"] == "ready"
    assert selected["documents"][0]["matched_files"] == [SOURCE]
    assert selected["documents"][0]["content"] == raw.strip()


def test_candidates_preserve_late_original_lines_without_generated_kb_text(tmp_path):
    source, root = tmp_path / "source", tmp_path / "kb"
    path = "docs/feature.md"
    target = source / path
    target.parent.mkdir(parents=True)
    target.write_text("# Feature\n\n" + "\n" * 250 + "The test checks configuration defaults and asserts cancellation output.\n")
    feature = SimpleNamespace(id="feature", title="Feature", entry_points=(SOURCE,), docs=(path,), page="repos/jiuwenswarm/components/x/feature-feature.md")
    report = {"pin": PIN, "production": [SOURCE], "original": {"items": [{"path": path, "production_references": []}]}}
    packet = feature_packet(feature, report, source, root)
    assert any(s["start"] > 180 and "asserts" in s["text"] for s in packet["documents"][0]["spans"])
    assert packet["code"] == []
    assert "existing_knowledge" not in packet
    assert packet["selection"]["offered_doc_chars"] == sum(len(s["text"]) for d in packet["documents"] for s in d["spans"])
    assert packet["candidate_inventory"][0]["omitted_paragraphs"] == 0


def test_original_line_numbers_survive_frontmatter():
    text = "---\nstatus: partial\n---\n# Example\n\nActual author paragraph.\n"
    assert body_lines(text)[1] == 3
    assert paragraphs(text)[-1] == {"start": 6, "end": 6, "text": "Actual author paragraph."}


def mapping_fixture():
    packet = {"feature": "example", "documents": [{"path": "docs/example.md", "spans": [{"start": 200, "end": 210}]}]}
    data = {"feature": "example", "facets": {f: {"status": "unknown", "source_consistency": "unknown",
                                               "reason": "The supplied author passage does not establish this facet.", "evidence": []}
                                                   for f in DEPTH_FACETS}}
    data["facets"]["api"].update(status="supported", evidence=[{"path": "docs/example.md", "start": 202, "end": 204}])
    return data, packet


def test_mapping_supported_requires_real_offered_author_passage():
    data, packet = mapping_fixture()
    validate_mapping(data, packet)
    for evidence in ([], [{"path": SOURCE, "start": 202, "end": 204}],
                     [{"path": "docs/example.md", "start": 199, "end": 204}],
                     [{"path": "docs/example.md", "start": True, "end": 204}]):
        invalid = deepcopy(data)
        invalid["facets"]["api"]["evidence"] = evidence
        with pytest.raises(ValueError):
            validate_mapping(invalid, packet)


def test_citation_can_cross_only_offered_paragraphs_and_verified_blank_lines():
    data, packet = mapping_fixture()
    packet["documents"][0]["spans"] = [{"start": 200, "end": 202}, {"start": 204, "end": 210}]
    data["facets"]["api"]["evidence"] = [{"path": "docs/example.md", "start": 201, "end": 207}]
    with pytest.raises(ValueError):
        validate_mapping(data, packet)
    packet["documents"][0]["blank_lines"] = [203]
    validate_mapping(data, packet)


def test_missing_or_extra_dimension_and_wrong_feature_cannot_count():
    data, packet = mapping_fixture()
    for altered in ("missing", "extra", "feature"):
        invalid = deepcopy(data)
        if altered == "missing":
            invalid["facets"].pop("flow")
        elif altered == "extra":
            invalid["facets"]["accuracy"] = invalid["facets"]["flow"]
        else:
            invalid["feature"] = "neighbor"
        with pytest.raises(ValueError):
            validate_mapping(invalid, packet)


def test_prepare_binds_real_git_pin_and_catalog_and_keeps_arms_separate(tmp_path):
    source, root, state = (tmp_path / name for name in ("source", "repo", "state"))
    for directory in (source, root):
        directory.mkdir()
        subprocess.run(["git", "-C", str(directory), "init", "-q"], check=True)
    code = source / SOURCE
    code.parent.mkdir(parents=True)
    code.write_text("def run():\n    return 1\n")
    doc = source / "docs/example.md"
    doc.parent.mkdir()
    raw = "# Example\n\nOriginal author's words and no newly generated conclusions.\n"
    doc.write_text(raw)
    policy = {"schema_version": 1, "core": {"roots": ["jiuwenswarm/"], "exclude": ["*/tests/*"], "target": 0.85},
              "features": [{"id": "example", "title": "Example", "owner": "runtime", "source_globs": [SOURCE],
                            "docs": ["docs/example.md"], "page": "repos/jiuwenswarm/components/runtime/feature-example.md",
                            "entry_points": [SOURCE]}]}
    policy_file = root / "adapters/jiuwenswarm/knowledge-coverage.yaml"
    policy_file.parent.mkdir(parents=True)
    policy_file.write_text(yaml.safe_dump(policy))
    current = root / "knowledge/repos/jiuwenswarm/components/runtime/feature-example.md"
    current.parent.mkdir(parents=True)
    current.write_text("---\ntype: guide\ntitle: Current\n---\n# Current generated explanation\n")
    for directory in (source, root):
        subprocess.run(["git", "-C", str(directory), "add", "."], check=True)
        subprocess.run(["git", "-C", str(directory), "-c", "user.name=Test", "-c", "user.email=test@example.com",
                        "commit", "-qm", "fixture"], check=True)
    pin = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    report = prepare(root, source, state, pin)
    assert report["association_count"] == 1
    assert report["production"] == [SOURCE]
    original = state / "snapshots/original-docs/repos/jiuwenswarm/docs/example.md"
    assert original.read_text().endswith(raw)
    assert "Current generated explanation" not in original.read_text()
    doc.write_text("changed")
    with pytest.raises(ValueError, match="clean at the exact pin"):
        prepare(root, source, state, pin)


def test_started_mapping_checkpoint_prevents_another_native_call_after_interruption(tmp_path, monkeypatch):
    import infermatrix_copilot.kb_service.models as models

    calls = []

    class InterruptedGateway:
        def __init__(self, *args, **kwargs):
            pass

        def subscription_billing(self, role):
            return True

        def call_json(self, *args, **kwargs):
            calls.append("dispatched")
            raise KeyboardInterrupt("simulated interruption after dispatch")

    feature = SimpleNamespace(id="example")
    packet = {"feature": "example", "documents": [], "selection": {}, "candidate_inventory": []}
    report = {"pin": PIN, "policy_sha256": "b" * 64, "snapshots": {"A": {"sha256": "c" * 64}}}
    monkeypatch.setattr(comparison, "coverage_policy", lambda _: SimpleNamespace(features=[feature]))
    monkeypatch.setattr(comparison, "feature_packet", lambda *args: packet)
    monkeypatch.setattr(models, "ModelGateway", InterruptedGateway)
    state = tmp_path / "state"
    with pytest.raises(KeyboardInterrupt):
        comparison.map_native(tmp_path, tmp_path, state, report, workers=1)
    persisted = (state / "mapping/features/example.json").read_text()
    assert '"dispatch_status": "started"' in persisted
    resumed = comparison.map_native(tmp_path, tmp_path, state, report, workers=1)
    assert calls == ["dispatched"]
    assert resumed["native_success_count"] == 0
    assert all(c == {"unknown": 1} for c in resumed["counts"].values())
