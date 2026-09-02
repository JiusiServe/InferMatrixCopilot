---
title: "Diffusion paged KV control plane"
created: 2026-09-02
updated: 2026-09-02
type: rule
tags: [vllm-omni, components, diffusion, scheduler]
sources: ["PR #5541", "PR #5550", vllm_omni/config/omni_config.py, vllm_omni/diffusion/data.py, vllm_omni/diffusion/diffusion_engine.py, vllm_omni/diffusion/diffusion_kv/config.py, vllm_omni/diffusion/diffusion_kv/metadata.py, vllm_omni/diffusion/diffusion_kv/request.py, vllm_omni/diffusion/executor/multiproc_executor.py, vllm_omni/diffusion/models/hunyuan_image3/pipeline_hunyuan_image3.py, vllm_omni/diffusion/models/hunyuan_image3/request_layout.py, vllm_omni/diffusion/request.py, vllm_omni/diffusion/sched/base_scheduler.py, vllm_omni/diffusion/sched/interface.py, vllm_omni/diffusion/worker/diffusion_model_runner.py, vllm_omni/diffusion/worker/diffusion_worker.py, vllm_omni/diffusion/worker/utils.py, tests/config/test_omni_config.py, tests/diffusion/diffusion_kv/test_config.py, tests/diffusion/diffusion_kv/test_metadata.py, tests/diffusion/diffusion_kv/test_request.py, tests/diffusion/diffusion_kv/test_worker_contract.py, tests/diffusion/models/hunyuan_image3/test_diffusion_kv_request.py, tests/diffusion/models/hunyuan_image3/test_hunyuan_image3_step_execution.py, tests/diffusion/test_diffusion_config_propagation.py, tests/diffusion/test_diffusion_engine.py, tests/diffusion/test_diffusion_engine_cleanup.py, tests/diffusion/test_diffusion_model_runner.py, tests/diffusion/test_diffusion_scheduler.py]
---

# Diffusion paged KV control plane

只有 `DIFFKV-数字字母` 是可审计规则 ID。本页描述目标 pin 的**请求控制面合同**；它没有
实现物理 KV cache、block table、slot mapping、paged attention 或跨请求命中。

## DIFFKV-1a — mode 必须显式选择，未实现模式 fail fast

- 触发：增加或修改 `diffusion_kv_mode`、structured/runtime config 投影、KV receive intent 或
  legacy dense KV 字段。
- 强制：`dense_legacy` 保持默认和原行为，只有 `paged_scheduler` 启用预处理与 Scheduler 所有权；
  `omni_kv_config` 是独立 transport 配置，不是 mode 别名。`paged_scheduler` 必须在初始化拒绝
  `need_recv_cache=True`，但仅携带 `kv_sender_info` 不能当成导入意图。
- 禁止：让预留的 `paged_worker_local` 静默退回 dense；在 paged mode 接受 request/sampling 上
  非空 `past_key_values` 或任何 `*_past_key_values`。dense mode 仍保留旧字段兼容。
