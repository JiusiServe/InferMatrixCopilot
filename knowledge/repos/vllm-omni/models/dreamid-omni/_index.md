---
title: "DreamID-Omni（Wan2.2 基座音视频身份生成）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/dreamid_omni/, vllm_omni/diffusion/registry.py]
---

# DreamID-Omni

以下事实在 `main @ 5d44868e` 复核（源码派生页,尚无本模型的运行经验沉淀）。

## 名称与范围

- 无别名、无变体有据,树内未 pin checkpoint。diffusion registry:
  `DreamIDOmniPipeline` →
  （`dreamid_omni`, `pipeline_dreamid_omni`, `DreamIDOmniPipeline`）,post
  `get_dreamid_omni_post_process_func`。单 stage diffusion,引擎默认 stage
  配置（[Config 组件](../../components/config/architecture.md)）。无 deploy YAML。
- 联合音频+视频身份保持生成:家族目录内含 TP 优化的 Wan2.2 相关实现
  （`wan2_2.py`：`WanSelfAttention` + 跨 TP rank 求全局 RMS 的
  `DistributedRMSNorm`）,但整体**硬依赖树外 `dreamid_omni` 包**（见下）;
  Wan 家族本体见 [wan2-2](../wan2-2/_index.md)。
- 依赖共享模块：[Diffusion 组件](../../components/diffusion/_index.md)。

## 结构与要点

- **硬依赖树外 `dreamid_omni` 包**（`fm_solvers`、`init_wan_vae_2_2`、
  `init_mmaudio_vae`、裁剪工具）——缺包直接 ImportError;树内代码不自足,
  改动/复现前先确认该 vendor 包版本（pin 上无 pin 记录）。
- 双 VAE：`vae_model_video` + `vae_model_audio` 同入 `_vae_modules`;
  `fusion.py` 的 `FusedBlock` 把 video block 与 audio block 配对做 layerwise
  offload（`FusionModel` 带 checkpoint key remap）。
- scheduler 在 forward 时可选 `FlowUniPCMultistepScheduler`/
  `FlowDPMSolverMultistepScheduler`/`FlowMatchEulerDiscreteScheduler`。
- 类混入 `CFGParallelMixin, SupportImageInput, SupportAudioInput`。

## 什么时候查这里

- 审查 dreamid_omni 的双 VAE、fused offload 或外部包依赖变化。
