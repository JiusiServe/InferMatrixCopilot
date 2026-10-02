"""Bounded review context must reach consumers without becoming rule evidence."""

import hashlib
import json
import re
from pathlib import Path

import pytest

from infermatrix_copilot.kb_service.knowledge_coverage import Feature, feature_metadata
from infermatrix_copilot.kb_service.knowledge_depth import render_block
from infermatrix_copilot.knowledge_docs import KnowledgeDocs, KnowledgeDocsError
from infermatrix_copilot.knowledge_service.lifecycle import DEPTH_BLOCK, Page

PIN = "a" * 40
FEATURE = Feature("models", "Model API", "core", ("pkg/models/*",), (),
                  "repos/r/features/models.md", ("pkg/models/catalog.py",))


def _page(root: Path, relative: str, body: str, feature=FEATURE, *, sources=()):
    text = (f'---\ntitle: "Model API"\ncreated: 2026-01-01\nupdated: 2026-01-01\n'
            f'type: architecture\ntags: [r]\nsources: {list(sources)!r}\n---\n\n{body}\n')
    text = feature_metadata(text, feature) if feature else text
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _block(tmp_path, facet="api", body="The catalog validates credentials before selecting a model."):
    source = tmp_path / "upstream" / "pkg/models/catalog.py"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("def validate(key):\n    return bool(key)\n")
    return render_block(FEATURE, {"facet": facet, "title": facet, "body": body,
                        "interpretation": "fact", "evidence": [
                            {"path": "pkg/models/catalog.py", "start": 1, "end": 2}]},
                        tmp_path / "upstream", "acme/r", PIN)


def test_changed_sources_select_depth_and_preserve_missing_facets(tmp_path):
    k = tmp_path / "knowledge"
    _page(k, FEATURE.page, "Basic overview")
    depth = _page(k, "repos/r/features/depth.md", _block(tmp_path))
    _page(k, "repos/other/secret.md", "OTHER REPO SECRET")
    _page(k, "general/background.md", "GENERAL BACKGROUND")
    _page(k, "repos/r/cards.md", "<!-- kb:file path=pkg/models/catalog.py -->\nSIGNATURES")
    docs = KnowledgeDocs(k, "repos/r")
    related = docs.related(["pkg\\models\\catalog.py"])
    assert [d["path"] for d in related["documents"]] == [depth.relative_to(k).as_posix()]
    selected = related["documents"][0]
    assert "validates credentials" in selected["content"]
    assert selected["source_pins"] == [PIN]
    assert selected["available_facets"] == selected["included_facets"] == ["api"]
    assert "failure_modes" in selected["missing_facets"]
    assert "kb:depth-proof" not in selected["content"]
    assert "SIGNATURES" not in selected["content"]
    assert docs.related(["unrelated.py"])["status"] == "no_match"
    assert KnowledgeDocs(k).related(["pkg/models/catalog.py"])["documents"] == []


def test_old_explanatory_pages_use_pinned_sources_without_new_metadata(tmp_path):
    k = tmp_path / "knowledge"
    _page(k, "repos/r/old.md", "Legacy caller contract", feature=None,
          sources=[f"acme/r@{PIN}:pkg/models/catalog.py:L1-L2"])
    selected = KnowledgeDocs(k, "repos/r").related(["pkg/models/catalog.py"])["documents"][0]
    assert selected["source_pins"] == [PIN]
    assert selected["matched_files"] == ["pkg/models/catalog.py"]
    assert selected["content"] == "Legacy caller contract"


def test_stronger_overview_match_cannot_hide_intact_feature_depth(tmp_path):
    k = tmp_path / "knowledge"
    _page(k, FEATURE.page, "Catalog overview", sources=[f"acme/r@{PIN}:pkg/models/catalog.py"])
    depth = _page(k, "repos/r/depth.md", _block(tmp_path))
    depth.write_text(depth.read_text().replace('title: "Model API"', 'title: "Detailed implementation"'))
    related = KnowledgeDocs(k, "repos/r").related(["pkg/models/catalog.py"], query="Model API models")
    assert related["documents"][0]["path"] == "repos/r/depth.md"
    assert related["documents"][0]["included_facets"] == ["api"]


