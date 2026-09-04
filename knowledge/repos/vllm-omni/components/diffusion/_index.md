---
title: "Diffusion"
created: 2026-07-10
updated: 2026-09-04
type: index
tags: [vllm-omni, components, diffusion]
sources: []
---

# Diffusion

- 源码入口：`vllm_omni/diffusion/` 全树，含 16 个子模块：attention、cache、distributed、executor、hooks、layers、lora、model_loader、models、offloader、postprocess、profiler、quantization、sched、utils、worker
- 源码校验：以上子模块均已在 `main @ d150a4fd` 验证存在；本轮新增/扩展的
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
| vLLM/torch rebase、MoE/quant helper 漂移、kernel backend capability 与 matched accuracy | [upstream 兼容规则](rules-upstream-compat.md) |
| 平台 IR-op priority、Inductor/eager 默认顺序与模型 hook 合并 | [platform runtime rules](rules-platform-runtime.md) |
| runtime temporary 与 loader-scoped parameter dtype、shared RMSNorm accuracy | [tensor dtype rules](rules-tensor-dtype.md) |
| Wan VAE height/width spatial reshard、empty tail、attention extent | [Wan spatial-shard rules](rules-wan-spatial-shard.md) |
| multi-DiT、dotted `_dit_modules` 与跨 Cache-DiT/compile/LoRA/offload lifecycle | [component lifecycle rules](rules-component-lifecycle.md) |
| PEFT 与 distilled LoRA、startup fusion、delta/key/alpha、Qwen/Wan transformer mapping | [LoRA rules](rules-lora.md) |
| local FlashAttention deterministic opt-in、NPU packed mask-free/laser fallback 与 config propagation | [attention rules](rules-attention.md) |
| SP auto-padding、`mask_sp_padding`、dense/varlen 与 advanced UAA 边界 | [SP padding rules](rules-sp-padding.md) |
| video/audio mux、DLO DP wave、result queue、async pump、SHM ownership、async-output wait 与 shutdown | [output/runtime rules](rules-output-lifecycle.md) |
| distilled continuous sigma schedule、boundary/step 语义与 modality shift | [sigma schedule rules](sigma-schedules.md) |
| diffusion step 与 request/continuous batching | [step and batching](step-and-batching.md) |
| request-wave admission coalescing、stable window、deadline 与 finite config | [admission wait rules](rules-admission-wait.md) |
| paged KV/cache 预算、native/backend/platform 闭环、GQA/Ring/Ulysses layout、FlashInfer plan、能力 metadata | [paged cache 与系统运行时规则](rules-system-runtime.md) |
| Scheduler-managed diffusion KV 的请求控制面、Hunyuan layout 与未实现边界 | [paged KV control plane](paged-kv-control-plane.md) |
| Cache-DiT、TeaCache 和 prefix cache | [cache acceleration](cache-acceleration.md) |
| TP/PP/SP/CFG/VAE/HSDP 等并行策略 | [parallelism](parallelism.md) |
| 实验性 world-model session 生命周期、LRU 与内存统计边界 | [session state](session-state.md) |
| checkpoint remap、HSDP/FSDP、component quantization 与在线量化加载 | [checkpoint 与加载合同](rules-checkpoint-loading.md) |
