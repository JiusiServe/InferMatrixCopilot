---
title: "NextStep-1.1（StepFun 自回归图像生成）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/nextstep_1_1/, vllm_omni/diffusion/registry.py]
---

# NextStep-1.1

以下事实在 `main @ 5d44868e` 复核（源码派生页,尚无本模型的运行经验沉淀）。

## 名称与范围

- StepFun NextStep-1.1：**自回归图像生成**——LLM 出图像 token + flow-matching
  头,Flux VAE 解码;挂在 diffusion registry 但没有 diffusers scheduler。
- registry：`NextStep11Pipeline` →（`nextstep_1_1`, `pipeline_nextstep_1_1`）,
  post `get_nextstep11_post_process_func`;在 `_NO_CACHE_ACCELERATION` 名单。
  单 stage,引擎默认 stage 配置
  （[Config 组件](../../components/config/architecture.md)）。无 deploy YAML。
- 源码：`pipeline_nextstep_1_1.py` + `modeling_nextstep*.py`
  （Config/Model/Llama 基座/flow 头）+ `modeling_flux_vae.py`
  （树内 `AutoencoderKL` 移植）。

## 结构与要点

- AR 解码循环用 transformers `StaticCache`;2D sincos 位置嵌入在 pipeline 内
  计算（`get_2d_sincos_pos_embed`,line 73）。
- CFG **不走 `CFGParallelMixin`**：直接用
  `get_cfg_group`/`get_classifier_free_guidance_rank/world_size` 跨 rank 实现
  ——审查 CFG-parallel 共享改动时,这家族和 z_image 一样要单独确认。

## 什么时候查这里

- 审查 nextstep 的 StaticCache 解码、flow 头或 CFG rank 划分改动。
- 语义验收见 [model-validation](../../review/guides/model-validation.md)。
