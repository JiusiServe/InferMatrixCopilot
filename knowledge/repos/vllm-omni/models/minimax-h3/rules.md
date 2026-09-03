---
title: "MiniMax H3 规则"
created: 2026-09-02
updated: 2026-09-04
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #5703", "PR #5706", "PR #5720", "PR #5737", "PR #5764", "PR #5779", "PR #5801", "PR #5824", "PR #5829", "PR #5836", "PR #5837", "PR #5840", "PR #5853", "PR #5881", "PR #5891", "PR #5896", "PR #5991", "PR #5997", "PR #6000", benchmarks/diffusion/backends.py, benchmarks/diffusion/diffusion_benchmark_serving.py, docs/user_guide/diffusion/attention_backends.md, vllm_omni/config/model.py, vllm_omni/config/omni_config.py, vllm_omni/diffusion/attention/backends/rainfusion_attn.py, vllm_omni/diffusion/attention/backends/trtllm_attn.py, vllm_omni/diffusion/cache/cachedit/backend.py, vllm_omni/diffusion/cache/cachedit/runtime.py, vllm_omni/diffusion/cache/teacache/, vllm_omni/diffusion/forward_context.py, vllm_omni/diffusion/layers/norm.py, vllm_omni/diffusion/layers/rope.py, vllm_omni/diffusion/model_metadata.py, vllm_omni/diffusion/models/minimax_h3/encoder.py, vllm_omni/diffusion/models/minimax_h3/minimax_h3_transformer.py, vllm_omni/diffusion/models/minimax_h3/pipeline_minimax_h3.py, vllm_omni/diffusion/models/minimax_h3/quality_policy.py, vllm_omni/diffusion/models/minimax_h3/time_request.py, vllm_omni/diffusion/models/minimax_h3/vae.py, vllm_omni/diffusion/sched/sigma_schedule.py, vllm_omni/diffusion/utils/hf_utils.py, vllm_omni/entrypoints/omni_base.py, vllm_omni/quantization/int8_config.py, tests/dfx/perf/scripts/run_diffusion_benchmark.py, tests/dfx/perf/tests/test_minimax_h3_vllm_omni.json, tests/diffusion/attention/test_rainfusion_plan.py, tests/diffusion/attention/test_trtllm_attn.py, tests/diffusion/cache/test_cache_backends.py, tests/diffusion/cache/test_cache_dit_request_runtime.py, tests/diffusion/cache/test_teacache_extractors.py, tests/diffusion/layers/test_norm.py, tests/diffusion/layers/test_rope_broadcast.py, tests/diffusion/models/minimax_h3/test_minimax_h3_contract.py, tests/diffusion/models/minimax_h3/test_minimax_h3_parallel.py, tests/diffusion/models/minimax_h3/test_minimax_h3_quality_policy.py, tests/diffusion/models/minimax_h3/test_minimax_h3_quantization.py, tests/diffusion/models/minimax_h3/test_minimax_h3_quantization_quality.py, tests/diffusion/quantization/test_int8_config.py, tests/diffusion/sched/test_dmd2_sigma_schedule.py, recipes/MiniMaxAI/MiniMax-H3.md, recipes/MiniMaxAI/MiniMax-H3-5090.md, recipes/MiniMaxAI/MiniMax-H3-MUSA.md, recipes/MiniMaxAI/MiniMax-H3-NPU.md, vllm_omni/diffusion/worker/diffusion_model_runner.py, vllm_omni/engine/async_omni_engine.py, "PR #5915"]
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
| RainFusion、block sparse、video layout、NPU INT8 | `MMH3-1d` | packed sequence → attention metadata/backend plan；quant config → prefixed linear → loader/post-load |
| TRTLLM、ragged packed metadata、SAGE、Skip-Softmax、Blackwell default | `MMH3-1e` | H3 metadata/roles → TRTLLM packed trim/quant gate → platform default |
| text encoder、missing q/k/v 或 gate/up、eager load bookkeeping | [MMH3-1f](rules-loading.md#mmh3-1f-text-encoder-eager-load-必须证明每个-source-shard-完整) | `encoder.py::_load_weights` → `pipeline_minimax_h3.py::load_weights` strict report |
| NPU packed varlen、quadratic mask、LaserAttention、prefix K/V | `MMH3-1g` | H3 packed producer → backend capability/metadata → NPU FlashAttention fallback |
| FL2VA keyframe、Ref2VA mixed reference/时域限界、shape/output matrix | [MMH3-2a](rules-media.md#mmh3-2a-taskreferenceshape-与多输出必须作为一个输入矩阵维护) | `pipeline_minimax_h3.py` → `reference_video.py` |
| media limit、typed/multipart reference、HTTP 400、temp source | [MMH3-2b](rules-media.md#mmh3-2b-media-ingress-在解码前限界request-错误保持-http-400) | `api_server.py` → `serving_video.py` → `reference_video.py` |
| conditioned VAE、fixed seed、`fork_rng`、MUSA/device RNG | `MMH3-2c` | `pipeline_minimax_h3.py` condition encode caller → `vae.py::{encode_image,encode_video}` |
| modular checkpoint、combined/partition task、两套 DiT、shared component | `MMH3-2d` | model index discovery → startup task selection → task-specific transformer/cache lifecycle |
| request `quality`、lossless/high、dynamic Cache-DiT | `MMH3-2e` | request sampling → quality policy → request Cache-DiT runtime → denoise |
| force-refresh hint、once/repeat、reinstall key | `MMH3-2f` | H3 `extra_args` validation → immutable cache config → installation key/refresh context |
| TeaCache、FL2VA coefficients、0.17、combined/Ref2VA | `MMH3-2g` | custom enabler → H3 extractor → module-resident hook state / per-generation reset |
| distilled、DMD2、`base_schedule`、4-step、sigma boundary | `MMH3-2h` | partition model metadata → `DMD2SigmaSchedule` → H3 video/audio shifted sigmas |
| DLO、TP-local、resident layers、encoder/VAE staging | [MMH3-3a](rules-deployment.md#mmh3-3a-h3-dlo-必须保持-loader-layout-与-component-stage-配对) | H3 `_offload_plan` → shared DLO backend → pipeline encode/denoise/decode stage contexts |
| RTX 5090/4090、24/32 GiB、consumer profile | [MMH3-3b](rules-deployment.md#mmh3-3b-consumer-gpu-profile-是有边界的容量证据) | recipe measurement commit/run record → exact target topology → quality/capacity validation |
| 4×H100、DFX perf、T2V/TI2V/V2V、synthetic H.264 reference | [MMH3-3c](rules-deployment.md#mmh3-3c-h100-dfx-fixture-只证明-exact-nightly-workload-与-payload-path) | nightly lane → perf JSON → benchmark request encoder/result artifact |
| ROCm、gfx942/gfx950、AITER、BF16、support matrix | [MMH3-3d](rules-deployment.md#mmh3-3d-rocm-support-必须按-sku镜像拓扑和测量协议限界) | support table/footnote → recipe protocol → ROCm backend gate → exact hardware evidence |
| DGX Spark、GB10、unified memory、FP8、offload/OOM | [MMH3-3e](rules-deployment.md#mmh3-3e-gb10-unified-memory-容量证据不等于离散-gpu-offload-合同) | single-partition recipe → allocator/header evidence → output probe |
| RTX PRO 6000、TP2、Ulysses、2/4/8 GPU、PCIe | [MMH3-3f](rules-deployment.md#mmh3-3f-rtx-pro-6000-scaling-只绑定单机-t2va-协议) | topology → exact warmed T2VA measurements → memory method |
| Ascend packed varlen、LaserAttention、mask churn、E2E/HBM | [MMH3-3g](rules-deployment.md#mmh3-3g-ascend-mask-free-数字只绑定报告的-h3-packed-workload) | H3 opt-in → exact NPU topology/workload → kernel/E2E/memory evidence |

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

## MMH3-1d — RainFusion 只在完整 H3 video tail 上稀疏

- 触发：修改 `RAINFUSION_ATTN`、`block_sparse`、packed video geometry、attention layout、
  denoise step/layer skip 或 NPU backend resolution。
- 强制：显式选择时所有平台在构造模型前检查 backend platform/dependency；RainFusion 仅支持
  Ascend NPU、要求 MindIE-SD，且不兼容 Ring（用 Ulysses）。H3 attention 显式声明 BSND，
  `VideoTokenLayout(prefix_len, latent_grid)` 必须证明 video 是 packed document 0 的 tail。
- 强制：只有 sparsity>0、step>=start_step、非 skip layer 且 video>=32×128 rows 时调用
  `rf_v2`；prefix/text/reference/audio 保持 dense。无 layout、无 `max_seqlen_q`、长度不闭合、
  短序列或未声明 layout 仍走 NPU Flash dense fallback。video rows 不被 128 整除时
  也传给 updated MindIE-SD，由它将 irregular real-video suffix 纳入 always-kept 段；
  vLLM 不 padding。shared planner 和 dependency 边界见 DIFF-1h。
- 禁止：把 nominal sparsity 当 realized sparsity或质量保证；未声明 layout 时不能让 sparse path
  假设 BSND 而 dense fallback 解释成 BNSD。INT8、RainFusion、no-AllGather DLO 可组合，但 online
  quantization 不得与 DLO+AllGather 组合；本 PR 没有证明 HSDP 或其他 quantizer 的组合语义。
- 验收：CPU plan tests 覆盖 aligned/irregular 均进 sparse plan、tail closure、min length、layout
  和 skip/step；
  NPU 条件数值测试以 `sparsity=0` 直接调用 kernel 对 dense reference，mean relative error 阈值
  为 `2e-3`；它不证明 `sparsity=0.8` 质量 parity。PR 的 Atlas 800I A3 8×NPU、
  CANN 9.0.1、T2VA 209-frame 三种生成仅证明这些 exact 配置能完成；视频样例不是质量阈值，
  没有 latency/repeats，不能宣称稳定加速或 FL2VA/Ref2VA 支持。1344×768
  H3 grid `(62,24,42)` 的 62496 video rows 只在 CPU plan test 证明会进 sparse plan；
  updated-MindIE NPU 对照用更小的 `(4,16,10)` grid 且 `sparsity=0`，仍不证明 0.8
  的质量或性能。^[PR #5706] ^[PR #6000]

## MMH3-1e — H3 TRTLLM 必须从 packed 结构裁掉 padding 并隔离短序列 role

- 触发：修改 H3 的 TRTLLM default、packed `cu_seqlens`/mask、SAGE quant、Skip-Softmax、
  token-refiner role 或 denoise timestep context。
- 强制：H3 只在支持的 datacenter Blackwell SM100/103、head_dim=128、FlashInfer kernel 可用且
  声明 compatible packed/mask-free path 时默认 dense BF16 TRTLLM；SM120/121、缺依赖、错误
  head dim 或需要任意 mask 的路径保留平台 fallback，默认不自动开启 SAGE/Skip-Softmax。
- 强制：四个 packed metadata key 必须完整、Q/K batch/terminal 覆盖一致；只接受 prefix-valid
  structural padding mask，按 boundary 裁掉无效 suffix 后再 quantize/attention，并把输出补零到
  Ulysses 物理 shape。`[0,N,N]` 必须折叠尾部空 sequence；任意 mask、缺失或矛盾 metadata
  fail closed。`attention_mask_free=True` 是 compatible packed-path capability，不表示物理 mask
  永远为空。AllGather-KV 的 local-Q/global-KV metadata 不对称合同在初始化时明确拒绝，真正
  支持按 review 明确延期。
- 强制：main DiT 与 `minimax_h3.token_refiner` 使用独立 role；任一 KV sequence 短于 SAGE
  `k_block_size` 时该 input 告警并走 dense TRTLLM，不能让 14-token refiner 产生 non-finite，
  也不能因此关闭 main DiT 的 SAGE。H3 将 scheduler 的降序 sigma（1→0）发布为
  `normalized_timestep`；Skip-Softmax 在 sigma 大于 `disabled_until_timestep` 时保持 dense，
  到达或低于阈值才启用。
- 禁止：把 structural prefix mask 泛化为任意 mask；让 padding 进入 SAGE block quantization；
  把 combined packed-H3 优化视频归因于本 PR 单一改动。请求级 `set_forward_context` wrapper
  会在 `finally` 恢复 prior context，因此 loop 内的 step mutation 不会泄漏到后续请求。
- 验收：测试覆盖 ragged batch、suffix trim/zero restore、empty terminal、invalid mask/metadata、
  short-role dense fallback、AllGather rejection 与 non-finite regression。PR 的 4×B300 SM103、
  1248×768、209 frames、50 steps FA4/TRTLLM 对比仅绑定该 prompt/seed/topology：PSNR 27.10、
  SSIM 0.8880 不是质量 gate；83.854→71.990 s diffusion、88.558→76.176 s wall 的 warmed A/B
  来自 review follow-up 外部分支 commit `20cc23ae`，其 artifacts 明确是 combined packed-H3
  optimization evidence，并非目标 commit 的隔离实验，不能泛化为稳定 14% 保证。^[PR #5779]

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

## MMH3-2c — conditioned VAE 的固定种子必须按实际设备隔离并恢复

- 触发：修改 H3 image/video reference 的 VAE encode、固定 keyframe seed、`fork_rng`、设备
  generator 或 accelerator backend 支持。
- 强制：`encode_image()`/`encode_video()` 在采样前暂时把 VAE 转成 FP32，在
  `torch.random.fork_rng` 同时传 `devices=...` 与 `device_type=parameter.device.type`，并在
  context 内播种 CPU default generator 与 active-device generator；退出时恢复 RNG state，
  在 `finally` 恢复原 dtype，image path 还必须恢复 `parallel_tiling`。这个 seed 是
  conditioned VAE 的固定内部 seed，不能描述成 request seed。
- 强制：`devices` 只决定保存/恢复哪些 device index，不能代替 `device_type` 选择 RNG module；
  目标 torch 版本省略后者会默认进入 CUDA。NPU 依赖 `torch_npu` 先注册 `torch.npu`，encode
  内的 `self.device_module` 则在同一 active device 上执行 `device(...)` 与 `manual_seed(...)`。
- 禁止：把 PR 文本中的 CUDA+MUSA allowlist 当成目标实现。目标代码实际以
  `parameter.device.type != "cpu"` 接纳已注册的 accelerator device module，并把真实 type
  交给 `fork_rng`；CPU 的
  `devices=[]` 仍保存/恢复 CPU RNG。实机证据覆盖 CUDA/MUSA，以及 PR #5837 报告的 Ascend
  NPU direct fork smoke 与一次双参考图 FL2VA serving 成功，不能外推 XPU 或 ROCm。也不能因
  `fork_rng` 最终恢复 state 就宣称并发安全：context 内仍会暂时改写 process-global CPU/device
  generator，重叠调用需要序列化或独立并发证明。
- 验收：同 seed 的 image/video condition latent 可重复，正常和 encode 异常后 CPU、目标设备
  RNG state、dtype 及 image tiling state 都恢复；CPU 与每个声称支持的 accelerator 分支分别
  覆盖，并加入重叠调用 fence。PR 中拟议的专用 VAE 单测按 review 被删除，目标 commit 没有
  新增测试；PR #5837 也只改两处参数，未提交 CPU/NPU 回归测试，其 NPU smoke、serving 结果
  与 CUDA 不变性说明只能作为外部证据，不能冒充持续回归覆盖。^[PR #5703] ^[PR #5837]

## MMH3-2d — modular H3 的 task selector 必须同步权重、能力与所有 DiT lifecycle

- 触发：修改 `modular_model_index.json`、`MiniMaxH3ModularPipeline`、`--task-type`、combined
  FL2VA/Ref2VA 服务、`_dit_modules` 或 shared text/VAE components。
- 强制：模型发现同时识别 `model_index.json` 与 `modular_model_index.json`，registry alias 与
  postprocess 都映射到同一 H3 pipeline。`auto/combined` 从 root 加载 FL2VA `transformer` 与
  Ref2VA `transformers_ref`，但共享 text encoder、video/audio VAE；单 task 只加载所需 DiT。
  request task 必须属于启动时 `supported_tasks`；combined 省略 task 时按无媒体→t2va、image-only
  →fl2va、video/audio→ref2va 推断，因此 image-only Ref2VA 必须显式给 task；Ref2VA-only
  省略 task 时保留 implicit ref2va。
- 强制：modular alias 复制 9-image/mixed-reference admission capability；所有基于
  `_dit_modules` 的 consumer（loader strictness、Cache-DiT enable/refresh/summary、LoRA/offload）
  遍历实际 DiT，不硬编码 `transformer`/`transformer_2`。共享 `--task-type` 放宽后，非 H3
  owner 仍 model-aware 校验；Qwen3-TTS 只接受既有三值。
- 缺口：目标 pin 的 modular metadata 虽修复 admission 字段，仍遗漏 canonical H3 的
  `attention_mask_free=True`。HF root 的两个 index 都解析成 modular alias，因此默认
  combined 服务在 Blackwell 不会自动选 TRTLLM，与 recipe 声明冲突；alias 必须校验全部能力
  字段 parity，不能只复制 review 点名的字段。
- 禁止：从 combined 注册推断双 DiT 性能已验证；recipe 最终只描述配置，没有 combined
  warm latency/throughput/output-parity qualification。也不能用单 DiT Cache-DiT 测试证明
  `transformers_ref` lifecycle。
- 验收：覆盖 local/Hub index discovery、snapshot allow-pattern、combined/单分区初始化、缺
  partition、task default/membership、modular admission、两 DiT cache lifecycle 与非法 TTS
  selector。PR body 的顺序 T2VA→Ref2VA 视频使用 `duration=2.0`，低于目标 pin 已生效的 4 秒
  下限，因此不能证明 final merge 的 combined 路径；148.27/158.67 GiB combined 与 86.27 GiB
  single-load 等数字来自缺硬件/协议/重复次数的 issue comment，不能作为容量保证。^[PR #5720]

## MMH3-2e — quality 映射只决定 request 的 Cache-DiT 目标

- 触发：修改公共 `quality` 值、H3 quality policy、startup cache adoption 或 denoise 前 prepare。
- 强制：公共层只接受 `None`、`lossless`、`high`，并保留 omitted 与 explicit lossless 的区别。
  对 request-scoped Cache-DiT，`lossless` 产生空 target；`high` 总是选择 model-owned conservative
  profile，即使启动时没有 cache backend；omitted 仅在启动配置为 Cache-DiT 时恢复 server generic
  profile，否则不安装 Cache-DiT。
  pipeline 必须在参数/任务/step 解析完成后、真实 denoise 紧邻之前 apply plan。
- 禁止：沿用 PR 早期描述，把无 startup cache 的 `high` 拒绝；让 unsupported quality 静默落入
  lossless；在 request 未显式提供 quality 时由 sync/streaming serving 覆盖 model default。recipe
  把同一组 quality 数字标为 4×H200，而 PR evidence 把它归于 4×L20X SP4；hardware provenance
  未统一前不得引用该表作为任一硬件的可靠 benchmark，更不能外推通用 speedup/quality。
- 验收：offline、chat、sync video、streaming video 都覆盖 omitted/lossless/high/非法值及显式字段
  传播；startup cache on/off × 三种 intent 验证 exact installation key，并断言 prepare 先于 diffuse。
  当前测试广泛覆盖 validation/routing/policy 和 mock 顺序，但真实 Cache-DiT transition 的并发、取消、
  failure rollback 仍缺证据；独立 reviewer 的单卡 B300 观察也显示 `high` 的质量/延迟与四卡表明显
  不同，只能支持 topology-dependent 边界。共享状态机与 batch 合同见
  [DIFF-2i–2j](../../components/diffusion/rules-component-lifecycle.md)。^[PR #5853]

## MMH3-2f — force-refresh hint 属于 active profile identity

- 触发：H3 request `extra_args` 使用 `force_refresh_step_hint` 或 `force_refresh_step_policy`。
- 强制：hint 是 1-based positive integer 且不超过 `num_inference_steps`，policy 只接受 once/repeat，
  省略 policy 默认 once；没有 active cache target 时两者都拒绝。用 dataclass replace 生成 request-local
  config，不修改 startup generic config；installation key 必须包含 hint+policy，因为 Cache-DiT 的
  incremental refresh 把 `None` 解释为保留旧 hint，变更或移除 hint 必须 reinstall hooks。
- 禁止：接受 bool 作为整数；只给 policy；跨 request 原地修改共享 config；same-key repeated request
  忘记重置 once hint，导致它只在首个 request 生效。
- 验收：边界 1/steps、0/越界/bool/非法 policy、无 target、hint add/change/remove、once/repeat 和
  repeated same-key request；断言每次 refresh 重建 hint context、generic config 不变，key 变化发生
  disable→enable。当前覆盖为 mock/config 合同，未证明不同 topology 下 hint 对质量/命中率的效果。
  ^[PR #5853]

## MMH3-2g — H3 TeaCache 只绑定 FL2VA 校准与 request state

- 触发：H3 选择 `tea_cache`、修改 extractor、polynomial coefficients、threshold 或 partition。
- 强制：只允许 `fl2va`/`combined`，Ref2VA-only fail fast；combined 只 hook FL2VA `transformer` 并
  告警 Ref2VA 不缓存。extractor 必须复刻 `_embed`、packed/SP block kwargs、final row selection 与
  video/audio update masks；缺/多 kwargs、空 blocks、shape/length 不闭合立即失败。runner 在每次
  generation 前 reset module-resident hook state；first step 强制计算，后续按累积距离计算或复用
  residual，目标 hook 没有 last-step 强制计算分支。
- 强制：H3 coefficients 只由 70 prompts、seed 42–111、256×448、107 frames、50 steps 的 3360
  adjacent pairs 校准；`TeaCacheConfig` 收到 `None` 时模型默认 0.17，自定义 coefficients/正 threshold
  可覆盖。但 public `AsyncOmniEngine._normalize_cache_config` 在省略 cache config 时仍先注入 0.2，
  因此 CLI/public omitted 路径没有获得 0.17；recipe 显式 0.17 不受影响。
- 禁止：把 FL2VA coefficients 用于 Ref2VA，或宣称 selector 已在 request 层强制互斥。目标 pin 中
  TeaCache 由 runner 持有；`quality=lossless` 只清除 Cache-DiT target、不会卸载 TeaCache，
  `quality=high` 还会尝试在同一 transformer 安装 Cache-DiT。修复或拒绝该组合前，TeaCache server
  不得用 request `quality` 承诺 lossless 或双 backend 安全。0.2 单 H100 A/B 虽约 1.20×，LPIPS
  0.3162 是显著视觉差异；0.17 在同 prompt 仅约 3% wall reduction、LPIPS 0.0134，均非通用保证。
  ^[PR #5840]
- 验收：CPU extractor tests 覆盖 native parity、packed kwargs、mask/SP 与错误路径；backend tests
  覆盖 partition/default/override。模型 E2E 仅两 steps 并检查输出 shape，未断言真实 cache hit；
  还必须从 public omitted config 断言最终 H3 threshold，不能只直接构造 backend；覆盖 TeaCache ×
  omitted/lossless/high，断言只存在一个 hook/backend 或明确拒绝。module state 若可交错还需并发隔离
  证明。单 H100 online/offline、
  Cache-DiT default/conservative 数据无多 prompt/repeats，不能升级为 gate。

## MMH3-2h — distilled sigma schedule 按 partition 所有且以区间计步

- 触发：H3 partition `model_index.json` 的 `_minimax_h3.base_schedule`、显式
  `num_inference_steps`、video/audio flow shift 或 combined FL2VA+Ref2VA。
- 强制：缺少 metadata key 或显式 null 都表示未蒸馏，保持旧
  `num_inference_steps or 50` 的 uniform-point 构造（默认 50 个点实际是 49 个 solver
  intervals）；explicit empty list 必须拒绝。调度至少两个有限点，严格
  从 1.0 递减到 0.0，并逐对验证相邻位置。
- 强制：5 个 sigma boundaries 只有 4 个 denoise intervals；`num_inference_steps`、
  Cache-DiT quality policy 和请求验证均使用 `len(base_schedule)-1`，solver 仍接收
  完整 boundary list。用户省略 step 时自动采用 checkpoint 步数；显式值只有
  精确相等才接受，否则 `OmniClientError`。同一 continuous base positions 分别
  应用 video/audio shift（默认 12/3），不得改用单模态 integer timesteps。
- 强制：schedule 从各 partition metadata 分别读取；`t2va`/`fl2va` 选 FL2VA，
  `ref2va` 选 Ref2VA。distilled FL2VA 不得拖普通 Ref2VA 进 4-step。类级空 map
  是 partially constructed pipeline 的 legacy fallback，避免 `object.__new__`/dummy fixture
  读未初始化属性。
- 边界：共享 `DMD2SigmaSchedule` 在 `diffusion/sched` 定义，但此 pin 只有
  H3 消费；现有 `DMD2PipelineMixin` 仍是 scheduler-backed，用
  `DMD2EulerScheduler`/integer `denoising_timesteps`，本次未接入新 utility。不得由
  `[NPU]` title 推导 NPU 实机已验：无 platform/deploy/recipe 改动，PR hardware
  与 branch-head 也留空；附件视频只是 smoke，无数值 teacher/student quality gate。
- 共享 boundary/interval、metadata null/empty 与 shift 有限性合同见
  [DIFF-4j](../../components/diffusion/sigma-schedules.md#diff-4j-continuous-sigma-boundaries-不得与-scheduler-integer-timesteps-混同)。
- 验收：shared class 覆盖长度/端点/单调/非有限/shift≤0、缺 key 与空 key；
  H3 覆盖双 shift 精确值、combined partition 隔离、4-step 传入 solver/quality、
  matching/mismatched explicit step 和 legacy/partially-constructed fallback。仍缺真实 distilled
  checkpoint 的 CUDA/NPU E2E 与 teacher/student 质量阈值。^[PR #5991]

共享 component quantization、checkpoint mapping 与 quality evidence 见
[Diffusion rules](../../components/diffusion/rules.md)。
