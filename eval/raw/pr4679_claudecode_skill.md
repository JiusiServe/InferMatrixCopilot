I now have a complete picture. Let me present the review.

---

## PR #4679 Review — Make speech streaming default to SSE

**PR:** [#4679](https://github.com/vllm-project/vllm-omni/pull/4679) by @syd520zy — **MERGED** (post-merge review)
**Status:** All CI green (DCO, pre-commit, build 3.11/3.12, buildkite, docs). 3 review rounds by @linyueqian, final: APPROVED.

### BLOCKER Scan

| Category | Result |
|----------|--------|
| Correctness | PASS — All 6 `stream` × `stream_format` combinations verified correct; `is_raw_audio_stream` / `is_sse_stream` / `is_streaming` truth table is sound |
| Reliability/Safety | PASS — `word_timestamps` guard now covers both raw audio and SSE paths |
| Breaking Changes | PASS — Intentional, well-documented, all in-repo consumers updated |
| Test Coverage | PASS — Unit tests cover all truth table combos + new helper dedup; e2e tests updated |
| Documentation | PASS — API doc table, response format docs, user guide, README, and recipes all updated |
| Security | PASS |

### Core Logic Verification

The three routing methods in `vllm_omni/entrypoints/openai/protocol/audio.py` are correct across all 6 combinations:

| `stream` | `stream_format` | `is_raw_audio_stream()` | `is_sse_stream()` | `is_streaming()` |
|----------|----------------|------------------------|-------------------|-----------------|
| false | None | false | false | false |
| true | None | false | **true** | true |
| false | `"audio"` | true | false | true |
| true | `"audio"` | true | false | true |
| false | `"sse"` | false | true | true |
| true | `"sse"` | false | true | true |

The `word_timestamps` guard hoisting in `serving_speech.py:4063` is correct — it now rejects `word_timestamps=true` for all HTTP streaming modes (both SSE and raw audio), which is more correct than the old code that only guarded the raw audio path.

### Finding: Missed consumer in Voxtral recipe

`recipes/mistralai/Voxtral-TTS.md:78-95` — The "Streaming PCM" curl example sends `"stream": true` with `"response_format": "pcm"` but is missing `"stream_format": "audio"`. After this PR, that request returns `text/event-stream` SSE instead of raw PCM, and the subsequent `ffmpeg -f s16le` at line 93 will choke on SSE text.

The PR did update the second streaming example later in the same file (line 156 in the new version), but this first one was missed.

```bash
# Line 83-91 — missing "stream_format": "audio"
  -d '{
    "model": "mistralai/Voxtral-4B-TTS-2603",
    "input": "Hello, this is Voxtral TTS streaming PCM on an NVIDIA GeForce RTX 5090.",
    "voice": "casual_female",
    "language": "English",
    "stream": true,
    "response_format": "pcm"          # ← needs "stream_format": "audio",
  }' \
```

### Recommended Verdict: APPROVE with follow-up fix

The core change is correct and well-tested. The one missed recipe example is a docs-only issue — no runtime code is affected. A follow-up PR to add `"stream_format": "audio"` to `recipes/mistralai/Voxtral-TTS.md` line 89 is all that's needed.