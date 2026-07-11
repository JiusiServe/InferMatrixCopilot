Root cause confirmed. I have everything I need.

---

## Answer for issue #4960

Thanks for the unusually detailed report — the metric tables and the two attached `*.log` files made this easy to pin down. This is a real bug, and your suspected root cause is almost right: the problem isn't in `orchestrator.py`, it's one level down in the stage pool.

### Root cause

The orchestrator does the right thing. At `vllm_omni/engine/orchestrator.py:701-713` it creates a single `IterationStats`, hands it to `process_llm_raw_outputs(...)`, and then passes that *same object* to the stat logger:

```python
record_stats = self._stat_logger is not None and raw_outputs.scheduler_stats is not None
iteration_stats = IterationStats() if record_stats else None
raw_output = await pool.process_llm_raw_outputs(
    replica_id, raw_outputs, iteration_stats=iteration_stats,
)
if record_stats:
    self._stat_logger.record(
        raw_outputs.scheduler_stats, iteration_stats,
        engine_idx=self._stage_replica_to_engine_idx[(stage_id, replica_id)],
    )
```

The whole design relies on `process_llm_raw_outputs` **mutating that passed-in `iteration_stats` in place** (the output processor does exactly that — `OmniOutputProcessor.process_outputs` calls `iteration_stats.update_from_output(...)` / `update_from_finished_request(...)`, see `vllm_omni/engine/output_processor.py:589-629` and `:697`).

But `StagePool.process_llm_raw_outputs` throws the caller's object away on its very first line:

```python
# vllm_omni/engine/stage_pool.py:1062-1079
async def process_llm_raw_outputs(
    self,
    replica_id: int,
    raw_outputs: EngineCoreOutputs,
    iteration_stats: IterationStats | None = None,   # <-- caller's object
) -> list[Any]:
    ...
    processor = self.output_processor
    iteration_stats = IterationStats()               # <-- BUG: overwrites it (line 1074)
    processed = processor.process_outputs(
        raw_outputs.outputs, raw_outputs.timestamp, iteration_stats,
    )
```

Line **1074** unconditionally rebinds `iteration_stats` to a brand-new local `IterationStats()`. `process_outputs` then dutifully populates that *local* instance, which is discarded when the method returns (the method only returns `request_outputs`, not the stats). The orchestrator's object is never touched, so `self._stat_logger.record(scheduler_stats, iteration_stats, ...)` records an **empty** `IterationStats`.

That is exactly the symptom you observed:
- Everything derived from `iteration_stats` — `vllm:prompt_tokens_total`, `generation_tokens_total`, `request_success_total`, and all the latency histograms (TTFT/ITL/TPOT/e2e/queue/prefill/decode/inference) — reads **0/count=0/sum=0** for every stage.
- The buckets are still *registered* because the metric families are constructed at logger init (`OmniPrometheusStatLogger`), independent of whether any observation is recorded.
- The `vllm_omni:*` pipeline-level metrics work because they go through a completely different path (`omni_base.py` → `OmniPrometheusMetrics.request_succeeded()`), which never touches this broken object.

(Note: if this code path ever also fed the scheduler-derived gauges like `num_requests_running`/`waiting`/KV-cache usage, those come from `scheduler_stats` and would *not* be zeroed — only the `iteration_stats`-derived time/token families are affected. That matches your log exactly.)

### Fix

Delete the overwrite so the caller's object is populated, falling back to a fresh one only when nothing was passed:

```python
# vllm_omni/engine/stage_pool.py — replace line 1074
if iteration_stats is None:
    iteration_stats = IterationStats()
```

That one change restores per-stage `vllm:*` token and latency metrics with the `{replica, stage}` labels. Since `process_outputs` already handles `iteration_stats=None` gracefully (`output_processor.py:694`, `:725`), the direct/standalone callers of `process_llm_raw_outputs` (which don't pass the argument) keep working unchanged.

Worth adding a regression test alongside `tests/metrics/test_stat_logger.py` that drives `process_llm_raw_outputs` with a caller-supplied `IterationStats` and asserts it comes back non-empty (e.g. `num_generation_tokens > 0` after a finished request) — the current tests exercise the logger's relabeling but not this end-to-end stats plumbing, which is why the overwrite slipped through.

### Workaround until a release

There's no runtime workaround for the zeroed per-stage `vllm:*` metrics — the fix is a code change. In the meantime, use the `vllm_omni:*` pipeline-level metrics for E2E latency and token accounting, which are accurate.

### On the separate `vllm_omni:audio_ttfp_s` = empty observation

That one is **not** a bug, and @ZacheryAU's earlier comment is the correct answer: `audio_ttfp_s`, `audio_underrun_s`, and `audio_continuity_ok_total` are streaming-only metrics. Your repro sends non-streaming chat completions, so no first-audio-packet timing is ever produced. Re-run with `"stream": true` and those buckets will populate. So please split expectations: the all-zero `vllm:*` per-stage block is the real defect fixed above; the empty `audio_ttfp_s` is working as intended.

I'll keep this open and labeled `bug` and target the `stage_pool.py` one-line fix plus a regression test.