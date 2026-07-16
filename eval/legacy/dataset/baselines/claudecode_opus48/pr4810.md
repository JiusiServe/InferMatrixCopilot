I have everything I need. Here's my review.

---

## Review of PR #4810 — `[BugFix] Use KV cache scale mapper in custom loaders`

**Repo:** vllm-project/vllm-omni · **State:** MERGED · **Author:** akshatvishu
**Files:** 4 loaders + 1 new test (+159 / −33)

### Verdict: ✅ APPROVE (no blockers)

The fix is correct. I verified the load path against the actual upstream vLLM checkout (`/rebase/vllm`), which is what settles the central design question the PR rests on.

**BLOCKER scan**

| Category | Result |
|---|---|
| Correctness | PASS |
| Reliability/Safety | PASS |
| Breaking Changes | PASS (removes reliance on an already-removed upstream API) |
| Test Coverage | PASS (regression test added; but see note 1) |
| Documentation | PASS (PR body is thorough) |
| Security | PASS |

**What I validated (the design is sound):**
- vLLM's `AutoWeightsLoader.load_weights` *itself* pulls `quant_config.get_cache_scale_mapper()` and applies it to the weight stream before delegating to child loaders (`/rebase/vllm/.../models/utils.py:408-415`). So for the two **delegated** loaders — `HunyuanModel` (`hunyuan_image3.py:151`) and `Qwen2Model` (`qwen2_old.py`) — `.k_proj.output_scale` → `.attn.k_scale` renaming happens in the outer loader, and the inner `maybe_remap_kv_scale_name` then no-ops on the already-mapped name (`weight_utils.py:1361`). Removing the manual branches is correct, not a regression. Both import the real `vllm.model_executor.models.utils.AutoWeightsLoader` (no local shadow).
- `fp8.py:227-233` confirms the mapper's suffix map (`.k_proj.output_scale → .attn.k_scale`, etc.), matching the removed branches' intent.
- The two **direct** loaders — `MammothModa2Qwen2ForCausalLM` (`mammoth_moda2.py:486-489`) and `MiMoAudioLLMForConditionalGeneration` (`mimo_audio_llm.py:1155-1158`) — are not wrapped by `AutoWeightsLoader`, so applying the mapper themselves is the right call. Re-application would be a harmless no-op anyway (suffix won't re-match).
- pre-commit / DCO / build (3.11, 3.12) / buildkite green.

### Non-blocking comments

**1. `tests/model_executor/models/test_kv_cache_scale_mapper.py:99` — the delegated-loader test doesn't exercise the thing it names.**
`test_auto_weights_loader_delegated_loaders_accept_mapped_cache_scale` feeds the *already-mapped* `_MAPPED_SCALE_NAME` (`layers.0.self_attn.attn.k_scale`) straight into the **inner** `HunyuanModel`/`Qwen2Model.load_weights`, bypassing `AutoWeightsLoader` entirely. That only asserts the inner loader accepts a pre-mapped name (trivially true) — it never verifies that the *outer* `AutoWeightsLoader` performs the `.output_scale → .k_scale` mapping, which is the actual behavior these two removals depend on. To have real regression value it should drive the raw `_SOURCE_SCALE_NAME` (`.k_proj.output_scale`) through `AutoWeightsLoader` (or the top-level `...ForConditionalGeneration.load_weights`) and assert it lands in `.attn.k_scale`. As written, the test would stay green even if upstream stopped auto-applying the mapper.

**2. `tests/model_executor/models/test_kv_cache_scale_mapper.py:15` — one known-affected loader was dropped from scope.**
The PR body's own "on current main" output lists `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py` among the files failing the `.get_cache_scale(` check, but it was removed from `_STALE_API_FILES` and left unfixed in this PR — despite the title covering "custom loaders." That loader called the removed API directly, so it would have hit the same failure. (It's since been addressed on main — `hunyuan_image3_transformer.py:2238` now carries a `# ... (see #4810)` comment and uses `maybe_remap_kv_scale_name` — but as scoped, this PR shipped an incomplete sweep of the affected loaders.)

**Minor:** the string-match test (`test_model_loaders_do_not_call_removed_get_cache_scale`, line 78) is a lint-grade guard, not a behavioral one — fine to keep, but it's the weakest of the three and the author already flagged uncertainty about keeping the file.

**Note:** This is a post-merge review; nothing was posted to GitHub.