@pytest.mark.parametrize("edit", ["body", "duplicate", "proof"])
def test_invalid_depth_is_not_exposed_as_checked_context(tmp_path, edit):
    k = tmp_path / "knowledge"
    block = _block(tmp_path)
    if edit == "body":
        block = block.replace("validates credentials", "ignores credentials")
    elif edit == "duplicate":
        block += "\n" + block
    else:
        block = block.replace('"start":1', '"start":false')
    _page(k, "repos/r/depth.md", block)
    assert KnowledgeDocs(k, "repos/r").related(["pkg/models/catalog.py"])["documents"] == []


@pytest.mark.parametrize("edit", ["missing_digest", "bad_digest", "absolute_path", "parent_path"])
def test_malformed_proof_is_refused_even_with_intact_body_digest(tmp_path, edit):
    k = tmp_path / "knowledge"
    block = _block(tmp_path)
    original = DEPTH_BLOCK.fullmatch(block)
    body = original[5]
    proof_match = re.search(r"<!-- kb:depth-proof (.*?) -->", body)
    proof = json.loads(proof_match[1])
    evidence = proof["evidence"][0]
    if edit == "missing_digest":
        evidence.pop("sha256")
    elif edit == "bad_digest":
        evidence["sha256"] = 42
    else:
        evidence["path"] = "/secret.py" if edit == "absolute_path" else "../secret.py"
    edited = body.replace(proof_match[1], json.dumps(proof))
    block = block.replace(body, edited).replace(original[4], hashlib.sha256(edited.encode()).hexdigest())
    _page(k, "repos/r/depth.md", block)
    assert KnowledgeDocs(k, "repos/r").related(["pkg/models/catalog.py"])["documents"] == []


def test_bounds_keep_large_depth_retrievable_and_budget_followup(tmp_path):
    k = tmp_path / "knowledge"
    _page(k, "repos/r/depth.md", _block(tmp_path, body="Long behavior. " * 300))
    other = Feature("caller", "Caller", "core", FEATURE.source_globs, (), "repos/r/caller.md",
                    FEATURE.entry_points)
    _page(k, other.page, "Caller context\n" * 400, other)
    third = Feature("third", "Third", "core", FEATURE.source_globs, (), "repos/r/third.md",
                    FEATURE.entry_points)
    _page(k, third.page, "Third context", third)
    related = KnowledgeDocs(k, "repos/r").related(["pkg/models/catalog.py"])
    assert len(related["documents"]) == 2 and related["content_chars"] <= 6000
    assert related["documents"][0]["included_facets"] == ["api"]
    assert all(d["more_available"] for d in related["documents"])


def test_snapshot_verifier_runs_before_read_even_for_excluded_cards(tmp_path):
    k = tmp_path / "knowledge"
    path = _page(k, "repos/r/depth.md", _block(tmp_path))
    originals = {p.relative_to(k).as_posix(): p.read_bytes() for p in k.rglob("*.md")}

    def verify(relative):
        assert (k / relative).read_bytes() == originals[relative], "snapshot changed"
        return k / relative

    docs = KnowledgeDocs(k, "repos/r", verify=verify)
    assert docs.related(["pkg/models/catalog.py"])["status"] == "ready"
    path.write_text("<!-- kb:file tampered -->" + "x" * 530000)
    with pytest.raises(AssertionError, match="snapshot changed"):
        docs.related(["pkg/models/catalog.py"])


def test_feature_hints_refresh_block_lists_without_changing_body(tmp_path):
    text = _page(tmp_path, FEATURE.page, _block(tmp_path)).read_text()
    text = text.replace('entry_points: ["pkg/models/catalog.py"]', 'entry_points:\n- old.py')
    text = text.replace('source_globs: ["pkg/models/*"]', 'source_globs:\n  - old/*')
    refreshed = feature_metadata(text, FEATURE)
    assert Page.parse(refreshed).frontmatter_data()["entry_points"] == list(FEATURE.entry_points)
    assert Page.parse(refreshed).frontmatter_data()["source_globs"] == list(FEATURE.source_globs)
    assert refreshed[len(Page.parse(refreshed).frontmatter):] == text[len(Page.parse(text).frontmatter):]
    assert feature_metadata(refreshed, FEATURE) == refreshed


@pytest.mark.parametrize("files", ["pkg/file.py", [None], ["../secret.py"], ["/secret.py"]])
def test_invalid_changed_file_inputs_are_refused(tmp_path, files):
    with pytest.raises(KnowledgeDocsError):
        KnowledgeDocs(tmp_path).related(files)
