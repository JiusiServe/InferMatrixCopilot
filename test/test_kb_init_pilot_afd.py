"""kb init pilot 1: the real afd-plugin adapter's init block parses and its
seeds exist in the real knowledge tree (design kb-init §12)."""

from __future__ import annotations

from infermatrix_copilot.kb_service.config import load_registry, validate_seeds
from infermatrix_copilot.sdk._resources import adapters_root, knowledge_root


def test_afd_plugin_init_block_is_valid_on_the_real_tree():
    lifecycle = load_registry(adapters_root())["afd-plugin"]
    # kb init's deepen stage flips `enabled` to true (design §9 PR 3); this test
    # pins the invariant either side of that flip: shadow, never auto_merge
    assert lifecycle.mode == "shadow" and not lifecycle.auto_merge
    init = lifecycle.init
    assert init is not None
    assert init.source_roots == ("afd_plugin/",)
    assert init.seeds, "the pilot seeds from existing knowledge"
    assert all(seed.startswith(("general/", "repos/vllm-omni/")) for seed in init.seeds)
    assert validate_seeds(init, knowledge_root()) == []
