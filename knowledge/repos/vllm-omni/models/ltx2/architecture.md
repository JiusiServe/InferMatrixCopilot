---
title: "LTX-2/2.3 模型架构与证据索引"
created: 2026-07-16
updated: 2026-08-05
type: architecture
tags: [vllm-omni, models, ltx2]
sources: [recipes/LTX/LTX-2.md, vllm_omni/diffusion/registry.py, "#4381", "#4464"]
---

# LTX-2/2.3 模型架构与证据索引

以下事实在 `v0.26.0 @ a4ea67a2` 复核（合并后的 recipe 与 live registry）。

## 结构与 serving

- 纯 diffusion（无 AR stage）：22B transformer + text encoder + VAE + vocoder；
  T2V 与 I2V 皆可，输出带 48kHz 同步音频。验证建议从 96GB 级 GPU 起步
  （recipe 原文）。
- serving 入口（LTX-2.3）：
  `vllm serve diffusers/LTX-2.3-Diffusers --omni --stage-init-timeout 600`；统一
  `LTX2Pipeline` 由 checkpoint metadata 选择 LTX-2 或 LTX-2.3 profile。
- pipeline 变体：one-stage 使用 `LTX2Pipeline`，distilled two-stage 使用
  `LTX2DistilledPipeline`，DMD2 使用 `LTX2T2VDMD2Pipeline`/
  `LTX2I2VDMD2Pipeline`；T2V/I2V 通过是否提供 `image=` 选择，不再使用单独的
  `*ImageToVideoPipeline` registry names。
- Python `forward` 只允许 `req` 作为 positional argument，其他参数必须 keyword-only；
  这对直接调用者和显式 `--model-class-name` 覆盖是 breaking change，CLI/HTTP recipe
  已按 named fields 调用。
- 单段 diffusion 模型不在 `OMNI_PIPELINES` registry（走
  `async_omni_engine.py` 的默认 diffusion stage 兜底），deploy 语义见
  [Config 组件](../../components/configuration/architecture.md)。

## 已有证据索引（只链接，不复制正文）

- 性能/profiling 陷阱：eager-trace 与 graph-benchmark 口径混同、mask-sync"优化"
  改变精度——见
  [benchmark incidents #19/#20](../../benchmark/incidents/_index.md)。
- L4 基线与远端验证长跑教训（半冷测量偏置、babysit 走偏）——见
  [remote performance-validation incidents](../../remote/incidents/performance-validation/_index.md)
  （030/031 两篇）。
- review 视角案例（PR #4381 的 reviewer-lens 教训）——见
  [reviewer-lens-cases](../../../../general/review/guides/reviewer-lens-cases.md)。
- checkpoint 布局差异（LTX-2 vs LTX-2.3）曾是 model-adaptation 审查的实例——见
  [model-adaptation-guardrails](../../review/guides/model-adaptation-guardrails.md)。
- 相关 PR：#4381、#4464（graph/profiling 与性能对比线索）。

源码会变化，具体类名和行号在改代码前必须以目标仓库当前版本为准。
