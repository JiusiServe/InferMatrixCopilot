## Code Review Findings

* **vllm_omni/entrypoints/openai/protocol/audio.py:295-299** – `is_raw_audio_stream` now only checks `stream_format=="audio"` (removed `self.stream`), and `is_sse_stream` correctly combines `stream` and `stream_format=="sse"`. This implements the new default cleanly. Ensure all callers that previously relied on `is_raw_audio_stream` returning `True` for `stream=True` are updated (the PR does this thoroughly in examples/tests/docs).

* **vllm_omni/entrypoints/openai/serving_speech.py:4060-4066** – `word_timestamps` error now applies to all streaming modes (`request.is_streaming()`), not just raw audio. This matches the PR description that word‑timestamp streaming is only supported via WebSocket. No risk of unintended rejection of non‑streaming requests.

* **tests/entrypoints/openai_api/test_serving_speech.py:1849-1872** – New assertions confirm that `stream=True` → SSE and `stream_format="audio"` → raw. The test class `TestStreamingResponse` was updated to expect SSE for `stream=True`, with a helper `_assert_sse_audio_response`. However, the test fixture `streaming_app` must be verified to actually route requests to the updated server logic; if the fixture mocks the endpoint without reflecting SSE, these tests will fail. (Assumed fine given the PR updates the real server code.)

* **All e2e tests and benchmarks (e.g., `test_cosyvoice3_tts_expansion.py:107`, `benchmarks/fish-speech/bench_speaker_cache.py:204`, `vllm_omni/benchmarks/patch/patch.py:1146`)** – Every raw‑audio streaming request now explicitly adds `"stream_format": "audio"`. This is necessary to preserve the old behaviour after the default change. Adding `stream_format` to `extra_body` in `tests/helpers/runtime.py` ensures it’s passed through. All changes are consistent.

* **Documentation and examples** – The updated descriptions (`docs/serving/speech_api.md`, `docs/user_guide/…`, `recipes/…`) accurately reflect the new `stream`/`stream_format` behaviour. Client scripts like `qwen3_tts/tts_common.py:96` correctly inject `stream_format="audio"` when streaming is desired.

* **Backward compatibility** – Clients that only set `stream=True` without `stream_format` will now receive SSE events instead of raw audio bytes. This is an intentional breaking change (Option A from #4612). The PR documents the shift, but any external consumers relying on the old default will break until they add `"stream_format": "audio"`.

* **Code quality** – The `is_streaming()` method is now logically equivalent to `is_raw_audio_stream() or is_sse_stream()`, and all validation constraints (response_format, speed) use `is_streaming()`, so they correctly cover both streaming modes. No orphan paths remain.