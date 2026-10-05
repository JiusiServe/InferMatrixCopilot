"""Repo-root citation checks must not reinterpret nested upstream paths."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


_SPEC = importlib.util.spec_from_file_location(
    "check_doc_citations", Path(__file__).resolve().parents[1] / "tools/check_doc_citations.py")
citations = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(citations)


@pytest.fixture
def source(tmp_path, monkeypatch):
    monkeypatch.setattr(citations, "REPO", tmp_path)
    root = tmp_path / "src"
    root.mkdir()
    return root / "sample.py"


@pytest.mark.parametrize("prefix", ["upstream-", "upstream/", "upstream_", ".", "../", "\\"])
def test_embedded_paths_are_not_local_citations(source, capsys, prefix):
    source.write_text(prefix + "doc/missing.py")  # doc-citation-exempt
    assert citations.main() == 0
    assert "0 citations resolve" in capsys.readouterr().out


@pytest.mark.parametrize("path", [
    "jiuwenswarm/resources/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/validator.py",  # doc-citation-exempt
    "https://example.test/doc/missing.md",  # doc-citation-exempt
    "https://example.test/component-doc/scripts/validator.py",  # doc-citation-exempt
])
def test_upstream_and_url_paths_are_not_local_citations(source, capsys, path):
    source.write_text(path)
    assert citations.main() == 0
    assert "0 citations resolve" in capsys.readouterr().out


@pytest.mark.parametrize("text", [
    "doc/missing.md",  # doc-citation-exempt
    "See `doc/missing.md`.",  # doc-citation-exempt
    "(doc/missing.md)",  # doc-citation-exempt
    "upstream-doc/remote.md and doc/missing.md",  # doc-citation-exempt
])
def test_missing_root_citations_still_fail(source, capsys, text):
    source.write_text(text)
    assert citations.main() == 1
    assert "1 dangling citation(s) of 1 checked" in capsys.readouterr().out


def test_valid_local_citation_and_root_segments_resolve(source, capsys):
    root = citations.REPO / "doc"
    root.mkdir()
    (root / "guide.md").write_text("guide")
    source.write_text('See `doc/guide.md`.\nROOT / "doc" / "guide.md"')  # doc-citation-exempt
    assert citations.main() == 0
    assert "2 citations resolve" in capsys.readouterr().out


def test_missing_root_segments_still_fail(source, capsys):
    source.write_text('REPO_ROOT / "doc" / "missing.md"')  # doc-citation-exempt
    assert citations.main() == 1
    output = capsys.readouterr().out
    assert "built from path segments" in output
    assert "1 dangling citation(s) of 1 checked" in output
