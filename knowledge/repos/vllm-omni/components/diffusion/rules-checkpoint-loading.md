---
title: "Checkpoint、加载与量化合同"
created: 2026-09-04
updated: 2026-09-04
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #5087", "PR #5088", "PR #5136", "PR #5544", "PR #5677", "PR #5737", "PR #5764", "PR #5802", "PR #5836", "PR #5839", "PR #5848", "PR #5872", "PR #5910", "PR #6070", "PR #6234", "PR #6279", "PR #6445", "PR #6486", "PR #6591", vllm_omni/diffusion/model_loader/, vllm_omni/quantization/, vllm_omni/diffusion/distributed/hsdp.py, vllm_omni/diffusion/offloader/, tests/diffusion/quantization/test_wan_autoround_mxfp4.py, "PR #5531", "PR #4061"]
confidence: high
---

# Checkpoint、加载与量化合同

`checkpoint-distributed` 审查组的 `DIFF-2a`–`DIFF-2s`：checkpoint remap、HSDP/FSDP 分片、component quantization、artifact identity、distributed layerwise offload，以及在线量化加载与权重布局。触发条件与其余审查组见 [Diffusion 共享规则](rules.md) 的 Direct 代码快速入口。

## DIFF-2a — checkpoint remap 必须追到已注册且真实消费的目标

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

## DIFF-2b — HSDP/FSDP 修复必须执行真实 fully_shard

