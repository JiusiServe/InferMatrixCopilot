---
title: "OmniGen2（指令驱动图像生成/编辑）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/omnigen2/, vllm_omni/diffusion/registry.py]
---

# OmniGen2

以下事实在 `main @ 5d44868e` 复核（源码派生页,尚无本模型的运行经验沉淀）。

## 名称与范围

- diffusion registry：`OmniGen2Pipeline` →（`omnigen2`, `pipeline_omnigen2`）,
  pre `get_omnigen2_pre_process_func` + post `get_omnigen2_post_process_func`。
  单 stage diffusion,引擎默认 stage 配置
  （[Config 组件](../../components/config/architecture.md)）。无 deploy YAML。
- 源码：`pipeline_omnigen2.py`（55 KB）+ `omnigen2_transformer.py`
  （50 KB,`OmniGen2Transformer2DModel` + `OmniGen2RotaryPosEmbed`）。
- 依赖共享模块：[Diffusion 组件](../../components/diffusion/_index.md)。

## 结构与要点

- **文件内 vendored `FlowMatchEulerDiscreteScheduler` 重实现**
  （`pipeline_omnigen2.py:66`,自带 `step()` 的 SchedulerMixin+ConfigMixin）
  ——不是 diffusers import;修 diffusers scheduler 兼容问题时这里不受影响,
  反之这里的 bug 也不会被 diffusers 升级修掉。
- prompt 编码 `Qwen2_5_VLForConditionalGeneration` + `Qwen2_5_VLProcessor`;
  自定义 `OmniGen2ImageProcessor(VaeImageProcessor)`（line 326）;参考图输入
  经 `is_valid_image_imagelist` 校验;CFG-parallel。

## 什么时候查这里

- 审查 omnigen2 的 vendored scheduler、参考图输入或编码链改动。
