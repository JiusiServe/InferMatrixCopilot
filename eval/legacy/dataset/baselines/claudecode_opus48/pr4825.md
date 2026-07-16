I have everything I need. This confirms my main finding. Here's my complete review.

---

## Review — PR #4825: `[Feature] Improve diffusion LoRA compatibility for SDXL`

**Author:** tthakkal · **State:** MERGED · +53 / −1 · `vllm_omni/diffusion/lora/manager.py` + test

**Recommended verdict: `COMMENT`** (approve-level; no blockers — two non-blocking design/robustness notes)

### Summary of what was validated
- **Correctness — PASS.** Adding `"unet"` to `default_components` is safe. The scan only inspects **top-level** pipeline attributes (`getattr(self.pipeline, component_name)`), and `StableDiffusionXLPipeline` is the only pipeline exposing a top-level `self.unet` (`pipeline_sdxl.py:110`). Internal `unet` submodules (soulx `note_transcription`, `rmvpe`) are never top-level pipeline attrs, so no other pipeline changes behavior. The `hasattr` guard makes it a no-op where absent.
- **Breaking changes — PASS.** Purely additive to a tuple; opt-in `_lora_components` path untouched.
- **Test coverage — PASS.** `test_lora_manager_discovers_unet_component` is a faithful, correct adaptation of the existing `bagel` test — verifies discovery, `_lora_modules` recording, and actual in-tree replacement. Pure unit test, no hardware needed.
- **PR body — adequate for a compat fix.** Script + before/after SDXL images provided showing base-identical → LoRA-differentiated output. (The heavy new-model gates — latency/VRAM/docs tables — don't apply here; this isn't a new model.)

### Comments

**1. `vllm_omni/diffusion/lora/manager.py:375` — reuse the pipeline's declared denoiser instead of a fourth hardcoded list**

Every pipeline already declares its denoiser via `_dit_modules` (SDXL: `["unet"]` at `pipeline_sdxl.py:46`), and `offloader/module_collector.py:110` already discovers components by reading `pipeline._dit_modules` through the `SupportsComponentDiscovery` protocol. This LoRA manager instead maintains its own hardcoded `default_components` tuple (and `registry.py:427` keeps yet another `["transformer","transformer_2","dit","unet"]`). Appending `"unet"` fixes SDXL but grows the drift — e.g. soulx declares `_dit_modules = ["cfm_decoder.model.diff_estimator"]`, which this list still won't cover. Consider reading `pipeline._dit_modules` here (like the offloader does) so per-pipeline declarations are the single source of truth. Not blocking.

**2. `vllm_omni/diffusion/lora/manager.py:372` — text-encoder LoRA is still a silent no-op**

SDXL declares `_encoder_modules = ["text_encoder", "text_encoder_2"]`, and many SDXL adapters ship text-encoder weights. Those keys still apply to zero layers — the exact "base-identical output" failure this PR describes, just moved to the encoders. Fine to scope this PR to unet (your test adapter is unet-only), but worth a note that this is a known gap. More broadly: the underlying footgun is that an adapter matching zero modules loads and activates silently — a `logger.warning` when a loaded adapter yields zero replacements would have surfaced both bugs immediately. Non-blocking / follow-up.

### Nit
- The test helpers (`_FakeLinearBase`, `fake_replace_submodule`, `_DummyBaseLayerWithLoRA`) are reused correctly; no issues.

---

*Note: per the skill and your instructions, I did **not** post anything to GitHub — this review is output here only. The PR is already merged, so these are best treated as follow-up items rather than merge gates.*