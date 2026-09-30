"""kb init pilot 2: the jiuwenswarm adapter is loadable, has no knowledge
pages yet, and its init block parses with seeds that exist (design kb-init §12)."""

from __future__ import annotations

from infermatrix_copilot.adapters.base import AdapterRegistry
from infermatrix_copilot.kb_service.config import load_registry, validate_seeds
from infermatrix_copilot.sdk._resources import adapters_root, knowledge_root


def test_jiuwenswarm_adapter_is_a_disabled_empty_kb_pilot():
    adapter = next(a for a in AdapterRegistry(adapters_root()).all() if a.name == "jiuwenswarm")
    assert adapter.manifest["repo"]["full_name"] == "openJiuwen-ai/jiuwenswarm"
    assert adapter.manifest["push"]["allowed"] is False
    lifecycle = load_registry(adapters_root())["jiuwenswarm"]
    assert lifecycle.enabled is False and lifecycle.mode == "shadow"
    assert lifecycle.upstream_visibility == "public"
    init = lifecycle.init
    assert init is not None
    assert all(seed.startswith("general/") for seed in init.seeds)
    assert validate_seeds(init, knowledge_root()) == []
    # the empty-KB path: kb init creates the tree, this PR must not
    assert not (knowledge_root() / "repos" / "jiuwenswarm").exists()


def test_jiuwenswarm_tag_is_in_the_knowledge_taxonomy():
    # kb init refuses to write pages whose repo tag the taxonomy lacks
    # (check_wiki_lint reads doc/knowledge/SCHEMA.md), so the tag is declared first
    import importlib.util
    from pathlib import Path

    lint_path = Path(__file__).resolve().parents[1] / "knowledge" / "tools" / "check_wiki_lint.py"
    spec = importlib.util.spec_from_file_location("check_wiki_lint", lint_path)
    lint = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lint)
    assert "jiuwenswarm" in lint.taxonomy()
