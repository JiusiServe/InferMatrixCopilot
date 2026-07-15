"""Adapter knowledge sourced from the referenced community docs (submodule):
briefing() reads the curated rules+index, the doc tools reach the deep pages on
demand (contained), and the legacy AI-profile path still degrades gracefully."""

from __future__ import annotations

from pathlib import Path

from omni_copilot.adapters.base import _BRIEFING_CAP, RepoAdapter
from omni_copilot.engine.agent_runtime.knowledge import _repo_docs_tool


def _adapter(tmp_path: Path, manifest: dict) -> RepoAdapter:
    root = tmp_path / "adapter"
    root.mkdir(exist_ok=True)
    return RepoAdapter(name="x", root=root,
                       manifest={"name": "x", "repo": {"path": str(tmp_path)}, **manifest})


# ── briefing() from the curated knowledge base ────────────────────────────────
def test_briefing_from_knowledge_docs(tmp_path):
    root = tmp_path / "adapter"
    d = root / "knowledge" / "repos" / "r"
    d.mkdir(parents=True)
    (d / "rules.md").write_text("# HARD GATES\nrule one", encoding="utf-8")
    (d / "_index.md").write_text("# NAV\nnav table", encoding="utf-8")
    a = _adapter(tmp_path, {"knowledge": {
        "source": "acme/kb", "dir": "knowledge", "repo_subdir": "repos/r",
        "briefing_docs": ["repos/r/rules.md", "repos/r/_index.md"]}})
    b = a.briefing()
    assert "HARD GATES" in b and "NAV" in b and "acme/kb" in b


def test_briefing_capped(tmp_path):
    root = tmp_path / "adapter"
    (root / "knowledge").mkdir(parents=True)
    (root / "knowledge" / "big.md").write_text("x" * 20_000, encoding="utf-8")
    a = _adapter(tmp_path, {"knowledge": {"dir": "knowledge",
                                          "briefing_docs": ["big.md"]}})
    b = a.briefing()
    assert len(b) <= _BRIEFING_CAP + 200 and "capped" in b


def test_briefing_empty_when_no_source(tmp_path):
    assert _adapter(tmp_path, {}).briefing() == ""


def test_briefing_ignores_missing_briefing_doc(tmp_path):
    # a declared doc that isn't on disk is skipped, not fatal -> empty
    a = _adapter(tmp_path, {"knowledge": {"dir": "knowledge",
                                          "briefing_docs": ["gone.md"]}})
    assert a.briefing() == ""


# ── doc tools: retrieval + containment ────────────────────────────────────────
def test_doc_tools_read_search_and_containment(tmp_path):
    root = tmp_path / "adapter"
    (root / "knowledge" / "guides").mkdir(parents=True)
    (root / "knowledge" / "guides" / "g.md").write_text(
        "# Guide\nSEMANTIC PARITY matters", encoding="utf-8")
    a = _adapter(tmp_path, {"knowledge": {"dir": "knowledge"}})
    tools = _repo_docs_tool(None, a)
    assert set(tools) == {"doc_search", "doc_read"}
    assert "SEMANTIC PARITY" in tools["doc_read"].handler(path="guides/g.md")
    assert "guides/g.md" in tools["doc_search"].handler(query="SEMANTIC PARITY")
    assert "refused" in tools["doc_read"].handler(path="../../../../etc/passwd")
    assert "no such doc" in tools["doc_read"].handler(path="guides/nope.md")


def test_doc_tools_absent_without_knowledge(tmp_path):
    assert _repo_docs_tool(None, _adapter(tmp_path, {})) == {}


# ── the shipped vllm_omni adapter (integration; skips if submodule absent) ────
def test_real_adapter_briefing_from_submodule():
    import pytest

    from omni_copilot.adapters.base import load_adapter
    root = Path(__file__).resolve().parents[1] / "adapters" / "vllm_omni"
    if not (root / "knowledge" / "repos").exists():
        pytest.skip("knowledge submodule not checked out")
    a = load_adapter(root)
    b = a.briefing()
    assert b and "zuiho-kai" in b
    assert not (root / "profile").exists()  # AI profile retired
