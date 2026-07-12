# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4802, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

Thanks for the thorough RFC @Ronnie-Rui, and thanks @LHXuuu for the detailed review.

**The core attribution need is already covered.** After #3576 (merged), the upstream `vllm:*` families — including KV cache usage, scheduler stats, and prefix-cache counters — are wrapped with `{stage, replica}` labels via `OmniPrometheusStatLogger` (`vllm_omni/metrics/stat_logger.py`). That directly answers questions 1–3 from the RFC motivation (which stage/replica/modality holds the most KV).

**The `make_stats` throttle is per-scheduler, not global.** `OmniSchedulerMixin.make_stats()` (`vllm_omni/core/sched/omni_scheduler_mixin.py:154-159`) throttles at 1 Hz per scheduler instance. The orchestrator's record path (`orchestrator.py:696`) gates solely on `raw_outputs.scheduler_stats is not None` — there is no second global throttle. PR #3576 added a regression test (`test_orchestrator_does_not_re_introduce_global_stats_throttle`) that fails if a global `_last_stats_ts` gate is reintroduced.

**On tail_waste / fragmentation:** As @LHXuuu noted, unused slots in the last block are expected paged-KV rounding overhead bounded by block size. @Ronnie-Rui agreed these are not needed as default Prometheus metrics. That leaves the narrower scope @hsliuustc0106 suggested — allocator-backed KV footprint/occupancy for LLM_AR/LLM_Generation stages only, diffusion deferred — as a valid future direction if concrete regression cases emerge.

**Closing** as the attribution concern is resolved by #3576 and the proposed additional metrics were withdrawn. Reopen if someone has a concrete case where existing `kv_cache_usage_perc` / scheduler / prefix-cache metrics with `{stage, replica}` labels fail to catch a real regression.

**Disposition:** close

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
