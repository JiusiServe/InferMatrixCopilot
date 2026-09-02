---
title: "Diffusion"
created: 2026-07-10
updated: 2026-09-02
type: index
tags: [vllm-omni, components, diffusion]
sources: []
---

# Diffusion

- 源码入口：`vllm_omni/diffusion/` 全树，含 16 个子模块：attention、cache、distributed、executor、hooks、layers、lora、model_loader、models、offloader、postprocess、profiler、quantization、sched、utils、worker
- 源码校验：以上子模块均已在 `main @ 53afbf3a` 验证存在；本轮新增/扩展的
  async output、distributed layerwise offload 和 MiniMax H3 仍按各自模型/机制规则审查
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
| 根据 PR 描述直达 execution parity、checkpoint/artifact identity、quality evidence 或 system-runtime 异常清理规则组与第一批源码 | [rules 与代码地图](rules.md) |
| multi-DiT、dotted `_dit_modules` 与跨 Cache-DiT/compile/LoRA/offload lifecycle | [component lifecycle rules](rules-component-lifecycle.md) |
| local FlashAttention deterministic opt-in、NPU packed mask-free/laser fallback 与 config propagation | [attention rules](rules-attention.md) |
| DLO DP collective wave、per-worker result queue、async pump、SHM ownership 与 shutdown | [multiprocess runtime rules](rules-output-lifecycle.md) |
| diffusion step 与 request/continuous batching | [step and batching](step-and-batching.md) |
| request-wave admission coalescing、stable window、deadline 与 finite config | [admission wait rules](rules-admission-wait.md) |
| Scheduler-managed diffusion KV 的请求控制面、Hunyuan layout 与未实现边界 | [paged KV control plane](paged-kv-control-plane.md) |
| Cache-DiT、TeaCache 和 prefix cache | [cache acceleration](cache-acceleration.md) |
| TP/PP/SP/CFG/VAE/HSDP 等并行策略 | [parallelism](parallelism.md) |
| 实验性 world-model session 生命周期、LRU 与内存统计边界 | [session state](session-state.md) |
