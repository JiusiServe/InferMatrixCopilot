---
title: "MiniMax H3"
created: 2026-08-05
updated: 2026-08-05
type: index
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/minimax_h3/, vllm_omni/diffusion/registry.py, recipes/MiniMaxAI/MiniMax-H3.md, recipes/MiniMaxAI/MiniMax-H3-NPU.md, tests/diffusion/models/minimax_h3/, vllm_omni/entrypoints/openai/video_api_utils.py]
confidence: high
---

# MiniMax H3

## 名称、源码与任务

- checkpoint：`MiniMaxAI/MiniMax-H3`；纯 diffusion registry architecture 是
  `MiniMaxH3Pipeline`，实现位于 `diffusion/models/minimax_h3/`。
- 支持 `t2va`、`fl2va`、`ref2va` 三种 joint video+audio 条件模式；一个 server 进程
  一次只加载 `FL2VA` 或 `Ref2VA` 分区，不能把两个分区当成同一份权重同时服务。
- 输出是带同步音频的 MP4；参考视频、图像和音频的预处理合同由 pipeline 与 video API
  共同决定，不能仅凭 endpoint 名称推断输入组合。
- 生成合同固定为 24 FPS 视频与 32 kHz 音频；空间尺寸必须按 32 对齐，宽高比限制在
  `1:4` 到 `4:1`，这些约束在 request validation 阶段执行而不是由 VAE 静默修正。

## 并行与加载约束

- H3 是 CFG-distilled pipeline，`cfg_parallel_size` 必须保持 `1`。VAE patch parallel
  使用 H3 原生 `tile` 模式；`text_encoder_tp_size` 作用在 DiT group 的前 N 个 rank，
  并且必须同时整除 Qwen3-VL 的 64 个 attention heads 与 8 个 KV heads。
- 单卡 accuracy 路径使用 CPU offload；多卡部署可使用 Ulysses、text-encoder TP、VAE
  tile/patch parallel 或 layerwise offload，但每个组合都必须按最终并行拓扑和设备数验证。
- 音频加载优先使用 torchaudio；当 TorchCodec/torchaudio 在 CPU-only aarch64 环境不可用
  时，`reference_video.load_audio_file` 回退到 soundfile，再对 libsndfile 不支持的格式
  通过 ffmpeg 转 WAV。该回退保持 `(channels, samples)` float32 与原始 sample rate 合同。

## 验证入口

模型专属 contract、packing、parallel 和 e2e 测试在 `tests/diffusion/models/minimax_h3/`。
硬件 recipe 只记录已验证的 GPU/NPU 形状；性能数字不能从 recipe 的配置示例泛化为全硬件
保证。共享 offloader、并行和请求合同分别归 [Diffusion](../../components/diffusion/_index.md)、
[Configuration](../../components/configuration/_index.md) 和 [Serving](../../components/serving/_index.md)。
