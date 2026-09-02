---
title: "MiniMax H3"
created: 2026-08-05
updated: 2026-09-02
type: index
tags: [vllm-omni, models, diffusion]
sources: ["PR #5709", "PR #5737", "PR #5740", "PR #5756", .buildkite/cuda/test-nightly.yml, apps/ComfyUI-vLLM-Omni/comfyui_vllm_omni/, docs/user_guide/quantization/fp8.md, vllm_omni/diffusion/models/minimax_h3/, vllm_omni/diffusion/registry.py, recipes/MiniMaxAI/MiniMax-H3.md, recipes/MiniMaxAI/MiniMax-H3-NPU.md, tests/diffusion/models/minimax_h3/, tests/e2e/accuracy/minimax_h3/, tests/e2e/features/comfyui/test_comfyui_integration.py, vllm_omni/entrypoints/openai/video_api_utils.py]
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
- H3 DiT 支持加载时 online FP8：默认覆盖 token-refiner/主 block 的 attention、MLP、
  condition projection 和 AdaLN projection；video/audio patch、timestep MLP、最终输出头、
  text encoder 与 VAE 保持 BF16/FP32。`ignored_layers` 按 DiT 内部的精确 runtime prefix
  匹配，不带 `transformer.` owner prefix。checkpoint 的 grouped-QKV reorder 和 fused-MLP
  gate/up split 在 `MiniMaxH3DiTModel.load_weights()` 内先执行，再交给当前 vLLM loader，
  以保留 TP shard 与 FP8 online-processing wrapper。
- H3 online FP8 当前不得与 layerwise offload 组合：offload 产生的 weight stride
  会被 Cutlass FP8 kernel 拒绝。变更量化覆盖范围时，除逐层命中/排除与加载转换测试外，
  必须同时保护 joint video/audio 质量；peak memory 只作为同 case report，不是稳定上界。
- 音频加载优先使用 torchaudio；当 TorchCodec/torchaudio 在 CPU-only aarch64 环境不可用
  时，`reference_video.load_audio_file` 回退到 soundfile，再对 libsndfile 不支持的格式
  通过 ffmpeg 转 WAV。该回退保持 `(channels, samples)` float32 与原始 sample rate 合同。

## ComfyUI 请求路由

MiniMax H3 的 `t2va`、`fl2va` 和 `ref2va` frontend 选择、reference multipart 字段及
Hub/local model lookup 合同由 [ComfyUI tooling rules](../../tooling/rules.md) 负责；模型页不复制
客户端规则。

## 验证入口

模型专属 contract、packing 和 parallel 测试在 `tests/diffusion/models/minimax_h3/`。
T2VA full-model accuracy 入口在 `tests/e2e/accuracy/minimax_h3/`：模型 snapshot 固定在
`73372e6c`，但该 revision 没有参考视频，official `assets/t2va.mp4` 实际从 Hugging Face
`resolve/main` 下载，不能把 golden 写成 revision-immutable。用例固定 1344x768/24 FPS/
243 帧/50 steps/seed 0，除视频和 AAC 32 kHz stereo metadata 外，还以 SSIM >= 0.82、
PSNR >= 20 dB gate 完整输出；nightly lane 使用 4x H100、USP4、HSDP4、text-encoder TP4
和 VAE patch parallel 4。该用例是精度/媒体合同，不是性能基线。
硬件 recipe 只记录已验证的 GPU/NPU 形状；性能数字不能从 recipe 的配置示例泛化为全硬件
保证。共享 offloader、并行和请求合同分别归 [Diffusion](../../components/diffusion/_index.md)、
[Configuration](../../components/configuration/_index.md) 和 [Serving](../../components/serving/_index.md)。

## 审查入口

H3 online FP8 的 component namespace、loader 顺序、joint quality 与 offload 边界见
[MiniMax H3 rules](rules.md#direct-代码快速入口)。
