"""The initialized Jiuwen adapter retains valid init seeds and gated publication."""

from __future__ import annotations

from infermatrix_copilot.adapters.base import AdapterRegistry
from infermatrix_copilot.kb_service.config import load_registry, validate_seeds
from infermatrix_copilot.sdk._resources import adapters_root, knowledge_root


def test_jiuwenswarm_adapter_retains_init_contract_after_publication_enablement():
    adapter = next(a for a in AdapterRegistry(adapters_root()).all() if a.name == "jiuwenswarm")
    assert adapter.manifest["repo"]["full_name"] == "openJiuwen-ai/jiuwenswarm"
    assert adapter.manifest["push"]["allowed"] is False
    lifecycle = load_registry(adapters_root())["jiuwenswarm"]
    assert lifecycle.mode == "auto_merge" and lifecycle.auto_merge
    assert lifecycle.calibration_set
    assert lifecycle.upstream_visibility == "public"
    init = lifecycle.init
    assert init is not None
    assert all(seed.startswith("general/") for seed in init.seeds)
    assert validate_seeds(init, knowledge_root()) == []
    # the empty-KB path: the tree is absent until kb init's skeleton PR lands,
    # and a proper repository entry from then on
    tree = knowledge_root() / "repos" / "jiuwenswarm"
    assert not tree.exists() or (tree / "_index.md").is_file()


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
