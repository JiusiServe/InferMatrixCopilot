---
title: "Diffusion paged cache 与系统运行时规则"
created: 2026-09-03
updated: 2026-09-04
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #5255", "PR #5344", "PR #5543", "PR #5838", "PR #6094", "PR #6102", "PR #6385", vllm_omni/diffusion/attention/backends/flashinfer_attn.py, vllm_omni/diffusion/attention/backends/ring/ring_kernels.py, vllm_omni/diffusion/attention/parallel/ulysses.py, vllm_omni/diffusion/model_metadata.py, vllm_omni/diffusion/registry.py, vllm_omni/diffusion/worker/diffusion_model_runner.py, "PR #5491", "PR #5194", "vllm_omni/diffusion/data.py", "vllm_omni/diffusion/utils/hf_utils.py"]
confidence: high
---

# Diffusion paged cache 与系统运行时规则

`system-runtime` 审查组的 `DIFF-4a`–`DIFF-4i`。触发条件、覆盖范围和其余审查组见
[Diffusion 共享规则](rules.md) 的 Direct 代码快速入口；上游兼容侧的 `DIFF-4k`–`DIFF-4l`
留在 [upstream 兼容规则](rules-upstream-compat.md)。

## DIFF-4a — 容量预算必须在影响峰值的初始化完成后测量

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

## DIFF-4b — 复用 native 组件仍须审计 caller/adapter 契约

- 触发：diffusion adapter 调用 vLLM 的 cache spec/config/manager、scheduler 或其他版本化 API。
- 强制：按仓库 pin 的精确 vLLM 版本核对 property/method、签名、sentinel、block-size 单位、
  max-length/capacity 前提、返回失败语义和 free/rollback 责任；分别证明 adapter 输入、调用时序、
  输出解释和 native 内部算法。
- 禁止：把“委托给 native vLLM”当作端到端正确性证明；native manager 不负责验证 Omni 在何时
  测量预算、是否漏算其他显存、是否正确传播失败，也不保证 adapter 模拟对象符合真实属性合同。
