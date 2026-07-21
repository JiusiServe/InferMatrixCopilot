---
title: "HiDream-I1（MoE DiT + 四编码器文本栈）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/hidream_image/, vllm_omni/diffusion/registry.py]
---

# HiDream-I1

以下事实在 `main @ 5d44868e` 复核（源码派生页,尚无本模型的运行经验沉淀）。

## 名称与范围

- diffusion registry：`HiDreamImagePipeline` →
  （`hidream_image`, `pipeline_hidream_image`）,post
  `get_hidream_image_post_process_func`。单 stage diffusion,引擎默认 stage
  配置（[Config 组件](../../components/config/architecture.md)）。无 deploy YAML。
- 源码：`pipeline_hidream_image.py`（49 KB）+ `hidream_image_transformer.py`
  （43 KB）。
- 依赖共享模块：[Diffusion 组件](../../components/diffusion/_index.md)。

## 结构与要点

- 文本编码栈：`CLIPTextModelWithProjection` + `T5EncoderModel` + 整个
  `LlamaForCausalLM` 作为附加编码器——全仓少见的重编码器配置,显存预算评审
  时别漏 Llama 编码器。
- transformer 是 routed-MoE feed-forward：`MoEGate`
  `num_routed_experts=4`/`num_activated_experts=2`
  （`hidream_image_transformer.py:347`）;TP 用 `DistributedRMSNorm`。
- `FlowMatchEulerDiscreteScheduler`;CFG-parallel;hub 子目录预取
  （`from_pretrained_with_prefetch`）。

## 什么时候查这里

- 审查 hidream 的 MoE 路由、编码器栈或预取逻辑改动。
