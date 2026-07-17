"""Adapter knowledge sourced from the SHARED community-docs submodule. General
(`general/`) and repo-specific (`repos/<repo>/`) knowledge are kept separate:
the general tree is shared across all repos (never nested under one adapter),
and each adapter's briefing is only its own slice. Deeper docs are reachable on
demand via the doc tools, contained under the shared base."""

from __future__ import annotations

import types
from pathlib import Path

import pytest

from omni_copilot.adapters.base import (
    _BRIEFING_CAP,
    RepoAdapter,
    render_briefing_docs,
)
from omni_copilot.engine.agent_runtime.knowledge import _repo_docs_tool


def _adapter(tmp_path: Path, manifest: dict) -> RepoAdapter:
    root = tmp_path / "adapter"
    root.mkdir(exist_ok=True)
    return RepoAdapter(name="x", root=root,
                       manifest={"name": "x", "repo": {"path": str(tmp_path)}, **manifest})


def _knowledge(tmp_path: Path) -> Path:
    """A shared knowledge base: general/ (general) + repos/r/ (repo-specific)."""
    k = tmp_path / "knowledge"
    (k / "general").mkdir(parents=True)
    (k / "general" / "_index.md").write_text("# GENERAL NAV\ngeneral topics",
                                               encoding="utf-8")
    (k / "repos" / "r").mkdir(parents=True)
    (k / "repos" / "r" / "rules.md").write_text("# HARD GATES\nrule one", encoding="utf-8")
    (k / "repos" / "r" / "_index.md").write_text("# REPO NAV\nnav", encoding="utf-8")
    return k


def _ctx(kdir: Path):
    return types.SimpleNamespace(settings=types.SimpleNamespace(knowledge_dir=kdir))


# ── the shared renderer ───────────────────────────────────────────────────────
def test_render_briefing_docs_concatenate_cap_and_missing(tmp_path):
    k = _knowledge(tmp_path)
    b = render_briefing_docs(k, ["general/_index.md", "repos/r/rules.md"], header="H")
    assert "H" in b and "GENERAL NAV" in b and "HARD GATES" in b
    assert render_briefing_docs(k, ["nope.md"]) == ""          # missing -> empty
    big = tmp_path / "kk"; big.mkdir()
    (big / "big.md").write_text("x" * 20_000, encoding="utf-8")
    assert len(render_briefing_docs(big, ["big.md"])) <= _BRIEFING_CAP + 200


def test_render_briefing_reports_missing_and_escape(tmp_path):
    k = _knowledge(tmp_path)
    warnings = []
    assert render_briefing_docs(
        k, ["missing.md", "../../outside.md"], warnings=warnings) == ""
    assert any("missing" in warning for warning in warnings)
    assert any("escapes" in warning for warning in warnings)


# ── repo-specific briefing (reads the SHARED root, excludes general) ─────────
def test_adapter_briefing_is_repo_specific_only(tmp_path):
    k = _knowledge(tmp_path)
    a = _adapter(tmp_path, {"knowledge": {
        "source": "acme/kb", "repo_subdir": "repos/r",
        "briefing_docs": ["repos/r/rules.md", "repos/r/_index.md"]}})
    b = a.briefing(k)
    assert "HARD GATES" in b and "REPO NAV" in b and "acme/kb" in b
    assert "GENERAL NAV" not in b  # general is injected separately, not here


def test_adapter_briefing_refuses_other_repo_doc(tmp_path):
    k = _knowledge(tmp_path)
    warnings = []
    a = _adapter(tmp_path, {"knowledge": {
        "repo_subdir": "repos/r",
        "briefing_docs": ["repos/r/rules.md", "general/_index.md"]}})
    b = a.briefing(k, warnings=warnings)
    assert "HARD GATES" in b and "GENERAL NAV" not in b
    assert any("outside repos/r" in warning for warning in warnings)


