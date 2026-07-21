---
title: "MagiHuman（音频驱动人像视频,单文件移植）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/magi_human/, vllm_omni/diffusion/registry.py]
---

# MagiHuman

以下事实在 `main @ 5d44868e` 复核（源码派生页,尚无本模型的运行经验沉淀）。

## 名称与范围

- SandAI daVinci-MagiHuman 移植：音频驱动人像视频,输出同步视频 + 44.1 kHz
  音频（post 返回 `{video, audio, audio_sample_rate: 44100, fps: 25}`）。
- 无别名、无变体有据,树内未 pin checkpoint。diffusion registry:
  `MagiHumanPipeline` →
  （`magi_human`, `pipeline_magi_human`, `MagiHumanPipeline`）,pre 为
  pass-through,post
  `get_magi_human_post_process_func`。单 stage diffusion,引擎默认 stage 配置
  （[Config 组件](../../components/config/architecture.md)）。无 deploy YAML。
- 源码仅 3 文件但全尾部最大：`pipeline_magi_human.py` **96 KB** +
  `magi_human_dit.py` 62 KB（头注：移植自 daVinci-MagiHuman
  `dit_module.py`,去掉了 Ulysses context-parallel）。

## 结构与要点

- **双 DiT**：`_dit_modules = ["dit", "sr_dit"]`（基座 + 超分）;VAE 双份——
  `DistributedAutoencoderKLWan` 视频 + 文件内 Oobleck 风格 `_AudioAutoencoder`
  （`_vae_modules = ["vae", "audio_vae"]`,`pipeline_magi_human.py:1684`）。
- 音频条件直接用 OpenAI `whisper`（`SAAudioFeatureExtractor`,
  `whisper.load_audio`/`pad_or_trim`）;`_T5GemmaEncoder` 文本编码器;文件内
  移植版 `FlowUniPCMultistepScheduler`（line 72）;内置超长音质负向 prompt。
- 单文件 monolith + 自带 `MagiDataProxy` 数据代理——跨家族 refactor 评审时
  把这份 96 KB 单文件移植列入检查清单。

## 什么时候查这里

- 审查 magi_human 的双 DiT/双 VAE、whisper 条件或 UniPC 移植改动。
- 共享 RNG/graph 规则见 [Diffusion rules](../../components/diffusion/rules.md)。
