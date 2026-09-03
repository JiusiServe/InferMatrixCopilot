---
title: "Diffusion 共享规则"
created: 2026-07-20
updated: 2026-09-04
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #4341", "PR #5001", "PR #5087", "PR #5088", "PR #5136", "PR #5255", "PR #5344", "PR #5543", "PR #5720", "PR #5737", "PR #5764", "PR #5801", "PR #5802", "PR #5838", "PR #5839", "PR #5848", "PR #5872", "PR #5881", "PR #5896", "PR #5981", "PR #6094", "PR #6102", "PR #6279", "PR #6385", "PR #6445", vllm_omni/diffusion/attention/backends/flashinfer_attn.py, vllm_omni/diffusion/attention/backends/ring/ring_kernels.py, vllm_omni/diffusion/attention/parallel/ulysses.py, vllm_omni/diffusion/cache/cachedit/backend.py, vllm_omni/diffusion/data.py, vllm_omni/diffusion/distributed/hsdp.py, vllm_omni/diffusion/executor/multiproc_executor.py, vllm_omni/diffusion/layers/norm.py, vllm_omni/diffusion/layers/rope.py, vllm_omni/diffusion/lora/manager.py, vllm_omni/diffusion/model_loader/diffusers_loader.py, vllm_omni/diffusion/model_metadata.py, vllm_omni/diffusion/offloader/, vllm_omni/diffusion/registry.py, vllm_omni/diffusion/worker/diffusion_model_runner.py, vllm_omni/engine/async_omni_engine.py, vllm_omni/entrypoints/openai/api_server.py, vllm_omni/quantization/component_config.py, vllm_omni/quantization/factory.py, tests/diffusion/attention/test_attention_sp.py, tests/diffusion/attention/test_ulysses_uaa.py, tests/diffusion/cache/test_cache_backends.py, tests/diffusion/layers/test_norm.py, tests/diffusion/layers/test_rope_broadcast.py, tests/diffusion/offloader/test_distributed_layerwise_backend.py, tests/diffusion/test_diffusion_config_propagation.py, "PR #4755", "PR #5990", "vllm_omni/diffusion/layers/fused_qk_norm_rope.py", "vllm_omni/diffusion/cache/teacache/extractors.py", "vllm_omni/diffusion/models/minimax_h3/minimax_h3_transformer.py", "tests/diffusion/layers/test_fused_qk_norm_rope.py", "PR #6165", "PR #5677", "vllm_omni/diffusion/quantization/hsdp_fp8.py", "tests/diffusion/quantization/test_hsdp_fp8.py", "PR #4845", "PR #6173", "PR #6070", "vllm_omni/diffusion/models/ltx2/ltx2_components.py", "vllm_omni/diffusion/model_loader/hub_prefetch.py", "PR #5910", "PR #5676"]
confidence: high
---

# Diffusion 共享规则

只有 `DIFF-数字字母` 是可审计规则 ID。模型专有常量和已验证偏差留在对应
[模型 owner](../../models/_index.md)；本页只承载多个 diffusion 模型共用的不变量。

## Direct 代码快速入口

- **DIFF-0a — PR 描述先选共享执行地图。** 按 title/body 的 graph、RNG、checkpoint、HSDP、quantization 或质量信号命中下表，再用 pinned files 验证 owner。
- **DIFF-0b — 共享 runner 与模型 pipeline 分层。** 先查命中行的共享 producer；只有 live 调用链落到单模型 pipeline/checkpoint/常量时才进入模型 owner，不横扫其他模型。

