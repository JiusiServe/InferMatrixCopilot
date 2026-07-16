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


# ── repo-specific briefing (reads the SHARED root, excludes general) ─────────
def test_adapter_briefing_is_repo_specific_only(tmp_path):
    k = _knowledge(tmp_path)
    a = _adapter(tmp_path, {"knowledge": {
        "source": "acme/kb", "repo_subdir": "repos/r",
        "briefing_docs": ["repos/r/rules.md", "repos/r/_index.md"]}})
    b = a.briefing(k)
    assert "HARD GATES" in b and "REPO NAV" in b and "acme/kb" in b
    assert "GENERAL NAV" not in b  # general is injected separately, not here


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
    tools = _repo_docs_tool(_ctx(k), None)  # adapter unused; base is settings.knowledge_dir
    assert set(tools) == {"doc_search", "doc_read"}
    assert "SEMANTIC PARITY" in tools["doc_read"].handler(path="general/g.md")
    assert "HARD GATES" in tools["doc_read"].handler(path="repos/r/rules.md")
    assert "general/g.md" in tools["doc_search"].handler(query="SEMANTIC PARITY")
    assert "refused" in tools["doc_read"].handler(path="../../../../etc/passwd")
    assert "no such doc" in tools["doc_read"].handler(path="repos/r/nope.md")


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
