---
title: "Cosmos3"
created: 2026-07-20
updated: 2026-09-02
type: index
tags: [vllm-omni, models, diffusion]
sources: ["PR #5001", "PR #5634", recipes/cosmos3/Cosmos3-Nano.md, vllm_omni/diffusion/models/cosmos3/, vllm_omni/platforms/rocm/platform.py]
confidence: high
---

# Cosmos3

## 名称与范围

- 正式 owner：Cosmos3 diffusion family；常见变体包括常规、Edge 与 Distilled。
- 模型实现：`vllm_omni/diffusion/models/cosmos3/`，包含 pipeline、常规/Edge
  transformer、audio tokenizer、guardrails 与 transfer。
- 请求扩展：`vllm_omni/model_extras/cosmos3.py`；注册入口在 diffusion registry。
- 共享依赖：[Diffusion component](../../components/diffusion/_index.md)。

## 配置与 checkpoint 差异

Distilled 变体不只是换权重：scheduler 配置必须包含 stochastic/SDE 采样合同；Edge
transformer 还要维护自己的 layerwise-offload block 声明。architecture 名称、checkpoint
配置和公开支持表必须共同证明实际变体，不能从同族名称推断能力。

## 从输入到输出

请求中的 seed/guidance 等字段进入 Cosmos3 pipeline，pipeline 选择变体 scheduler，使用
请求本地 generator 创建噪声并完成 denoise/transfer，最后交给共享 diffusion 输出路径。
变体专有不变量与描述直达源码入口见 [rules](rules.md#direct-代码快速入口)。新模型通用验证见
[model validation](../../review/guides/model-validation.md)。

## ROCm evidence scope

ROCm recipe 的 MI350X latency/显存只来自 `b3f4fbf9` 上单卡 gfx950、Nano T2I/T2V、
guardrails off 的一次 warmup + 一次测量，不是当前 pin 或通用 ROCm 保证。gfx942 只命中
platform 的 AITER capability gate，未在该 PR 实测；质量、multi-GPU 与 Cosmos3-Super 也未覆盖。
引用具体数字或扩展支持矩阵时按本页审查入口中的 `COSMOS-3b` 复核。

## 什么时候查这里

- 审查 Cosmos3 Edge/Distilled scheduler、RNG、guidance、offload 或 capability claim。
- 同一问题影响多个 diffusion 模型时返回 [Diffusion rules](../../components/diffusion/rules.md)。