| PR 描述在做什么 | 精确规则组 | 第一批 live 源码 |
|---|---|---|
| CUDA Graph、compile、fused solver/norm/RoPE、FA determinism、eager parity、tensor dtype/device、async output/teardown | `execution-parity`：`DIFF-1a`–`1j` | `compile.py::regionally_compile` → shared layer/backend → model denoise/output pump/shutdown |
| seed、request-local generator、guidance=0、并发 RNG、batched generators | `execution-parity`：`DIFF-1b` | `inputs/data.py::OmniDiffusionSamplingParams` → runner `_initialize_generator` → request-batch generator collate |
| ModelOpt/checkpoint adapter、weight/scale remap、unknown tensor、resolution path | `checkpoint-distributed`：`DIFF-2a` | `diffusers_loader.py::{_get_checkpoint_adapter,load_weights}` → `modelopt.py::{_resolve_target_and_output_names,adapt}` |
| host-weight artifact、source identity、layout/dtype、warm restore | `checkpoint-distributed`：`DIFF-2d` | `model_loader/host_weights/{source_identity,contracts,identity_adapter}.py` → policy/restorer |
| HSDP/FSDP、`fully_shard`、DeviceMesh、packed/scalar parameter、FP8 | `checkpoint-distributed`：`DIFF-2b` | `distributed/hsdp.py::{apply_hsdp_to_model,shard_model}` → loader `_load_model_with_hsdp` → `hsdp_fp8.py` |
| distributed layerwise offload、AllGather、异构 block、shared buffer | `checkpoint-distributed`：`DIFF-2e` | `offloader/distributed_layerwise_backend.py::{DistributedLayerwiseOffloadHook.initialize_hook,prefetch_layer,DistributedLayerwiseOffloadBackend._allocate_shared_buffers}` |
| DLO+AllGather、DP wave、result queue、shutdown、constructor cleanup | `checkpoint-distributed`/`execution-parity`：`DIFF-2k`, `DIFF-1d/1g/1h/1j` | request compatibility key → multi-rank RPC → worker-owned queue/pump → bounded teardown |
| component quantization、text encoder/transformer/VAE 独立配置、owner prefix、meta/offload | `checkpoint-distributed`：`DIFF-2c` | `quantization/factory.py::{build_quant_config,resolve_quant_config_from_disk}` → `component_config.py::ComponentQuantizationConfig.resolve` → `data.py::_propagate_quantization_from_tf_config` → component linear consumer |
| modular/multi-DiT、`_dit_modules`、request-scoped Cache-DiT/compile/SP/LoRA/offload lifecycle | `checkpoint-distributed`：`DIFF-2f`–`2j` | request batch key → model policy/cache runtime；pipeline component list → shared consumers |
| LPIPS/PSNR/相似度阈值、CPU offload、量化质量证据 | `quality-evidence`：`DIFF-3a` | changed exact case → runner `execute_model` → model pipeline；A/B 同路径 |
| Wan VAE spatial shard、gather/trim/reshard、empty tail、attention extent | `distributed-vae`：`DIFF-3b` | `distributed/autoencoders/wan_spatial_shard.py` → patched decoder attention/conv → gather final frame |
| paged KV/cache、backend/platform、GQA/layout、Ring/Ulysses、FlashInfer quant、预算与 admission | `system-runtime`：`DIFF-4a`–`4j` | engine init → metadata/config → attention parallel/backend → platform hook → scheduler/serving |
| worker/RPC 异常、rank-status、traceback/device cache 清理 | `system-runtime`：`DIFF-4d` | `diffusion_worker.py::{_execute_rpc,_worker_busy_loop}` 的 raise/reply/status 路径 |

