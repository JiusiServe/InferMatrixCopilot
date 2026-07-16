## Review

### High-level

The change is deliberate and well-documented. It updates the server, tests, examples, benchmarks, and docs to default `stream=True` to SSE and require `stream_format="audio"` for the old raw-byte path. The protocol model and serving logic reflect the new semantics correctly. The risk lies in the breadth of the mechanical updates: 35+ files touched, and the PR description states that **full e2e tests were not run**. That’s a gap before merging, but the modifications themselves are low-risk.

### Blocker scan

| Category            | Result |
|---------------------|--------|
| Correctness         | PASS — logic in `is_raw_audio_stream()`, `is_sse_stream()`, `is_streaming()` matches the stated behavior matrix. Validation and error checks are consistent. |
| Reliability/Safety  | PASS — no resource or concurrency issues introduced. |
| Breaking Changes    | PASS (**deliberate**) — `stream=True` now returns SSE instead of raw audio. Clients must opt back in with `stream_format="audio"`. |
| Test Coverage       | PASS — new protocol tests cover the updated model and streaming dispatch. E2E request configs and a test helper were updated, but the PR states they were not executed locally. |
| Documentation       | PASS — API docs, user guides, and recipes all reflect the new default. |
| Security            | PASS — no security impact. |

### Recommended actions before merge

- **Run the affected e2e tests** — the configs were changed but not validated against a live server. At minimum, execute the streaming-dependent tests for one or two model families (e.g., Qwen3-TTS, Fish Speech) to confirm the `stream_format` payload reaches the server and returns raw audio.
- **Verify the benchmark benchmark** — `vllm_omni/benchmarks/patch/patch.py` now sets `stream_format="audio"`; ensure the benchmark still measures TTFP correctly.

### Observations

- The word-timestamp rejection moved from inside `is_raw_audio_stream()` to a broader `is_streaming()` gate. This now correctly applies to SSE streaming as well, closing a gap where SSE could previously pass `word_timestamps` through HTTP (unsupported). Clean fix.
- The new test `test_stream_true_with_stream_format_sse_uses_sse` verifies that the combination works, and `test_stream_format_audio_with_stream_true_opts_into_raw_audio` confirms explicit raw audio override — both good.
- The diff updates every in-repo raw-audio consumer to explicitly include `"stream_format": "audio"`. No stray `stream=True` without the opt-in remains.

The change is ready to land after the e2e smoke test. No blocking issues.