---
title: "Diffusion 共享规则"
created: 2026-07-20
updated: 2026-09-04
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #4341", "PR #5001", "PR #5087", "PR #5088", "PR #5136", "PR #5255", "PR #5344", "PR #5543", "PR #5720", "PR #5737", "PR #5764", "PR #5801", "PR #5802", "PR #5838", "PR #5839", "PR #5848", "PR #5872", "PR #5881", "PR #5896", "PR #5981", "PR #6094", "PR #6102", "PR #6279", "PR #6385", "PR #6445", vllm_omni/diffusion/attention/backends/flashinfer_attn.py, vllm_omni/diffusion/attention/backends/ring/ring_kernels.py, vllm_omni/diffusion/attention/parallel/ulysses.py, vllm_omni/diffusion/cache/cachedit/backend.py, vllm_omni/diffusion/data.py, vllm_omni/diffusion/distributed/hsdp.py, vllm_omni/diffusion/executor/multiproc_executor.py, vllm_omni/diffusion/layers/norm.py, vllm_omni/diffusion/layers/rope.py, vllm_omni/diffusion/lora/manager.py, vllm_omni/diffusion/model_loader/diffusers_loader.py, vllm_omni/diffusion/model_metadata.py, vllm_omni/diffusion/offloader/, vllm_omni/diffusion/registry.py, vllm_omni/diffusion/worker/diffusion_model_runner.py, vllm_omni/engine/async_omni_engine.py, vllm_omni/entrypoints/openai/api_server.py, vllm_omni/quantization/component_config.py, vllm_omni/quantization/factory.py, tests/diffusion/attention/test_attention_sp.py, tests/diffusion/attention/test_ulysses_uaa.py, tests/diffusion/cache/test_cache_backends.py, tests/diffusion/layers/test_norm.py, tests/diffusion/layers/test_rope_broadcast.py, tests/diffusion/offloader/test_distributed_layerwise_backend.py, tests/diffusion/test_diffusion_config_propagation.py, "PR #4755", "PR #5990", "vllm_omni/diffusion/layers/fused_qk_norm_rope.py", "vllm_omni/diffusion/cache/teacache/extractors.py", "vllm_omni/diffusion/models/minimax_h3/minimax_h3_transformer.py", "tests/diffusion/layers/test_fused_qk_norm_rope.py", "PR #6165"]
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
| `checkpoint-distributed` | checkpoint、quantization、HSDP/FSDP、artifact identity、distributed offload、multi-DiT/cache lifecycle | `DIFF-2a`–`2n` |
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

### DIFF-2a — checkpoint remap 必须追到已注册且真实消费的目标

- 触发：增加或修改 weight mapper、scale 名称、quantization adapter 或 key resolution。
- 强制：从序列化 key 追到目标 layer 注册的 parameter/buffer 和 forward consumer；
  多条 resolution path 必须返回对称、由合同解释的目标名。模型专属 grouped-QKV reorder、
  fused gate/up split 等布局变换必须在调用 active weight loader 前完成，让 quantization wrapper
  与 TP shard 接收最终语义布局。
- 禁止：把 producer 有而当前 consumer 不支持的 tensor 静默过滤；必须 fold/map 或
  fail fast，并在错误中标明依赖的 upstream 版本边界。
