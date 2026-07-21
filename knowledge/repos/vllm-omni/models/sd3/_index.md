---
title: "Stable Diffusion 3（MMDiT,三文本编码器）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/sd3/, vllm_omni/diffusion/registry.py]
---

# Stable Diffusion 3

以下事实在 `main @ 5d44868e` 复核（源码派生页）。

## 名称与范围

- diffusion registry：`StableDiffusion3Pipeline` →（`sd3`, `pipeline_sd3`）,
  post `get_sd3_image_post_process_func`。单 stage diffusion,引擎默认 stage
  配置（[Config 组件](../../components/config/architecture.md)）。无 deploy YAML。
- 源码：`pipeline_sd3.py`（33 KB）+ `sd3_transformer.py`
  （`SD3Transformer2DModel`）。无变体有据,无 deploy YAML,树内未 pin
  checkpoint。
- 依赖共享模块：[Diffusion 组件](../../components/diffusion/_index.md)。

## 结构与要点

- 编码器栈：2× `CLIPTextModelWithProjection` + `T5EncoderModel`;
  `FlowMatchEulerDiscreteScheduler`;`CFGParallelMixin`。
- `DistributedAutoencoderKL`（可 patch-parallel 的共享 VAE 实现）;批量输出用
  `split_diffusion_output_by_request` 拆分。

## 什么时候查这里

- 审查 sd3 的三编码器栈或分布式 VAE 改动;与 sdxl 的 UNet/epsilon 路线对照见
  [sdxl](../sdxl/_index.md)。
