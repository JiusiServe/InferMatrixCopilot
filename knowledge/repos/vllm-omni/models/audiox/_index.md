---
title: "AudioX（文本/视频条件音频 DiT）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/audiox/, vllm_omni/diffusion/registry.py]
---

# AudioX

以下事实在 `main @ 5d44868e` 复核（源码派生页,尚无本模型的运行经验沉淀）。

## 名称与范围

- 正式名称 AudioX,无别名、无变体有据。diffusion registry:
  `AudioXPipeline` →（`audiox`, `pipeline_audiox`, `AudioXPipeline`）,post
  `get_audiox_post_process_func`;在 `_NO_CACHE_ACCELERATION` 名单
  （不吃 cache_dit/tea_cache 加速）。
- 单 stage diffusion,不在 `OMNI_PIPELINES`（引擎默认 diffusion stage 配置,
  见 [Config 组件](../../components/config/architecture.md)）。无 deploy YAML。
- 源码：`vllm_omni/diffusion/models/audiox/`（`pipeline_audiox.py` 40 KB +
  `audiox_transformer.py`,`MMDiffusionTransformer`）。
- 依赖共享模块：[Diffusion 组件](../../components/diffusion/_index.md)。

## 结构与要点

- 条件侧：T5 文本 + `CLIPVisionModelWithProjection` 视频条件,MAF 融合块
  （`_MAFCrossAttentionBlock`/`MAF_Block`）;任务模式 VIDEO_ONLY/TEXT_VIDEO
  来自 `vllm_omni/transformers_utils/processors/audiox.py`。
- `AutoencoderOobleck` 音频 VAE;采样用 `torchsde`
  `_BrownianTreeNoiseSampler` 自定义 SDE——代码注释明确与 diffusers
  EDMDPMSolverMultistep 的 v-prediction 预处理有差异,改采样器前先读该注释。
- `SupportAudioOutput` 输出。

## 什么时候查这里

- 审查 AudioX 的 SDE 采样、视频条件或 Oobleck VAE 改动;RNG/graph 共享规则见
  [Diffusion rules](../../components/diffusion/rules.md)。
