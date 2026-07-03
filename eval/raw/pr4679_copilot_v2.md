## Final Review

### Findings

**`tests/e2e/online_serving/test_indextts2.py:6`** [nit] — The module docstring still references the old `stream=True` compatibility path. After this PR `stream=True` defaults to SSE, and the test explicitly opts into raw audio via `stream_format="audio"`. Update the module and function docstrings to say the test explicitly requests raw audio streaming with `stream_format="audio"`.

**`vllm_omni/entrypoints/openai/serving_speech.py:4154` (and nearby log statements)** [nit] — The success/cancelled/error log messages in `_generate_audio_chunks` hardcode `stream=true`, but this function is now called for both raw-audio and SSE streaming paths. Replace the hardcoded `stream=true` with the actual streaming mode or a neutral label like `streaming=true` to avoid misleading operators.

**`vllm_omni/entrypoints/openai/serving_speech.py:4063`** [nit] — The `word_timestamps` guard was moved from inside the raw-audio-only block to `request.is_streaming()`, so SSE streaming requests now also explicitly reject `word_timestamps=true`. This is a deliberate expansion, but the PR description’s behavior table does not mention it. Add a note in the endpoint’s docstring or the PR summary that SSE streaming also rejects `word_timestamps=true`, as this changes the error surface for consumers.

**`tests/e2e/online_serving/test_voxtral_tts_expansion.py:56-63`** [unverified] — The test sends `stream=True, stream_format="audio", response_format="pcm"` and checks `min_audio_bytes`. Confirm this passes against a live Voxtral server to ensure raw audio streaming still works after the default flip to SSE.

**`vllm_omni/entrypoints/openai/serving_speech.py` (inside `_generate_audio_sse_events`)** [unverified] — When a `CancelledError` occurs, the function re-raises without yielding a terminal `speech.audio.error` SSE event, unlike the `Exception` path. Verify that this is intentional (the client connection is already gone) or document whether a terminal event is needed for proxy/caching consistency.

---

**Verdict:** APPROVE