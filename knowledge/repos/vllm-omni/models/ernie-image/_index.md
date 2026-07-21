---
title: "ERNIE-Image（flow-matching DiT + 可选 prompt-enhancer）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/ernie_image/, vllm_omni/diffusion/registry.py]
---

# ERNIE-Image

以下事实在 `main @ 5d44868e` 复核（源码派生页,尚无本模型的运行经验沉淀）。

## 名称与范围

- diffusion registry：`ErnieImagePipeline` →
  （`ernie_image`, `pipeline_ernie_image`）,post
  `get_ernie_image_post_process_func`。单 stage diffusion,引擎默认 stage
  配置（[Config 组件](../../components/config/architecture.md)）。无 deploy YAML。
- 源码：`pipeline_ernie_image.py`（23 KB）+ `ernie_image_transformer.py`
  （`ErnieImageTransformer2DModel`）。
- 依赖共享模块：[Diffusion 组件](../../components/diffusion/_index.md)。

## 结构与要点

- **可选 "PE" prompt 增强 LLM**：从 checkpoint 子目录 `pe/` + `pe_tokenizer/`
  加载 causal LM,经
  `download_weights_from_hf_specific(model, revision, ["pe/*", "pe_tokenizer/*"])`
  选择性拉取——审查下载/缓存路径改动时注意这个子目录选择性拉取模式。
- `AutoencoderKLFlux2` VAE;`FlowMatchEulerDiscreteScheduler`;
  `CFGParallelMixin`,CFG 由 `is_distilled` 旗标门控。另:无变体有据,树内未
  pin checkpoint。

## 什么时候查这里

- 审查 ernie_image 的 PE 加载、蒸馏 CFG 门控或 VAE 改动。
- 语义验收见 [model-validation](../../review/guides/model-validation.md)。
