---
title: "CosyVoice3 规则"
created: 2026-09-04
updated: 2026-09-04
type: rule
tags: [vllm-omni, models]
sources: ["PR #5673", vllm_omni/model_executor/models/cosyvoice3/code2wav_core/cfm.py, vllm_omni/model_executor/models/cosyvoice3/flow_estimator_trt.py, tests/model_executor/models/cosyvoice3/test_cosyvoice3_components.py, benchmarks/tts/benchmark_cosyvoice3_trt_streams.py]
confidence: high
---

# CosyVoice3 规则

## COSYVOICE3-1a — TensorRT CFM 的跨 stream handoff 必须同时守住顺序和 allocator lifetime

- 触发：修改 CosyVoice3 `ConditionalCFM.forward_estimator` 的非-`torch.nn.Module`
  TensorRT 分支、`TrtContextWrapper` 的 context/stream pool，或 raw device-pointer
  输入/输出、dtype conversion 和 CUDA stream handoff。
- 强制：pool 中保存每个 execution context 配对的原始 `torch.cuda.Stream`；在 estimator
  stream 上先 `wait_stream(caller_stream)`，在其 raw `cuda_stream` handle 上 enqueue TRT，
  然后让 caller `wait_stream(estimator_stream)` 再消费输出。对每个以 raw pointer 绑定的
  CUDA input/output record estimator stream，且在返回/转换前对 output record caller stream。
  context 只有在地址已 enqueue 到其专属 stream 后才能归还同一个 pair。
- 禁止：以 host `synchronize()` 替代任一依赖；把 `torch.cuda.stream(...)` 的 context
  manager 当作 pool stream；只保护输出或只保护输入，使 caching allocator 能在 TRT 完成前
  重用 `.to(...).contiguous()` buffer；在未建立 consumer wait 前复用 CFG 的原地写入 buffer。
  不得把这个优化扩展为改变 `torch.nn.Module` estimator 路径，或静默改变
  `COSYVOICE3_TRT` 关闭和非-CUDA fallback。
- 验收：CPU fake-stream 回归断言零 `synchronize`、两个方向各一次 `wait_stream`、TRT 接到
  estimator raw handle，且 context/stream pair 原样回池；真实 CUDA/TensorRT 覆盖 raw-pointer
  input/output 的 allocator-lifetime 与数值 parity。性能报告要分开写 submission、engine 和
  E2E 指标：受控 handoff microbenchmark 只能证明消除了 host blocking，有限的 E2E 样本或
  engine 小幅变化不能声称模型吞吐/延迟提升。^[PR #5673]
