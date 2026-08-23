---
title: "Diffusion 共享规则"
created: 2026-07-20
updated: 2026-08-23
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #4341", "PR #5001", "PR #5087", "PR #5088", "PR #5136", "PR #5543", "PR #5848", "PR #5872", "PR #5981", "PR #6094", "PR #6102", "PR #6279", "PR #6385", "PR #6445", vllm_omni/diffusion/worker/diffusion_model_runner.py, vllm_omni/diffusion/model_loader/diffusers_loader.py, vllm_omni/diffusion/distributed/hsdp.py]
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
| CUDA Graph、compile、fused solver、eager parity、tensor dtype/device | `execution-parity`：`DIFF-1a`–`1c` | `compile.py::regionally_compile` → runner batch → model denoise/solver |
| seed、request-local generator、guidance=0、并发 RNG、batched generators | `execution-parity`：`DIFF-1b` | `inputs/data.py::OmniDiffusionSamplingParams` → runner `_initialize_generator` → request-batch generator collate |
| ModelOpt/checkpoint adapter、weight/scale remap、unknown tensor、resolution path | `checkpoint-distributed`：`DIFF-2a` | `diffusers_loader.py::{_get_checkpoint_adapter,load_weights}` → `modelopt.py::{_resolve_target_and_output_names,adapt}` |
| host-weight artifact、source identity、layout/dtype、warm restore | `checkpoint-distributed`：`DIFF-2d` | `model_loader/host_weights/{source_identity,contracts,identity_adapter}.py` → policy/restorer |
| HSDP/FSDP、`fully_shard`、DeviceMesh、packed/scalar parameter、FP8 | `checkpoint-distributed`：`DIFF-2b` | `distributed/hsdp.py::{apply_hsdp_to_model,shard_model}` → loader `_load_model_with_hsdp` → `hsdp_fp8.py` |
| component quantization、text encoder/transformer/VAE 独立配置、owner prefix、meta/offload | `checkpoint-distributed`：`DIFF-2c` | `data.py::_propagate_quantization_from_tf_config` → loader weight sources/post-load → component linear consumer |
| LPIPS/PSNR/相似度阈值、CPU offload、量化质量证据 | `quality-evidence`：`DIFF-3a` | changed exact case → runner `execute_model` → model pipeline；A/B 同路径 |
| paged KV/cache、backend/platform、GQA/layout、预算与 admission | `system-runtime`：`DIFF-4a`–`4f` | engine init → `diffusion_kv/{initialization,paged_attention_adapter}.py` → platform hook → scheduler |
| worker/RPC 异常、rank-status、traceback/device cache 清理 | `system-runtime`：`DIFF-4d` | `diffusion_worker.py::{_execute_rpc,_worker_busy_loop}` 的 raise/reply/status 路径 |

| 审查组 | 什么时候触发 | 规则 ID |
|---|---|---|
| `core` | 每次共享 diffusion 审查 | `DIFF-1a`, `DIFF-1b`, `DIFF-1c` |
| `execution-parity` | graph/eager、solver、RNG、generator、tensor dtype/device | `DIFF-1a`, `DIFF-1b`, `DIFF-1c` |
| `checkpoint-distributed` | checkpoint、quantization、HSDP/FSDP、artifact identity | `DIFF-2a`, `DIFF-2b`, `DIFF-2c`, `DIFF-2d` |
| `quality-evidence` | 质量阈值、offload、A/B case | `DIFF-3a` |
| `system-runtime` | cache/预算、native/backend/platform、attention layout、异常与并发 | `DIFF-4a`–`4f` |
| `author-routing` | 只供 Direct reviewer 导航，不作为 finding 规则 | `DIFF-0a`, `DIFF-0b` |

## 优化路径与 eager 的等价合同

### DIFF-1a — graph/compile/fused 路径逐项复刻 eager 数值边界

- 触发：新增或修改 CUDA Graph、compile、fused scheduler/solver 或缓存执行路径。
- 强制：逐项对齐初始噪声、solver/timestep dtype、每步 cast 边界、最后一步更新、
  CFG=0/近零分支和输出 dtype；依赖行为有版本差异时固定并验证版本。
