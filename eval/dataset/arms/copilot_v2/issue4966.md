# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4966, 'report_only': True, 'post': False, 'params': {}}

## fetch
- **state_updates**: {'issue_text': '{"body":"### Your current environment\\n\\n### Environment\\n**Deployment**\\n- Docker image: `vllm/vllm-omni:v0.24.0` (container `qwen3tts`), serving `:8091`\\n- Server reported version: 0.24.0\\n**vLLM / vLLM-Omni**\\n- vLLM 0.24.0\\n- vLLM-Omni 0.24.0\\n**CUDA / PyTorch**\\n- PyTorch 2.11.0+cu130 (CUDA build 13.0), CUDA available: yes\\n- torchaudio 2.11.0+cu130\\n- GPU: NVIDIA H100 80GB HBM3\\n**Python libraries**\\n- transformers 5.12.1\\n- numpy 2.2.6\\n- triton 3.6.0\\n- flashinfer-python 0.6.12\\n**OS**\\n- Ubuntu 22.04.5 LTS (container)\\n\\n### Your code version\\n\\nvllm-omni 0.24.0\\n\\n\\n### 🐛 Describe the bug\\n\\n**Summary**\\nIn `x_vector_only_mode=True` (Base voice clone), generated audio starts with a\\nsubstantial, highly variable leading silence — mean ~326 ms, ranging 125–460 ms\\nacross prompts. This inflates perceived time-to-first-audio and makes a fixed\\nserver-side trim hard to tune.\\n\\n**Environment**\\n- Qwen3-TTS Base, single-H100 deploy (vllm-omni), 24 kHz output\\n- Endpoint: `POST /v1/audio/speech`, `stream=false` (non-streaming path, so this\\n  reflects the model\'s generated codes, not the streaming/chunk pipeline)\\n- Reference: `jim.wav` (ref audio\'s own leading silence is ~20 ms)\\n\\n**Measurement**\\n8 prompts × 5 reps = 40 samples. Leading silence = time until audio first crosses\\na −34 dB (peak 0.02) energy threshold, 5 ms frame resolution.\\n\\n| Prompt | leading silence (ms) |\\n|--------|----------------------|\\n| Hello there, how are you doing today? | 330 |\\n| Absolutely, let me check that for you right now. | 340 |\\n| The quick brown fox jumps over the lazy dog. | 125 |\\n| Seven. | 380 |\\n| Thanks for calling, my name is Alex and I can help. | 460 |\\n| Could you confirm your account number, please? | 375 |\\n| It looks like your order shipped this morning. | 205 |\\n| Let\'s schedule a follow up for next Tuesday. | 390 |\\n\\nOverall: mean 326 ms · median 358 ms · stdev 101.6 ms · range 125–

## draft
- **status**: success
- **summary**: Analysed the full issue thread and relevant source code (qwen3_tts_talker.py, code predictor). The root cause is a talker cold-start: x-vector-only mode always opens generation with silence codec token 1995, and the apparent per-prompt determinism is a cudagraph replay artifact (the sampler's per-row generators are disabled under full cudagraphs, so seed=42 always replays the same captured RNG stream). IneshReddy249 confirmed that varying the true seed produces 330–740 ms onset spread within a single prompt — wider than the original 125–460 ms cross-prompt range. Priming with a short ICL prefix (~10 frames / 0.8s) reduces median onset from 393→119 ms and sd ~40% while retaining speaker similarity, but it is a mitigation, not a fix. A draft answer synthesising these findings and recommending next steps is provided.
- **findings**: ['Root cause confirmed: x-vector-only mode is a talker cold-start — the model always opens with silence codec token 1995 (verified by encoding digital silence and comparing codebook-0 ids).', 'The apparent within-prompt determinism (stdev=0 at seed=42) is a cudagraph replay artifact — under full cudagraphs, `qwen3_tts_talker.py:328-350` disables per-row generators so a single captured RNG stream replays identical draws regardless of per-request seed.', 'True onset variance is sampler-driven, not content-driven: varying the seed shows 330–740 ms onset spread within a single prompt, wider than the 125–460 ms cross-prompt range in the original report.', 'Mini-ICL priming (short reference + ICL prefix, ~10 frames / 0.8s) substantially reduces onset: median 393→119 ms, sd drops ~40%, speaker cosine similarity barely moves (0.982→0.969).', 'Priming effect is non-monotonic in reference length — ~10 frames is the sweet spot; 33 frames (2.6s) is near baseline on variance.', 'Naive truncation of a long reference does NOT work (model finishes the reference sentence first, leaking reference text into output). The prefix must be a genuinely short reference with matching text.', 'Server-side silence trimming is fragile: a single fixed threshold must cope with a ~300 ms moving target even after priming, risking soft-onset clipping.', 'The `seed=` kwarg bug (not reaching the sampler under full cudagraphs) is tracked as TODO(#4923) in the code.']
- **files_read**: ['/rebase/vllm-omni-copilot/eval/dataset/arms/copilot_v2/runs/issue4966/run-20260711-231753/evidence/issue_text.txt', '/rebase/vllm-omni/vllm_omni/model_executor/models/qwen3_tts/qwen3_tts_talker.py', '/rebase/vllm-omni/vllm_omni/model_executor/models/qwen3_tts/qwen3_tts_code_predictor_vllm.py']
- **files_modified**: []
- **tests_requested**: []
- **tests_run**: []
- **assumptions**: ['The issue comment thread is complete and no later comments (after 2026-07-11T06:05:14Z) contain contradictory findings.', 'The cudagraph-mode defaults described by IneshReddy249 (full cudagraphs enabled by default for the talker stage) are accurate per the deploy config header notes.']
- **blockers**: []
- **confidence**: high
- **failure_kind**: None
- **next_action**: The draft answer is ready for review and posting. Before posting, confirm with the team whether to recommend the mini-ICL priming approach as a user-facing workaround or to prioritise the TODO(#4923) seeding fix first, since the cudagraph replay artifact affects the validity of all x-vector-only reproducibility claims.
- **answer_draft**: Thank you for the exceptionally clear bug report and the follow-up investigation by @IneshReddy249. Here is a synthesis of the findings and the current recommendation.

---

## Root cause: talker cold-start, not vocoder or content

**The silence is baked into the generated codec tokens, not the vocoder.**

- Round-trip (real speech trimmed to start loud → encode → decode) returns loud at frame 0, so Code2Wav is not muting the opening.
- Splicing the first generated frames into the middle of a loud sequence still decodes quiet — quiet wherever you put them.
- Encoding digital silence gives cb0 token `1995`, and **every x-vector-only generation opens with `1995`**. The model is emitting silence tokens as its first codec frames because it has no speech context to anchor phonation.
- In contrast, ICL mode (ref codec prefix + ref_text) provides that anchor, so onset is much tighter.

## The apparent determinism is a cudagraph replay artifact

The original report noted stdev=0 within-prompt at `seed=42`. That is not the seed taking effect — it is the cudagraph capturing and replaying a single RNG stream.

`qwen3_tts_talker.py` (lines 328–350) explicitly documents this: under full cudagraphs, `talker_mtp` loses its per-row generators and runs with a single captured RNG stream, so the per-request `tts_local_seed` is **not reproducible**. All 40 samples in the original report are effectively 8 prompts × 5 replays of one fixed noise realisation.

Varying the actual seed (via global `torch.manual_seed`) reveals the true picture:

| Metric | Original (one seed) | Across seeds |
|---|---|---|
| Onset range | 125–460 ms | 330–740 ms (within a *single prompt*) |
| Per-prompt sd | 0 | 110–220 ms |

**The variance is sampler noise, not content-driven.** Any prompt can land anywhere in ~200–800 ms depending on trajectory. A fixed trim threshold cannot track that.

> **Related bug**: `seed=` kwarg doesn't reach the sampler under full cudagraphs — tracked as `TODO(#4923)` in the code.

- **draft_answer**: Thank you for the exceptionally clear bug report and the follow-up investigation by @IneshReddy249. Here is a synthesis of the findings and the current recommendation.

---

## Root cause: talker cold-start, not vocoder or content

**The silence is baked into the generated codec tokens, not the vocoder.**

- Round-trip (real speech trimmed to start loud → encode → decode) returns loud at frame 0, so Code2Wav is not muting the opening.
- Splicing the first generated frames into the middle of a loud sequence still decodes quiet — quiet wherever you put them.
- Encoding digital silence gives cb0 token `1995`, and **every x-vector-only generation opens with `1995`**. The model is emitting silence tokens as its first codec frames because it has no speech context to anchor phonation.
- In contrast, ICL mode (ref codec prefix + ref_text) provides that anchor, so onset is much tighter.

## The apparent determinism is a cudagraph replay artifact

The original report noted stdev=0 within-prompt at `seed=42`. That is not the seed taking effect — it is the cudagraph capturing and replaying a single RNG stream.

`qwen3_tts_talker.py` (lines 328–350) explicitly documents this: under full cudagraphs, `talker_mtp` loses its per-row generators and runs with a single captured RNG stream, so the per-request `tts_local_seed` is **not reproducible**. All 40 samples in the original report are effectively 8 prompts × 5 replays of one fixed noise realisation.

Varying the actual seed (via global `torch.manual_seed`) reveals the true picture:

| Metric | Original (one seed) | Across seeds |
|---|---|---|
| Onset range | 125–460 ms | 330–740 ms (within a *single prompt*) |
| Per-prompt sd | 0 | 110–220 ms |

**The variance is sampler noise, not content-driven.** Any prompt can land anywhere in ~200–800 ms depending on trajectory. A fixed trim threshold cannot track that.

> **Related bug**: `seed=` kwarg doesn't reach the sampler under full cudagraphs — tracked as `TODO(#4923)` in the code.

- **state_updates**: {'draft_answer': 'Thank you for the exceptionally clear bug report and the follow-up investigation by @IneshReddy249. Here is a synthesis of the findings and the current recommendation.\n\n---\n\n## Root cause: talker cold-start, not vocoder or content\n\n**The silence is baked into the generated codec tokens, not the vocoder.**\n\n- Round-trip (real speech trimmed to start loud → encode → decode) returns loud at frame 0, so Code2Wav is not muting the opening.\n- Splicing the first generated frames into the middle of a loud sequence still decodes quiet — quiet wherever you put them.\n- Encoding digital silence gives cb0 token `1995`, and **every x-vector-only generation opens with `1995`**. The model is emitting silence tokens as its first codec frames because it has no speech context to anchor phonation.\n- In contrast, ICL mode (ref codec prefix + ref_text) provides that anchor, so onset is much tighter.\n\n## The apparent determinism is a cudagraph replay artifact\n\nThe original report noted stdev=0 within-prompt at `seed=42`. That is not the seed taking effect — it is the cudagraph capturing and replaying a single RNG stream.\n\n`qwen3_tts_talker.py` (lines 328–350) explicitly documents this: under full cudagraphs, `talker_mtp` loses its per-row generators and runs with a single captured RNG stream, so the per-request `tts_local_seed` is **not reproducible**. All 40 samples in the original report are effectively 8 prompts × 5 replays of one fixed noise realisation.\n\nVarying the actual seed (via global `torch.manual_seed`) reveals the true picture:\n\n| Metric | Original (one seed) | Across seeds |\n|---|---|---|\n| Onset range | 125–460 ms | 330–740 ms (within a *single prompt*) |\n| Per-prompt sd | 0 | 110–220 ms |\n\n**The variance is sampler noise, not content-driven.** Any prompt can land anywhere in ~200–800 ms depending on trajectory. A fixed trim threshold cannot track that.\n\n> **Related bug**: `seed=` kwarg doesn\'t reach the sampler under full cuda