- 触发：改动 diffusion HSDP/FSDP 参数过滤、packed/scalar parameter 或 DeviceMesh。
- 强制：至少用单 rank Gloo + CPU DeviceMesh 执行一次真实 `fully_shard`。
- 禁止：只断言传给 mock 的 kwargs 后声称分布式语义已覆盖。
- 验收：普通 float parameter 变为 DTensor；packed uint8/scalar parameter 保持本地
  identity，并覆盖 loader 的真实调用边界；replicate size 非正值拒绝，1 用 1D、>1 用 2D
  DeviceMesh，测试 world size 与参数一致。 ^[PR #5088] ^[PR #5872]

## DIFF-2c — component quantization 独立解析且 namespace 端到端一致

- 触发：diffusion pipeline 为 text encoder、transformer、VAE 等组件增加独立量化配置。
- 强制：每个组件独立解析量化配置，并选择一个端到端一致的 namespace：要么 selector
  保留 `text_encoder` 等完整 component owner prefix 到持权 layer，要么 pipeline 先 resolve
  单一 component，再让内部 layer 使用 component-relative prefix。只量化明确支持的 linear，
  embedding、LM head、patch/final projection 等排除项必须显式保持未量化。
- 强制：`ComponentQuantizationConfig.resolve()` 只对 `get_quant_method` 收到的 runtime prefix 做
  longest-prefix match，未命中才落到 default；它不会自动感知 checkpoint `WeightsMapper`。
  因此 mapper、pipeline 与 layer 必须显式维持同一 namespace，并测试重叠 prefix 的最长匹配。
- 强制：离线 AutoRound checkpoint 若 `config.json` 以 `data_type="mx_fp"` 声明 MXFP，
  `resolve_quant_config_from_disk()` 必须用 checkpoint 的 `bits`（或现有 config 的
  `weight_bits` fallback）重建量化 config，使 4-bit 与 8-bit 路径都由真实位宽选择；不能把
  这种 metadata 当作只有 serialized flag 才会触发的 online/default config。Wan runtime
  prefix 的 `block_name_to_quantize=["blocks"]` 必须只命中 `blocks.*` 的 linear，并保留
  `condition_embedder.*` 等范围外层未量化。
- 禁止：半途裁掉 owner prefix；resolve component 后又要求 ignored layer 带 owner；用一个
  组件配置隐式覆盖其他组件；因为同属一个模型就量化全部 linear。
- 验收：至少覆盖“只量化一个组件、其他组件保持 BF16”的真实构造与加载，逐层断言
  命中/排除集合，并验证 meta-device parameter 不会被提前 move。FLUX.2 的具体边界见
  [FLUX.2 规则](../../models/flux2/rules.md)，component-relative 变体见
  [MiniMax H3 规则](../../models/minimax-h3/rules.md)；新增 quantization×offload 组合需给兼容矩阵，
  未验证 quantizer fail-closed，并核对 dtype/shape/stride。 ^[PR #5136] ^[PR #5737]
  ^[PR #6279]
  对 AutoRound MXFP4，构造 Wan config 后用 runtime `WanTransformer3DModel` 配置量化层，断言
  packed mapping identity、`blocks.*` 的 MXFP4 method dispatch 与范围外 non-quantized control；
  再以 XPU B60 的 Wan2.1 离线 T2V smoke 验证成功响应、5×256×256 帧形状和非零帧方差。
  这只证明 PR #5544 的离线 Wan2.1/XPU case；PR body 提到的 FLUX.1-dev 示例及任何 online/
  serving/backend 兼容性均未由合入 diff 的测试覆盖，不得扩展为支持声明。^[PR #5544]

## DIFF-2d — Artifact identity 只信任已验证的不可变来源

- 触发：新增或修改 host-weight artifact、warm restore、source identity、layout/dtype policy。
- 强制：共享 identity、restore 和 model ABI 保持 representation-neutral，dtype/layout 只属于
  具体 policy/producer；只有同时验证 source kind、snapshot revision、repo topology 和 blob
  位置的内容寻址仓库，才可用 blob 名代替内容哈希，其他本地文件和 symlink 必须按内容定身份。
- 禁止：因 symlink 目标名看似 40/64 位十六进制就假设不可变；把 `bf16`、具体 layout 或首个
  producer 名写进共享 identity/restorer API；用进程内 inode/mtime guard 代替跨启动身份校验。
- 强制：node-local canonical-source digest cache 只能是 metadata-validated 的哈希工作复用；路径、
  inode、size、timestamp、symlink target 或 cache-record checksum 任一不符即重算，cache I/O/coordination
  失败也必须直接哈希 canonical source。它不改变 identity 内容、artifact selection 或 fallback policy。
- 验收：第二种 synthetic representation 复用共享 identity/restorer；任意本地十六进制命名
  symlink 在同大小内容被替换后产生不同 identity；合法 Hub snapshot→blob 拓扑仍走受控快捷路径。
  ^[PR #6445]

## DIFF-2e — distributed layerwise offload 只能选择一个一致的权重分片合同

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

## DIFF-2p — HSDP/FSDP2 必须同时识别 legacy 与 online FP8 linear method

- 触发：修改 diffusion HSDP/FSDP2 参数准备、online FP8 quantization method 或非连续权重布局处理。
- 强制：同时识别 `Fp8LinearMethod` 与 `Fp8PerTensorOnlineLinearMethod`；当 FP8 权重是转置形成的非连续 view 时，先将底层 `(out, in)` row-major storage 替换为 contiguous weight 供 FSDP2 接受，再让 kernel 的 `_get_layer_params` 返回对应转置 view，且同一 kernel 只 patch 一次。
- 禁止：只检查 legacy `Fp8LinearMethod`、把非连续 transpose view 直接交给 `fully_shard`，或因新版 online method 已被识别就宣称所有 FP8 method 和布局均兼容。
- 验收：legacy 与 `Fp8PerTensorOnlineLinearMethod` 都覆盖 regression test，断言重写层数、weight contiguous、`(out, in)` shape，以及 kernel 返回的转置 view shape/stride；另按 HSDP/FSDP 规则执行真实 `fully_shard` 验证。^[PR #5677]

## DIFF-2q — LTX checkpoint profile 必须贯穿 revision 与 transformer 子目录

- 触发：新增 LTX checkpoint/version profile、Hub `revision`、Full/Distilled transformer 配置或组件加载路径。
- 强制：显式 `model_version` 优先于结构启发式；`revision` 必须贯穿 metadata detection、prefetch、tokenizer、全部组件、transformer config/weight source、scheduler 和 post-process sample-rate；LTX-2.5 Full/SFT 使用 `transformer_full`，distilled 与旧版本使用 `transformer`，并在缺少 Gemma4 时提示 `transformers>=5.10.1,<5.15`。
- 禁止：按路径名识别版本；只给 config lookup 传 revision 而让权重加载回到 HEAD；用 `transformer/config.json` 解释 Full checkpoint；把 transient metadata/Hub 异常静默降级为 LTX-2 并宣称 profile 已确定。
- 验收：固定 revision 的 converted/official split 链路逐项断言所有 loader 调用和输出 metadata；用两个 transformer config marker 验证 Full 子目录选择，覆盖 local/HF、legacy/distilled/Full profile 及缺失 encoder 版本错误。^[PR #6070]

## DIFF-2s — 在线量化加载与 layerwise offload 必须保留物理权重布局

- 触发：修改在线/runtime quantization 与 layerwise offload、DLO 权重加载、非连续 FP8 权重 flatten/repoint 或加载后处理流程。\n- 强制：在线量化层必须在消费完对应 checkpoint weight 后才可流式移回 CPU，并跳过已完成层的重复 `process_weights_after_loading`；继续加载其他模型权重前释放可复用的量化缓存。对非连续权重按物理 storage 顺序打包，记录 `shape`、`stride` 和实际 storage span，并在普通 layerwise、DLO prefetch 与 resident replay 中用 `torch.as_strided` 重建；runtime-created FP8 与 DLO 组合必须使用 no-AllGather 路径。\n- 禁止：对转置 Cutlass FP8 weight 使用逻辑 `.flatten()` 后再 `.view(shape)`，丢失物理布局；为调用幂等处理而把已量化 CPU 层重新搬回 accelerator；把 runtime-created FP8 宣称支持 sharded DLO AllGather。\n- 验收：CPU/mock 测试验证普通 layerwise、DLO prefetch 和 resident replay 的值与 stride 均保持，覆盖不同 storage span、streaming 顺序、已处理层跳过与缓存释放；online FP8 + DLO AllGather 必须 fail fast，no-AllGather 路径须完成加载并通过对应输出/资源 smoke。^[PR #5910]

相关执行流见 [Diffusion architecture](architecture.md)；component lifecycle 见 [component lifecycle 规则](rules-component-lifecycle.md)。

## DIFF-2t — DLO AllGather 只允许已验证的 per-tensor online FP8 布局

- 触发：修改 DLO+AllGather 与在线量化的兼容门禁、普通 loader fallback，或 FP8 权重/scale 的分片重建。
- 强制：仅允许 `Fp8PerTensorOnlineLinearMethod` 进入 DLO+AllGather；由于 direct checkpoint mmap 不能生成运行时量化布局，必须先由普通 loader 完成 FP8 权重和 scale，再交给 DLO 按 dtype 分片，并按记录的 shape、stride 重建转置 Cutlass 权重。每个 rank 启动时可能暂存完整 FP8 模型，运行时才保留 DLO shard。
- 禁止：把该 allowlist 扩展到未经验证的在线量化方法；绕过普通 loader 直接 mmap 在线量化权重；丢失非连续权重的物理 stride；将 transient 完整模型 host memory 峰值描述为运行时常驻开销。此前 DIFF-2s 对所有 runtime-created FP8 的 AllGather 禁止由本规则收窄覆盖。
- 验收：loader 测试必须证明 allowlist 分支确实执行、普通 loader 在 DLO 前完成权重与 scale 处理，并对未验证 method fail fast；DLO 测试必须验证 FP8 weight/scale 的 dtype、值、shape 和转置 stride 重建。另覆盖 no-AllGather 路径及至少一次真实多 rank AllGather smoke；声明质量或性能 parity 仍需固定模型、硬件和 exact workload 的独立证据。^[PR #6279]

## DIFF-2u — diffusion 并行状态必须保持单一拓扑所有权并原子清理

- 触发：修改 diffusion `parallel_state`、HSDP/FSDP2 `DeviceMesh`、SP/CFG/PP group、VAE patch parallel 或并行状态初始化与销毁。
- 强制：`RankGenerator` 只表达真实正交的 TP/SP/PP/CFG/DP 轴；HSDP 不得作为额外轴，FSDP2 `DeviceMesh` 独占 replicate/shard 进程组；VAE tile parallel 直接从 WORLD 选 rank。初始化前验证 distributed 已启动且状态为空，组创建失败时必须清理本次已创建的 diffusion 与 vLLM 组；销毁时同时清空 vLLM `_PP` 等引用。
- 禁止：重新创建冗余 `_DIT` 或 `_FS` 组；把 HSDP shard 当作 `RankGenerator` 的乘法维度；让 HSDP 继续依赖已移除的 fully-shard accessor；清理后保留已销毁的 pipeline group 或允许残留部分状态阻塞下一次初始化。
- 验收：覆盖 HSDP standalone、HSDP+SP/CFG、VAE WORLD group、mesh 维度与实际 WORLD 不一致、初始化中途异常、重复初始化和销毁后重初始化；断言失败后无残留组，vLLM `_PP` 被置空，MiniMax H3 的 VAE/pipeline caller 使用 `get_world_group().device_group`，并以真实多 rank smoke 验证 DeviceMesh 与 collective 拓扑。^[PR #5531]

## DIFF-2v — SANA-WM Stage-1 checkpoint 必须保持标准 Diffusers 布局

- 触发：新增或修改 SANA-WM Stage-1 的 checkpoint resolution、Diffusers component source、HF download allow-pattern、transformer config/weight loading，或尝试直接接入 NVLabs 原始发布布局。
- 强制：运行时只消费离线转换的标准 Diffusers 树：`model_index.json` 必须解析为 `SanaWmPipeline`，并同时提供 `transformer/config.json`、`transformer/diffusion_pytorch_model.safetensors`、`vae/config.json` 和 `vae/diffusion_pytorch_model.safetensors`；从 transformer config 构造 `SanaWmConfig`，Stage-1 download pattern 只包含这组必要文件，refiner 不进入该路径。
- 禁止：用运行时 YAML parser、原始 NVLabs key remap、layout sniff 或宽泛下载模式弥补不兼容的 checkpoint；把命名为 `SanaWmTwoStagesPipeline` 的旧两阶段 repo 当作当前 Stage-1 registry 自动发现成功，或静默跳过缺文件、未知/重复/shape 不符权重。
- 验收：local path 与 HF snapshot 都验证上述文件、`model_index.json` class 和 transformer config 读取；weight loader 对 unknown/duplicate/shape mismatch fail fast 并由 strict coverage 检查 expected keys；Stage-1 smoke 证明不下载/初始化 refiner，旧 layout 只能在显式且兼容的 class override 下运行。^[PR #4061]

## DIFF-2y — Diffusers component index 必须是唯一的 shard manifest

- 触发：修改 Diffusers component 的 safetensors index resolution、Hub/cache download、subfolder
  path、`allow_patterns` 或本地 checkpoint discovery。
- 强制：没有显式 `allow_patterns_overrides` 时，先在 local path 或配置的 Hub cache/remote
  解析 component-local index；保留 `subfolder`、`revision`、`cache_dir` 和 offline
  `local_files_only` 语义。唯一 index 的非空 `weight_map` 是唯一权威 shard manifest：只下载并加载
  去重、稳定排序后的其中文件，且任何缺失 shard 都失败。没有 index 时，必须拒绝同一 shard
  family 出现冲突的 `of-N` totals。
- 禁止：因离线模式跳过已缓存 index、重复拼接 subfolder、用宽泛 glob 混入 snapshot 的陈旧
  shard，或让目录枚举顺序决定 loader 行为。显式 override 是最高优先级选择，不能被 index
  悄然改写。
- 验收：覆盖 local、online 与 offline-cache index resolution，断言 revision/cache/subfolder
  透传、只选择 manifest files 且缺文件失败；再覆盖显式 override、无 index 的冲突 shard
  totals 拒绝，以及顺序无关的 manifest selection。^[PR #6234]

## DIFF-2z — final-layout HWR 只能接入 eligible no-AllGather DLO

- 触发：修改 Diffusers loader 的 host-weight runtime selection、final-layout producer/restorer、
  `HostWeightPlan`，或 DLO loader/backend handoff。
- 强制：在 import、source preparation、identity/store construction 和 observer event 之前完成
  mode/DLO/no-AllGather eligibility gate；disabled、DLO-disabled 和 AllGather 保持既有
  checkpoint-mmap 或 ordinary-loader 路径且零 HWR interaction。eligible warm hit 必须跳过
  ordinary DiT materialization，plan/commit 后把 exact final-layout tensors 作为 rank-local DLO
  source；preferred miss 才 canonical load 并 post-load publish，required 对 miss 或
  incompatible artifact fail startup，不能借 producer bootstrap。
- 强制：eligible warm HWR hit 的 registered transport 只在 `pin_cpu_memory` 开启时尝试，先对完整
  page-aligned mapped ranges 做 read-only capability 与可选 per-worker budget preflight；成功后直接从
  immutable final-layout mmap copy 到既有 HBM buffers，且不分配 private staging。unsupported、budget
  exceeded 或已完整 rollback 的 registration failure 必须回到既有两槽 bounded staging；AllGather、
  checkpoint mmap 和全部 zero-interaction gates 不得尝试 registration。该路径不减少 H2D payload，
  也不是 GPU 直接访问 host memory。
- 禁止：把 preferred 当成对 identity/configuration/compatibility error 的宽泛 fallback；让
  HWR warm restore 重走 ordinary DiT loader、checkpoint mmap 或 byte-changing finalization；把
  no-AllGather 的 rank-local staging 扩展成跨 rank collective 或 generic HWR support。
- 验收：覆盖所有 zero-interaction gates、preferred hit/miss、required miss、mixed/dedicated
  source rejection、warm path zero ordinary DiT materialization，以及 shared finalization 前后
  restored tensor byte/backing-pointer equality；验证 checkpoint mmap control path 不变。另覆盖 registration
  capability/budget/pin-memory gates、partial registration rollback、direct/staged transfer parity、没有
  staging allocation 的成功路径，以及 teardown 前 unregister。^[PR #6486] ^[PR #6591]
