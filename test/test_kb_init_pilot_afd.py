"""kb init pilot 1: the real afd-plugin adapter's init block parses and its
seeds exist in the real knowledge tree (design kb-init §12)."""

from __future__ import annotations

from infermatrix_copilot.kb_service.config import load_registry, validate_seeds
from infermatrix_copilot.sdk._resources import adapters_root, knowledge_root


def test_afd_plugin_init_block_is_valid_on_the_real_tree():
    lifecycle = load_registry(adapters_root())["afd-plugin"]
    # Init seeds remain valid after the owner's gated publication enablement.
    assert lifecycle.mode == "auto_merge" and lifecycle.auto_merge
    assert lifecycle.calibration_set
    init = lifecycle.init
    assert init is not None
    assert init.source_roots == ("afd_plugin/",)
    assert init.seeds, "the pilot seeds from existing knowledge"
    assert all(seed.startswith(("general/", "repos/vllm-omni/")) for seed in init.seeds)
    assert validate_seeds(init, knowledge_root()) == []
