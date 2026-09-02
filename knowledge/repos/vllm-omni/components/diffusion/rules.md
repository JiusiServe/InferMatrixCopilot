---
title: "Diffusion 共享规则"
created: 2026-07-20
updated: 2026-09-02
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #4341", "PR #5001", "PR #5087", "PR #5088", "PR #5136", "PR #5255", "PR #5344", "PR #5543", "PR #5720", "PR #5737", "PR #5764", "PR #5801", "PR #5802", "PR #5838", "PR #5839", "PR #5848", "PR #5872", "PR #5881", "PR #5896", "PR #5981", "PR #6094", "PR #6102", "PR #6279", "PR #6385", "PR #6445", vllm_omni/diffusion/attention/backends/flashinfer_attn.py, vllm_omni/diffusion/attention/backends/ring/ring_kernels.py, vllm_omni/diffusion/attention/parallel/ulysses.py, vllm_omni/diffusion/cache/cachedit/backend.py, vllm_omni/diffusion/data.py, vllm_omni/diffusion/distributed/hsdp.py, vllm_omni/diffusion/executor/multiproc_executor.py, vllm_omni/diffusion/layers/norm.py, vllm_omni/diffusion/layers/rope.py, vllm_omni/diffusion/lora/manager.py, vllm_omni/diffusion/model_loader/diffusers_loader.py, vllm_omni/diffusion/model_metadata.py, vllm_omni/diffusion/offloader/, vllm_omni/diffusion/registry.py, vllm_omni/diffusion/worker/diffusion_model_runner.py, vllm_omni/engine/async_omni_engine.py, vllm_omni/entrypoints/openai/api_server.py, vllm_omni/quantization/component_config.py, vllm_omni/quantization/factory.py, tests/diffusion/attention/test_attention_sp.py, tests/diffusion/attention/test_ulysses_uaa.py, tests/diffusion/cache/test_cache_backends.py, tests/diffusion/layers/test_norm.py, tests/diffusion/layers/test_rope_broadcast.py, tests/diffusion/offloader/test_distributed_layerwise_backend.py, tests/diffusion/test_diffusion_config_propagation.py]
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
| paged KV/cache、backend/platform、GQA/layout、Ring/Ulysses、FlashInfer quant、预算与 admission | `system-runtime`：`DIFF-4a`–`4j` | engine init → metadata/config → attention parallel/backend → platform hook → scheduler/serving |
| worker/RPC 异常、rank-status、traceback/device cache 清理 | `system-runtime`：`DIFF-4d` | `diffusion_worker.py::{_execute_rpc,_worker_busy_loop}` 的 raise/reply/status 路径 |

| 审查组 | 什么时候触发 | 规则 ID |
|---|---|---|
| `core` | 每次共享 diffusion 审查 | `DIFF-1a`, `DIFF-1b`, `DIFF-1c`, `DIFF-1d`, `DIFF-1e` |
| `execution-parity` | graph/eager、solver、RNG、generator、tensor dtype/device、fused layer、FA determinism、async output/shutdown | `DIFF-1a`–`1j` |
| `checkpoint-distributed` | checkpoint、quantization、HSDP/FSDP、artifact identity、distributed offload、multi-DiT/cache lifecycle | `DIFF-2a`–`2n` |
| `quality-evidence` | 质量阈值、offload、A/B case | `DIFF-3a` |
| `system-runtime` | cache/预算、native/backend/platform、attention layout、能力 metadata、异常与并发 | `DIFF-4a`–`4j` |
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

## Paged cache、资源预算与系统运行时

### DIFF-4a — 容量预算必须在影响峰值的初始化完成后测量

- 触发：新增或修改 KV/cache block 数、GPU/CPU memory budget、auto-fit、warmup/profile、
  dummy run 或物理 cache 分配。
- 强制：写出并核对 `model load → activation warmup/profile → available-memory measurement
  → logical config → physical allocation → first real request` 的真实顺序；预算必须包含真实
  activation/graph/lazy-kernel 峰值及明确 headroom。若当前阶段故意只建逻辑控制面，必须使用
  显式固定预算或把最终容量决定推迟到数据面 profile 之后。
- 禁止：用 warmup 前的当前 free/process residency 推导可用 cache，再在之后执行会常驻或抬高
  峰值的 dummy/profile；也不能用 native auto-fit 或 allocator 成功证明预算来源正确。