- 禁止：只比较 shape、无 NaN 或“能运行”；这些不能证明数值和请求语义等价。
- 验收：固定输入和 request-local generator，对 eager/优化路径逐步比较关键状态并覆盖
  零值和最后一步边界。Ming-TTS 的具体反例见
  [Ming-Omni-TTS 规则](../../models/ming-omni-tts/rules.md)。 ^[PR #4341]

### DIFF-1b — 随机状态属于请求，零值不是缺省值

- 触发：pipeline/scheduler 接收 seed、generator、guidance 或其他允许为零的数值。
- 强制：使用请求本地 generator 并证明当前依赖版本真正消费它；用 `is None` 区分
  缺省与 `0`/`0.0`。
- 禁止：并发请求中修改 process-global RNG；使用 `x or default` 吃掉合法零值。
- 验收：两个并发请求用不同 generator 可重复且互不影响，`0.0` 从 request 构造一路
  到达 consumer。Cosmos3 的落地约束见
  [Cosmos3 规则](../../models/cosmos3/rules.md)。 ^[PR #5001]

### DIFF-1c — 新 tensor 从真实 consumer 派生 dtype 和 device

- 触发：mixed precision pipeline 中新建 mask、index、constant、buffer 或预计算 tensor。
- 强制：从输入或目标权重派生 device/dtype，整数 index 显式使用 consumer 要求的类型；
  graph/eager 与 batch 重排后保持 shape、alias 和数值语义。
- 禁止：依赖 process 默认 fp32/CPU 或隐式 cast/move；只测 shape 而不执行 BF16 consumer。
- 验收：BF16、错长、batch reorder 和 graph/eager 用例断言 consumer 收到相同 device/dtype、
  alias 与结果。 ^[PR #5067] ^[PR #5068] ^[PR #5174] ^[PR #5981]

## Checkpoint 与分布式加载

### DIFF-2a — checkpoint remap 必须追到已注册且真实消费的目标

- 触发：增加或修改 weight mapper、scale 名称、quantization adapter 或 key resolution。
- 强制：从序列化 key 追到目标 layer 注册的 parameter/buffer 和 forward consumer；
  多条 resolution path 必须返回对称、由合同解释的目标名。
- 禁止：把 producer 有而当前 consumer 不支持的 tensor 静默过滤；必须 fold/map 或
  fail fast，并在错误中标明依赖的 upstream 版本边界。
- 验收：测试覆盖已消费 key、未知 key、当前版本不支持的 scale 以及两条 resolution
  path 的输出名；fused mixed-FP8 还须覆盖 weight/scale/shard、gate/up 顺序、nested serialized
  FP8 和 combined projection，缺 shard 不得默认 0。 ^[PR #5087] ^[PR #5848]

### DIFF-2b — HSDP/FSDP 修复必须执行真实 fully_shard

- 触发：改动 diffusion HSDP/FSDP 参数过滤、packed/scalar parameter 或 DeviceMesh。
- 强制：至少用单 rank Gloo + CPU DeviceMesh 执行一次真实 `fully_shard`。
- 禁止：只断言传给 mock 的 kwargs 后声称分布式语义已覆盖。
- 验收：普通 float parameter 变为 DTensor；packed uint8/scalar parameter 保持本地
  identity，并覆盖 loader 的真实调用边界；replicate size 非正值拒绝，1 用 1D、>1 用 2D
  DeviceMesh，测试 world size 与参数一致。 ^[PR #5088] ^[PR #5872]

### DIFF-2c — component quantization 独立解析且保留完整 owner 前缀

- 触发：diffusion pipeline 为 text encoder、transformer、VAE 等组件增加独立量化配置。
- 强制：每个组件独立解析量化配置，并把包含 component owner 的完整模块名前缀传到
  真正持有权重的 layer；只量化明确支持的 attention/MLP linear，embedding、LM head
  等排除项必须显式保持未量化。
- 禁止：先裁掉 `text_encoder` 等 owner 前缀再匹配 component 规则；用一个组件的配置
  隐式覆盖其他组件；因为同属一个模型就量化全部 linear。
- 验收：至少覆盖“只量化一个组件、其他组件保持 BF16”的真实构造与加载，逐层断言
  命中/排除集合，并验证 meta-device parameter 不会被提前 move。FLUX.2 的具体边界见
  [FLUX.2 规则](../../models/flux2/rules.md)；新增 quantization×offload 组合需给兼容矩阵，
  未验证 quantizer fail-closed，并核对 dtype/shape/stride。 ^[PR #5136] ^[PR #6279]

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

相关执行流见 [Diffusion architecture](architecture.md)；benchmark 证据合同见
[performance evidence](../../benchmark/guides/performance-evidence.md)。
