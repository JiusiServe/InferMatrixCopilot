---
title: "Higgs-Audio 规则"
created: 2026-09-05
updated: 2026-09-05
type: rule
tags: [vllm-omni, models, model-executor]
sources: ["PR #6422", vllm_omni/model_executor/models/higgs_audio_v3/higgs_audio_v3_talker.py, vllm_omni/worker/gpu_model_runner.py, tests/model_executor/models/higgs_audio_v3/test_higgs_audio_v3.py, tests/e2e/online_serving/test_higgs_audio_v3.py]
confidence: high
---

# Higgs-Audio 规则

## HIGGS-1a — V3 codec sampling 与 decode state 必须按 request 所有

- 触发：Higgs-Audio V3 seeded sampling、八 codebook flatten/compaction、GPU decode delay 或 replacement request。
- 强制：每个 logical request 的八个 contiguous codebook rows 必须在一次 multinomial 中使用该
  request row 的 `SamplingMetadata.generators[req_idx]`；generator 由 vLLM request lifecycle 提供，
  talker 不按 request ID 另建 RNG。`has_codes`、last codes、delay/EOC countdown 与 done state 必须由
  request ID 映射到 pool row；reorder/condense 前保存旧 row、再恢复新顺序。finished ID 先释放映射，
  slot 复用时重新初始化；即使 `previous_req_ids == req_ids`，当前 ID 缺 pool entry 也必须重同步。
- 禁止：共享/global RNG、把一个 generator 按八行独立重采样、按临时 batch row 保存 decode state，
  或把 finished callback 描述成会清零 tensor（fresh allocation 才初始化）。`transcript_expected_text`
  只是在 control-token request 与 spoken reference 不同的测试 helper 中覆盖 assertion，默认取
  `input`；它不是 OpenAI request 字段或 runtime 模型语义。
- 验收：覆盖同 seed 单独/带邻居 batch、异 seed、reorder/condense 连续性、finish、distinct-ID slot
  reuse 与 same-ID replacement，并验证 runner 把 live `input_batch.req_ids` 传入 decode metadata。
  ROCm 配置测试只证明 V3 Stage 0 的 `TRITON_ATTN` overlay/collection；作者报告的单次 MI300X case
  不构成通用确定性、音质、吞吐或跨平台支持。^[PR #6422]
