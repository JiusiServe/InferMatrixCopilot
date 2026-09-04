---
title: "MiniMax H3 规则"
created: 2026-09-02
updated: 2026-09-05
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #5703", "PR #5706", "PR #5720", "PR #5737", "PR #5764", "PR #5779", "PR #5801", "PR #5824", "PR #5829", "PR #5836", "PR #5837", "PR #5840", "PR #5853", "PR #5881", "PR #5891", "PR #5896", "PR #5991", "PR #5997", "PR #6000", "PR #6040", benchmarks/diffusion/backends.py, benchmarks/diffusion/diffusion_benchmark_serving.py, docs/user_guide/diffusion/attention_backends.md, vllm_omni/config/model.py, vllm_omni/config/omni_config.py, vllm_omni/diffusion/attention/backends/rainfusion_attn.py, vllm_omni/diffusion/attention/backends/trtllm_attn.py, vllm_omni/diffusion/cache/cachedit/backend.py, vllm_omni/diffusion/cache/cachedit/runtime.py, vllm_omni/diffusion/cache/teacache/, vllm_omni/diffusion/forward_context.py, vllm_omni/diffusion/layers/norm.py, vllm_omni/diffusion/layers/rope.py, vllm_omni/diffusion/model_metadata.py, vllm_omni/diffusion/models/minimax_h3/encoder.py, vllm_omni/diffusion/models/minimax_h3/lora.py, vllm_omni/diffusion/models/minimax_h3/minimax_h3_transformer.py, vllm_omni/diffusion/models/minimax_h3/pipeline_minimax_h3.py, vllm_omni/diffusion/models/minimax_h3/quality_policy.py, vllm_omni/diffusion/models/minimax_h3/time_request.py, vllm_omni/diffusion/models/minimax_h3/vae.py, vllm_omni/diffusion/offloader/module_residency.py, vllm_omni/diffusion/sched/sigma_schedule.py, vllm_omni/diffusion/utils/hf_utils.py, vllm_omni/entrypoints/omni_base.py, vllm_omni/quantization/int8_config.py, tests/dfx/perf/scripts/run_diffusion_benchmark.py, tests/dfx/perf/tests/test_minimax_h3_vllm_omni.json, tests/diffusion/attention/test_rainfusion_plan.py, tests/diffusion/attention/test_trtllm_attn.py, tests/diffusion/cache/test_cache_backends.py, tests/diffusion/cache/test_cache_dit_request_runtime.py, tests/diffusion/cache/test_teacache_extractors.py, tests/diffusion/layers/test_norm.py, tests/diffusion/layers/test_rope_broadcast.py, tests/diffusion/models/minimax_h3/test_minimax_h3_contract.py, tests/diffusion/models/minimax_h3/test_minimax_h3_dlo_lifecycle.py, tests/diffusion/models/minimax_h3/test_minimax_h3_lora.py, tests/diffusion/models/minimax_h3/test_minimax_h3_parallel.py, tests/diffusion/models/minimax_h3/test_minimax_h3_quality_policy.py, tests/diffusion/models/minimax_h3/test_minimax_h3_quantization.py, tests/diffusion/models/minimax_h3/test_minimax_h3_quantization_quality.py, tests/diffusion/offloader/test_module_residency.py, tests/diffusion/quantization/test_int8_config.py, recipes/MiniMaxAI/MiniMax-H3.md, recipes/MiniMaxAI/MiniMax-H3-5090.md, recipes/MiniMaxAI/MiniMax-H3-MUSA.md, recipes/MiniMaxAI/MiniMax-H3-NPU.md, vllm_omni/diffusion/worker/diffusion_model_runner.py, vllm_omni/engine/async_omni_engine.py, "PR #5915", "PR #5990", "vllm_omni/diffusion/layers/fused_qk_norm_rope.py", "vllm_omni/diffusion/cache/teacache/extractors.py", "tests/diffusion/layers/test_fused_qk_norm_rope.py", "PR #6061", "vllm_omni/platforms/npu/models/minimax_h3.py", "vllm_omni/platforms/npu/platform.py", "tests/diffusion/models/minimax_h3/test_minimax_h3_qwen3vl_rope.py", "PR #6167", "PR #6173", "PR #6283", "PR #6281", "vllm_omni/diffusion/attention/ops/minimax_h3_modulation.py", "PR #6476", "PR #6526", "PR #6410", vllm_omni/diffusion/models/minimax_h3/denoise_loop.py]
confidence: high
---

# MiniMax H3 规则

只有 `MMH3-数字字母` 是可审计规则 ID。

## Direct 代码快速入口

