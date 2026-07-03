I now have a thorough understanding of the PR. Let me compile the blocker scan and write the review.

---

## BLOCKER Scan

| Category | Result |
|----------|--------|
| Correctness | PASS — `is_raw_audio_stream()`, `is_sse_stream()`, and `is_streaming()` logic is internally consistent and matches the PR description's behavior table. The `word_timestamps` check hoisting (from raw-audio-only to all streaming) is intentional and correct. |
| Reliability/Safety | PASS — No resource leaks, race conditions, or missing guards. `_assert_sse_audio_response` helper extracts cleanly shared assertion logic. |
| Breaking Changes | PASS — `stream=True` now returns SSE instead of raw audio. This is intentional, documented in the PR body, and all in-repo consumers (examples, benchmarks, e2e tests, recipes, docs) have been updated to pass `stream_format="audio"` where they expect raw bytes. |
| Test Coverage | Minor gaps (non-blocking): no explicit unit test for `stream=True` + `word_timestamps=true` rejection on the SSE path. E2E updates are semantically correct but were not hardware-validated per the PR notes. |
| Documentation | PASS — `speech_api.md`, user guide, recipe files, and example READMEs are all updated consistently. |
| Security | PASS — No security-relevant changes. |

---

**No blockers.** The core change is a clean 3-method refactor in `protocol/audio.py` plus a hoisted `word_timestamps` gate in `serving_speech.py`. All in-repo consumers are updated. Tests verify the new behavior matrix explicitly.

Two non-blocking observations:

**`tests/entrypoints/openai_api/test_serving_speech.py`** — The word_timestamps rejection gate was hoisted from the raw-audio branch to apply to all streaming modes. The SSE path now correctly rejects `word_timestamps=true`, but there's no unit test covering that specific combination (`stream=True` + `word_timestamps=true` → error). The existing `test_sse_rejects_unsupported_response_format` and `test_sse_rejects_speed_adjustment` cover the other validation paths. Adding one for `word_timestamps` would close the coverage gap.

**`tests/helpers/runtime.py:1773`** — Adding `stream_format` to the `extra_body` allowlist in `send_audio_speech_request` is essential: without it, the e2e test configs that now set `"stream_format": "audio"` would silently drop the field, and `stream=True` would route through SSE instead of raw audio, likely breaking those tests. This is correct.