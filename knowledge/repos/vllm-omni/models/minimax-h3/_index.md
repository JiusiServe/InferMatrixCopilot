---
title: "MiniMax H3"
created: 2026-08-05
updated: 2026-09-05
type: index
tags: [vllm-omni, models, diffusion]
sources: ["PR #5703", "PR #5706", "PR #5709", "PR #5720", "PR #5723", "PR #5737", "PR #5740", "PR #5752", "PR #5756", "PR #5764", "PR #5779", "PR #5785", "PR #5801", "PR #5824", "PR #5829", "PR #5837", "PR #5840", "PR #5850", "PR #5857", "PR #5881", "PR #5885", "PR #5891", "PR #5896", "PR #5914", "PR #5946", "PR #5972", "PR #5978", "PR #5991", "PR #5863", "PR #6476", "PR #6555", "PR #6556", .buildkite/cuda/test-nightly.yml, .buildkite/cuda/test-ready.yml, .buildkite/cuda/test-merge.yml, apps/ComfyUI-vLLM-Omni/comfyui_vllm_omni/, docs/design/architecture_overview.md, docs/models/supported_models.md, docs/user_guide/quantization/fp8.md, vllm_omni/config/omni_config.py, vllm_omni/diffusion/attention/backends/flash_attn.py, vllm_omni/diffusion/attention/backends/rainfusion_attn.py, vllm_omni/diffusion/attention/backends/trtllm_attn.py, vllm_omni/diffusion/cache/cachedit/backend.py, vllm_omni/diffusion/cache/teacache/, vllm_omni/diffusion/forward_context.py, vllm_omni/diffusion/layers/norm.py, vllm_omni/diffusion/layers/rope.py, vllm_omni/diffusion/model_metadata.py, vllm_omni/diffusion/models/minimax_h3/, vllm_omni/model_executor/models/minimax_h3/, vllm_omni/model_executor/stage_input_processors/minimax_h3.py, vllm_omni/diffusion/registry.py, vllm_omni/diffusion/sched/sigma_schedule.py, vllm_omni/diffusion/utils/hf_utils.py, vllm_omni/entrypoints/omni_base.py, vllm_omni/platforms/npu/platform.py, vllm_omni/platforms/rocm/platform.py, vllm_omni/quantization/int8_config.py, recipes/MiniMaxAI/MiniMax-H3.md, recipes/MiniMaxAI/MiniMax-H3-4090.md, recipes/MiniMaxAI/MiniMax-H3-5090.md, recipes/MiniMaxAI/MiniMax-H3-MUSA.md, recipes/MiniMaxAI/MiniMax-H3-NPU.md, recipes/MiniMaxAI/MiniMax-H3-Spark-GB10.md, recipes/MiniMaxAI/MiniMax-H3-RTX-PRO-5000.md, recipes/MiniMaxAI/MiniMax-H3-RTX-PRO-6000.md, tests/diffusion/attention/test_rainfusion_plan.py, tests/diffusion/attention/test_trtllm_attn.py, tests/diffusion/cache/test_cache_backends.py, tests/diffusion/cache/test_teacache_extractors.py, tests/diffusion/layers/test_norm.py, tests/diffusion/layers/test_rope_broadcast.py, tests/diffusion/models/minimax_h3/, tests/diffusion/quantization/test_int8_config.py, tests/e2e/accuracy/minimax_h3/, tests/e2e/features/comfyui/test_comfyui_integration.py, tests/e2e/online_serving/minimax_h3/, tests/e2e/online_serving/test_minimax_h3_dlo_dp2_t2va.py, vllm_omni/entrypoints/openai/video_api_utils.py, "PR #6213", "PR #6742", "PR #6666", "PR #6824", "PR #6714"]
confidence: high
---

# MiniMax H3

## 名称、源码与任务

- checkpoint：`MiniMaxAI/MiniMax-H3`；纯 diffusion registry architecture 是
  `MiniMaxH3Pipeline`，实现位于 `diffusion/models/minimax_h3/`。
- root `modular_model_index.json` 可解析为 `MiniMaxH3ModularPipeline` alias：combined 默认加载
  FL2VA/Ref2VA 两套 DiT 并共享 text encoder 与 VAE；`--task-type` 可限制到单分区，完整
  discovery、task、capability 与多 DiT lifecycle 合同见 MMH3-2d。目标 pin 的 modular alias
  遗漏 TRTLLM auto-default 所需 capability，默认 combined 服务需显式 backend 或先修 metadata。
- combined root 同一进程服务 `t2va`、`fl2va`、`ref2va`；启动时 `--task-type t2va/fl2va`
  选择 FL2VA-only，`ref2va` 选择 Ref2VA-only。combined 省略 request task 时，无媒体→t2va、
  image-only→fl2va、video/audio→ref2va（因此 image-only Ref2VA 必须显式 task）；Ref2VA-only
  省略时固定→ref2va。