- 验收：走完整 `VllmOmniConfig.from_pipeline_config()` 与 runtime config 路径，分别覆盖默认、
  paged、unknown、worker-local、receive=true 和 sender-metadata-only，不能只测 enum parser。
  ^[PR #5541]

## DIFFKV-1b — 预处理恰好一次，并在 admission lock 之前完成

- 触发：修改 Engine admission 入口、模型 preprocessor、`prepared_layout` 或 Worker step-state 初始化。
- 强制：streaming、`add_request`、async/sync wait 与 dummy warmup 都只调用一次
  `_prepare_request_for_admission`，再把 prepared request 送入内部 admission；模型预处理必须在
  Engine condition/RPC lock 之前完成。`prepared_layout` 随 Worker payload 进入 step state；泛型字段
  实际是 `Any | None`，Hunyuan consumer 必须用 `get_hunyuan_prepared_layout` 校验具体类型。
- 禁止：某入口漏做或重复 chat template；把 Scheduler-owned KV request 或物理 block ID 放进
  prepared layout。Hunyuan layout 只承载 tokenizer tokens、image geometry、RoPE/positions、masks
  与 scatter indices。
- 验收：所有入口断言 exactly once；prepared/local A/B 覆盖 CFG=1/2、含/不含 reference image，
  比较 tokens、RoPE、mask、scatter index 和 step update。reference-image case 只证明规划等价；
  Worker `prepare_encode()` 调用 helper 时仍设 `allow_cond_image=False` 并拒绝非 dummy image-edit，不能宣称 paged
  image editing 已可执行。^[PR #5541]

## DIFFKV-2a — Scheduler 持有逻辑请求，Worker 不得收到可变管理状态

- 触发：修改逻辑 KV length、CFG row mapping、context 表达、Scheduler admission 或 Worker payload。
- 强制：每个 CFG row 建一个 Scheduler-owned `DiffusionKVRequest`；主序列是
  `[prefix | target | suffix]`，`prefix_len` 可复用，`target_len` 每步重写，`seq_len` 是首步完整
  allocation boundary，并允许 `prefix_len + target_len < seq_len`。Hunyuan 分别从
  `gen_timestep_scatter_index[row,-1]`、生成图+timestep/guidance token 和 `real_pos[row,-1]`
  取得三段长度；prompt/reference image 已在同一 self-attention sequence，所以 `kv_contexts=()`。
- 禁止：把独立 cross/joint context 塞入主 token axis，或把可变 `DiffusionKVRequest` 送给 Worker；
  admission 必须把 tuple 移入 `SchedulerRequestState` 并清空 Worker-bound 字段。
- 验收：CFG=1/2、suffix、reference image 与独立 context 都验证 identity/length/owner。失败路径也要
  原子：目标 `_make_request_state` 在 `_build_sampling_params_key` 前清空原 request，后者抛错时会
  丢失 tuple；修复前必须保留 retry gap，修复时增加失败后重试测试或延后 destructive move。
  ^[PR #5541]

## DIFFKV-2b — 空 hash 只允许 request-local paging，禁止发布 prefix

- 触发：增加 block hashes、native `KVCacheManager` 调用、physical cache spec/config 或 prefix 发布。
- 强制：Hunyuan 当前保持 `block_hashes=[]` 与 `skip_reading_prefix_cache=True`，只允许请求内 page
  allocation；只有模型预处理为每个可缓存完整 block 生成 canonical hash 后，才可条件调用
  `cache_blocks(request, prefix_len)`。物理 geometry 必须以后续 Worker 已加载 attention module
  暴露的 native `KVCacheSpec` 为真源，再经 Engine 配置和 Worker 初始化。
- 禁止：空 hash 无条件发布 prefix，或从静态 HF config 复制 TP heads、dtype、PP layer ownership、
  cache sharing 和 backend tensor layout；当前合同没有跨 request/CFG semantic hit。
- 验收：空 hash case 分配后不发布；完整测试 hash 的 delayed commit 只发布 prefix、不发布 target；
  native manager facade test 不得冒充 Scheduler allocation、BlockTable、slot mapping、paged attention
  或跨请求正确性。^[PR #5541]

## DIFFKV-2c — Worker 只接收请求级 allocation snapshot，不接收 Scheduler 可变状态

- 触发：增加 `DiffusionKVMetadata`、`NewRequestData` 字段，或修改 request/batch/step 的
  Scheduler→Executor→Worker→ModelRunner RPC。snapshot 在 request scope 保存 generation、sequence
  的 prefix/target/full length、可引用的独立 context，以及每个 native cache group 的 block ID；
  多个 CFG sequence 可引用同一个 context，也可引用各自 context。
- 强制：metadata 与已初始化 request 原子放在同一个 new-request envelope，且 envelope ID、实际转发
  的 `req.request_id`、metadata ID 在任何 model work/RPC 前一致。request mode 只在 metadata 存在时
  追加第四个 RPC 位置参数，保持 dense 历史三参数 shape；batch/step 则随完整
  `DiffusionSchedulerOutput` 传输。`prepared_layout` 仍是独立的 model-owned payload，不能从它派生
  block ID。Worker wrapper 也只在非空时向旧 runner 增加 keyword，避免破坏 dense/custom runner。
- 强制：W0 尚无 allocator/installer，因此 `paged_scheduler` 接受 metadata 但不得强制要求；
  `dense_legacy` 必须拒绝 metadata。带 metadata 的多请求 wave 不能走 DLO 的 list-request 快捷 RPC，
  因为该路径没有逐请求 snapshot 参数；应退回逐请求 dispatch。^[PR #5550]
- 禁止：把这些可变 dataclass 当成已验证的安全边界。当前只验证 mode 与顶层 request identity，
  不检查 generation/sequence/block ID 正数、`prefix+target<=seq_len`、精确 sequence/context 集合、
  cache-group 数/顺序、block-table 长度/范围或 null block。上述检查必须由未来 Scheduler producer
  对照 `SchedulerRequestState.diffusion_kv_requests`，再由 Worker installer 对照 rank-local native
  `KVCacheConfig` 与 generation registry，而不是用 DTO 自证正确。
- 验收：request/batch/step 覆盖 metadata 缺省、传播与三方 ID mismatch；dense metadata fail-fast，
  DLO metadata wave 不进入 list-request 分支，legacy positional shape 与 `prepared_layout` identity
  保持。严格 layout/range/generation 测试只能在独立 truth owner 落地后升级为已实现合同。

## 证据边界

- 目标实现只提供 logical request/control-plane contracts、request-scoped Scheduler→Worker metadata
  DTO/RPC 与 native-manager conformance tests；没有 cache manager、physical allocation、Worker
  installer/registry、BlockTable、slot mapping 或 paged attention。metadata 可选且未被消费，内部
  数值字段也未做严格校验，因此不能把“到达 runner”解释为 allocation 可用。
- 目标 Hunyuan E2E 运行 `dense_legacy`，只证明既有 dense path；不能作为 Scheduler-managed paged
  data plane、attention 或 cross-request caching 正确性的证据。
