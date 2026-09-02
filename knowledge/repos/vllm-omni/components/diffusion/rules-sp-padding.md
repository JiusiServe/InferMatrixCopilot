---
title: "Diffusion SP padding 规则"
created: 2026-09-02
updated: 2026-09-02
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #4645", docs/user_guide/diffusion/parallelism/sequence_parallel.md, vllm_omni/config/omni_config.py, vllm_omni/diffusion/data.py, vllm_omni/diffusion/distributed/sp_plan.py, vllm_omni/diffusion/forward_context.py, vllm_omni/diffusion/hooks/sequence_parallel.py, vllm_omni/diffusion/models/flux2/flux2_transformer.py, vllm_omni/diffusion/models/hunyuan_video/hunyuan_video_15_transformer.py]
confidence: high
---

# Diffusion SP padding 规则

只有 `SPPAD-数字字母` 是可审计规则 ID。

## SPPAD-1a — padding mask 是显式正确性/性能策略，不是无损优化

- 触发：修改 `DiffusionParallelConfig.mask_sp_padding`、SP `auto_pad`、forward context 的
  `sp_original_seq_len/sp_padding_size`，或模型传给 attention 的 hidden-state mask。
- 强制：只有 sequence-parallel size > 1、确实发生 auto-padding 且 `mask_sp_padding=True` 时，才按
  global 原长度构造 bool mask，将尾部 padding 标 false 并传给模型 attention。默认 false 时不传
  hidden mask，让 attention 留在 dense fast path；必须 warning once，明确 padding 数、原长度、SP
  degree、潜在数值差异与 strict opt-in 方法。无 padding 或 SP=1 不改变 mask 选择。
- 禁止：把未 mask 的零 token 当数学等价；它们仍可参与 softmax，影响有效 token。也不能把
  `mask_sp_padding=False` 描述为没有 padding：模型 `_sp_plan` 的 `auto_pad=True` 已在 attention 前补齐
  sequence。文档列出的 consumer 是 Wan2.2、Wan2.2 VACE、Qwen-Image、Flux2 与 HunyuanVideo1.5，
  不能由 config 字段存在外推到其他 pipeline。
- 验收：每个 consumer 至少覆盖 SP=1、可整除 SP、不可整除且 mask true/false；断言 false 不传 mask
  并走 dense backend，true 只遮尾部 pad 并走对应 masked/varlen path，同时比较有效 token/output 的
  有界数值差异。PR #4645 只修改 Flux2/HunyuanVideo1.5 源码与文档，没有新增自动测试。

## SPPAD-1b — advanced UAA 与模型前置 auto-padding 属于不同层

- 触发：把 `ulysses_mode=advanced_uaa` 作为 padding-mask 替代方案或性能对照。
- 强制：advanced UAA 在 Ulysses attention 内用 variable split 处理不等 sequence/head division；
  若模型 `_sp_plan` 已 `auto_pad=True`，它收到的仍是补齐后的 evenly-divisible tensor，不会撤销 padding，
  也不会自动恢复 strict mask。两项选择必须按真实 hook→attention 顺序分别验证。
- 禁止：因为 advanced UAA 支持 arbitrary sequence length 就推断 Flux2 不再 auto-pad，或把两条路径的
  latency/数值声明为等价。^[PR #4645]

## SPPAD-2a — 性能数字绑定 exact padded workload，视觉附件不构成质量 gate

- 触发：引用 skip-mask 的 latency、百分比或“无质量下降”。
- 强制：PR 数据只绑定 vLLM 0.23.0、Omni pre-final `ad07f98b7`、Ulysses degree 8：Flux2-dev 1304²、25 steps、
  6561→6568 tokens 为 7049.25→5444.68 ms；HunyuanVideo1.5 T2V 848×480、33 frames、30 steps、
  14310→14312 tokens 为 16518.37→11729.65 ms。它是一次报告的 `e2e_total_ms` request timing
  observation，不是重复测量或 SLA。
- 禁止：泛化 -22.8%/-29.0% 到其他尺寸、SP degree、backend/hardware 或 merge target。附件图片/视频
  和作者未附数字的 rebase 后复跑没有 LPIPS、PSNR、逐帧误差、重复次数或机器可审计日志，不能证明
  numerical/quality parity；默认 false 仍是明确的近似策略。
- 验收：性能结论须在目标 SHA 固定硬件/backend、warmup/repeats 与 exact case 重跑；质量结论对
  mask true/false 使用相同 seed/input 并设模型合适的图像/视频 metric gate。^[PR #4645]