| 审查组 | 什么时候触发 | 规则 ID |
|---|---|---|
| `core` | 每次共享 diffusion 审查 | `DIFF-1a`, `DIFF-1b`, `DIFF-1c`, `DIFF-1d`, `DIFF-1e` |
| `execution-parity` | graph/eager、solver、RNG、generator、tensor dtype/device、fused layer、FA determinism、async output/shutdown | `DIFF-1a`–`1j` |
| `checkpoint-distributed` | checkpoint、quantization、HSDP/FSDP、artifact identity、distributed offload、multi-DiT/cache lifecycle | `DIFF-2a`–`2e`, `2p`, `2q`, `2s` 见 [checkpoint 与加载合同](rules-checkpoint-loading.md)；`2f`–`2j`, `2r` 见 [component lifecycle](rules-component-lifecycle.md)；`2k` 见 [output/runtime](rules-output-lifecycle.md)；`2l`–`2o` 见 [LoRA](rules-lora.md) |
| `quality-evidence` | 质量阈值、offload、A/B case | `DIFF-3a` |
| `distributed-vae` | Wan VAE spatial height/width shard、rank context、extent/padding | `DIFF-3b` |
| `system-runtime` | cache/预算、native/backend/platform、attention layout、能力 metadata、异常与并发 | `DIFF-4a`–`4j`（`4a`–`4i` 见 [paged cache 与系统运行时规则](rules-system-runtime.md)） |
| `author-routing` | 只供 Direct reviewer 导航，不作为 finding 规则 | `DIFF-0a`, `DIFF-0b` |

## 优化路径与 eager 的等价合同

### DIFF-1a — graph/compile/fused 路径逐项复刻 eager 数值边界

- 触发：新增或修改 CUDA Graph、compile、fused scheduler/solver 或缓存执行路径。
- 强制：逐项对齐初始噪声、solver/timestep dtype、每步 cast 边界、最后一步更新、
  CFG=0/近零分支和输出 dtype；依赖行为有版本差异时固定并验证版本。