- 验收：enabled 路径在真实初始化顺序下记录测量前后峰值，低显存/最大合法请求不会因漏算
  activation 在首次或后续执行 OOM；显式预算分支和自动预算分支各有测试。 ^[PR #6094]

### DIFF-4b — 复用 native 组件仍须审计 caller/adapter 契约

- 触发：diffusion adapter 调用 vLLM 的 cache spec/config/manager、scheduler 或其他版本化 API。
- 强制：按仓库 pin 的精确 vLLM 版本核对 property/method、签名、sentinel、block-size 单位、
  max-length/capacity 前提、返回失败语义和 free/rollback 责任；分别证明 adapter 输入、调用时序、
  输出解释和 native 内部算法。
- 禁止：把“委托给 native vLLM”当作端到端正确性证明；native manager 不负责验证 Omni 在何时
  测量预算、是否漏算其他显存、是否正确传播失败，也不保证 adapter 模拟对象符合真实属性合同。
- 验收：真实 pin 的 contract test 覆盖正常值、边界/sentinel、容量不足、property 访问和清理；
  fake 不能把真实 property 改成同名 method 或跳过 native precondition。 ^[PR #6094]

### DIFF-4c — Feature gate 只限制影响范围，enabled 路径必须独立闭环

- 触发：新增或修改 `dense_legacy`/paged、eager/optimized 或其他默认关闭的 diffusion 路径。
- 强制：分别审计 disabled/default 与 enabled；enabled 至少覆盖单请求、并发/多 rank、低资源、
  partial allocation、执行异常、取消、timeout、shutdown 和重复释放。异常必须到达终端请求或
  engine 信号并唤醒 waiter，所有已分配资源由明确 owner 回收。
- 禁止：用“默认路径有 gate”“dense 未回归”或单请求 smoke 推导新路径正确；也不能让 scheduler/
  busy-loop 异常逃逸后留下永远等待的 stream。
- 验收：path/lifecycle matrix 每行有 production-path 测试或明确 `MISSING_EVIDENCE`；enabled
  关键行缺失时审查只能是 partial，不能输出 clean/no findings。 ^[PR #6094]

### DIFF-4d — 异常清理覆盖每种错误传递形态

- 触发：worker/RPC 在异常后清 traceback、释放 device tensor/cache，或把异常转换成
  reply、rank-status envelope、`DiffusionOutput`。
- 强制：先保存对外所需的字符串化错误，再对 raise、普通错误回复和 collect-status 正常返回
  三条路径逐一执行同一清理；调用方把异常折叠成成功返回形态时仍必须释放原异常引用。
- 禁止：只在最外层 `except` 清理，却让内部状态封装路径正常返回；清理后继续从异常对象读取
  message/traceback；用单一路径 mock 证明所有 RPC mode 都不会保留 device tensor。
- 验收：测试分别覆盖 `collect_rank_status=true` 与抛出/错误回复路径，断言错误文本仍可见、
  `exc.__traceback__ is None`、cache cleanup 被调用，后续健康 RPC 仍成功。 ^[PR #6385]

### DIFF-4e — paged backend 在启动时按平台和逐层能力闭环

- 触发：启用 paged scheduler、增加 diffusion attention backend 或平台 override。
- 强制：启动阶段解析并验证每层实际 backend 与当前平台；走 Omni platform hook，保留
  piecewise/SP 等能力。尚无生产 caller 的模式必须明确告警并文档化。
- 禁止：未知平台继承 GPU 默认；分配 cache 后到首次 dispatch 才失败；静默占用 paged KV
  却继续 dense；直接换用 upstream backend 丢失 Omni 能力。
- 验收：unsupported platform/backend fail-fast；CUDA/NPU 对应 lane 和正式模型 E2E 证明
  resolved backend；mixed-mask piecewise/SP 回归通过。 ^[PR #5543] ^[PR #6102]

### DIFF-4f — paged attention metadata 不从 padding 猜逻辑布局

- 触发：paged adapter 修改 GQA、prefix/current-token packing、LSE layout 或二维特例。
- 强制：显式传递 Q/KV head 数、每请求 prefix/current span 和 layout；保持压缩 GQA 与 packed
  current-token 语义，单 token/单 head 二维输入仍使用同一合同。
- 禁止：从 padding 长度推断逻辑跨度；在 `sequence == heads` 时猜 LSE 维度；fallback 静默换
  backend 或把 KV heads 扩成 Q heads。
- 验收：32Q/8KV、异构 prefix、单 token/单 head、非对称等维 LSE 和 batch compaction 精确
  对照 dense/reference 输出。 ^[PR #5543] ^[PR #6102]

### DIFF-4g — Ring GQA 只在通信后扩展，Hybrid Ulysses 不把 padding 当真 head

- 触发：修改 Ring SDPA、GQA/MQA head 数、LSE accumulation、Ulysses all-to-all 或
  `advanced_uaa` head padding。
- 强制：Ring 始终以原始 `H_kv` 通信 K/V；仅在本 rank 的 aten SDPA 调用前，当
  `H_q != H_kv` 时要求 `H_q % H_kv == 0`，再用 `repeat_interleave(H_q/H_kv)` 将 K/V 扩成
  Q head 数。该 local materialization 增加 kernel 输入计算/显存，但不增加 ring 通信量；不能
  提前到 send/recv 前。之所以不能直接用 `enable_gqa`，是该 path 需要 aten flash/efficient
  SDPA 返回 LSE 供 ring accumulation，而这些调用没有该参数。实现以 K head 数计算 factor 并
  同样 repeat V，却未显式检查 `H_v == H_k`；现有测试始终令两者相等，future caller/backend 必须
  保持或提前断言该 invariant，不能等 SDPA 在更深处 cryptic failure。
- 强制：`advanced_uaa` + Hybrid Ulysses/ Ring 时，在 Ulysses all-to-all 前检查 key 和 value
  原始 head 数均可被 `ulysses_degree` 整除；否则 fail-fast。padding 出来的 zero K/V head 若交给
  Ring 再 replicate 会被当成真实 group，不能作为合法 MQA/GQA。pure Ring（Ulysses=1）仍支持
  1 或多 KV heads；valid Hybrid positive fixture 必须使用可整除布局。
- 禁止：用默认 backend 的绿测证明 SDPA 修复（安装 FA/FA3 时会绕过）；用 num_heads=3、
  Ulysses=2 的 padded case 当 Hybrid 正向测试；从通信量不变推断端到端性能不变。
- 验收：4-card test 显式设 `TORCH_SDPA`，以 single-rank baseline 对 pure Ring GQA(8Q/2KV)、
  MQA(8Q/1KV) 和既有 Ulysses+Ring/AllGather-KV 输出，BF16 容差 5e-2；CPU guard 覆盖 Hybrid
  padded-MQA 拒绝，另以 4Q heads、Ulysses2×Ring2 验证 valid Hybrid。ready CI 的 L4×4 job
  已收集 `test_attention_sp.py`，但不收集 `test_ulysses_uaa.py`；PR comment 的 primary matrix
  是 pre-final head `e6857888` 在 4×B300 上 4 passed、max abs 0.015625，runtime fix 已在但 final
  target 未复测。修正为 4 heads 的 Hybrid 25.30s pass 只见 final PR body，未附 hardware/SHA/log。
  因此目标 pin 有局部数值证据和未来 L4 gate wiring，但没有附带 L4 run 产物，Hybrid
  guard/positive 也未被该新 job 覆盖。^[PR #5255]

### DIFF-4h — FlashInfer mixed-dtype plan 必须绑定完整 runtime shape 与 mask 内容

- 触发：修改 `FLASHINFER_ATTN`、`BatchPrefillWithRaggedKVCacheWrapper`、QK16/V8、backend
  selection、ragged indptr/plan cache 或 custom mask fallback。
- 强制：输入保持初始化时 CUDA device；Q/K 只允许 fp16/bf16 override，V 另允许
  fp8_e4m3，wrapper 输出恢复原 query dtype。auto backend 按 compute capability 选 major>=10
  `cute-dsl`、major>=9 `fa3`、否则 `fa2`；non-CuTe 才接受 custom mask，CuTe nontrivial mask、
  causal+explicit mask 或无法 pack 的 mask 必须回退原始输入的 Torch SDPA。
- 强制：plan key 至少绑定 batch、Q/KV length、Q/KV heads、QK/K/VO head dim、Q/K/V/output
  dtype、causal、scale 与是否有 mask；shape/dtype 改变重建 indptr/plan，unmasked 同 key 可复用。
  mask shape 相同也可能内容不同，所以每次 masked call 都必须重新 plan，不能只按 pointer/shape
  cache。Q/K/V cast 留在 compile-visible path，wrapper plan/run 边界才 disable compiler。目标 key
  虽记录 `head_dim_k`，plan 只接收 `head_dim_qk` 与 `head_dim_vo`，且未断言 Q/K head dim 相等；
  caller 必须保持 `D_q == D_k`，并补 mismatch fail-fast test，不能把 key 字段误当 backend 已消费。
- 禁止：把本 PR 早期 Sage/TRTLLM kernels 当成 merged scope（review 后删除并转交 TRTLLM
  backend）；把 activation 直接 cast 成 FP8 描述成带 scale 的 checkpoint quantization；用
  `supports_attention_mask=True` 推断 CuTe 支持任意 mask。
- 验收：mixed QK/V dtype 只能在 FlashInfer >=0.6.16rc1；目标对可解析的 <=0.6.15 fail-fast，
  但没有 dependency pin，只有 docs/code gate。该 gate 比较配置 override：两者均为 None 时立即
  返回，即使 caller 实际传入 mixed Q/K 与 V tensor 也不拦；capability 必须最终按 plan 中真实
  q/k/v dtype 校验。缺失/非法 `flashinfer.__version__` 也会直接放行，是未封闭 gap。须补测试覆盖
  dtype allowlist、old/missing version、auto backend、device mismatch、plan reuse/replan、同 shape
  不同 mask、CuTe/causal fallback、GQA 与 output dtype；本 PR 没有新增 repo test，只有外部 smoke。
  PR 的 Cosmos3 1280×720、35 steps、seed42，B200/B300 DiT timing 与 Nano 前24帧 LPIPS=0.051496
  只绑定 vLLM-Omni `4ce23c33` + FlashInfer `d0889c7c` 的 pre-final 环境；final config/version gate
  commit 后无复测，且这些不是端到端 latency、稳定 speedup 或通用质量阈值。^[PR #5344]

### DIFF-4i — 模型能力 metadata 必须跨 architecture 与 pipeline 两个 key space 解析

- 触发：修改 diffusion registry、HF `architectures`、`model_class_name` 或共享
  `DiffusionModelMetadata`，尤其是多图数量、mixed-reference 与 attention-mask-free 能力。
- 强制：先接受 metadata 表中的 direct pipeline key；未命中时只通过 registry 的
  `architecture → pipeline class` 映射解析一次，再查 metadata。unknown architecture、`None`，以及
  registry 映射到没有 metadata 的 pipeline 都保持空 defaults；registry tuple 用解包读取，使布局
  变化显式失败。此 helper 返回整份 metadata，影响 config、AsyncOmni serving view、视频 mixed
  reference 和 attention backend，不得把修改只当作 image-count 局部修复。
- 禁止：因 architecture 已注册就假定其 pipeline 有 metadata；递归猜测别名；让 direct key 被
  registry 映射覆盖；或把 defaults 的 `supports_multimodal_inputs=false` 当成“数量未知”——image-edit
  admission 会把它解释为最多一张图，而 `supports=true, max=None` 才是不设上限。
- 验收：同时覆盖 direct pipeline key、architecture→metadata-bearing pipeline、unknown/`None`、
  以及 architecture→无 metadata pipeline；通过 `OmniDiffusionConfig.update_multimodal_support()`
  断言整份能力传播，并在 serving 边界验证 false→1、true+整数上限与无上限行为。PR #5838 只新增
  Qwen direct 与 Hunyuan architecture→pipeline 的手动 config 测试；未执行真实 architecture 解析、
  AsyncOmni 或 HTTP edit 路径，也没有 registry/metadata census 和 negative alias 回归。其 E2E 结果
  只有截图，缺命令文本日志、vLLM 版本、upstream SHA 与重复次数。helper 仍 function-local import
  私有 `_DIFFUSION_MODELS`，review 提议公开改名但 final 未采用。^[PR #5838]

相关执行流见 [Diffusion architecture](architecture.md)；benchmark 证据合同见
[performance evidence](../../benchmark/guides/performance-evidence.md)。
