---
title: "SANA Video 架构"
created: 2026-09-04
updated: 2026-09-04
type: architecture
tags: [vllm-omni, models, diffusion]
sources: ["PR #5508", vllm_omni/diffusion/models/sana_video/pipeline_sana_video.py, vllm_omni/diffusion/models/sana_video/pipeline_sana_video_i2v.py, vllm_omni/diffusion/models/sana_video/transformer_sana_video.py, vllm_omni/diffusion/models/diffusers_adapter/pipeline_utils.py, vllm_omni/diffusion/request.py]
confidence: high
---

# SANA Video 架构

## 模型专有部分与共享模块的边界

`sana_video` owner 包含 native `SanaVideoPipeline`（T2V）、
`SanaImageToVideoPipeline`（I2V）和 `SanaVideoTransformer3DModel`。Transformer 的
self-attention 是模型专有 ReLU-kernel linear attention；prompt cross-attention 交给共享
`vllm_omni.diffusion.attention.Attention`。VAE、component discovery、offload、request batch、
postprocess 与 worker 生命周期仍属于共享 diffusion owner。

## 配置、checkpoint 与兼容范围

两个 released 2B checkpoint 由 `sample_size` 决定默认 profile：30 对应 480×832，22 对应
704×1280。pipeline 只接受 Wan 或 LTX-2 video VAE class，分别接入对应 shared distributed
wrapper；scheduler 保留 checkpoint 的 `DPMSolverMultistepScheduler` 配置。

Diffusers-adapter 并非 native pipeline 的替代实现：它由 model class 选择 SANA-specific hooks。
特别是 checkpoint 声明的 T2V Diffusers class 在请求 I2V 时必须改装为 Diffusers I2V class，且
shared `num_frames` 要翻译为 Diffusers 的 `frames`。当前 native 范围只由单 GPU 证明；sequence/
tensor/CFG parallel、Cache-DiT、TeaCache 和 step execution 未验证，adapter 也不提供 native
continuous batching 或并行能力。

## 从输入到输出的主要流程

native T2V 解析 prompt、采样参数和 extras，按 profile 的分辨率 bin 处理尺寸，编码文本，初始化
latents，然后在 checkpoint scheduler 上运行 CFG denoise 并经 VAE 解码视频。真实请求将公共
image-oriented `num_frames=1` omitted sentinel 解析为 81；profile dummy run 保留一帧。

I2V 在同一主干前处理输入 PIL image，按目标尺寸编码它，并把首帧 latent 写入初始 latents；
conditioning mask 令该首帧在 denoise 中固定，同时使用 spatial timestep conditioning。没有
`multi_modal_data.image`、或传入不支持的 image type/path，必须在 model boundary 明确失败。

## 怎样验证功能、精度和性能

组件、权重名和 pipeline contract 由 `tests/diffusion/models/sana_video/` 覆盖。SANA I2V 不进入
通用 tiny alignment harness（该 harness 不提供 image task）；专有 component tests 和 L4
`tests/e2e/online_serving/test_sana_video_expansion.py` 覆盖真实权重的 native/adapter、T2V/I2V、
480p/720p matrix。golden 与逐 stage alignment 仅用于调查数值变化，运行前需要其外部 artifact/
硬件前提，不能把收集或跳过当作完整功能验证。480p T2V 的 frozen golden 只使用 case-specific
0.91 SSIM gate；其余三例保持 0.93。该差异从 native prompt cross-attention 的 vLLM-Omni
Attention 与 reference SDPA 边界开始，不能据此放宽其他 case。^[PR #5508]
