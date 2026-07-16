## Final Review

`vllm_omni/entrypoints/openai/serving_speech.py:4063` [normal] — The `word_timestamps` rejection was broadened to all streaming paths. Add a matching check in `validate_streaming_constraints` (in `audio.py`) to raise a 422 at parse time for `word_timestamps=true` + any streaming request, keeping error reporting consistent with other streaming constraints.

`vllm_omni/benchmarks/patch/patch.py:1147` [normal] — The `stream_format="audio"` assignment happens before `_update_payload_common`, risking it being overwritten if the helper ever sets a different format. Move the assignment to **after** the common-update call in both the main payload and the Seed-TTS branch so it remains the final word.

`vllm_omni/entrypoints/openai/protocol/audio.py:297` [normal] — The precedence logic in `is_sse_stream()` relies on `not self.is_raw_audio_stream()` to prevent `stream=True` from overriding an explicit `stream_format="audio"`. Add a short comment above the method explaining this intentional short-circuit, as it is the only guard against `stream=True` changing an explicit raw-audio opt-in.

`docs/serving/speech_api.md:125` [nit] — The `stream_format` row still says “If omitted, `stream=true` selects SSE …”. Replace that phrase with “When `stream=true`, the default is `sse`; use `stream_format='audio'` to override.” This makes the row self-contained and eliminates the lingering “omitted” ambiguity.

`tests/e2e/online_serving/test_qwen3_tts_base.py:100-103` [unverified] — The test was updated to include `stream_format="audio"`, but it is unclear whether any other e2e test sends `stream=true` without `stream_format` via a raw `httpx` call (bypassing the helper) and depends on the old raw-audio behavior. Verify that all such paths now explicitly opt in to raw audio.

`tests/helpers/runtime.py:1772` [unverified] — The helper now forwards `stream_format`, but any test that calls the endpoint directly with `httpx` and passes `stream=true` without `stream_format` may silently receive SSE instead of raw audio. Confirm that no raw-audio test uses a direct client without updating the payload.

**Verdict: APPROVE**  
The core change is correctly implemented and tested. The above suggestions improve clarity, error-surface consistency, and test robustness, but none are blocking.