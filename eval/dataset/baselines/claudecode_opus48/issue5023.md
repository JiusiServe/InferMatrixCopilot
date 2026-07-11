I now have a complete, code-grounded picture from three independent investigations plus my own reading. Here is the maintainer answer.

---

## Answer to vllm-project/vllm-omni#5023

Thanks — this is an unusually well-constructed report (50 runs, 0 failures, and a genuine attempt to isolate a duration-independent signal). Let me answer both asks directly, then give you a concrete way to separate the two effects, because I think they're entangled in a way the current data can't split.

### First, a caveat about the "TTFP is duration-independent" premise

The benchmark's TTFP is measured purely as *wall-clock from just-before-HTTP-send to the first non-empty PCM byte* off the streamed body — see `async_request_openai_audio_speech` in `vllm_omni/benchmarks/patch/patch.py:1166` (`st = time.perf_counter()`) and `:1180-1183` (`output.audio_ttfp = timestamp - st` on the first chunk). It never reads total output length, so you are right that the **metric formula** is output-duration-independent.

But that does **not** make it empirically decoupled from output length at fixed concurrency. Concurrency is enforced by a client-side `asyncio.Semaphore(max_concurrency)` (`patch.py:1461-1465`); the slot is held for the *entire* request. So at fixed `max_concurrency=N`, N requests are always in flight on the server, and TTFP for any one of them still spans *server admission → scheduler queue → prefill/first-decode → first vocoder chunk*. Longer outputs keep every one of those N slots occupied longer, which deepens the queue that a newly-admitted request's first packet has to clear. **That is a real coupling channel, and the send→first-byte number alone cannot distinguish it from a "pure" scheduler regression.** This turns out to be central to your Hypothesis #3, which I'd promote from "worth ruling out" to "probably a primary driver."

### How Qwen3-TTS produces the first packet (so the mechanisms make sense)

Qwen3-TTS runs as two stages (`vllm_omni/model_executor/models/qwen3_tts/pipeline.py:16-56`): **stage 0 talker** (autoregressive codec-token generation) → SharedMemoryConnector → **stage 1 code2wav** (codec→PCM vocoder). In the shipped configs this streams chunk-by-chunk (`async_chunk: true`). So:

```
TTFP ≈ talker prefill + talker generates the first codec window
        + connector first-chunk handoff + one code2wav decode
```

The serving layer itself adds no buffering — `_generate_audio_chunks` (`vllm_omni/entrypoints/openai/serving_speech.py:2700-2797`) yields each vocoder chunk as raw PCM the moment it's decoded (only a WAV header precedes the first chunk). So the knee is upstream of the HTTP layer, in the talker/connector/vocoder scheduling.

### Ask 1 — scheduler/streaming changes that would explain the c≥8 knee

Three compounding, concurrency-sensitive mechanisms, all present in current `main`. I only have a post-merge checkout (not a v0.22↔v0.24 diff), so I'm pointing at the code that *controls* each effect and the exact things to diff.

**(1) The sharp cliff shape (c8→c16 is ~6×: 223ms→1297ms) looks like capacity saturation, not a smooth prefill slowdown.** The generation scheduler admits a new request only while `len(self.running) < self.max_num_running_reqs` (`vllm_omni/core/sched/omni_generation_scheduler.py:149-153`), and the high-concurrency profile deliberately caps the vocoder at **`max_num_seqs: 10`** with `decode_batch_max_size: 1`, `enforce_eager: true` (`vllm_omni/deploy/qwen3_tts_high_concurrency.yaml:75,43,77`). Once offered concurrency exceeds the effective per-step batch capacity, new requests queue for a running slot and their first packet can't be produced until an earlier one frees it — TTFP then grows roughly linearly past the knee, which is exactly what your table shows. **Check the effective `max_num_seqs` on both stages in the config the v0.24.0 image actually loads.**

**(2) Dynamic initial-chunk sizing — a config-dependent TTFP-vs-concurrency ramp.** `compute_dynamic_initial_chunk_size` (`vllm_omni/model_executor/stage_input_processors/chunk_size_utils.py:12-33`), called at `stage_input_processors/qwen3_tts.py:102-113`, scales the *first* codec window emitted to the vocoder by `load_factor = active_requests / max_num_seqs`:

```python
load_factor = min(active_requests / max_num_seqs, 1.0)
idx = int(round(load_factor * (len(steps) - 1)))   # steps = [2,4,8,16] for codec_chunk_frames=25
```

Low load → IC=2 frames (fast first packet); high load → up to IC=16 frames. At 12 Hz that pushes the first-packet threshold from ~2 frames to as much as ~16 frames of talker generation → hundreds of ms to >1s of extra time-to-first-packet, *by design*. **Crucially, this ramp only runs when `initial_codec_chunk_frames` is not pinned** — `fixed_initial_chunk_size` at `qwen3_tts.py:88,103`. Both shipped profiles pin `initial_codec_chunk_frames: 1` (`deploy/qwen3_tts.yaml:29`, `qwen3_tts_high_concurrency.yaml:34`), which *bypasses* the ramp. So: **if the v0.24.0 default deploy config for `Qwen3-TTS-12Hz-*` dropped that pin (or this dynamic-IC feature landed in v0.24), TTFP degrades with concurrency by construction.** This is the single highest-value thing to diff between the two images. (Note: with `max_num_seqs=64` the ramp is mild — IC≈4 at c=25 — so on its own it doesn't fully explain the cliff; it's an amplifier on top of (1).)