- 验收：真实 pin 的 contract test 覆盖正常值、边界/sentinel、容量不足、property 访问和清理；
  fake 不能把真实 property 改成同名 method 或跳过 native precondition。 ^[PR #6094]

## DIFF-4c — Feature gate 只限制影响范围，enabled 路径必须独立闭环

- 触发：新增或修改 `dense_legacy`/paged、eager/optimized 或其他默认关闭的 diffusion 路径。
- 强制：分别审计 disabled/default 与 enabled；enabled 至少覆盖单请求、并发/多 rank、低资源、
  partial allocation、执行异常、取消、timeout、shutdown 和重复释放。异常必须到达终端请求或
  engine 信号并唤醒 waiter，所有已分配资源由明确 owner 回收。
- 禁止：用“默认路径有 gate”“dense 未回归”或单请求 smoke 推导新路径正确；也不能让 scheduler/
  busy-loop 异常逃逸后留下永远等待的 stream。
- 验收：path/lifecycle matrix 每行有 production-path 测试或明确 `MISSING_EVIDENCE`；enabled
  关键行缺失时审查只能是 partial，不能输出 clean/no findings。 ^[PR #6094]

## DIFF-4d — 异常清理覆盖每种错误传递形态

- 触发：worker/RPC 在异常后清 traceback、释放 device tensor/cache，或把异常转换成
  reply、rank-status envelope、`DiffusionOutput`。
- 强制：先保存对外所需的字符串化错误，再对 raise、普通错误回复和 collect-status 正常返回
  三条路径逐一执行同一清理；调用方把异常折叠成成功返回形态时仍必须释放原异常引用。
- 禁止：只在最外层 `except` 清理，却让内部状态封装路径正常返回；清理后继续从异常对象读取
  message/traceback；用单一路径 mock 证明所有 RPC mode 都不会保留 device tensor。
- 验收：测试分别覆盖 `collect_rank_status=true` 与抛出/错误回复路径，断言错误文本仍可见、
  `exc.__traceback__ is None`、cache cleanup 被调用，后续健康 RPC 仍成功。 ^[PR #6385]

## DIFF-4e — paged backend 在启动时按平台和逐层能力闭环

- 触发：启用 paged scheduler、增加 diffusion attention backend 或平台 override。
- 强制：启动阶段解析并验证每层实际 backend 与当前平台；走 Omni platform hook，保留
  piecewise/SP 等能力。尚无生产 caller 的模式必须明确告警并文档化。
- 禁止：未知平台继承 GPU 默认；分配 cache 后到首次 dispatch 才失败；静默占用 paged KV
  却继续 dense；直接换用 upstream backend 丢失 Omni 能力。
- 验收：unsupported platform/backend fail-fast；CUDA/NPU 对应 lane 和正式模型 E2E 证明
  resolved backend；mixed-mask piecewise/SP 回归通过。 ^[PR #5543] ^[PR #6102]

## DIFF-4f — paged attention metadata 不从 padding 猜逻辑布局

- 触发：paged adapter 修改 GQA、prefix/current-token packing、LSE layout 或二维特例。
- 强制：显式传递 Q/KV head 数、每请求 prefix/current span 和 layout；保持压缩 GQA 与 packed
  current-token 语义，单 token/单 head 二维输入仍使用同一合同。
- 禁止：从 padding 长度推断逻辑跨度；在 `sequence == heads` 时猜 LSE 维度；fallback 静默换
  backend 或把 KV heads 扩成 Q heads。
- 验收：32Q/8KV、异构 prefix、单 token/单 head、非对称等维 LSE 和 batch compaction 精确
  对照 dense/reference 输出。 ^[PR #5543] ^[PR #6102]

## DIFF-4g — Ring GQA 只在通信后扩展，Hybrid Ulysses 不把 padding 当真 head

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

## DIFF-4h — FlashInfer mixed-dtype plan 必须绑定完整 runtime shape 与 mask 内容

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

## DIFF-4i — 模型能力 metadata 必须跨 architecture 与 pipeline 两个 key space 解析

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

相关执行流见 [Diffusion architecture](architecture.md)；paged attention 的 layout 细节见
[attention 规则](rules-attention.md)。

## DIFF-4o — AR-Diffusion 容量必须覆盖持久状态，分页图输入必须显式

- 触发：AR-Diffusion runner 修改 paged self-attention KV、resident session capacity、scratch/cross-attention reservation、model-owned CUDA state、commit pruning 或 CUDA Graph 输入。
- 强制：按有效 resident capacity 完整计算 `sink + recent window`、单个 in-flight block、scratch、cross-attention 和每 session 的 model-owned state；`gpu_memory_fraction` 只能控制额外 residency，至少一个能装入实际空闲显存的 session 必须先被接纳，并在分配 self-KV 前扣除所有持久 reservation。成功 commit 后立即释放 skipped paged blocks；paged attention 将可变 key/value pool 作为显式可变 graph input。worker-local state 仍须保持 `max_num_seqs=1`，多副本必须先具备 session affinity。
- 禁止：用只覆盖一个 session 的固定 floor 忽略声明 capacity；只为 self-KV 预算而漏算 cross-attention、scratch 或模型自有状态；使用 process-global KV pool registry；让各 TP rank 依据不同的本地 free-memory 计算不同 capacity 后继续 collective；把单次 TP replay 或能启动当作多 session/多 rank 预算正确性的证明。
- 验收：覆盖 LingBot 两个 resident window、DreamZero 声明 capacity 64 的预算封顶、LRU eviction、失败 forward 清理、commit 后 block 回收和显式 graph pool 输入；真实 TP 还要用统一的 min free-memory/all-reduce 或 rank-0 广播验证所有 rank 得到相同 capacity，并分别验证 paged/direct 数值与单副本路由。^[PR #5491]

## DIFF-4p — Scheduler-managed Diffusion KV 必须原子分配并绑定请求生命周期

- 触发：启用 `paged_scheduler`，或修改 Worker KV geometry discovery、显存 profile、Scheduler admission、CFG allocation、`NewRequestData`/DLO RPC envelope 和 request terminal cleanup。
- 强制：模型加载后从每个 Worker 的 cache-enabled attention 生成 rank-local native `FullAttentionSpec`，以最大 per-rank profile batch 测量 KV headroom，再通过 `get_kv_cache_configs()`、`generate_scheduler_kv_cache_config()` 和 `resolve_kv_cache_block_sizes()` 构造 Worker/Scheduler 配置。Scheduler 侧只能以 native `KVCacheManager` 的薄 wrapper 为物理 owner；每个 CFG sequence 按完整首步 `seq_len` 以 `full_sequence_must_fit=True` 分配，先按空池所需 block 总数做 never-fit 检查，并在所有 sequence 成功前保持原子性。生成的 `DiffusionKVMetadata` 必须与请求绑定并随完整 `NewRequestData` envelope 传到 Worker；完成、取消、错误、pop 和 close 都必须释放整组 allocation，preemption 只保留既有 allocation。
- 禁止：引入独立 block pool、KV spec、refcount 或 physical lifecycle；把部分 CFG 分配当作成功；把临时容量不足误报为永久失败，或让 never-fit 请求在 FIFO 头部无限阻塞；在 DLO DP wave 中拆开 request 与对应 metadata，或让 scheduler/busy-loop 异常逃逸而不唤醒请求流。
- 验收：覆盖 dense 默认旁路、rank/spec/memory mismatch、profile 顺序、CFG partial rollback、临时压力返回 `None` 后 FIFO 重试、空池也放不下时只终止该请求、native allocation error、preemption metadata 保留，以及 finish/cancel/error/pop/close 全部释放；DLO 多 rank RPC 必须逐 envelope 保持 request 与 metadata 配对。 ^[PR #6094]

## DIFF-4t — HiDream-O1 checkpoint signature 必须正向门禁

- 触发：diffusion registry、`resolve_model_class_name()`、`OmniDiffusionConfig` enrichment 或 HF checkpoint 自动识别逻辑需要区分 HiDream-O1 与普通 Qwen3-VL。
- 强制：仅当 `config.json` 的 `model_type` 为 `qwen3_vl`，且 `model.safetensors.index.json` 的原始 `weight_map` 含 `model.final_layer2.linear.weight` 或 `final_layer2.linear.weight` 时，才返回 `HiDreamO1ImagePipeline`；`resolve_model_class_name()` 与 config enrichment 必须复用同一正向 signature，registry 同时登记 pipeline 与 post-process。
- 禁止：把任意 `qwen3_vl` 配置归类为 HiDream-O1；给 raw index key 强加 `model.` 前缀；只增加显式 `model_class_name` 映射而让通用 text-to-image/server 自动解析仍落到未注册 architecture；缺失或格式异常的 index 不得误报命中。
- 验收：覆盖 HiDream signature 命中、普通 Qwen3-VL、缺失/错误 `weight_map`、显式类名与 signature 不一致，以及 resolver/enrichment 两条路径；再断言 registry pipeline 和 module-level post-process 均可解析。^[PR #5194]

