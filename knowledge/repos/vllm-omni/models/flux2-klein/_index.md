---
title: "FLUX.2-Klein（Qwen3 编码的 T2I/I2I）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/flux2_klein/, vllm_omni/diffusion/registry.py]
---

# FLUX.2-Klein

以下事实在 `main @ 5d44868e` 复核（源码派生页,尚无本模型的运行经验沉淀）。

## 名称与范围

- diffusion registry：`Flux2KleinPipeline` →
  （`flux2_klein`, `pipeline_flux2_klein`）,post
  `get_flux2_klein_post_process_func`——**独立于 flux2 家族目录**,与
  [flux2](../flux2/_index.md)、[flux](../flux/_index.md) 互为姊妹家族。
- 单 stage diffusion,引擎默认 stage 配置
  （[Config 组件](../../components/config/architecture.md)）。无 deploy YAML。
- 源码：`pipeline_flux2_klein.py`（46 KB）+ `flux2_klein_transformer.py`（41 KB）。

## 结构与要点

- 文本编码用 `Qwen3ForCausalLM` + `Qwen2TokenizerFast`（不是 CLIP/T5）;
  `AutoencoderKLFlux2` VAE,自定义
  `Flux2ImageProcessor(VaeImageProcessor)`（`pipeline_flux2_klein.py:55`）。
- 类混入 `CFGParallelMixin, SupportImageInput`;**单架构无变体**——蒸馏
  行为是构造期 `is_distilled` 旗标;无 deploy YAML/checkpoint 映射记录;
  img2img latents 走 diffusers `retrieve_latents`。

## 什么时候查这里

- 审查 flux2_klein 的 Qwen3-LLM 编码链、图像输入或蒸馏旗标改动;文本编码
  方案与 flux2 家族不同,勿混（见该页）。