| PR 描述信号 | 规则 | 第一批源码 |
|---|---|---|
| online FP8、`ignored_layers`、component prefix | [MMH3-1a](rules-loading.md#mmh3-1a-component-namespace-与-checkpoint-transform-必须在-active-loader-前闭合) | `pipeline_minimax_h3.py::_resolve_component_quant_config` → `MiniMaxH3DiTModel` linear prefix |
| grouped QKV、fused MLP、weight loader、TP | [MMH3-1a](rules-loading.md#mmh3-1a-component-namespace-与-checkpoint-transform-必须在-active-loader-前闭合) | `minimax_h3_transformer.py::MiniMaxH3DiTModel.load_weights` → active vLLM loader |
| FP8 quality、audio metric、layerwise offload | `MMH3-1b` | quantization quality test → recipe/support matrix → nightly lane |
| RMSNorm、RoPE、96/128 rotary dim、fused backend | `MMH3-1c` | `MiniMaxH3Attention` → shared `RMSNorm`/`RotaryEmbedding` → platform dispatch |
| RainFusion/NPU INT8；decoded video BCTHW→BTHWC uint8 | `MMH3-1d`, [MMH3-1o](rules-media.md#mmh3-1o-h3-decoded-video-必须在-transfer-前定型为-contiguous-uint8) | attention plan；H3 output prepare/postprocess → video uint8 consumer |
| TRTLLM、ragged packed metadata、SAGE、Skip-Softmax、Blackwell default | `MMH3-1e` | H3 metadata/roles → TRTLLM packed trim/quant gate → platform default |
| text encoder、missing q/k/v 或 gate/up、eager load bookkeeping | [MMH3-1f](rules-loading.md#mmh3-1f-text-encoder-eager-load-必须证明每个-source-shard-完整) | `encoder.py::_load_weights` → `pipeline_minimax_h3.py::load_weights` strict report |
| NPU packed varlen、quadratic mask、LaserAttention、prefix K/V | `MMH3-1g` | H3 packed producer → backend capability/metadata → NPU FlashAttention fallback |
| Qwen3-VL encoder、NPU causal GQA、AddRMSNorm residual | `MMH3-1k` | encoder SDPA helper/residual call → NPU model patch → `torch_npu` op |
| Qwen3-VL encoder、cuDNN SDPA、process-global backend state、encoder TP | [MMH3-1n](rules-encoder-state.md#mmh3-1n-qwen3-vl-encoder-的-cudnn-sdpa-override-必须恢复原状态) | `encode_ids` state capture/restore → encoder-rank call → VAE boundary |
| VAE decoder、Triton exact ops、FP16 materialization、SM90/100/103、compile/SP fallback | [MMH3-4c](rules-vae-ops.md#mmh3-4c-h3-vae-eager-ops-必须以完整远程模型合同和-reference-fallback-安装) | `vae.py::MiniMaxH3VideoVAE.__init__` → `ops/vae::{dispatch,install}` → target tests |
| FL2VA keyframe、Ref2VA mixed reference/时域限界、shape/output matrix | [MMH3-2a](rules-media.md#mmh3-2a-taskreferenceshape-与多输出必须作为一个输入矩阵维护) | `pipeline_minimax_h3.py` → `reference_video.py` |
| media limit、typed/multipart reference、HTTP 400、temp source | [MMH3-2b](rules-media.md#mmh3-2b-media-ingress-在解码前限界request-错误保持-http-400) | `api_server.py` → `serving_video.py` → `reference_video.py` |
| split text encoder、H3 presentation/tag、conditioning bridge、prepared artifact | [MMH3-2l](rules-media.md#mmh3-2l-split-text-encoder-必须保持-h3-presentation条件载荷与原始媒体的所有权) | Stage-0 prompt transform → `MiniMaxH3TextEncoder` → prefix-cache payload → Stage-1 H3 diffusion |
| conditioned VAE、fixed seed、`fork_rng`、MUSA/device RNG | [MMH3-2c](rules-cache-task.md#mmh3-2c-conditioned-vae-的固定种子必须按实际设备隔离并恢复) | `pipeline_minimax_h3.py` condition encode caller → `vae.py::{encode_image,encode_video}` |
| modular checkpoint、combined/partition task、两套 DiT、shared component | [MMH3-2d](rules-cache-task.md#mmh3-2d-modular-h3-的-task-selector-必须同步权重能力与所有-dit-lifecycle) | model index discovery → startup task selection → task-specific transformer/cache lifecycle |
| request `quality`、lossless/high、dynamic Cache-DiT | [MMH3-2e](rules-cache-task.md#mmh3-2e-quality-映射只决定-request-的-cache-dit-目标) | request sampling → quality policy → request Cache-DiT runtime → denoise |
| force-refresh hint、once/repeat、reinstall key | [MMH3-2f](rules-cache-task.md#mmh3-2f-force-refresh-hint-属于-active-profile-identity) | H3 `extra_args` validation → immutable cache config → installation key/refresh context |
| TeaCache、FL2VA coefficients、0.17、combined/Ref2VA | [MMH3-2g](rules-cache-task.md#mmh3-2g-h3-teacache-只绑定-fl2va-校准与-request-state) | custom enabler → H3 extractor → module-resident hook state / per-generation reset |
| distilled、DMD2、`base_schedule`、4-step、sigma boundary | [MMH3-2h](rules-cache-task.md#mmh3-2h-distilled-sigma-schedule-按-partition-所有且以区间计步) | partition model metadata → `DMD2SigmaSchedule` → H3 video/audio shifted sigmas |
| LightX2V Turbo、legacy dynamic LoRA、packed QKV/FC1、five sigma points、DLO resident A/B sidecars | [MMH3-2j](rules-cache-task.md#mmh3-2j-turbo-lora-只接受精确发布-artifact并与-h3-tasksampling-和-offload-lifecycle-共同门禁) | `lora.py::load_minimax_h3_turbo_lora` → pipeline hook/sampling validation → `DiffusionLoRAManager` |
| FlashGen native LoRA、grouped QKV、adapter sigma schedule、legacy manager binding | [MMH3-2m](rules-cache-task.md#mmh3-2m-flashgen-native-lora-必须保持-artifactschedule-与-legacy-manager-边界) | `npu/lora.py::load_minimax_h3_native_lora` → H3 pipeline active-adapter validation → unchanged `DiffusionLoRAManager` ^[PR #6666] |
| FastH3 VSA、`vsa-datafree`、`FASTVIDEO_VSA`、four-step、load-time fusion | [MMH3-2n](rules-cache-task.md#mmh3-2n-fasth3-只接受精确-artifact并将-vsa-gate-在启动时一次性融合) | `fasth3.py` identity/strict fusion → pipeline gate injection/consumption → serving/request gate |
| step execution、continuous batching、multi-document packing、rank-0 prepare failure | [MMH3-2k](rules-cache-task.md#mmh3-2k-h3-step-execution-必须保持请求状态attention-文档和-rank-0-prepare-隔离) | `pipeline_minimax_h3.py::{prepare_encode,denoise_step,step_scheduler}` → `batched_packing.py` → runner |
| DLO、TP-local、resident layers、allocator cache、encoder/VAE staging | [MMH3-3a](rules-deployment.md#mmh3-3a-h3-dlo-必须保持-loader-layout-与-component-stage-配对) | H3 `_offload_plan` → `BoundedAllocatorCache`/`PinnedModuleStager` → pipeline encode/denoise/decode stage contexts |
| RTX 5090/4090、24/32 GiB、consumer profile | [MMH3-3b](rules-deployment.md#mmh3-3b-consumer-gpu-profile-是有边界的容量证据) | recipe measurement commit/run record → exact target topology → quality/capacity validation |
| 4×H100、DFX perf、T2V/TI2V/V2V、synthetic H.264 reference | [MMH3-3c](rules-deployment.md#mmh3-3c-h100-dfx-fixture-只证明-exact-nightly-workload-与-payload-path) | nightly lane → perf JSON → benchmark request encoder/result artifact |
| ROCm、gfx942/gfx950、AITER、BF16、support matrix | [MMH3-3d](rules-deployment.md#mmh3-3d-rocm-support-必须按-sku镜像拓扑和测量协议限界) | support table/footnote → recipe protocol → ROCm backend gate → exact hardware evidence |
| DGX Spark、GB10、unified memory、FP8、offload/OOM | [MMH3-3e](rules-deployment.md#mmh3-3e-gb10-unified-memory-容量证据不等于离散-gpu-offload-合同) | single-partition recipe → allocator/header evidence → output probe |
| RTX PRO 6000、TP2、Ulysses、2/4/8 GPU、PCIe | [MMH3-3f](rules-deployment.md#mmh3-3f-rtx-pro-6000-scaling-只绑定单机-t2va-协议) | topology → exact warmed T2VA measurements → memory method |
| Ascend packed varlen、LaserAttention、mask churn、E2E/HBM | [MMH3-3g](rules-deployment.md#mmh3-3g-ascend-mask-free-数字只绑定报告的-h3-packed-workload) | H3 opt-in → exact NPU topology/workload → kernel/E2E/memory evidence |
| H100_2 merge、FL2VA/Ref2VA DP2、Turbo、FastH3 | [MMH3-3m](rules-deployment.md#mmh3-3m-h100_2-merge-lane-只覆盖精确-h3-ci-matrix) | one CI job → four isolated pytest processes → bounded media assertions |

## MMH3-1b — joint video/audio quality 与 offload 兼容性必须一起验收

- 触发：改变 H3 FP8 layer scope、kernel/loader、quality threshold、offload 或 nightly lane。
- 强制：H3 online FP8 与 layerwise offload 当前标为 incompatible；resident FP8 可与 TP、VAE
  tiling 组合。BF16/FP8 A/B 使用同一 immutable checkpoint、prompt、seed、size、frames、
  steps、输入合同与并行/资源设置；T2VA case 即使显式给出 width/height，也必须在
  `sampling_params.extra_args` 带合法 named `aspect_ratio`。joint output 同时检查 video LPIPS
  和 32 kHz audio 的 spectral cosine/RMS ratio。PSNR、MAE 与 peak memory 是 report-only
  指标，不能冒充 gate。
- 禁止：只验视频就宣称 H3 joint-output quality；把一次 22% memory observation 写成稳定
  上界；让 FP8+layerwise offload 到 Cutlass kernel 才因 flattened-weight stride 失败。
- 验收：当前 2x H100 case 的 gates 是 LPIPS <= 0.20、audio spectral cosine >= 0.80、
  RMS ratio 在 0.50–2.00，且 sample rate 为 32000；单测还要证明 phase-tolerant metric
  接受相移但拒绝 spectral drift。质量 test 的 T2VA `aspect_ratio="16:9"` 是同一 case 的
  必填输入，不是量化变量；输入合同演进后应修正 fixture，不能靠跳过 case 或放宽质量 gate
  恢复 CI。^[PR #5737] ^[PR #5829]

## MMH3-1c — H3 fused norm/RoPE 必须保持 checkpoint dtype 与 partial-rotation 布局

- 触发：修改 H3 q/k norm、RoPE frequency packing、head dim 或 shared fused-layer dispatch。
- 强制：H3 使用共享 `RMSNorm`，gamma 保持 BF16，而 native reduction/scale 在 FP32 累加后
  cast 回输入 dtype。CUDA/HIP eager 尝试 fused RMSNorm、异常时回退 native，compile tracing
  直接 native；MUSA 独立走 `F.rms_norm` 以保留 dynamic Inductor 可融合 graph；XPU 走 native，
  NPU 直接调用 `npu_rms_norm` 且没有该
  fallback。RoPE 使用 NeoX `RotaryEmbedding(half_head_dim=False)`：128 维 head 只旋转前 96 维
  并原样保留末 32 维；CUDA/HIP/native 把 H3 的 tiled full frequencies 转为 half kernel layout，
  XPU 走 native；MUSA 对这个 full-dim、非 interleaved NeoX case 走 inline full-frequency 公式，
  其他 layout 回 native；MindIE 接收 full layout。H3 `_apply_rope` 的 q/k 是 3D `[S,H,D]`；
  MindIE-SD kernel 只收 4D，因此 shared adapter 必须临时变为 `[1,S,H,D]` 并把输出恢复到 3D。
- 强制：H3 旋转宽度从 config 静态派生为 `rot_dim = 6 * rope_inv_freq_len`，默认 16 得到 96，
  不再在 forward 从 `freqs.shape[-1]` 读取动态 symbol。这样 compile 保持静态 slice，但 caller 仍
  只调用 shared `RotaryEmbedding`、不含平台分支；config 与 frequency producer 不一致必须由 parity
  test 暴露，不能静默旋转另一宽度。^[PR #5881]
- 禁止：把任意 96 维随机 frequency 当成 H3 producer 合同；合法 full layout 是同一 48 维
  half 的拼接。也不能从 CPU/reference 与 mocked NPU/MindIE wiring 推断真实 fused-kernel parity。
  PR #5896 的新增 mock 只断言 MindIE 收到 4D、输出恢复 3D 且 identity 回传不变；没有执行真实
  rotary 数学，也没有新增原生 4D control。
- 验收：以 `cat([half, half])` frequency 对照 native reference，逐值断言 96 维旋转和 32 维
  passthrough；另测 BF16 gamma/FP32 accumulation、compile native path 与各平台参数 wiring。
  真实 kernel 性能与数值结论需目标硬件复测；PR 报告的 491014→475070 ms 来自非目标
  `5215e03a` 且缺硬件与重复次数，只能作为有界外部观察，不能写成稳定 3.35% 保证。PR #5896
  body 报告 8×Ascend 910B3、USP8/Ring1/DLO、50-step T2VA 完成并附视频，但 commit 只写
  `main`、无数值对照或重复测量；它只补充运行完成证据。^[PR #5801] ^[PR #5896]
- 验收：MUSA 性能证据只绑定 1×MTT S5000、driver 3.3.5-server、immutable container digest、
  BF16 packed QKV、S=96000、7 local heads、head_dim 128/rot_dim 96、
  `torch.compile(fullgraph=True,dynamic=True)`，5 warmups、2 discarded pilots、20 个带 512 MiB
  cache flush 的交错样本。该 exact Q/K RMSNorm+RoPE region 的 event median
  30.0062→1.6323 ms（18.38×），同步 wall 30.0695→1.6893 ms（17.80×）；不是 TP8、端到端
  request、其他 shape/dtype/layout 或其他 MUSA SKU 的保证。finite/shape/BF16 gate 与 direct-inline
  接近只覆盖该 A/B，且未给 correctness tolerance/reference、benchmark script 或 raw artifact；
  当前自动测试没有 MUSA dispatch/parity，CPU reference 只验证 96 维旋转和 32 维
  passthrough。^[PR #5881]

## MMH3-1e — H3 TRTLLM 必须从 packed 结构裁掉 padding 并隔离短序列 role

- 触发：修改 H3 的 TRTLLM default、packed `cu_seqlens`/mask、SAGE quant、Skip-Softmax、
  token-refiner role 或 denoise timestep context。
- 强制：H3 只在支持的 datacenter Blackwell SM100/103、head_dim=128、FlashInfer kernel 可用且
  声明 compatible packed/mask-free path 时默认 dense BF16 TRTLLM；SM120/121、缺依赖、错误
  head dim 或需要任意 mask 的路径保留平台 fallback，默认不自动开启 SAGE/Skip-Softmax。
- 强制：四个 packed metadata key 必须完整、Q/K batch/terminal 覆盖一致。单 request 的
  producer-owned `[real,pad]` path 仅在 non-Ring backend 声明 `supports_packed_mask_free()` 时可省略
  `attn_mask`，并同时发布 Python `q_length`/`kv_length` 与同 device、`int32`、canonical
  `[0,length]` 的 `PackedPaddingMetadata` views；TRTLLM 必须核对长度、bounds、max-length 与
  `valid_kv_length` 后裁掉 suffix、再 quantize/attention，并把输出补零到 Ulysses 物理 shape。
  TRTLLM 对任何 nonempty `attn_mask` 一律 fail closed；generic ragged cu_seqlens 仍是多 document
  block-diagonal path，`[0,N,N]` 尾部空 sequence 必须折叠。AllGather-KV 的 local-Q/global-KV
  metadata 不对称合同在初始化时明确拒绝，真正支持按 review 明确延期。
- 强制：main DiT 与 `minimax_h3.token_refiner` 使用独立 role；任一 KV sequence 短于 SAGE
  `k_block_size` 时该 input 告警并走 dense TRTLLM，不能让 14-token refiner 产生 non-finite，
  也不能因此关闭 main DiT 的 SAGE。H3 将 scheduler 的降序 sigma（1→0）发布为
  `normalized_timestep`；Skip-Softmax 在 sigma 大于 `disabled_until_timestep` 时保持 dense，
  到达或低于阈值才启用。
- 禁止：把 producer-owned packed-padding shortcut 泛化为任意 mask、multi-request batch 或第三方
  metadata；让 padding 进入 SAGE block quantization；把 combined packed-H3 优化视频归因于本 PR
  单一改动。请求级 `set_forward_context` wrapper 会在 `finally` 恢复 prior context，因此 loop 内的
  step mutation 不会泄漏到后续请求。
- 验收：测试覆盖 generic ragged batch、single-request packed-padding suffix trim/zero restore、empty
  terminal、complete packed metadata 加 nonempty mask 的 unconditional rejection、invalid metadata、
  short-role dense fallback、AllGather rejection 与 non-finite regression。Continuous batching 必须
  覆盖 aligned non-final request 的严格递增 `cu_seqlens`；SAGE gate 应只依据 real documents，当前
  multi-request alignment-tail case 仍可能使整 batch dense，是 PR #6542 留下的 unresolved P3，不能
  声称 SAGE 保持启用。PR 报告的 4×B300 SXM6、TP1/Ulysses4/Ring1、1344×768、243 frames、49
  updates、dense BF16 TRTLLM、单 warmup 后 Nsight interval 从 final Ulysses all-to-all 到 main FMHA：
  9,797/9,680 paired samples的 gap p50 499.683→0.352 us、p95 698.308→0.384 us，且中间 GPU
  activity/D2H copy 为 244,925/97,970→0/0；这只证明该 exact profiling interval，不是 E2E
  latency、quality 或其他 workload/backend/topology 的保证。此前 PR 的 4×B300 SM103、
  1248×768、209 frames、50 steps FA4/TRTLLM 对比仅绑定该 prompt/seed/topology：PSNR 27.10、
  SSIM 0.8880 不是质量 gate；83.854→71.990 s diffusion、88.558→76.176 s wall 的 warmed A/B
  来自 review follow-up 外部分支 commit `20cc23ae`，其 artifacts 明确是 combined packed-H3
  optimization evidence，并非目标 commit 的隔离实验，不能泛化为稳定 14% 保证。^[PR #5779] ^[PR #6542]

## MMH3-1g — H3 NPU mask-free opt-in 必须保留 Ring 与 malformed-metadata fallback

- 触发：修改 H3 `_run_packed_attention`、NPU Flash backend capability、packed padding 或
  LaserAttention scale。
- 强制：H3 在非 Ring 时可因 backend 的 prefix slicing 或 packed-mask-free capability 不构造 mask，
  并发布四个 cu/max key、`valid_kv_length`、`npu_attn_varlen=True` 和
  `laser_input_scale=256.0`。Ring 必须令 opt-in false 并保留 padding mask，因为 aligned rows 是固定
  P2P buffer 合同；CUDA packed varlen/cuDNN prefix slicing 继续走各自 capability，H3 caller 不按
  platform 分支。shared NPU resolver/fallback 细节见 DIFF-1g。
- 禁止：让 capability method 变成 duck-typed backend 的硬依赖却不更新 doubles/plugins；不能把
  H3 的 `[real,pad]` contract 泛化为 ragged multi-document。Laser 的 256 缩放只针对报告的 fp16
  workspace overflow，其他 backend 忽略；online KV quant path不经过本优化。repo 内 TeaCache
  `FakeBackend` 现已实现 capability 并返回 false，所以 extractor tests 保持 abstract-default 的
  masked path；这不等于 production consumer 已有 default-safe access。第三方 duck-typed backend
  仍必须继承 base 或实现该 classmethod，并对 registry override 做 capability census。
- 验收：model contract tests 分别覆盖 prefix-slice、packed-mask-free、普通 backend 与 Ring；backend
  tests 再覆盖 malformed fallback 和 Laser math。真实 Ascend parity/内存/延迟证据不能由 CPU mock
  替代；同 seed E2E output comparison 与重新抓 memory snapshot 在 PR 中仍列为 follow-up。
  ^[PR #5891] ^[PR #5997]

## MMH3-1h — H3 必须预构造 packed RoPE table 并让缓存提取器复用

- 触发：修改 MiniMax H3 的 `MiniMaxH3Rope`、`MiniMaxH3Attention`、SP prepare、TeaCache extractor 或 q/k fused 调用。
- 强制：H3 先将 `MiniMaxH3Rope` 的 tiled frequency 输出交给 `_build_rope_table`，只从其前半段构造 cos/sin 并生成 BF16 packed table；该 table 必须在完整 packed sequence 上构造一次，经 `sp_prepare` 原样传给所有 DiT blocks 和 attention，TeaCache extractor 复用同一 helper。`rope_table=None` 的 token-refiner 路径继续只做 q/k RMSNorm；H3 的 128 维 head 只旋转前 96 维并保留后 32 维。共享算子边界以 [DIFF-1l](../../components/diffusion/rules.md#diff-1l-fused-qk-rmsnorm-与-packed-rope-必须共享布局并保留-eager-fallback) 为准。
- 禁止：把 H3 已复制的第二个 frequency half 当成独立 sin 输入，向 fused API 传 raw `rope_freqs`，或在每个 block、SP 分支和 TeaCache extractor 内重建不同 table；也不能把 token-refiner 的无 RoPE 路径误接到 fused table 调用。
- 验收：模型合同测试须断言完整 sequence 的 table shape 与 `[cos, sin]` 数值、SP 透传 identity、DiT q/k 的 96/128 partial rotation 和 32 维 tail preservation，并覆盖 TeaCache extractor 与 `rope_table=None` 分支。当前 PR 新增的仅是独立 fused-kernel BF16 测试，没有 H3 集成或 TeaCache 数值回归，因此不能据此宣称模型端到端 parity。^[PR #5990]
  在 NPU，BF16 packed table 必须 request-/SP-rank-local，且 shape、width、device、dtype 与本 rank span 一致；不能重建 model-global table 或把复用写成通用性能保证。^[PR #6410]

## MMH3-1i — Qwen3-VL 文本编码器 NPU RoPE 必须保持 BNSD 与逐样本 M-RoPE

- 触发：修改 MiniMax H3 Qwen3-VL text encoder 在 Ascend NPU 上的 `_apply_rotary_pos_emb`、`npu_rotary_mul_with_bsnd_fallback`、BNSD/BSND layout 或逐样本 M-RoPE。
- 强制：q/k 保持 BNSD `[batch, heads, seq, head_dim]`，`cos/sin` 保持逐样本 `[batch, seq, dim]` 并通过 `unsqueeze_dim=1` 对齐；优先使用 CANN 支持的 BNSD fused path，仅在不支持的 BNSD tiling shape 下回退 BSND，同时保留每个样本的 M-RoPE 频率，不改 MiniMax H3 DiT 的 `RotaryEmbedding` 路径。
- 禁止：把 batch-specific frequency 广播、展平或转置成单样本语义；绕过共享 helper 直接调用 NPU 算子而失去 fallback；用 helper 直测代替生产 platform hook 验证，或把该 text-encoder 优化外推到其他 H3 RoPE 路径和平台。
- 验收：NPU correctness tests 覆盖 BNSD fast shapes、BSND fallback shapes 和不同样本的真实 M-RoPE positions，分别以 NeoX reference 核对 q/k 输出并断言样本频率确实不同；另从平台注册入口验证生产 consumer 已启用 fused path。^[PR #6061]

## MMH3-1k — Qwen3-VL encoder 的 NPU GQA 与 AddRMSNorm 只改变目标平台合同

- 触发：修改 Qwen3-VL text encoder 的 `_scaled_dot_product_attention`、post-attention residual、NPU MiniMax-H3 patch 或 `RMSNorm` 的 optional residual 参数。
- 强制：通用 encoder helper 保持 causal SDPA 的 reference 语义：当本地 Q heads 多于 K/V heads 时先沿 head 维 repeat-interleave K/V；NPU patch 才保留压缩 BNSD `[B,Q,S,D]` / `[B,KV,S,D]` 输入并调用 `F.scaled_dot_product_attention(..., dropout_p=0.0, is_causal=True, enable_gqa=Q != KV)`。进入该 NPU op 前必须拒绝 K/V head 数不等、零 KV head 和不能整除的 Q:KV 比率。patch 与已有 RoPE/SwiGLU patch 独立且幂等，并仅在 NPU diffusion runtime 已建立、pipeline 尚未加载时注册到此 encoder helper。
- 强制：shared `RMSNorm(x, residual)` 的语义为先计算 `updated_residual = residual + x`，再以该值 norm，返回 `(normalized, updated_residual)`；MiniMax-H3 decoder 必须将此 updated residual 用于后续 MLP residual add。仅 NPU residual 分支调用 `torch_npu.npu_add_rms_norm`；CUDA、HIP、MUSA 和 XPU residual 分支保留 native equivalent，不能由这个补丁推断其他平台获得 fused AddNorm。
- 禁止：把 NPU compressed-GQA patch 提升为 shared diffusion Attention/backend policy、改变 DiT attention 或其他 encoder，或用 NPU mock wiring 宣称真实 kernel parity。不得把 PR 的单次 A3 eight-card FL2VA observation（one warmup；249028.120→248662.942 ms）写成跨 workload、checkpoint、topology 或平台的性能保证。
- 验收：CPU contract 覆盖通用 expanded-K/V fallback 与 decoder residual order；NPU 覆盖独立/幂等生产 patch、valid/invalid head shapes，以及真实 BF16 causal GQA 相对 expanded-K/V reference（PR fixture：`B=1,Q=8,KV=2,S=16,D=128`，`atol=rtol=2e-2`）。还应保留 native NPU op 的目标硬件数值测试；mock 仅可证明 parameters and registration wiring。^[PR #6040]

## MMH3-1j — strict Ulysses 必须保持局部 embedding 与 projection-before-gather 的边界

- 触发：修改 MiniMax-H3 的 strict Ulysses、`_embed()`、packed RoPE、`local_sp_prepare`、DiT final projection 或 `sp_gather` 边界。
- 强制：只有共享 strict-Ulysses gate 通过时，按 rank 的 packed span 先筛选 image/audio latent rows；token refiner 仍处理完整 text context 后再筛选 text rows；构造局部 embedding 与对应局部 RoPE rows，使用 `local_sp_prepare` 运行 blocks。局部 transformer 输出必须先执行 final projection，再拼接 video/audio logits 并 gather compact FP32 rows；恢复后按 architecture output width 拆分并执行原有 target/condition row selection。其余路径保留完整 embedding、RoPE、`sp_prepare`、hidden gather 后 projection 的旧顺序。
- 强制：TeaCache 的 strict-SP 路径保持 modulation input、hidden state、residual 与 cache decision 为 rank-local；以 SP MAX reduction 同步是否 compute，cache-forced rank 必须重置累计 L1 state，compact projected logits 只 gather 一次。非 strict/global 路径仍保留一次 hidden-state gather。^[PR #6410]
- 禁止：在局部路径 gather `[S, 5376]` BF16 hidden state；绕过 `sp_input---local_sp_prepare` hook；只截取 text embedding 而不先运行完整 refiner；修改 Ulysses Q/K/V all-to-all、attention backend、packed-prefix 或 scheduler 语义；把约 21 倍 gather payload 降低写成端到端性能保证。
- 验收：模型合同测试须证明各 rank 的局部 multimodal rows 拼接等于完整 embedding、RoPE 行数与 span 对齐、所有 fallback 恢复旧路径，并断言 projection-before-gather 的 payload width 与最终 logits/target/condition rows 等价；性能和 video/audio quality 只能在固定 PR workload、硬件、steps、seed 与 gate 下复核，不能外推到其他 task 或拓扑。 ^[PR #6173]

## MMH3-1m — H3 modulation 融合必须保持操作顺序、精度与平台回退

- 触发：修改 MiniMax H3 的 AdaLN scale/shift、gated residual、`norm1`/`norm2` 融合、最终输出调制、Triton modulation wrapper 或 TeaCache extractor 的对应调用。
- 强制：保持 H3 的操作顺序：`norm1` 后执行 indexed scale/shift，attention 后执行 gated residual 并紧接 `norm2` 与第二组 indexed affine，最终层继续在投影前调制；CUDA 融合路径使用 FP32 累加并在输出边界转换到目标 dtype。CPU fallback 必须保留旧的两步数值边界，即 RMSNorm 结果先转换为输入 dtype，再执行 affine；所有路径都必须按 `combined_indices` 逐行选择同一 shift、scale 和 gate。
- 禁止：交换 residual、RMSNorm、affine 或 MLP 的顺序；在 CUDA 融合路径重新引入 BF16 中间舍入后宣称同一精度；让非 CUDA 平台绕过原生 RMSNorm backend；把 CPU fallback 的结果或一次 H3 性能观察描述成 CUDA bit-exact、跨平台 parity 或通用加速保证。
- 验收：H3 contract test 以 eager 公式分别核对 `norm1` 调制、gated residual+`norm2` 调制和 final-layer 调制，覆盖 index reorder、空行、输出 dtype、CPU 两步 fallback 与 CUDA FP32 容差；NPU 测试必须确认使用 `RMSNorm.forward_npu`/`torch_npu.npu_rms_norm` 而非 Triton，并在固定 shape、steps、seed、硬件和 checkpoint 下单独验证 kernel 数量与性能。^[PR #6281]

## MMH3-4a — H3 Qwen3-VL NPU 文本 MLP 必须使用 packed gate/up 与融合 SwiGLU

- 触发：修改 MiniMax H3 Qwen3-VL text encoder 的 MLP、`gate_up_proj` packing、NPU fused operator 或对应 platform override。
- 强制：NPU 路径使用一次 `F.linear(x, self.gate_up_proj.weight)` 生成 packed gate/up，再调用 `torch_npu.npu_swiglu(gate_up, dim=-1)`，最后复用既有 `down_proj`；gate/up 顺序和结果须等价于 `F.silu(gate) * up`，且补丁只作用于 NPU 目标 text MLP，CPU/CUDA 保持原路径。
- 禁止：在 NPU 上切分 packed 权重后发起两次 `F.linear` 或使用未融合的 SiLU 乘法；只直接调用 helper 而不验证生产注册链；把该优化扩展到 H3 DiT 或其他模型。
- 验收：NPU 测试以多个 packed shape 对照 split projection reference，并从真实 diffusion runner 初始化入口断言目标 `MiniMaxH3Qwen3VLTextMLP.forward` 已替换且重复初始化幂等；未通过生产入口的 helper 数值测试不能作为 hook 生效证据。^[PR #6167]

## MMH3-4b — H3 DiT 的 packed SwiGLU 必须通过本地 activation 接入

- 触发：修改 MiniMax H3 `MiniMaxH3MLP`、`fc1` packed gate/up 输出或 DiT activation 实现。
- 强制：`MiniMaxH3MLP` 必须把 `fc1` 的 packed 输出按 `[gate, up]` 顺序直接交给本地 `SiluAndMul`，再将结果交给既有 `fc2`；模型接入遵循 [DIFF-1v](../../components/diffusion/rules.md) 的平台与精度合同，且只改变 H3 DiT，不改变 Qwen3-VL text encoder 的独立 MLP 路径。
- 禁止：在已选择 fused 路径后重新 `chunk` 并执行两次 native SiLU/乘法；用通用 vLLM activation 类替代本地 diffusion layer；把当前 NPU native fallback 描述成 H3 NPU fused support，或把一次 H3 性能/精度观察推广到其他 task、平台和拓扑。
- 验收：H3 contract test 用 packed sentinel 验证 gate/up 顺序、半维输出及 `fc2` 输入，并分别覆盖 CUDA fused 与 NPU/XPU/native fallback；固定 checkpoint、seed、steps 和输入对照 native/fused 输出并设数值容差，同时以 kernel/profile 证据确认优化路径确实生效。^[PR #6283]
