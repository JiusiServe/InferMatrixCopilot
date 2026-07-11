I have everything I need. Here is my answer as a maintainer.

---

**Answer to issue #4952 — [New Model]: nvidia/Nemotron-Labs-Audex 30B-A3B, 2B**

Thanks for filing this and for volunteering to drive it, @yuekaizhang. Audex is a great fit for vllm-omni and this issue is already correctly triaged — you're assigned, and #4976 is the tracking implementation. Below is a maintainer's take on how it maps onto our architecture and what "done" looks like, so the issue and PR review stay aligned.

**This is a feature request, not a bug — keep it open as the tracking issue for #4976 and close it when that PR merges.** No action needed from anyone else beyond review.

### How Audex maps onto our multi-stage omni pipeline

vllm-omni models are a set of stage sub-models wired into a pipeline, each registered as an HF architecture in `OmniModelRegistry` (`vllm_omni/model_executor/models/registry.py:8-368`) and given a `PipelineConfig` in `vllm_omni/config/pipeline_registry.py`. Qwen3-Omni is the canonical example: it decomposes into `thinker → talker → code2wav` stages, each a separately-registered arch, orchestrated by `Qwen3OmniMoeForConditionalGeneration` which switches behavior on `model_config.model_stage` (see `vllm_omni/model_executor/models/qwen3_omni/qwen3_omni.py:81-217`).

Audex is close in *spirit* to Qwen3-Omni but meaningfully different in structure, which is worth calling out since #4952 lists Qwen3-Omni as the closest supported model:

- **No separate talker stage.** In Qwen3-Omni the talker is a second LM that autoregressively turns thinker hidden states into RVQ codec codes, with an elaborate thinker→talker projection (`qwen3_omni.py:932-1206`). Audex's **thinker emits codec tokens directly in its own vocabulary** — `<speechcodec_N>` for speech and an interleaved 4-codebook `<audiocodec_N>` RVQ block for general audio. That collapses thinker+talker into one stage and drops all the hidden-state projection machinery.
- **Two distinct decode paths, both new.** A streaming causal speech decoder (`audex/speech_decoder/`) → 16 kHz for speech, and an *external* XCodec1 checkpoint (`audex_xcodec.py`, `AudexXCodec1`) for general audio/sound effects. That external-codec dependency is not something any current omni model has.
- **Classifier-free guidance as a first-class inference feature** (`cfg.py`, ~567 LoC) — effectively mandatory for TTA (default scale 3.0), recommended for TTS. This is genuinely new surface area for the engine, not a copy of Qwen3-Omni behavior.
- **One checkpoint, four tasks** (TTS, TTA, audio-QA/ASR, S2S), each a distinct pipeline. S2S is a three-pass cascade (ASR → chat → TTS) over a *single* deployment — only the last pass touches the codec path.

So the registry/pipeline wiring follows the established pattern (per #4976: `NemotronDenseForCausalLM` thinker, `AudexCode2Wav`, `AudexXCodec1`, and unified `NemotronDenseAudexForConditionalGeneration` / `NemotronHAudexForConditionalGeneration`, plus `audex_{tts,tta,thinker_only,s2s}` pipelines and a `nemotron_labs_audex` model_type alias for bare `serve`), but the *internals* (direct codec emission, external XCodec1, CFG) are where the real work and review attention should go.

### 2B vs 30B-A3B

These share token space and decoder — the only real divergence is the thinker backbone: 2B is a dense `NemotronDenseForCausalLM`; 30B-A3B is a **hybrid Mamba + MoE NemotronH** thinker (`NemotronHAudexForConditionalGeneration`). Two consequences reviewers should verify:

1. **Prefix caching must be off for the 30B** (hybrid Mamba state) — the PR's 30B yamls already do this. Confirm the 2B path isn't silently inheriting that.
2. The 30B **requires an explicit `*_30b.yaml`** because repo-root auto-detection lands on the 2B-tuned configs. That's a sharp edge; make sure it's documented in the error/log path, not just the README.

Re @Sy0307's suggestion to split basic-function vs perf — agreed, that's the right decomposition. #4976 lands correctness/functionality (thinker, both codec paths, four pipelines, e2e tests); perf work (CFG batching so guided requests don't run one-at-a-time, Code2Wav CUDA-graph capture à la `qwen3_omni.py:1321-1336`, KV/Mamba-state headroom on the 30B) can follow as separate PRs.

### What "done" looks like for #4976 to land

- Weight-loading + all four pipelines exercised by the e2e tests already in the PR (`tests/e2e/{offline_inference,online_serving}/test_audex_*`), run against real 2B **and** 30B checkpoints with results pasted into the PR description (the template's Test Result section is currently empty).
- On our H200s the README's "single H100 80 GB" 30B claim should hold comfortably; please confirm actual weights (~61 GiB) + KV headroom on this hardware and note whether TP2 was needed.
- Verify the XCodec1 download/resolution path (env var / `--xcodec1-path` / default repo) fails gracefully offline, since it's an external dependency.

Assigning to @yuekaizhang; #4976 is the tracking PR. Ping @linyueqian / @hsliuustc0106 when it's ready for review, and let's keep #4952 open until it merges.