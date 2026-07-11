I now have everything needed. Here is my answer as a maintainer.

---

## Re: [RFC]: vLLM-Omni KV Cache Efficiency and Attribution Metrics (#4802)

Thanks for the detailed RFC and the reworked Qwen3-TTS evidence — the multi-stage attribution framing is genuinely well-motivated. Agreeing with the resolution you and @LHXuuu already converged on: **closing this is the right call**, and I want to record the technical reasoning against the code so it's clear *why*, and to flag the one piece worth spinning out separately.

### 1. The stage/replica attribution need is already met

The RFC's strongest argument is dimensional attribution ("which stage/replica holds the most KV"). But that dimension already exists on the entire upstream `vllm:*` surface, not just a few families. `OmniPrometheusStatLogger` rewrites the upstream single `engine` label into a `(stage, replica)` pair for **all ~37 `vllm:*` families** — including the KV, scheduler, and prefix-cache metrics:

- `vllm_omni/metrics/stat_logger.py:1-18` — module docstring states the intent explicitly.
- `_rewrite_labelnames()` (`stat_logger.py:41-59`) turns `["model_name","engine",…]` into `["model_name","stage","replica",…]` at family-creation time, applied via the `_RelabelGauge/Counter/Histogram` mixins.

So `vllm:kv_cache_usage_perc{stage,replica}`, `vllm:prefix_cache_hits/queries{stage,replica}`, and the scheduler counters already answer questions 1–3 for production monitoring. The omni-native families (`vllm_omni/metrics/definitions.py:153`, `STAGE_LABELS = ("model_name","stage","replica")`) confirm the same label vocabulary is the established convention. This is exactly the point @LHXuuu made — the new families would be re-deriving a dimension the codebase already exposes.

### 2. `tail_waste` / `fragmentation` measure expected paged-KV rounding, not a defect

The Qwen3-TTS "94% fragmentation" figure for the code2wav stage is, as you concluded, the `source="stage_tokens"` **estimate fallback**, not an allocator read — the table in the RFC labels it as such. For real allocator-backed stages, tail waste is bounded by `block_size` per sequence by construction (last-block rounding). Surfacing that as a default Prometheus histogram invites operators to "optimize" a quantity that is a fixed design constant of paged attention. Without a demonstrated case where `kv_cache_usage_perc{stage,replica}` looks healthy while these catch a real regression, these belong in an offline/profiling tool, not the default scrape surface. Agreed with dropping them.

### 3. The one observation worth keeping — but it's a separate bug, not a metrics RFC

The most valuable finding buried in the RFC is the `make_stats` throttle, and I want to make sure it doesn't get lost when this closes. Confirmed in code:

- `vllm_omni/core/sched/omni_scheduler_mixin.py:154-159`: within `_STATS_INTERVAL_S = 1.0` (`:17`) of the last emission, `make_stats()` returns `None` **without** calling `super().make_stats()`.
- Upstream `super().make_stats()` (`vllm/v1/core/sched/scheduler.py:2276-2310`) is where prefix-cache/token stats are produced, and `kv_cache_manager.make_prefix_cache_stats()` is **get-and-reset** (`vllm/v1/core/kv_cache_manager.py:194-204`).

One correction to the RFC's framing, though: because the upstream accumulator is only drained *when* `make_stats` runs, the throttled cycles don't *lose* counter deltas — they defer them. The KV manager keeps accumulating and the next non-throttled call (>1 s later) drains the whole backlog, so `vllm:prefix_cache_*` and `vllm:prompt_tokens_total` still increment cumulatively; they're just reported at ~1 Hz, which is well inside a normal Prometheus scrape interval. The "reads 0 under real load" symptom is therefore most plausibly a **short-window artifact** (a benchmark whose entire measured span sits inside the throttle, or a gauge like `kv_cache_usage_perc` sampled between updates), not a permanent blind spot. That said, a 1 s throttle that gates the *entire* upstream stats layer (spec-decode, KV-connector, cudagraph, perf stats all ride on the same return) is a coarse instrument, and downsampling a monotonically-draining accumulator to 1 Hz is a legitimate correctness smell worth a closer look.

If that throttle is causing observable metric gaps for you, please open a **focused issue** on `OmniSchedulerMixin.make_stats` — e.g. only throttle the expensive/duplicative work while still letting the counter-draining path through, or decouple the throttle from `super().make_stats()`. That's a concrete, mergeable fix with a clear contract, independent of adding new metric families.

### Disposition

Closing as **won't-implement for the default Prometheus surface**, per the author's own conclusion and @LHXuuu's analysis:
- stage/replica attribution → already delivered by the `OmniPrometheusStatLogger` relabeling (the #3576 line of work);
- slot/tail-waste/fragmentation → expected block-rounding overhead, better suited to an opt-in profiling tool if a real regression case appears;
- the `make_stats` throttle → the one real, actionable item; please file it separately so it gets fixed on its own merits.

Thanks again @Ronnie-Rui for the thorough measurement work and for engaging with the pushback constructively — the diffusion abstraction ETA (Q3) and the LLM_AR/LLM_Generation scoping discussion are both captured, so if a concrete regression case does surface later, we have a clear starting point to reopen from.