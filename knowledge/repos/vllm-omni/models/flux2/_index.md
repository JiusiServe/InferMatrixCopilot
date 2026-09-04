---
title: "FLUX.2"
created: 2026-07-20
updated: 2026-09-05
type: index
tags: [vllm-omni, models, diffusion]
sources: ["PR #5136", "PR #3027", "PR #6390", vllm_omni/diffusion/models/flux2/, vllm_omni/diffusion/models/mistral_encoder/]
confidence: high
---

# FLUX.2

## 名称与范围

- 正式 owner：FLUX.2 diffusion pipeline 与其 Mistral text encoder 接线。
- 主要路径：`vllm_omni/diffusion/models/flux2/` 与
  `vllm_omni/diffusion/models/mistral_encoder/`。
- 共享量化和质量合同见 [Diffusion rules](../../components/diffusion/rules.md)。

## 什么时候查这里

- 审查 FLUX.2 text-encoder-only FP8、transformer block 的 online FP8 prefix、component prefix、meta 初始化或 CPU offload，或 Mistral hidden-state 提取层的 checkpoint 配置。
- 描述直达源码与具体不变量见 [FLUX.2 rules](rules.md#direct-代码快速入口)；通用模型适配检查见
  [model adaptation guardrails](../../review/guides/model-adaptation-guardrails.md)。
