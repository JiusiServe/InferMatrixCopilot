# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4802, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

Thanks for the thorough RFC and the Qwen3-TTS evidence, @Ronnie-Rui. Here's where things stand after the discussion:

### What's already resolved

- **Attribution gap (questions 1–3):** PR [#3576](https://github.com/vllm-project/vllm-omni/pull/3576) (merged) wraps ~65 upstream `vllm:*` families — including `kv_cache_usage_perc`, `prefix_cache_*`, and scheduler stats — with `{stage, replica}` labels. On a multi-stage Qwen3-TTS deployment with `--log-stats`, you can already answer "which stage holds the most KV?" and "which replica is under pressure?" from `/metrics`.

- **The `make_stats` throttle:** The 1-second interval at [`vllm_omni/core/sched/omni_scheduler_mixin.py:139-143`](https://github.com/vllm-project/vllm-omni/blob/main/vllm_omni/core/sched/omni_scheduler_mixin.py#L139-L143) is **per-scheduler (per-replica)**, not global. The orchestrator's loop iterates all `(stage_id, replica_id)` pairs independently — the code comment at the `record()` site in `orchestrator.py` explicitly guards against a second global throttle. So after #3576, per-stage KV cache metrics should not be swallowed the way the RFC describes. Worth re-verifying with a Qwen3-TTS deployment to confirm `prefix_cache_*` is no longer reading 0.

- **Scope:** LLM_AR / LLM_Generation stages first (allocator-backed), diffusion deferred to Q3 when the general abstraction lands — agreed by @hsliuustc0106.

- **Tail waste / fragmentation:** These measure paged-KV block rounding overhead — unused slots in the last block of each allocation, bounded by `block_size`. @LHXuuu correctly pointed out this is by-design and not actionable for production monitoring. You've agreed to defer these from the default Prometheus surface. :+1:

### What remains open

- **`kv_footprint_tokens` / `kv_footprint_bytes`:** Slot-level KV usage per-stage. This is a different view from `kv_cache_usage_perc` (which is percentage-based). Before building this, it'd help to have a concrete case where the percentage alone is insufficient — e.g., two stages both at 90% but one has 100× more absolute slots.

- **`kv_cached_tokens` / `kv_prefix_hit_ratio`:** The RFC claims upstream `prefix_cache_*` reads 0 on the Omni path. If this is still true after #3576, these metrics with a bypass path are justified. If #3576 already surfaces real prefix-cache counters with stage labels, they may be redundant.

### Suggested next step

1. Deploy Qwen3-TTS with `--log-stats` on the current `main` (post-#3576) and check whether `vllm:prefix_cache_*` and `vllm:kv_cache_usage_perc` with `{stage, replica}` labels already answer questions 1–4.
2. If upstream prefix-cache counters still read 0, that becomes the concrete justification for `kv_cached_tokens` / `kv_prefix_hit_ratio` via the orchestrator bus.
3. If they work, the remaining value-add is `kv_footprint_tokens` (absolute slot count) — consider whether that justifies a new metric family or whether a `kv_cache_usage_perc` + `gpu_cache_usage` dashboard suffices.

Keeping this RFC open for the remaining footprint/prefix-cache plan. The tail-waste/fragmentation subset is deferred by mutual agreement.

**Disposition:** keep-open

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
