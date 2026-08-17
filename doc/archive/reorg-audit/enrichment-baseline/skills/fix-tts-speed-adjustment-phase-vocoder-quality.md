---
name: fix-tts-speed-adjustment-phase-vocoder-quality
description: Voxtral TTS test_speech_speed fails at speed>=2.0 on non-H100 hardware — KNOWN UPSTREAM BUG awaiting a main-branch PR. Do NOT modify the test or apply local workarounds in the rebase branch.
trigger: test_speech_speed in test_voxtral_tts.py fails at speed >= 2.0 with ASR cosine similarity below 0.9 (typically 0.5-0.75). Transcript garbled, e.g. 'with the Blue\'s Air with the Sun Rose'. Files are byte-identical to origin/main.
modules: [input_output, entrypoints]
status: active
created_at: 2026-06-10
last_used_at: 2026-07-11
run_count: 37
---

## Status: known upstream bug — do NOT "fix" locally

This failure is a **pre-existing defect in upstream vllm-omni main**, not a rebase regression. A proper fix is being submitted as a PR to main (replace the phase vocoder with ffmpeg `atempo`/WSOLA via PyAV — see Background). Until that PR lands and is pulled in by a rebase:

- Do NOT edit `tests/e2e/online_serving/test_voxtral_tts.py` (e.g. removing speeds 2.0/2.5). The test must stay byte-identical to origin/main.
- Do NOT re-apply any multi-pass decomposition in `vllm_omni/entrypoints/openai/audio_utils_mixin.py`. Both variants have been tried and do NOT fix the test:
  - 2026-06-10: sqrt decomposition (split until each pass <= 2.0x) — improved similarity 0.50 → 0.75, still below 0.9.
  - 2026-06-28: n-th-root decomposition with `MAX_PASS_RATIO = 1.4` — reached 0.88, still below 0.9. Reverted.
- This is also the single skill for this failure. A duplicate skill `fix-audio-stretching-sqrt-decomposition` was created on 2026-06-28 advising the opposite (apply the decomposition); it was deleted as wrong. Do not recreate it.
- Treat this failure as a known/expected baseline failure for this test on non-H100 hardware and report it as such instead of patching.

## Confirmed recurrences
- 2026-06-11: speed=2.5, similarity=0.499, transcript="with the Blue's Air with the Sun Rose."
- 2026-06-12: speed=2.5, similarity=0.499, transcript="with the Blue's Air with the Sun Rose." (4th recurrence)
- 2026-06-28: build #2423, similarity=0.88, transcript="The boy was there in the sun rose." The agent wrongly treated this as actionable (CI baseline-matching bug misclassified it) and applied an n-th-root decomposition fix; both that fix and the test retry were reverted.
- Files verified byte-identical to origin/main via `git diff`.
- Test is annotated `@hardware_test(res={"cuda": "H100"})` — only expected to pass on H100.

## Diagnose (to confirm this skill applies)

1. Failure is `test_speech_speed` at speed >= 2.0; lower speeds pass.
2. Confirm `_apply_speed_adjustment` in `audio_utils_mixin.py` and the test file are identical to origin/main (`git diff` is empty). If they differ, this is NOT this skill — investigate the diff instead.
3. Check whether the upstream fix PR has landed (look for WSOLA/atempo in `_apply_speed_adjustment`). If it has and the test still fails, this skill is stale — re-debug from scratch.

## Background / root cause

- `_apply_speed_adjustment` uses torchaudio's phase vocoder (Spectrogram → TimeStretch → InverseSpectrogram). At stretch ratios >= 2.0-2.5x it produces artifacts that make speech unintelligible to Whisper ASR.
- The pass criterion (transcript trigram-cosine >= 0.9) sits right at the quality cliff: upstream CI (H100 + vLLM v0.22.0 release) lands just above the threshold; this rebase environment (L20X + nightly vLLM wheel) lands well below (0.50). Same code, different environment → main CI green, local red.
- The test was added upstream the same day it first ran here (aa92a3a3 [CI/Build] Voxtral TTS Tests #3738) and was never validated off-H100.
- Validated proper fix (for the main-branch PR, not the rebase branch): ffmpeg's `atempo` filter via PyAV (already a vLLM dependency) is WSOLA-based, preserves pitch (verified 440 Hz → 440 Hz at 2.5x), keeps clean amplitude, and is designed for speech tempo change up to 100x. torchaudio.sox_effects is unavailable (removed in torchaudio 2.11); librosa is banned by pyproject.