**(3) Longer outputs feed (1) and (2) — the duration↔TTFP coupling.** In the default single-GPU `deploy/qwen3_tts.yaml`, both stages sit on `devices: "0"` at `gpu_memory_utilization: 0.3` each (`:39,50,71,83`), so talker decode and vocoder decode contend for the same SMs; the schedulers are single-threaded and share each step (`omni_generation_scheduler.py:442-447`). ~30% longer talker output (your 8.0s vs 6.2s) means ~30% more decode steps per request, which (a) raises `active_requests` feeding the dynamic-IC load factor, (b) holds each vocoder slot longer, deepening the queue in (1), and (c) keeps the shared GPU busier during the vocoder step that emits the first packet. **This is why I'd treat your Hypothesis #3 as a leading contributor rather than an also-ran** — and it's inseparable from a "pure" scheduler regression using send→first-byte alone.

### Ask 2 — is the audio-duration change (6.2s → 8.0s) intentional?

Almost certainly **not** an intended feature; it points to the talker emitting codec-EOS *later* on v0.24. Duration = codec-frames-before-stop ÷ 12 Hz, so 6.2s≈74 frames vs 8.0s≈96 frames is ~+22 frames (~+30%) of generation before stop. The controlling knobs are the stage-0 sampling defaults in `deploy/qwen3_tts.yaml:53-61`:

- **`repetition_penalty: 1.05` is the prime suspect.** The codec-EOS is a *normal* id in the talker vocab and is explicitly allowed by the logit mask (`qwen3_tts_talker.py:413-422`, `codec_eos_token_id`, default 4198 in `configuration_qwen3_tts.py`). vLLM applies the repetition penalty over accumulated output ids, so as codec tokens pile up the EOS logit gets relatively suppressed → later EOS → longer audio. A `1.0`→`1.05` bump lengthens every clip systematically.
- **`temperature: 0.9` / `top_k: 50`** raise sampling entropy and also delay EOS selection.
- Secondary: confirm `stop_token_ids: [2150]` (`pipeline.py:32`) still matches the loaded checkpoint's real stop id and is consistent with `codec_eos_token_id=4198`; a drift there would let the talker run toward the `max_tokens: 4096` fallback.

This deserves its own bug. It's the same "talker stops too late on 0.24" family as the earlier report of Base voice-clone running all the way to `max_tokens` without EOS on 0.24 — this looks like a milder, systematic version of that.

### How to A/B this cleanly (and pin old behavior)

1. **Kill the concurrency ramp:** run with `initial_codec_chunk_frames: 1` pinned (as `deploy/qwen3_tts.yaml` does) or pass it per-request. If the c≥8 knee flattens, mechanism (2) is confirmed and it's a config regression.
2. **Pin output length for comparability:** set identical stage-0 sampling params on both images (start with `repetition_penalty=1.0`, and fix `temperature`/`top_k`/`max_tokens`). If TTFP at c≥8 converges once mean audio duration matches, the regression is duration-coupled (mechanism (3)), not a standalone scheduler change.
3. **Remove stage co-location:** run `vllm_omni/deploy/qwen3_tts_high_concurrency.yaml` (talker on GPU0, vocoder on GPU1, S1=10, fixed IC). This is the intended high-concurrency profile and isolates talker↔vocoder SM contention.
4. **Diff the actual default config the v0.24.0 image loads** for `Qwen3-TTS-12Hz-*` against v0.22.0 — specifically the connector `extra` block (`codec_chunk_frames`, `initial_codec_chunk_frames`, `connector_get_max_wait*`) and stage-0 `default_sampling_params`. That one diff will localize both the TTFP ramp and the duration change.
5. **On `--gpu-memory-utilization 0.45`:** the shipped single-GPU profile budgets 0.3+0.3=0.6 across the two co-located stages. Running 0.45 changes KV headroom and can shift batching/preemption at high c, so for an apples-to-apples v0.22 vs v0.24 comparison, match the shipped split rather than a custom 0.45.

### Disposition

Keeping this **open** and labeling it `performance-regression` + `needs-bisect`. Two separable follow-ups look warranted: (a) whether the default deploy config for the stock image should pin `initial_codec_chunk_frames` (and whether the dynamic-IC high-load ramp is too aggressive for real-time serving), and (b) the talker EOS/duration change via sampling defaults. If you can run steps 1–2 above and post the config from `wget .../collect_env.py` (or just the resolved deploy YAML the image uses) plus the mean audio-duration column alongside the TTFP column, that will let us bisect quickly — and re-testing on the latest `main` commit (per @amy-why-3459's note) is worth doing first, since the EOS behavior may already have a follow-up fix. Happy to drive the bisect from our side once we know which config path the image takes.