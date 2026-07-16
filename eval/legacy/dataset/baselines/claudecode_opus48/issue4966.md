I've investigated the code paths. Here is my answer as a maintainer.

---

## Answer to #4966 — Leading-silence variance in Qwen3-TTS x-vector-only mode

Thanks for the unusually careful write-up, and thanks to @IneshReddy249 for the follow-up experiments. I've gone through the talker and prompt-assembly code and I want to confirm the diagnosis, correct the framing of the "variance" a bit, and point at what a real fix should look like. The short version: **this is expected behavior of a cold phonation start under stochastic sampling, the per-seed determinism you observed is a CUDA-graph replay artifact (not the seed working), and the mini-ICL priming direction is the right one.** I would *not* land a server-side silence trim.

### 1. Why x-vector-only has a cold start (and ICL doesn't)

This is structural, and you can see it directly in the prompt builder. In Base mode we branch on `x_vector_only_mode`:

- **x-vector-only** (`in_context_mode=False`): the talker prompt is `role → codec think-tags → speaker x-vector → codec_bos → first text token`, and decoding starts from there — see `vllm_omni/model_executor/models/qwen3_tts/prompt_embeds_builder.py:1233-1240` and `:1298-1307`. There are **no reference codec frames in context**. The talker has a timbre anchor (the ECAPA x-vector) but has never "heard" itself speak, so the first codec frames it samples are a cold-start into phonation.
- **ICL** (`in_context_mode=True`): `_generate_icl_prompt(...)` prepends the reference codec frames to the talker context (`:1265-1274`, assembly at `:830-876`). Generation *continues* an already-voiced trajectory, which is exactly why you see a much tighter onset.

So your contrast between the two modes is real and expected — it's the difference between continuing speech and initiating it. @IneshReddy249's round-trip test (silence lives in the *codes*, Code2Wav decodes frame-0 loud when fed loud codes) is consistent with this: the vocoder isn't muting anything, the talker is emitting near-silent frames until phonation catches.

### 2. The "variance is content-driven, deterministic" framing is measuring one fixed noise realization

This is the important correction. The talker is **not** greedy — the deploy config samples it at `temperature: 0.9, top_k: 50, repetition_penalty: 1.05` (`vllm_omni/deploy/qwen3_tts.yaml:53-61`). So onset length is a property of the sampled trajectory, and it will vary run-to-run *if the sampler is actually reseeded*.

Your `stdev=0` across 5 reps at `seed=42` is **fixed-seed replay, not stability** — and on the vLLM serve path it's very likely not even the seed doing the work. Look at `qwen3_tts_talker.py:327-350`:

> under full cudagraphs, `talker_mtp` loses its per-row generators and runs with a single captured RNG stream, so **per-request `tts_local_seed` is not reproducible** … the determinism may be a cudagraph replay artifact rather than the seed taking effect.

The code literally sets `talker_mtp_accepts_per_row_generators = not talker_mtp_graph_wrapped` (`:350`), and the talker "runs cudagraph by default" per the deploy comment (`qwen3_tts.yaml:11`). When full cudagraphs are on, every launch replays the *same* captured RNG stream, which produces `stdev=0` regardless of the seed value. That matches @IneshReddy249's in-process finding that outputs are byte-identical only under a global `torch.manual_seed`, and that varying the seed swings onset 330–740 ms *within a single prompt* — wider than your entire 125–460 ms cross-prompt table.

**Conclusion:** your 8×5 table is 8 prompts under one frozen noise realization. The per-prompt numbers aren't a stable "this prompt has long silence" signal; any prompt can land anywhere in ~200–800 ms depending on trajectory. This is not a new bug — it's the documented consequence tracked by #4883 and #4923 (the follow-up to make per-row MTP seeding cudagraph-safe). It's worth cross-linking here because it directly undermines any "tune a fixed trim per content" plan.

Quick confirmation anyone can run: same prompt, `seed=42` vs `seed=1234`, on the serve path. If the audio is byte-identical, the seed isn't reaching the sampler and you're in the cudagraph-replay regime.

### 3. Why I'd reject the server-side silence trim

I agree with @iancarrasco-b10's instinct. A −34 dB / peak-0.02 gate on the emit path adds a hyperparameter that has to separate genuine soft onsets (fricatives, breathy voice, low-energy vowels) from cold-start silence, against a target that moves 125–460 ms (and really 200–800 ms once you account for §2). The shortest-onset cases are exactly where you'll clip real speech. It's cosmetic, mode-agnostic, and fragile — the wrong layer to fix a talker-trajectory problem. If anyone wants it as a stopgap it should be opt-in and off by default, never the recommended answer.

### 4. The right direction: mini-ICL priming (with the caveats already surfaced)

@IneshReddy249's priming experiment is the promising result and matches how the model is built. A short, speech-onset-aligned reference (~0.8 s / ~10 codec frames) with **matching `ref_text`** constrains the trajectory into phonation while the x-vector still carries timbre; median onset 393→119 ms with ~40% less per-prompt sd and speaker-cosine essentially unchanged (0.982→0.969) is a good trade. The non-monotonicity (10 frames beats 20 beats 33) is plausible — a longer reference gives the model more prosodic room to wander before your target text — though I'd want it reproduced on the actual serve path before treating the sweet-spot as a tuned constant.

Two things I want to underline for whoever implements this:

- **The two hard caveats are load-bearing.** (a) Variance is *reduced, not eliminated* — a deploy still sees a moving onset, just smaller; don't sell this as a fix. (b) Naive `ref_code[:N]` truncation while keeping the full `ref_text` does **not** work — the model finishes the reference sentence first and the "zero onset" is just the reference leaking through (your N=6 transcript proving this is the key artifact). The prefix must be a genuinely short reference whose `ref_text` matches its codes, verified by transcription.
- **It reuses machinery we already have.** This is essentially the existing ICL path (`_generate_icl_prompt`, `prompt_embeds_builder.py:830-876`) plus Code2Wav's reference-context trim (`qwen3_tts_code2wav.py` — `left_context_size` / `ref_context_size` handling around `:320-355`, which already keeps ref frames out of the emitted audio). So a "mini-ICL x-vector" mode is mostly plumbing: keep the x-vector timbre anchor, inject a short canned/derived voiced prefix + matching ref_text, and let the existing context-trim drop it from the output. That's much lower-risk than a new emit-path DSP heuristic.

### Recommended next steps

1. **Don't** merge a server-side silence trim as the primary fix.
2. First, settle the seeding question on the serve path (#4923). Until per-request seeding is cudagraph-safe, all onset measurements on vLLM are under a single frozen noise realization and shouldn't be read as content-driven. This is a prerequisite for evaluating any mitigation honestly.
3. Prototype **mini-ICL in x-vector mode** as an opt-in flag, reusing `_generate_icl_prompt` + Code2Wav context-trim, with the short-matched-reference constraint (not truncation). Validate on the serve path with @iancarrasco-b10's 40-sample harness *and* transcription checks that every output speaks only the target text.
4. Report onset **distributions across seeds**, not fixed-seed reps, and speaker-similarity, so we can see whether variance actually narrows on the real deploy.

I'll keep this open and labeled `bug`, but I'd reframe the title toward "cold-start onset in x-vector-only mode" — the leading silence is a symptom of the cold phonation start plus stochastic sampling, not a fixed per-prompt defect. Happy to review a mini-ICL PR along the lines above.

---

Would you like me to save anything from this investigation (e.g. the cudagraph-seeding gotcha or the x-vector cold-start mechanism) as a rebase-agent skill for future reference?