- 禁止：只比较 shape、无 NaN 或“能运行”；这些不能证明数值和请求语义等价。
- 验收：固定输入和 request-local generator，对 eager/优化路径逐步比较关键状态并覆盖
  零值和最后一步边界。Ming-TTS 的具体反例见
  [Ming-Omni-TTS 规则](../../models/ming-omni-tts/rules.md)；local FlashAttention deterministic
  opt-in 的共享合同见 [DIFF-1f](rules-attention.md)，Qwen accuracy 边界见
  [Qwen-Image 规则](../../models/qwen-image/rules.md)。
  ^[PR #4341]

### DIFF-1b — 随机状态属于请求，零值不是缺省值

- 触发：pipeline/scheduler 接收 seed、generator、guidance 或其他允许为零的数值。
- 强制：使用请求本地 generator 并证明当前依赖版本真正消费它；用 `is None` 区分
  缺省与 `0`/`0.0`。
- 禁止：并发请求中修改 process-global RNG；使用 `x or default` 吃掉合法零值。
- 验收：两个并发请求用不同 generator 可重复且互不影响，`0.0` 从 request 构造一路
  到达 consumer。Cosmos3 的落地约束见
  [Cosmos3 规则](../../models/cosmos3/rules.md)。 ^[PR #5001]

mixed-precision tensor/parameter dtype 合同见 [DIFF-1c 专页](rules-tensor-dtype.md)。
async output readiness、per-worker result channel、shutdown 与 constructor cleanup 合同见
[DIFF-1d/1g/1h/1j 专页](rules-output-lifecycle.md)。

### DIFF-1e — fused layer 必须保留精度、布局与平台分派合同

- 触发：共享 norm/RoPE 增加 fused op、平台专用实现、compile 分支或可配置 parameter dtype。
- 强制：把 parameter 存储 dtype 与 reduction/累加 dtype 分开约束；CUDA/HIP eager 可尝试
  fused op，但异常必须回退到数值等价的 native 实现，`torch.compile` tracing 直接走 native，
  NPU/MindIE 等专用 backend 则按其真实参数与频率布局调用。RoPE 适配器必须显式区分 full-dim
  tiled frequency 与 fused kernel 的 half layout，并保持未旋转 head tail 不变。若 caller 可传
  无 batch 的 `[S,H,D]`，进入只接受 `[B,S,H,D]` 的 fused kernel 前必须补 batch 维，返回后仅在
  本次确实补维时移除；原生 4D 输入不得被 squeeze。
- 强制：MUSA 是独立 dispatch，不再假设兼容 CUDA。shared `RMSNorm.forward_musa` 保留
  `F.rms_norm(x, (hidden_size,), weight, eps)` 的 aten graph，供 dynamic Inductor fusion；不能改走
  带 output mutation/`.data` 的 CUDA custom op。此共享路径直接影响 Cosmos3、HunyuanImage3、
  MiniMax-H3、Wan2.2 与 Z-Image 的 `RMSNorm` consumers。shared RoPE 只有 full-dimension、非
  interleaved NeoX layout 可走 MUSA inline 公式，当前还覆盖 Bagel/HunyuanImage3；half-dimension
  或 interleaved layout 必须退回 native。3D cos/sin 只取共享 batch 0，再插 head broadcast 维；
  这些 fallback/shape 条件是 correctness contract，不能为 fusion 删除。^[PR #5881]
- 禁止：用 platform dispatch 推断所有 backend 接收同一布局；用 CPU/reference 或 mock 参数
  wiring 测试声称真实 CUDA/HIP/NPU/MUSA fused kernel 已完成数值 parity。
- 验收：native reference 覆盖 parameter dtype、FP32 accumulation、旋转维度与 untouched tail；
  compile 路径断言不调用 fused op，平台 mock 只作为 wiring 证据。声称 fused parity 还需目标
  硬件上的同输入数值测试。mock kernel 的维度断言与 identity 回传只证明 adapter wiring/shape，
  不证明实际旋转数值。当前自动测试没有 MUSA dispatch/parity 或 shared-consumer census，也未证明
  `F.rms_norm` 的 FP32 accumulation；CPU H3 reference fixture 强制 `forward_native`，只覆盖
  `rot_dim=96`。硬件 A/B 是有界性能证据，不是持续回归 gate。
  ^[PR #5801] ^[PR #5881] ^[PR #5896]

## Checkpoint 与分布式加载

### DIFF-1l — fused Q/K RMSNorm 与 packed RoPE 必须共享布局并保留 eager fallback

- 触发：共享 diffusion attention 新增或修改 Q/K RMSNorm+RoPE fused op、packed frequency table、custom-op dispatch，或 TeaCache 等 extractor 复用该边界。
- 强制：公共 API 固定 `q/k` 为 `[tokens, heads, head_dim]`、norm weight 为 `[head_dim]`、`rope_table` 为 `[tokens, rotary_dim]`，并按 non-interleaved `[cos(theta), sin(theta)]` 存储；先完成 RMSNorm，再只旋转前 `rotary_dim`，原样保留 head tail。仅在 CUDA、Triton、BF16、`head_dim=128`、`rotary_dim=96` 时走 fused fast path，其余 device、dtype 与 geometry 必须走 eager reference；输入、权重和 table 的 dtype/device 合同必须保持一致。
- 禁止：把模型原始或 tiled `freqs` 直接当作 packed cos/sin table，交换 cos/sin、改用 interleaved layout，或仅因 Triton/custom op 可用就强制走 fast path；fast path 也不得物化 normalized Q/K 与 rotary 中间结果来掩盖布局错误。
- 验收：CUDA/Triton 测试以 `F.rms_norm` 加显式 packed RoPE reference 对照 q、k，并覆盖 sequence length `1`、`257`、`1024`；另须覆盖 unsupported fallback、参数校验和非 contiguous 权重/table。当前 PR 只证明 BF16 专用 geometry 的三组数值对照，未证明 fallback、H3 集成或跨硬件 parity；4×B300 上一次 warmup/一次测量的 109.687→106.205 秒仅是该 workload 的性能观察。^[PR #5990]

### DIFF-1m — 局部 SP 边界必须由已注册 strict-Ulysses hook 显式证明

- 触发：修改 diffusion 模型的 rank-local sequence boundary、`local_sp_prepare`、SP layout 判定或 TeaCache extractor 的 `_embed()` 调用。
- 强制：局部路径必须同时确认已注册 `sp_input---local_sp_prepare` hook、forward context 可用、`get_ulysses_mode() == "strict"`、sequence-parallel world size 大于 1 且等于 Ulysses size、Ring/AllGather size 均为 1，并确认 `seq_len` 可均匀切分；任一条件不满足都使用完整 sequence。需要完整上下文的 TeaCache extractor 必须显式传 `local_span=(0, seq_len)`。
- 禁止：仅凭 SP rank/world size 推断局部 embedding 安全；让 Ring、AllGather-KV、advanced UAA、缺少 hook、非 forward context 或不可整除长度误走局部路径；把模型专属的局部 row 重建合同泛化为所有 diffusion 模型。
- 验收：覆盖 strict hook 的 rank span、缺 hook、forward context 不可用、SP=1、advanced UAA、Ring、AllGather-KV 和非整除长度 fallback，并回归 TeaCache extractor 的完整 span；当前合同只由 MiniMax-H3 caller 证明，其他模型仍需独立验证。 ^[PR #6173]

### DIFF-1p — LTX-2.5 I2V 必须先执行 CRF conditioning 再 resize

- 触发：LTX-2.5 I2V 修改 reference-image conditioning、`image_crf`、resize 顺序或 PyAV/FFmpeg 依赖。
- 强制：PIL 输入默认执行 CRF 18，再进行 aspect-preserving resize；非零 `image_crf` 只接受 PIL 图像，tensor 输入必须显式使用 `image_crf=0` opt out；缺少 PyAV/libx264 要返回明确错误，任一尺寸小于 2 时在编码前原样返回。
- 禁止：在 CRF round trip 前 resize 或 squash 图像；按模型路径名猜版本；把非零 CRF 静默应用到 tensor；将 1-pixel 维度向下取整为零后交给 libx264。
- 验收：覆盖默认/显式 CRF、PIL/tensor、无 PyAV、缺少 libx264、1xN 图像和非等比例输入，断言 CRF 顺序、错误类型、原图保护以及最终 conditioning shape。^[PR #6070]

## 质量阈值与资源辅助

### DIFF-3a — 质量阈值必须由完全相同的测试 case 产生

- 触发：新增 LPIPS/PSNR/相似度阈值，或用 CPU offload 等资源选项支撑量化质量测试。
- 强制：阈值证据与测试中的 step、seed、size、guidance、checkpoint 和量化组件完全一致；
  仅为避免 OOM 的 offload 必须在 baseline/candidate 对称启用并说明它不属于待比较变量。
- 禁止：用 50-step A/B 数字为 10-step 测试阈值背书；只写“需要 offload”而不说明
  是资源前提还是功能行为。
- 验收：运行测试文件中的 exact case，并在规则/配置旁保留最短资源原因；对称 baseline
  证明质量差异来自目标量化变量。低 steps smoke 只能证明 runtime compatibility，不得声称
  BF16 quality parity。 ^[PR #5136] ^[PR #6279]

### DIFF-5a — diffusion metrics 的 per-step 计算必须保留请求步数

- 触发：修改 diffusion output formatter、sampling params metadata 或 diffusion metrics accumulation，使请求级 DiT execution time 需要按 denoising step 归一化。
- 强制：`format_diffusion_outputs()` 必须保留 `sampling_params.num_inference_steps` 并传入 stage stats；aggregator 保留该 scalar，仅在 execution time 与正步数同时存在时按 `exec_time / num_inference_steps` 观测 per-step metric。
- 禁止：丢弃请求步数、用 stage 总生成时间替代 DiT execution time，或把跨多个结果的 scalar 累加后再计算 per-step 值。
- 验收：覆盖完整 metadata、缺失/`None`/零步数、正步数、重复结果与零 execution time；分别断言 per-step 值精确、无效步数跳过且 scalar 不累加。^[PR #4755]

### DIFF-4m — diffusion worker spawn 前必须限制继承的线程数

- 触发：修改 `MultiprocDiffusionExecutor._launch_workers`、worker spawn 流程或 diffusion 多进程的 OMP/Torch 线程环境。
- 强制：在设置 multiprocessing start method 并创建 worker 进程前调用 `set_multiprocessing_worker_envs()`；未设置 `OMP_NUM_THREADS` 时沿用其线程上限策略，显式用户值必须保留。
- 禁止：worker 已 spawn 后才设置线程环境；覆盖用户显式的 `OMP_NUM_THREADS`；把默认线程值 1 宣称为所有 diffusion host-side work 的最优值。
- 验收：在固定镜像中验证环境未设置时 worker 的 `OMP_NUM_THREADS` 与 `torch.get_num_threads()` 均为 1，并验证显式线程值仍生效；多 GPU 启动不得因每个 worker 继承全部可见 CPU 线程而产生 N 倍过量线程。^[PR #6165]

相关执行流见 [Diffusion architecture](architecture.md)；benchmark 证据合同见
[performance evidence](../../benchmark/guides/performance-evidence.md)。

### DIFF-4n — 大体积广播溢出消息必须无损配对接收

- 触发：修改 `WorkerProc` 忙循环、`MessageQueue` 广播接收或 SHM overflow marker 与 socket multipart 的配对逻辑。
- 强制：消费 overflow marker 后必须通过 `recv_message()` 调用 `self.mq.dequeue(indefinite=True)`，等待对应的完整 socket payload 到达后才能继续接收下一条消息，并保持 FIFO 顺序。
- 禁止：对已消费 marker 的 multipart 使用有限超时；超时后重新 `dequeue` 并把后续 marker 或 inline 消息与迟到 payload 配对；仅把有限超时调大作为修复。
- 验收：单测断言接收调用使用 `indefinite=True`，并让 overflow payload 延迟超过任何有限超时后再发送 inline 消息，断言 worker 按 `overflow-1`、`inline-2` 顺序处理。当前 PR 的 0.1 秒延迟仍在旧 1 秒超时内，且 monkeypatch 的模块变量未被生产代码读取，不能单独证明旧实现会失败。^[PR #4845]

### DIFF-6a — request-level batching 必须由结构兼容键和请求隔离共同约束

- 触发：diffusion pipeline 宣布支持 request-level batching，或 scheduler/admission 增加模型条件、`extra_args` 结构与 request-level output split。
- 强制：预处理必须为影响物理 batch 兼容性的 pipeline condition 写入 `batch_compatibility_key`；`RequestScheduler` 必须将显式 `sample_solver` 规范化为去空格小写、将 `flow_shift` 转为 `float`，并保留未指定值为 `None`，再与现有 batch-wide sampling key 一起决定 admission。pipeline 只能批处理兼容 key 相同的请求，按 `num_outputs_per_prompt` 合并 prompt/embedding、latents、request-local generators 和条件，并拆回每个原始请求一个 `DiffusionOutput`；S2V 等 request-local metadata 不得为输出数重复物化。
- 禁止：只按原始 `extra_args`、第一条请求或 pipeline 名称决定兼容性；把不兼容的 image/last-image、VACE 或 S2V 条件混入同一 batch；共享全局 RNG；返回无法按请求对应的聚合输出；把请求隔离和 output split 误当成不同物理 batch shape 的数值等价。
- 验收：scheduler 测试必须区分不同 `sample_solver`、`flow_shift` 和 condition key，并证明等价显式值可归一化合批；Wan2.2 T2V/I2V/VACE/S2V 测试覆盖 generators、latents、prompt embeddings、output split 以及 image shape、last-image presence、VACE condition/reference count、S2V `init_first_frame`/`num_repeat`/audio time length/raw shape/sample rate 的拒绝路径。真实验证还必须分别检查同批请求的身份、prompt、条件、顺序和请求级 RNG 隔离；Wan2.2 BF16 的 batch-1 与 batch-2 轨迹可能不同，未经固定精度策略和 exact case 验证不得声称 bitwise 或生产级等价。^[PR #5676]
