---
title: "LongCat-Image（Qwen2.5-VL 编码 T2I + 编辑）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/longcat_image/, vllm_omni/diffusion/registry.py]
---

# LongCat-Image

以下事实在 `main @ 5d44868e` 复核（源码派生页,尚无本模型的运行经验沉淀）。

## 名称与范围

- 正式名称 LongCat-Image;base/Edit 是**变体不是别名**,无 deploy
  YAML/checkpoint 映射记录。diffusion registry:
  `LongCatImagePipeline`（`pipeline_longcat_image`）与
  `LongCatImageEditPipeline`（`pipeline_longcat_image_edit`,
  `SupportImageInput`）→ 家族目录 `vllm_omni/diffusion/models/longcat_image/`;
  post 共用 `get_longcat_image_post_process_func`,pre 仅 Edit 绑定
  `get_longcat_image_edit_pre_process_func`。
- 单 stage diffusion,引擎默认 stage 配置
  （[Config 组件](../../components/config/architecture.md)）。无 deploy YAML。
- 依赖共享模块：[Diffusion 组件](../../components/diffusion/_index.md)。

## 结构与要点

- prompt 编码：`Qwen2_5_VLForConditionalGeneration` + `Qwen2VLProcessor`,
  **中/英双语系统提示直接 import 自
  `diffusers.pipelines.longcat_image.system_messages`**
  （`SYSTEM_PROMPT_EN/ZH`）——prompt 模板烙进编码路径;diffusers 升级评审
  时点名核对这两个 import 常量。
- `FlowMatchEulerDiscreteScheduler` + `AutoencoderKL`;CFG-parallel;hub
  子目录预取。

## 什么时候查这里

- 审查 longcat 的双语系统提示、Edit 前处理或编码链改动。
