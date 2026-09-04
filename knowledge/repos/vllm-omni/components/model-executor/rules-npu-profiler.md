---
title: "NPU profiler 规则"
created: 2026-09-05
updated: 2026-09-05
type: rule
tags: [vllm-omni, components, model-executor]
sources: ["PR #6518", vllm_omni/platforms/npu/profiler.py]
confidence: high
---

# NPU profiler 规则

## EXEC-13g — NPU profiler metric 必须显式保留 trace 的利用率语义

- 触发：修改 `NPUTorchProfilerWrapper`、`torch_npu.profiler._ExperimentalConfig` 或 NPU trace 默认项。
- 强制：默认 `aic_metrics` 使用 `AiCMetrics.PipeUtilization`，令导出的 Text/tensorboard trace 包含
  operator-pipeline utilization；保留 Level1、CPU+NPU activities、offline `analyse()` 提示和现有 trace
  directory/handler 合同。
- 禁止：把这个 telemetry default 说成 RainFusion/MiniMax-H3 kernel 的性能或质量证据，或由它推断任何
  Ascend SKU 的 utilization 已测得；它影响所有 NPU profiling run，不能静默改回无 AiCore metric。
- 验收：mock `torch_npu` profiler config，精确断言 metric enum、活动与 handler 参数；真实 NPU trace
  另验证工具版本和可解析指标。PR #6518 没有提交该类 profiler artifact。^[PR #6518]
