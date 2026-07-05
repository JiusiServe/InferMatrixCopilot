Verification complete. Here is my final review.

---

# Review — PR #4679: "Make speech streaming default to SSE"

**Repo:** `vllm-project/vllm-omni` · **State:** MERGED · **Author:** syd520zy · `+146 / −58`, 39 files · base `main`
Reviewed against the post-merge checkout at `/rebase/vllm-omni`. *(Not posted to GitHub, per request.)*

## Recommended verdict: **APPROVE** (one minor inline fix worth a follow-up)

Clean, well-scoped implementation of Option A from #4612. The core is a small, correct logic edit; the rest is a mechanical migration of in-repo raw-audio consumers to the explicit `stream_format="audio"` opt-in. Unit-test coverage of the new dispatch matrix is thorough. One doc example was missed by the migration (below).

## Blocker scan

| Category | Result |
|---|---|
| Correctness | PASS — dispatch logic verified against the PR's behavior table |
| Reliability/Safety | PASS — exhaustive dispatch, no fall-through |
| Breaking Changes | INTENTIONAL — `stream=True` flips raw-audio → SSE (reverses #4490); documented + acknowledged |
| Test Coverage | PASS (unit); e2e configs updated but not executed (acknowledged) |
| Documentation | ISSUES — one un-migrated streaming curl example (see comment) |
| Security | PASS |

## Comments

**`recipes/mistralai/Voxtral-TTS.md:88`** *(the one real fix)*
```
    "stream": true,
    "response_format": "pcm"     # RTX 5090 "Streaming PCM" block, --output …pcm + ffmpeg -f s16le
```
Missed by the migration — needs `"stream_format": "audio",` here. After this PR `stream=true` alone returns `speech.audio.*` SSE, so this block writes event-stream text into `/tmp/voxtral_5090_stream.pcm` and the raw-PCM `ffmpeg -f s16le` decode (line 93) breaks. The sibling "Streaming audio" block at lines 147–159 in the RTX 4090 section already sets `stream_format="audio"` — same fix here.

**Non-blocking notes**

1. Public-API default change — worth a CHANGELOG/migration note. External clients sending `stream=True` expecting raw PCM/WAV now silently get `text/event-stream`. All in-repo consumers are migrated, but downstream integrators aren't warned; `docs/serving/speech_api.md` documents the new behavior but doesn't flag it as a break from #4490.
2. E2E not run. The response content-type/body contract changes here; a one-model smoke over both paths (raw + SSE) is the ideal evidence. Since it's merged, a `merge-test` CI run covers it.

## What I verified
- **Logic** (`protocol/audio.py:296-303`): truth table matches the PR behavior table exactly, incl. `stream=True + stream_format="audio"` → raw (short-circuit). SSE path still runs `_validate_speech_streaming_request` (`serving_speech.py:4092`), so pcm/wav + `speed==1.0` are enforced for SSE too; `word_timestamps` guard (`:4063`) now correctly rejects all streaming; no dispatch fall-through.
- **Migration completeness** (my sweep + an independent sweep agent): all standalone streaming clients, gradio demos (via in-file or `tts_common.build_payload`), `benchmarks/patch/patch.py` incl. the Seed-TTS WER path, and ~20 e2e + unit tests are correctly updated. WebSocket `/v1/audio/speech/stream` clients and `/v1/chat/completions` omni tests are a different path and unaffected. **The only un-migrated raw-audio consumer is the Voxtral recipe block above.**