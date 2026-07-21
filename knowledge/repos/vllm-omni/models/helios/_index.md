---
title: "Helios（分块长视频 + 金字塔多段去噪）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/helios/, vllm_omni/diffusion/registry.py]
---

# Helios

以下事实在 `main @ 5d44868e` 复核（源码派生页,尚无本模型的运行经验沉淀）。

## 名称与范围

- diffusion registry：`HeliosPipeline` 与 `HeliosPyramidPipeline` **映射同一个类**
  （`helios`, `pipeline_helios`, `HeliosPipeline`）;pre+post
  `get_helios_{pre,post}_process_func` 对两个架构名都绑定。
- 单 stage diffusion,引擎默认 stage 配置
  （[Config 组件](../../components/config/architecture.md)）。无 deploy
  YAML,树内未 pin checkpoint。
- 源码：`pipeline_helios.py`（78 KB）、`helios_transformer.py`
  （`HeliosTransformer3DModel`）、`scheduling_helios.py`（自定义
  `HeliosScheduler`,不用 diffusers scheduler）。

## 结构与要点

- docstring：支持 T2V、I2V（图像输入）、V2V（视频输入）;分块视频生成 +
  多期记忆历史上下文。
- 金字塔去噪由请求 `extras` 驱动：`pyramid_num_stages`（默认 3）+
  `pyramid_num_inference_steps_list`（默认 `[10,10,10]`）;
  `supports_step_execution: ClassVar = True`。
- UMT5 文本编码器 + `AutoencoderKLWan` 视频 VAE。
- **未决**：`HeliosPyramidPipeline` 别名在运行时产生什么差异未确认（金字塔
  行为看起来只由 extras 驱动）——评审涉及别名分派时先 live 验证。

## 什么时候查这里

- 审查 Helios 分块/金字塔/自定义 scheduler 改动;共享 RNG/graph 规则见
  [Diffusion rules](../../components/diffusion/rules.md)。
