# Run report

- task: {'kind': 'pr_review', 'repo': 'vllm-omni', 'pr': 4825, 'issue': None, 'report_only': True, 'post': False, 'params': {}}

- checkout: PR-TIME TREE (head ac3a2ce5a9b9) — the tree matches the diff exactly; repo-wide greps DO reflect PR-time state

## review_text

**Validated:**
- [validated] manager.py:375-381 — Adding "unet" to default_components: the loop already guards with `hasattr(self.pipeline, component_name)` and `isinstance(component, nn.Module)` so pipelines lacking a top-level unet nn.Module are unaffected. SDXL pipeline has `self.unet = SDXLUNet2DConditionModel(...)` (pipeline_sdxl.py:110), confirmed as nn.Module denoiser.
- [validated] manager.py:382-383 — `extra_components` from `_lora_components` (e.g. SenseNovaU1's `["language_model"]`) correctly merges with default_components; the splat `(*default_components, *extra_components)` preserves all entries with no ordering dependency.
- [validated] test_lora_manager.py:587 — `isinstance(layer, _FakeLinearBase)` branch is reachable (the test constructs `_FakeLinearBase()` layers and the fake `from_layer_diffusion` dispatches on it) and correctly mirrors the real `from_layer_diffusion` which replaces LinearBase layers with LoRA wrappers.
- [sweep] manager.py:368-382 — No rebase/merge damage: the hunk adds one entry to an existing tuple literal; no duplicated code blocks, no stale symbol references.
- [sweep] test_lora_manager.py:575-617 — New test follows the identical structural pattern as `test_lora_manager_discovers_bagel_component` above it; no merge damage or duplicated test logic beyond the intentional mirroring.
- [sweep] vllm_omni/diffusion/models — Searched for all `self.unet =` assignments and `_lora_components` declarations. Only SDXL pipeline has a top-level `self.unet` as nn.Module. SoulXSinger's `self.unet` lives in a submodule (rmvpe.py), unreachable by `hasattr(self.pipeline, 'unet')`. No false-positive risk.
- [sweep] registry.py:427 — `transformer_attrs = ["transformer", "transformer_2", "dit", "unet"]` in `_apply_sequence_parallel_if_enabled` serves a different purpose (SP hooks); the LoRA manager's `default_components` is a separate concern, so deduplication across these two lists is not warranted.
- [validated] manager.py:384 — `hasattr` guard ensures pipelines without `unet` skip the component; no crash risk on non-SDXL pipelines.

`tests/diffusion/lora/test_lora_manager.py:614` [minor] — The diff adds `test_lora_manager_discovers_unet_component`, which verifies layer discovery for the `unet` component (asserts module presence in `_lora_modules` and replacement), but it does not test the activation path (loading/activating LoRA weights). The bagel component has `TestBagelLoRARoundTrip` (in `test_bagel_lora.py:149-217`) that exercises the full round‑trip: synthetic checkpoint → adapter load → activation → weight verification. An equivalent round‑trip test for a `unet`‑scoped module (e.g., targeting `'unet.down_block.proj'`) would guard against the risk of prefix mismatch in `_get_lora_weights` during activation, a regression the discovery‑only test would miss. Consider adding such a test to ensure unet LoRA adapters apply correctly. (evidence: Read test_bagel_lora.py:149-217 (TestBagelLoRARoundTrip) and test_lora_manager.py:578-618 (new unet discovery test). The bagel round-trip exercises synthetic-checkpoint → load → activate → verify-weights; the new unet test only verifies layer replacement in _lora_modules and the module tree, not weight activation.)

`tests/diffusion/lora/test_lora_manager.py:575` [nit] — The diff adds `test_lora_manager_discovers_unet_component`, which is structurally identical to the existing `test_lora_manager_discovers_bagel_component` (around line 560). Both tests monkeypatch the same three symbols, construct a pipeline with a single component, call `_replace_layers_with_lora`, and assert the same three conditions; the only differences are the component attribute (`unet` vs `bagel`) and the submodule path (`unet.down_block.proj` vs `bagel.language_model.qkv_proj`). Consider using `@pytest.mark.parametrize` to eliminate this duplication and simplify adding tests for future components. (evidence: Read tests/diffusion/lora/test_lora_manager.py lines 560-617: both tests construct a pipeline with a single component, monkeypatch the same three symbols identically, call `_replace_layers_with_lora`, and assert the same three conditions. The only differences are the component attribute name and the submodule path.)

**Verdict:** COMMENT

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
