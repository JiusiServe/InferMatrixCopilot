---
title: "Qwen-Image（base/Edit/EditPlus/Layered/DMD2 五变体）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/qwen_image/, vllm_omni/diffusion/registry.py]
---

# Qwen-Image

以下事实在 `main @ 5d44868e` 复核（源码派生页,尚无本模型的运行经验沉淀）。
同厂牌 AR 侧家族另见 [qwen-omni](../qwen-omni/_index.md)。

## 名称与范围

- 尾部最宽家族,5 个 pipeline（变体）共享一套 transformer/VAE,模块映射:
  `QwenImagePipeline`→`pipeline_qwen_image`;
  `QwenImageEditPipeline`→`pipeline_qwen_image_edit`;
  `QwenImageEditPlusPipeline`→`pipeline_qwen_image_edit_plus`;
  `QwenImageLayeredPipeline`→`pipeline_qwen_image_layered`;
  `QwenImageDMD2Pipeline`→`pipeline_qwen_image`（与 base 同模块）→ 家族
  目录 `vllm_omni/diffusion/models/qwen_image/`（9 文件）;pin 上无
  checkpoint↔变体映射记录。
- pre/post 绑定不对称：pre 有 edit/edit-plus/layered;post 有
  base/edit/edit-plus（DMD2 复用 base）——**Layered 有 pre 无 post 绑定**,
  layered 输出后处理是否在 pipeline 内完成未在 pin 上追清,评审 layered 输出
  路径改动时先追这条线。
- 单 stage diffusion,引擎默认 stage 配置
  （[Config 组件](../../components/config/architecture.md)）。无 deploy YAML。

## 结构与要点

- `Qwen2_5_VLForConditionalGeneration` prompt 编码;**分布式 VAE**
  `DistributedAutoencoderKLQwenImage`（`diffusion/distributed/autoencoders/`,
  少数带 VAE patch-parallel 的家族）;树内 `autoencoder_kl_qwenimage.py`
  （42 KB）。
- 家族专属 `cfg_parallel.py`（`QwenImageCFGParallelMixin`,四个非 DMD2
  pipeline 共用）;DMD2 经 `DMD2PipelineMixin`
  （`pipeline_qwen_image.py:1097`）;prompt 长度校验
  `validate_prompt_sequence_lengths`。

## 什么时候查这里

- 审查 qwen_image 任一变体的 CFG-parallel、分布式 VAE 或 DMD2 改动——五变体
  共栈,单变体改动先扫其余四个;共享 mixin 见
  [Diffusion 组件](../../components/diffusion/_index.md)。