- 验收：测试覆盖已消费 key、未知 key、当前版本不支持的 scale 以及两条 resolution
  path 的输出名；fused mixed-FP8 还须覆盖 weight/scale/shard、gate/up 顺序、nested serialized
  FP8 和 combined projection，缺 shard 不得默认 0。 ^[PR #5087] ^[PR #5737] ^[PR #5848]
- 强制：读取 transformer-local `config.json` 时，disk method 与 active method 归一化后不一致
  必须失败；disk 声明 serialized、`data_type=mx_fp` 或不同 `ignored_layers` 时应按该 component
  重建 config，不能用 online/default 配置解释 serialized 权重。目标 pin 的
  `resolve_quant_config_from_disk` 只有 Wan2.2 一个 live caller，且无 helper 直测；在补齐多模型
  caller 与 mismatch/serialized/ignored-layers 测试前，这只是局部 loading guard，不是全局自动
  checkpoint reconciliation 支持。^[PR #5839]

### DIFF-2b — HSDP/FSDP 修复必须执行真实 fully_shard

- 触发：改动 diffusion HSDP/FSDP 参数过滤、packed/scalar parameter 或 DeviceMesh。
- 强制：至少用单 rank Gloo + CPU DeviceMesh 执行一次真实 `fully_shard`。
- 禁止：只断言传给 mock 的 kwargs 后声称分布式语义已覆盖。
- 验收：普通 float parameter 变为 DTensor；packed uint8/scalar parameter 保持本地
  identity，并覆盖 loader 的真实调用边界；replicate size 非正值拒绝，1 用 1D、>1 用 2D
  DeviceMesh，测试 world size 与参数一致。 ^[PR #5088] ^[PR #5872]

### DIFF-2c — component quantization 独立解析且 namespace 端到端一致

- 触发：diffusion pipeline 为 text encoder、transformer、VAE 等组件增加独立量化配置。
- 强制：每个组件独立解析量化配置，并选择一个端到端一致的 namespace：要么 selector
  保留 `text_encoder` 等完整 component owner prefix 到持权 layer，要么 pipeline 先 resolve
  单一 component，再让内部 layer 使用 component-relative prefix。只量化明确支持的 linear，
  embedding、LM head、patch/final projection 等排除项必须显式保持未量化。
- 强制：`ComponentQuantizationConfig.resolve()` 只对 `get_quant_method` 收到的 runtime prefix 做
  longest-prefix match，未命中才落到 default；它不会自动感知 checkpoint `WeightsMapper`。
  因此 mapper、pipeline 与 layer 必须显式维持同一 namespace，并测试重叠 prefix 的最长匹配。
- 禁止：半途裁掉 owner prefix；resolve component 后又要求 ignored layer 带 owner；用一个
  组件配置隐式覆盖其他组件；因为同属一个模型就量化全部 linear。
- 验收：至少覆盖“只量化一个组件、其他组件保持 BF16”的真实构造与加载，逐层断言
  命中/排除集合，并验证 meta-device parameter 不会被提前 move。FLUX.2 的具体边界见
  [FLUX.2 规则](../../models/flux2/rules.md)，component-relative 变体见
  [MiniMax H3 规则](../../models/minimax-h3/rules.md)；新增 quantization×offload 组合需给兼容矩阵，
  未验证 quantizer fail-closed，并核对 dtype/shape/stride。 ^[PR #5136] ^[PR #5737]
  ^[PR #6279]

### DIFF-2d — Artifact identity 只信任已验证的不可变来源

- 触发：新增或修改 host-weight artifact、warm restore、source identity、layout/dtype policy。
- 强制：共享 identity、restore 和 model ABI 保持 representation-neutral，dtype/layout 只属于
  具体 policy/producer；只有同时验证 source kind、snapshot revision、repo topology 和 blob
  位置的内容寻址仓库，才可用 blob 名代替内容哈希，其他本地文件和 symlink 必须按内容定身份。
- 禁止：因 symlink 目标名看似 40/64 位十六进制就假设不可变；把 `bf16`、具体 layout 或首个
  producer 名写进共享 identity/restorer API；用进程内 inode/mtime guard 代替跨启动身份校验。
- 验收：第二种 synthetic representation 复用共享 identity/restorer；任意本地十六进制命名
  symlink 在同大小内容被替换后产生不同 identity；合法 Hub snapshot→blob 拓扑仍走受控快捷路径。
  ^[PR #6445]

### DIFF-2e — distributed layerwise offload 只能选择一个一致的权重分片合同

- 触发：新增 `enable_distributed_layerwise_offload`、`dlo_use_allgather`、模型
  `OffloadPlan` 或 block discovery。
- 强制：明确 rank 本地 CPU shard、固定双 GPU buffer、H2D/AllGather stream 和模型
  block list 的 owner；`dlo_use_allgather=false` 保留 standard loader 已生成的每-rank
  ready-to-run layout（没有其他分片维度时才是 full weight，TP 下则是 TP-local shard），开启
  AllGather 时不得再叠加已 DTensor-sharded 的 HSDP 参数。共享 output buffer 可按所有 hook
  的最大 block 分配，但每个 hook 调 collective 前必须按 dtype 截成自己的
  `_ag_output_sizes[dtype] == dp_size * local_shard.numel()` 前缀；block-flat-relative repoint
  offset 只能在这段实际 block buffer 内解释。
- 强制：AllGather 权重组复用既有 topology：DP>1 优先 DP group；DP=1 且 SP>1 才用 SP group。
  TP 不作为 DLO AllGather group；进入 mmap path 时 TP>1 必须因绕过 TP-aware weight-loader
  callback 而拒绝。no-AllGather 只关闭 DLO 新增的权重 collective，不关闭 standard loader
  已建立的 TP/HSDP/SP 语义，也不提供跨 rank host-weight 节省。DP=SP=1 不能从“无 process
  group”推断为可用的 rank-local AllGather 模式：目标 pin 的 loader 在 DLO+AllGather、支持 mmap
  时会跳过 `load_weights()`，但 backend 只有 `dp_size>1` 才执行 mmap load，两个 gate 不一致；
  修复并回归前单 rank 应使用 no-AllGather 或普通 layerwise offload。
- 强制：非 DiT component 的 staging 必须由 `OffloadPlan` 显式声明：encoder block group
  rank-local streaming 不借用 DiT AllGather group，on-demand component 由 pipeline 在真实
  encode/decode stage 成对 load/offload，resident layer 只对声明的 DiT path 生效。no-AllGather
  路径保留 standard loader 产生的 TP-local layout；若模型 loader 还做 QKV/MLP transform，
  mmap 必须显式 opt out，直到 transform-before-shard 等价性有测试。
- 禁止：用 heuristic 找不到 block 时静默假装 offload 已启用；对 HSDP 参数二次分片；
  把 CPU 内存、AllGather 同步和设备显存开销隐藏在一个泛化的 `enable_cpu_offload` 开关；
  把 max-sized shared buffer 原样交给较小 block 的 `all_gather_into_tensor`。
- 验收：CPU/Gloo 单 rank 覆盖 DTensor wrapper、shard padding、双 buffer 和 disable
  cleanup；配置测试覆盖 AllGather+HSDP 的明确失败及 no-AllGather 的允许路径。另以至少两个
  不同 block size 验证 small/large hook 都满足 collective size equality、重建权重和 repoint。
  当前回归用 mocked collective 检查 8/32-element、dp=2 合同；没有真实 multi-rank collective
  覆盖，PR 的 8×NPU H3 E2E 说明也缺少已填写的 commit 证据，不能升级为验证结论。 ^[PR #5802]
  DLO DP collective-wave admission 见 [DIFF-2k](rules-output-lifecycle.md)；no-AllGather 的
  TP-local request 不得误走 fused batch。文档 compatibility matrix 中
  “accepted” 默认只代表配置/源码 guard；PR #5836 的 predecessor partition-path commit 为 H3
  USP4+HSDP4+no-AllGather+8 resident layers 提供一次 4×H100、3/3 completion/perf run，故该 exact
  组合不再是纯 config evidence，但没有 ordinary-offload 数值/输出质量对照，且 profiler 开启、
  final repo-root modular route 未复测，仍不得升级为 production support。TP+no-AllGather、一般
  DP+SP 等其他组合仍缺完整 model×hardware E2E。^[PR #5764] ^[PR #5839] ^[PR #5836]

多 DiT component discovery 与 dotted-path lifecycle 合同见
[DIFF-2f–2j 专页](rules-component-lifecycle.md)。

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