- pipeline 边界输出 decoded frames、stereo audio tensor、FPS 与 sample rate；serving/example
  output layer 才负责编码 H.264 和 mux 成带同步音频的 MP4。FL2VA 接受首帧、尾帧或有序首尾帧，Ref2VA 支持 image-only
  及有 visual reference 的 image/video/audio mixed matrix。完整计数、媒体和 API 合同见
  MMH3-2a/2b。^[PR #5914]
- decoded video 在两条 H3 decode 路径中于 transfer 前准备为 contiguous `uint8` BTHWC；raw
  offline frame ABI 因而从 `[0,1]` float 改为 `[0,255]` uint8，audio 不变。此布局本身不保证
  frontend direct-planar route；其 converter/fallback contract 见 `SERV-1k`，完整 H3 owner rule
  完整 owner contract 见 media rules 的 `MMH3-1o`。^[PR #6824]
- 生成合同固定为 24 FPS 视频与 32 kHz 音频；官方输出 duration、named ratio、768
  short-edge 与 32-pixel canvas policy 在 request validation 阶段执行，而不是由 VAE 静默修正。
- `minimax_h3_disaggregated` 是显式 deploy 选取的两 stage topology：Stage 0 的
  `MiniMaxH3TextEncoder` 用 native vLLM Qwen3-VL runner 产生 layer-50 residual hidden states
  和 token-role tags，Stage 1 不加载 text encoder、保留原始媒体并 inline 执行 H3 diffusion。
  裸 checkpoint discovery 仍走 fused single-stage fallback；不可将 split profile 当成默认拓扑。
  `text_encoder_tp_size` 在该 profile 只是 Stage 0 `tensor_parallel_size` alias，stage-scoped
  Stage 0 override 优先，Stage 1 的同名 override 被拒绝。^[PR #5885]

## 并行与加载约束

- H3 是 CFG-distilled pipeline，`cfg_parallel_size` 必须保持 `1`。VAE patch parallel
  使用 H3 原生 `tile` 模式；`text_encoder_tp_size` 作用在 DiT group 的前 N 个 rank，
  并且必须同时整除 Qwen3-VL 的 64 个 attention heads 与 8 个 KV heads。
- 单卡 accuracy 路径使用 CPU offload；多卡部署可使用 Ulysses、text-encoder TP、VAE
  tile/patch parallel 或 layerwise offload，但每个组合都必须按最终并行拓扑和设备数验证。
- bundled split defaults bind Stage 0 to TP2/max-num-seqs 1 and Stage 1 to TP1 + USP4 + VAE
  patch parallel 4 with `model_loaded.text_encoder: false`; regular uses 50 steps and the Turbo
  LoRA profile uses five steps with its flow shifts. They are an H3-specific placement profile,
  not a cross-node transport or general throughput claim.^[PR #5885]
- H3 DiT 支持加载时 online FP8：默认覆盖 token-refiner/主 block 的 attention、MLP、
  condition projection 和 AdaLN projection；video/audio patch、timestep MLP、最终输出头、
  text encoder 与 VAE 保持 BF16/FP32。`ignored_layers` 按 DiT 内部的精确 runtime prefix
  匹配，不带 `transformer.` owner prefix。checkpoint 的 grouped-QKV reorder 和 fused-MLP
  gate/up split 在 `MiniMaxH3DiTModel.load_weights()` 内先执行，再交给当前 vLLM loader，
  以保留 TP shard 与 FP8 online-processing wrapper。
- H3 text encoder 的 eager loader 按 source shard 分别证明 fused q/k/v 与 gate/up 完整，且任何
  未加载 plain retained parameter 都令启动失败；pipeline 批量上报 encoder parameter 的严格性
  依赖这项保证。video/audio VAE 没有等价 completeness guarantee，不能由此推断。见 MMH3-1f。
- H3 online FP8 当前不得与 layerwise offload 组合：offload 产生的 weight stride
  会被 Cutlass FP8 kernel 拒绝。变更量化覆盖范围时，除逐层命中/排除与加载转换测试外，
  必须同时保护 joint video/audio 质量；peak memory 只作为同 case report，不是稳定上界。
- The two-GPU H100-80GB full-model FP8 quality test must apply `text_encoder_tp_size=2` in the
  shared eager, TP2, VAE-tiling kwargs used by both the fused BF16 baseline and transformer-FP8
  candidate. It prevents baseline initialization OOM by sharding the colocated text encoder;
  it is test-only resource-topology evidence, not a runtime behavior or cross-hardware claim.
  ^[PR #6742]
- 音频加载优先使用 torchaudio；当 TorchCodec/torchaudio 在 CPU-only aarch64 环境不可用
  时，`reference_video.load_audio_file` 回退到 soundfile，再对 libsndfile 不支持的格式
  通过 ffmpeg 转 WAV。该回退保持 `(channels, samples)` float32 与原始 sample rate 合同。
- conditioned image/video VAE 用固定内部 seed，并把 parameter 的真实 `device_type` 传给
  `fork_rng`，以保存/恢复 CPU 与对应 accelerator RNG；MUSA recipe 记录 MTT S5000，PR #5837
  另报告 Ascend NPU smoke/FL2VA 成功。目标实现接纳已注册的非 CPU device module，但持续
  回归、XPU/ROCm 与并发边界仍见 MMH3-2c。
- H3 q/k 使用共享 RMSNorm（BF16 gamma、native FP32 accumulation）与 NeoX RoPE；每个
  128 维 head 只旋转前 96 维并保留后 32 维；MindIE-SD 前还要把 H3 的 3D q/k 临时补成
  4D batch layout，再恢复原 shape。MUSA dynamic compile 独立保留 aten RMSNorm graph 并内联
  full-dim NeoX RoPE，静态 rot width 从 config 派生；平台 fallback、共享 blast radius 与有界
  region-only 性能证据见 MMH3-1c/DIFF-1e。
- H3 VAE decoder 的 exact eager ops 仍由 model owner 管理：只有 SM90/SM100/SM103 allowlist、
  remote-code structure 和每个 tensor guard 都满足时才安装。仅 decoder Transformer-block
  Linear 固化为 decode autocast 已使用的 FP16；keyframe encode 与 `proj_out` 等非 block
  parameter 继续 FP32。compile、spatial-parallel 及任何 platform/shape/dtype/layout/gradient
  guard 均回原 operation；完整合同见 MMH3-4c。^[PR #6607]
- Ascend NPU 可选择 RainFusion 稀疏 video tail，并从 BF16 checkpoint 做 online INT8；两者只在
  exact T2VA/Ulysses/no-AllGather DLO 配置有完成证据，几何 fallback、TP width 与组合边界见
  MMH3-1a/[RainFusion rules](rules-rainfusion.md)。
- Ascend NPU `FLASH_ATTN` 的 H3 non-Ring packed path 可 opt in mask-free varlen，Laser env 改走
  prefix K/V slice + 256 input scale；shared fallback/metadata 与 target TeaCache regression 见
  MMH3-1g/DIFF-1g，有界 kernel/E2E/HBM 证据见 MMH3-3g。
- ROCm BF16 的 gfx942/MI300X 四卡与 gfx950/MI350 单卡 functional evidence、AITER backend gate、
  mutable image 和 support-table 不一致边界见 MMH3-3d；不得从 gfx architecture 名直接扩展 SKU。
- TeaCache 只 hook FL2VA DiT，Ref2VA-only 拒绝；model default、public 入口覆盖、request `quality`
  交互与单 H100 校准边界见 MMH3-2g。
- distilled checkpoint 的 continuous RF `base_schedule`、四步语义与 partition
  隔离见 MMH3-2h；它不替换 H3 的自定义 solver。
- FastH3 是 exact FastVideo artifact 的 startup-only t2va fusion；它不使用 Turbo/native dynamic
  manager，strict artifact/request/offload gates 见 MMH3-2n。^[PR #6714]
- H100_2 merge lane 的 FL2VA/Ref2VA/Turbo/FastH3 四个隔离 process 只构成精确 L3 media
  contract，不能升级为 runtime 或性能支持声明；见 MMH3-3m。^[PR #6556]
- step execution 是 H3 的模型专有 stateful path：只在 resolved attention backend 能隔离多个 packed documents 时合并 request；否则仍逐 request 前向。request state、rank-0 preparation、Cache-DiT/DLO/multi-output 排除与有界验证证据见 MMH3-2k，不能由 generic runner guard 推断 multi-rank failure synchronization。^[PR #5810]
- LightX2V Turbo v1.0 仅支持 legacy dynamic LoRA；精确 artifact mapping、packed QKV/FC1
  binding、active-request sampling 合同与 DLO-resident A/B sidecar 边界见 MMH3-2j；转换后的 mixed-rank
  native PEFT checkpoint 不在该支持声明内。
- FlashGen native v1.0 同样经 legacy `DiffusionLoRAManager` dynamic path，但以 safetensors
  `key_format=minimax-h3-native` 选择独立 parser；artifact、packing、schedule 与 offload gates
  见 MMH3-2m。NPU 子目录或作者报告均不构成平台、性能或端到端验证。^[PR #6666]
- datacenter Blackwell 上 H3 可默认 dense BF16 TRTLLM；single-request producer-owned
  `PackedPaddingMetadata` 可替代 structural suffix mask，generic ragged/continuous batches仍按
  cu_seqlens 隔离 documents。SAGE short-role 与 multi-request tail gate、mask/metadata fail-closed、
  AllGather-KV 禁用及有界 performance evidence 见 MMH3-1e。^[PR #6542]
- 2×consumer-GPU profile 使用 TP-local no-AllGather DLO、VAE patch parallel、cuDNN attention
  和 eager execution；resident layers 只改变 HBM/transfer，不减少 pinned host master。
  实现合同与 standalone-audio staging 缺口见 MMH3-3a，5090/4090 证据边界见 MMH3-3b。
- DGX Spark/GB10 的 unified-memory profile 必须保持单分区 resident FP8，禁用 CPU/DLO offload
  并显式提高 sync timeout；单图 Ref2VA/T2VA 的 exact workload、容量、热态测量与未测扩展边界见
  MMH3-3e。
- RTX PRO 6000 的 2/4/8-GPU BF16 profile 保持 TP2 并扩大 Ulysses；单次 T2VA scaling、SM120
  backend、PCIe/NUMA 与未测 Ref2VA/替代拓扑边界见 MMH3-3f。
- RTX PRO 5000 的 2 卡低显存路径使用 20 resident-layer rank-local DLO，4/8 卡使用 resident
  TP×Ulysses；topology-aware device order、单请求测量范围及明确未测 Ref2VA 的边界见 MMH3-3h。

## ComfyUI 请求路由

MiniMax H3 的 `t2va`、`fl2va` 和 `ref2va` frontend 选择、reference multipart 字段及
Hub/local model lookup 合同由 [ComfyUI tooling rules](../../tooling/rules.md) 负责；模型页不复制
客户端规则。

## 验证入口

模型专属 contract、packing 和 parallel 测试在 `tests/diffusion/models/minimax_h3/`。
full-model accuracy/nightly 入口现保留 I2VA 与 Ref2VA，两者都从
Hugging Face `main` 下载模型分区与 SHA-256 固定的 official assets；模型
`main` 仍可漂移。两例固定 1344x768/24 FPS/AAC 32 kHz stereo/50 steps/
seed 0，帧数分别 192/124，共用 SSIM>=0.97、PSNR>=34 dB gate。nightly
lane 声明 4x H100，PR 数值则来自 4x B300，不得混为同一硬件证据。
T2VA 因当前严格 gate 未达标被移出；这表示“无 retained pixel-level gate”，
不是 T2VA 功能不支持。该用例是精度/媒体合同，不是性能基线。^[PR #5978]
硬件 recipe 只记录已验证的 GPU/NPU 形状；性能数字不能从 recipe 的配置示例泛化为全硬件
保证。目标 pin 的 MUSA Ref2VA recipe 已改为 `MODEL_ROOT/Ref2VA` + `--task-type ref2va`；
它只验证单分区启动，不能外推 combined 双 DiT 的容量或性能。共享 offloader、并行和请求合同分别归 [Diffusion](../../components/diffusion/_index.md)、
[Configuration](../../components/configuration/_index.md) 和 [Serving](../../components/serving/_index.md)。

另有 ready L2 smoke 使用 TP=1/DP=2 的 distributed layerwise offload、two concurrent
`/v1/videos/sync` T2VA requests、4 steps 和 1344×768/24 FPS；它同时断言 MP4 video 与
nonempty decodable audio。该 YAML job 配置为两张 H100，但 PR 仅报告 local two-card B300
execution，不能代替 retained accuracy gate、Buildkite H100 result 或其他 parallel topology
的支持证据。^[PR #6555]

## 审查入口

H3 input matrix/media ingress，以及 text-encoder completeness、online FP8 的 component namespace、loader 顺序、joint quality 与 offload 边界见
[media rules](rules-media.md) 与 [MiniMax H3 rules](rules.md#direct-代码快速入口)；checkpoint transform、quantized loader 与
text-encoder fused-source 完整性正文见 [loading rules](rules-loading.md)；DLO、consumer/H100/ROCm
部署和硬件证据正文见 [deployment rules](rules-deployment.md)；conditioned VAE 确定性、modular task 选择与 request 级 Cache-DiT/TeaCache/sigma schedule/Turbo LoRA 生命周期见 [缓存与任务生命周期规则](rules-cache-task.md)。

H3 VAE decoder 的 model-local eager dispatch、remote-code eligibility、exactness guards、selective
FP16 materialization 与 compile/spatial-parallel fallback 见 [VAE eager-ops rules](rules-vae-ops.md)。
Qwen3-VL text encoder 的 cuDNN SDPA process-global-state restore、encoder-rank/VAE boundary 和
CPU-only validation limit 见 [encoder state rules](rules-encoder-state.md)。
