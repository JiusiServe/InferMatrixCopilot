---
name: fix-tts-realtime-asr-accuracy-flake-whisper-small
description: A TTS/realtime audio accuracy assertion fails "transcript should match model text (sim<threshold)" because whisper-small MISHEARS the generated audio (esp. short Chinese clips), not because the model regressed. Retry passes. Grade with whisper large-v3 instead.
trigger: An audio/tts/realtime test (e.g. test_qwen3_omni_realtime_websocket, *_tts) fails with AssertionError "Output audio transcript should match model text (sim=0.XXX)" or similarity/SSIM-style text mismatch; the run-immediately retry PASSES; the whisper transcript is garbled vs the model text.
modules: [online_serving]
status: active
created_at: 2026-07-11
last_used_at: 2026-07-11
run_count: 3
---

## Diagnose
1. The failure is an `AssertionError` comparing a Whisper transcription of the generated audio against the model's own text stream via `cosine_similarity_text(...)`, e.g. `sim=0.443, whisper='韦京,他是文化和政治的中心', model_text='北京是中国的首都。它是文化和政治的中心。'`.
2. Confirm the grader is **whisper-small**: `tests/helpers/media.py::convert_audio_bytes_to_text(..., model_size="small")` is the default. small mishears short Chinese TTS clips (observed 北京→韦京, dropped leading sentence) and is nondeterministic.
3. Confirm it is flaky, not a regression: the immediate retry passed (e.g. `15 passed` where attempt 0 had `1 failed`), and the audio smoke asserts (`len(out_pcm) >= 4096`, `delta_events >= 1`) passed — audio generation was fine; only the ASR grade varied.
4. This is an ASR grader flake, **not** a model/rebase regression. Same class as the Higgs-Audio-V3 "Shhh!" similarity<0.9 flake.

## Fix
Grade the accuracy assertion with **whisper large-v3**, which transcribes these clips reliably where small mishears (large-v3 is cached at `~/.cache/whisper/large-v3.pt` on the H200 host):
```python
# in the accuracy helper (e.g. _assert_realtime_accuracy):
whisper_text = convert_audio_bytes_to_text(wav_out, model_size="large-v3").strip()
```
`convert_audio_file_to_text`/`convert_audio_bytes_to_text` already thread `model_size` through to `whisper.load_model(model_size)` and run it in a spawn subprocess on the spare GPU (device n-1 on a 2-card runner). After the change, a failure here genuinely points at the model, not the grader.
- Optionally also add bounded in-test reruns for async/chunked modes where codec pacing adds variability.
- If the test is not yet fixed and is blocking a rebase, treat this specific assertion as a known ASR flake (do not hard-pause on a lone sim<threshold miss whose retry passes).

## Verification
Re-run on 2×H100 (GPU 0,1), which serves the model and grades with large-v3:
```bash
cd /rebase/vllm-omni && CUDA_VISIBLE_DEVICES=0,1 /rebase/.venv/bin/python -m pytest -s -v \
  tests/entrypoints/openai_api/test_qwen3_omni_realtime_websocket.py \
  -m "advanced_model and cuda and H100" --run-level advanced_model
```
Expect the accuracy assertion to pass (confirmed: `2 passed` async_chunk + sync with large-v3, where whisper-small had failed async_chunk at sim=0.443).

## Anti-patterns
- **DO NOT grade audio accuracy with whisper-small** — it mishears short/Chinese clips.
- **DO NOT lower the similarity threshold** to swallow a whole-sentence ASR miss — that guts the test's signal. Fix the grader model instead.
- **DO NOT classify a lone sim<threshold audio-accuracy failure as a model regression** or hard-pause the rebase on it, especially when the immediate retry passes and the smoke asserts pass.
