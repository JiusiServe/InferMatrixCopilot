---
title: "FLUX.1（base / Kontext 编辑 / DMD2 蒸馏）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/flux/, vllm_omni/diffusion/registry.py]
---

# FLUX.1

以下事实在 `main @ 5d44868e` 复核（源码派生页）。FLUX.2 在独立家族——见
[flux2](../flux2/_index.md)（含 Klein 的注记）。

## 名称与范围

- diffusion registry：`FluxPipeline`、`FluxDMD2Pipeline`（同模块
  `pipeline_flux`）、`FluxKontextPipeline`（`pipeline_flux_kontext`）→ 家族目录
  `vllm_omni/diffusion/models/flux/`;post 分别为
  `get_flux_post_process_func`（base+DMD2）与
  `get_flux_kontext_post_process_func`。
- 单 stage diffusion,引擎默认 stage 配置
  （[Config 组件](../../components/config/architecture.md)）。无 deploy YAML。
- 依赖共享模块：[Diffusion 组件](../../components/diffusion/_index.md)、
  `diffusion/models/t5_encoder`。

## 结构与变体

- 三变体共享 transformer 栈（`flux_transformer.py`,含
  `FluxKontextTransformer2DModel`）与 `FluxPipelineMixin.calculate_shift`
  （分辨率相关 timestep-shift mu）：
  - **base**：CLIP + T5 双文本编码器,`FlowMatchEulerDiscreteScheduler`,
    guidance-embeds（`transformer.guidance_embeds`）。
  - **Kontext**：图像编辑（`SupportImageInput`,文本引导改图）。
  - **DMD2**：`class FluxDMD2Pipeline(DMD2PipelineMixin, FluxPipeline)`
    （`pipeline_flux.py:685`,FastGen DMD2 蒸馏少步数变体）。
- CFG-parallel 有 `check_cfg_parallel_validity` 对
  `get_classifier_free_guidance_world_size()` 的校验。

## 什么时候查这里

- 审查 FLUX.1 的 shift 计算、Kontext 编辑输入或 DMD2 mixin 改动;DMD2 合同是
  跨家族 mixin,qwen_image 等也用——改 mixin 先扫全部使用方。
