I have what I need. Here is my maintainer's answer to issue #4815.

---

## Response to #4815 — Qwen3-TTS Base voice-clone (ICL) runs to `max_tokens` without EOS on vLLM 0.24

**Verdict: closing as not-reproducible was the right call, and I'd keep it closed.** 55/55 clean back-to-back trials on a fresh checkout + fresh editable install, across both `main` (`e4a2d367`) and #4559's head (`289107b1`), with zero runaways, is strong negative evidence. The most self-consistent explanation is the one @linyueqian already landed on: a long-lived session with repeated hot-patches, dependency swaps, and *at one point a shared GPU with another process* — i.e. a corrupted/contended runtime state, not a 0.24-vs-0.23 code regression. That said, the isolation work in the report is good enough that it's worth recording *why* the symptom is plausible, so we recognize it fast if it ever recurs.

### The isolation is architecturally sound, which is why it looked like a real bug

The two "fixes" the reporter found aren't arbitrary — they line up exactly with how completion is signaled in each path:

- **ICL/`task_type=Base` with `ref_audio`:** the whole reference (codes + text) and the target text are baked into the *prefill*, and the talker is expected to recognize "text is done → emit codec EOS" purely through attention over that prefill. There is **no decode-time completion cue**.
- **`x_vector_only_mode: true`:** completion is driven by an explicit per-step signal. In `qwen3_tts_talker.py:770-796`, the streaming path walks `talker_text_offset` through the trailing text and, once `text_offset >= tail_len`, switches the text stream to `tts_pad_embed`. That pad transition is a strong, deterministic "text exhausted" cue that pushes EOS — so this path stops robustly even if the acoustic model is a bit off.

So the ICL path is genuinely the more fragile one for *emitting* EOS, and it's the only path that would expose a subtle numerical perturbation in the backbone forward. That matches `enforce_eager: true` being the other thing that fixed it: stage 0 runs cudagraph/`torch.compile` by default on GPU (`deploy/qwen3_tts.yaml:11`, and `stage_config.py` leaves `enforce_eager`/`compilation_config` unset so the GPU path inherits vLLM 0.24's compiled defaults; only the NPU block pins `cudagraph_mode: PIECEWISE`). Ruling out chunked prefill (prefill was well under `max_num_batched_tokens=32768`) but not `enforce_eager` correctly narrows it to the *compiled* forward, not vllm-omni's prompt construction.

### Why "intermittent" + "then never reproduces" fits a runtime-state fluke, not a regression

Stage 0 samples with **`temperature: 0.9, top_k: 50, repetition_penalty: 1.05`** (`deploy/qwen3_tts.yaml:53-61`). EOS in the ICL path is a comparatively low-probability event whose logit is held up by attention over the prefill. Codec EOS *is* reachable — `_codec_eos_token_id` (2150) loads in range and the constant logit mask explicitly whitelists it (`qwen3_tts_talker.py:300, 413-422`), consistent with the reporter's finding. But with stochastic sampling, a *small* systematic depression of the EOS logit (a few tenths of a nat) is enough to occasionally miss EOS and fall into a repetition attractor — which is exactly the degenerate "Hello. Hello. My name. My." stutter that runs to 4096 tokens. A mild `repetition_penalty` of 1.05 won't pull the model out of that once it's in. That's a hallmark of a *transient* numerical perturbation (stale captured graph buffers, GPU memory contention from the co-tenant process), and it explains perfectly why a clean environment gives 55/55: the perturbation was in the session state, not the code.

### One genuinely sharp edge nearby — related, but *not* the cause

There is a documented determinism caveat in this exact area worth being aware of: under **full** cudagraphs the runner wraps `talker_mtp` with a single captured RNG stream, so per-request `tts_local_seed` seeding is silently dropped (`qwen3_tts_talker.py:327-350`, TODO #4923). That affects *reproducibility of which token is sampled*, not the EOS logit itself, so it isn't the runaway's root cause — but it's the same "compiled path changes sampling behavior for this backbone" family, and if this ever recurs it's the first place I'd instrument.

### If it recurs — a concrete, low-cost diagnostic path (don't ship `enforce_eager` broadly)

I agree with the reporter that blanket `enforce_eager` on stage 0 is the wrong fix — it forfeits the compile/graph speedup for *every* voice-clone request. Better next steps, in order:

1. **Confirm it's full-cudagraph-specific, not compile-specific.** Try `--stage-overrides '{"0": {"compilation_config": {"cudagraph_mode": "PIECEWISE"}}}'` (the NPU path already runs PIECEWISE) *before* reaching for `enforce_eager`. If PIECEWISE is clean, you keep most of the speedup and you've localized it to full-graph capture/replay for this backbone.
2. **Instrument the EOS logit at the sampler for the ICL request**, compiled vs eager, per decode step near where the model *should* stop. If the codec-EOS logit is systematically lower under the compiled path right at the completion point, that's the smoking gun and isolates a graph-capture/numerics issue in vLLM 0.24's compiled forward for this stage — worth a focused 0.23↔0.24 diff of cudagraph/compile handling for the Qwen3 backbone.
3. **Keep the exact repro script and env pinned.** The report is unusually well-instrumented; if it comes back, having step-2 logging ready turns "one-off fluke" into an actionable bisect immediately.

Net: nothing to fix in vllm-omni today — the completion logic, EOS token, and logit mask are all correct — so closed/not-reproducible stands. Thanks for the thorough write-up and the honest re-verification; happy to reopen with the step-2 logit trace if it ever recurs.