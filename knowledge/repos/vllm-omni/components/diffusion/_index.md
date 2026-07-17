---
title: "Diffusion"
created: 2026-07-10
updated: 2026-07-10
type: index
tags: [vllm-omni, components, diffusion]
sources: []
---

# Diffusion

- 源码入口：`vllm_omni/diffusion/` 全树，含 16 个子模块：attention、cache、distributed、executor、hooks、layers、lora、model_loader、models、offloader、postprocess、profiler、quantization、sched、utils、worker
- 源码校验：以上子模块均已在 `main @ 238fc0a6`（此前亦在 `dev/vllm-align @ 4f2b32c` 验证，结果一致） 验证存在
- 主要职责：多个 diffusion 模型共用的 pipeline、执行循环、scheduler 接入和运行机制

## 什么时候查这里

- 根因位于共享 diffusion 代码，可能影响多个模型。
- 调查 denoise loop、diffusion runner、scheduler 或共享 attention 执行机制。

## 不放什么

- HunyuanImage3 独有 pipeline、配置和 checkpoint 问题；这些放模型目录。
- 通用 benchmark 方法；这些放 `general/benchmark/`。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 理解共享职责和数据流 | [architecture](architecture.md) |
| step 执行/batching/缓存加速/并行等特性语义 | [特性指南](guides/_index.md) |
