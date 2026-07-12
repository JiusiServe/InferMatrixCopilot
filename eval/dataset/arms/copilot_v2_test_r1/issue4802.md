# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4802, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Summary

Thanks for the thorough RFC, @Ronnie-Rui. The core need — per-stage and per-replica KV cache attribution — has been addressed by **#3576** (merged), which wraps all upstream `vllm:*` metrics with `{stage, replica}` labels via `OmniPrometheusStatLogger`.

### What's already covered (post-#3576)

These upstream Prometheus metrics now carry `{stage, replica}` labels, directly answering your questions 1–2:

| Metric | Type | What it tells you |
|---|---|---|
| `vllm:kv_cache_usage_perc` | Gauge | KV cache usage fraction, per stage/replica |
| `vllm:prefix_cache_queries` | Counter | Tokens queried against prefix cache |
| `vllm:prefix_cache_hits` | Counter | Tokens served from prefix cache |
| `vllm:prompt_tokens_cached` | Counter | Cached prompt tokens (local + external) |
| `vllm:kv_block_lifetime_seconds` | Histogram | Block residency time (gated by `--kv-cache-metrics`) |
| `vllm:kv_block_idle_before_evict_seconds` | Histogram | Idle time before eviction |
| `vllm:kv_block_reuse_gap_seconds` | Histogram | Gaps between consecutive block accesses |

All are emitted per-(stage, replica) through `OmniPrometheusStatLogger` at `vllm_omni/metrics/stat_logger.py`. The `make_stats` throttle is per-scheduler at 1 Hz (`omni_scheduler_mixin.py:154-159`) — no global gate starves replicas, and `test_orchestrator_does_not_re_introduce_global_stats_throttle` guards against regression.

### What was deferred

Per thread consensus (cc @LHXuuu, @hsliuustc0106):

- **`kv_tail_waste_tokens` / `kv_fragmentation_ratio` / `kv_block_occupancy_ratio`**: These measure paged-KV block rounding overhead — the unused slots in the last block of each allocation. This is bounded by block size and expected by design. Without a concrete case where this overhead causes a capacity or latency regression invisible to `kv_cache_usage_perc` + prefix-cache metrics, they shouldn't be default Prometheus metrics.
- **`kv_cached_tokens` / `kv_prefix_hit_ratio` per stage**: Partially covered by upstream's `vllm:prefix_cache_hits` / `vllm:prefix_cache_queries` counters. A derived ratio can be computed in PromQL.
- **Diffusion stages**: Deferred to Q3 when a general diffusion abstraction lands (hsliuustc0106, 2026-07-04).

### Scope if revisited

Per hsliuustc0106's direction: LLM_AR / LLM_Generation stages only. The contributor proposed using the `source` label (`kv_cache_manager` vs `stage_tokens`) to keep allocator reads auditable — that design pattern is sound if there's ever a concrete regression to chase.

### Closing

I'm closing this RFC as the core attribution need is met by #3576 and the remaining proposed metrics were deferred after maintainer review. Please reopen if you encounter a concrete case where paged-KV block overhead causes regressions not visible through the existing `{stage, replica}`-labeled `kv_cache_usage_perc` and prefix-cache metrics.

**Disposition:** close

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