def test_render_briefing_strips_page_frontmatter(tmp_path):
    k = tmp_path / "k"; k.mkdir()
    (k / "page.md").write_text(
        "---\ntitle: \"T\"\ncreated: 2026-01-01\nupdated: 2026-01-01\n"
        "type: index\ntags: [general]\nsources: []\n---\n\n# BODY HEADING\ncontent",
        encoding="utf-8")
    b = render_briefing_docs(k, ["page.md"])
    assert "BODY HEADING" in b and "content" in b
    assert "created: 2026-01-01" not in b and not b.startswith("---")


def test_adapter_briefing_empty_without_root_or_docs(tmp_path):
    k = _knowledge(tmp_path)
    # no knowledge_root -> no repo briefing (and no legacy profile) -> ""
    a = _adapter(tmp_path, {"knowledge": {"briefing_docs": ["repos/r/rules.md"]}})
    assert a.briefing(None) == ""
    # no knowledge section at all -> ""
    assert _adapter(tmp_path, {}).briefing(k) == ""


# ── doc tools over the SHARED base (general + repos), contained ─────────────
def test_doc_tools_reach_general_and_repo_specific(tmp_path):
    k = _knowledge(tmp_path)
    (k / "general" / "g.md").write_text("SEMANTIC PARITY in general", encoding="utf-8")
    adapter = _adapter(tmp_path, {"knowledge": {"repo_subdir": "repos/r"}})
    tools = _repo_docs_tool(_ctx(k), adapter)
    assert set(tools) == {"doc_search", "doc_read"}
    assert "SEMANTIC PARITY" in tools["doc_read"].handler(path="general/g.md")
    assert "HARD GATES" in tools["doc_read"].handler(path="repos/r/rules.md")
    assert "general/g.md" in tools["doc_search"].handler(query="SEMANTIC PARITY")
    assert "refused" in tools["doc_read"].handler(path="../../../../etc/passwd")
    assert "no such doc" in tools["doc_read"].handler(path="repos/r/nope.md")


def test_doc_tools_are_cross_platform_literal_and_repo_scoped(tmp_path):
    k = _knowledge(tmp_path)
    (k / "repos" / "other").mkdir()
    (k / "repos" / "other" / "secret.md").write_text(
        "OTHER REPO SECRET", encoding="utf-8")
    (k / "repos" / "r" / "literal.md").write_text(
        "Literal bracket [abc and metadata", encoding="utf-8")
    adapter = _adapter(tmp_path, {"knowledge": {"repo_subdir": "repos/r"}})
    tools = _repo_docs_tool(_ctx(k), adapter)

    # No external grep and no regex interpretation: this works on Windows too.
    assert "literal.md" in tools["doc_search"].handler(query="[abc")
    # The active adapter can read general + its own slice, never another repo.
    assert "outside the selected" in tools["doc_read"].handler(
        path="repos/other/secret.md")
    assert "non-negative" in tools["doc_read"].handler(
        path="repos/r/rules.md", offset=-1)
    assert "regular file" in tools["doc_read"].handler(path="repos/r")


def test_doc_tools_absent_when_no_knowledge_base(tmp_path):
    assert _repo_docs_tool(_ctx(tmp_path / "missing"), None) == {}


# ── shipped setup: shared knowledge/ submodule + vllm_omni adapter ────────────
def test_real_setup_separates_general_and_repo_specific():
    from omni_copilot.adapters.base import load_adapter
    from omni_copilot.config import Settings

    s = Settings()
    if not (s.knowledge_dir / "repos").exists():
        pytest.skip("knowledge submodule not checked out")
    # general/ (general) lives at the shared base, NOT under the adapter
    assert (s.knowledge_dir / "general").exists()
    assert not (Path(s.adapters_dir) / "vllm_omni" / "knowledge").exists()
    # general briefing renders from the shared base
    assert render_briefing_docs(s.knowledge_dir, s.knowledge_general_docs)
    # repo-specific briefing renders from the shared root
    adapter = load_adapter(Path(s.adapters_dir) / "vllm_omni")
    repo = adapter.briefing(s.knowledge_dir)
    assert repo and "zuiho-kai" in repo
    assert not (Path(s.adapters_dir) / "vllm_omni" / "profile").exists()
