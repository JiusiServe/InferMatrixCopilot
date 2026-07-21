---
title: "Stable Audio Open（T2A,cosine DPM-solver）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/stable_audio/, vllm_omni/diffusion/registry.py]
---

# Stable Audio Open

以下事实在 `main @ 5d44868e` 复核（源码派生页）。

## 名称与范围

- diffusion registry：`StableAudioPipeline` →
  （`stable_audio`, `pipeline_stable_audio`）,post
  `get_stable_audio_post_process_func`。单 stage diffusion,引擎默认 stage
  配置（[Config 组件](../../components/config/architecture.md)）。无 deploy YAML。
- 源码：`pipeline_stable_audio.py`（24 KB）+ `stable_audio_transformer.py`
  （`StableAudioDiTModel` + `StableAudioSchedulerWrapper`）。
- 依赖共享模块：[Diffusion 组件](../../components/diffusion/_index.md)。

## 结构与要点

- **尾部唯一 cosine DPM-solver 家族**：`CosineDPMSolverMultistepScheduler`
  包在家族内 `StableAudioSchedulerWrapper`（`pipeline_stable_audio.py:167`）
  ——scheduler 抽象改动的另一个反例（对照 [sdxl](../sdxl/_index.md) 的
  EulerDiscrete）。
- `AutoencoderOobleck` 音频 VAE;T5 编码器 + `StableAudioProjectionModel` 做
  `seconds_start`/`seconds_total` 时长条件;1D rotary 位置嵌入
  （`get_1d_rotary_pos_embed`）;`SupportAudioOutput`。

## 什么时候查这里

- 审查 stable_audio 的 scheduler wrapper、时长条件或 Oobleck VAE 改动。
