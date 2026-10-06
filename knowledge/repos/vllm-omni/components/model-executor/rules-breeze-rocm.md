---
title: "Breeze ROCm graph 与 autotune 合同"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, components, model-executor]
sources: ["PR #8342", vllm_omni/model_executor/models/breeze_tts_2/depth_decoder.py, tests/model_executor/models/test_breeze_tts_2_first_code_sampler.py, tests/model_executor/models/test_breeze_tts_2_graphs.py]
confidence: high
---

# Breeze ROCm graph 与 autotune 合同

入口见 [Model Executor 规则](rules.md)。

## EXEC-17a — Breeze graph RNG 与深度层 autotune 必须按真实平台能力分支

- 触发：修改 Breeze first-code sampler、depth decoder graph 测试或 depth-layer compile options。
- 强制：captured-generator-state 路径仅在 NVIDIA CUDA 且 `CUDAGraph.register_generator_state`
  可用时成立。ROCm 保留既有 eager sampling fallback，测试应断言无 sampler graph，同时继续
  验证 token、每 request generator state、全局 RNG 与返回 tensor 的独立存储。
- 强制：深度层 compile 固定 `epilogue_fusion=False`；`max_autotune` 在 ROCm 为 false，
  其他平台保持 true。greedy/不支持 generator registration 时不得要求随机 replay 命中 capture。
- 禁止：因 `torch.cuda` 命名就把 ROCm 当 NVIDIA；为 graph-count 断言关闭 token/RNG/owned-output
  验证；把关闭一个不稳定 Triton GEMM autotune 路径外推为无 compile 或全模型性能保证。
- 验收：CPU options test 分别断言 ROCm/non-ROCm；GPU matrix 分别验证 capture 与 eager fallback
  的 token/state/output，且 fallback 不污染全局 RNG。已报告的精确 AMD R2-01 结果只资格化该
  source/config，不代替其它 hardware 或全模型质量与性能证据。^[PR #8342]
