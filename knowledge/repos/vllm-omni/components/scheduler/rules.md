---
title: "Scheduler 规则"
created: 2026-07-16
updated: 2026-09-04
type: rule
tags: [vllm-omni, components, scheduler]
sources: ["PR #5957", "PR #5976", tests/core/sched/test_omni_ar_scheduler_stale_drain.py, "vllm-omni-rebase-agent@122a9468:agent/skills/fix-talker-truncated-prefill-prefix-cache-key-cap/SKILL.md", "vllm-omni-rebase-agent@122a9468:agent/skills/gpu-hang-low-max-num-batched-tokens/SKILL.md", vllm_omni/worker/gpu_ar_model_runner.py, vllm_omni/core/prefix_cache.py, vllm_omni/utils/mm_outputs.py, vllm_omni/core/sched/omni_ar_scheduler.py, vllm_omni/core/sched/omni_generation_scheduler.py, vllm_omni/core/sched/omni_scheduler_mixin.py, vllm_omni/core/sched/omni_scheduling_coordinator.py, vllm_omni/core/sched/output.py, tests/core/test_prefix_cache.py, tests/core/test_prefix_cache_async_write.py, tests/core/sched/test_omni_scheduler_mixin_shared.py, tests/utils/test_mm_outputs.py, tests/entrypoints/test_omni_new_request_data.py, "PR #4106", "PR #5310", "PR #5461", "PR #4795", "PR #5842", "PR #6033", "PR #6360"]
---

# Scheduler 规则

只有 `SCHED-数字字母` 是可审计规则 ID。运营 runbook 以 rebase-agent 仓库为准，
本页是知识树沉淀快照（2026-07-16，agent @122a9468；skills 工作树含未提交遥测更新，
快照以工作树为准）。

## Direct 代码快速入口

PR 描述先命中下表，再打开对应规则组和首批源码；changed files 强制校验并补齐是否还
跨到 Distributed、Serving 或 Model Executor，描述与 diff 冲突时以后者为准。

| PR 描述信号 | 规则组 | 第一批源码 |
|---|---|---|
| prefix cache、truncated prefill、mm key、deferred/passthrough payload | SCHED-1a/1b | `core/prefix_cache.py::OmniTensorPrefixCache`；`utils/mm_outputs.py::{build_mm_cpu,to_payload_element}`；`worker/gpu_ar_model_runner.py::_deferred_prefix_cache_mm_keys` |
| `max_num_batched_tokens`、prefill throttle、低预算 GPU hang | SCHED-2a | `core/sched/omni_ar_scheduler.py::OmniARScheduler.schedule`；`core/sched/omni_generation_scheduler.py::OmniGenerationScheduler.schedule`；触发它的 deploy/test 配置 |
| vLLM bump、scheduler rebase、KV connector stats | SCHED-3a | 两个 scheduler 的 `schedule` / `update_from_output` 与 live upstream `vllm/v1/core/sched/` |
| side-stream D2H、pinned host tensor、源 buffer 复用 | SCHED-4a/4b | `worker/gpu_ar_model_runner.py::_copy_tensor_payload_to_cpu`、`_get_or_create_omni_payload_copy_stream`；`core/prefix_cache.py` 的 async copy 路径 |
| sampled-token logprobs、spec decode trim、request-local output error | SCHED-5a | `core/sched/omni_ar_scheduler.py::_slice_sampled_logprobs`、`update_from_output` |
| stateful async chunk、full-payload input、KV cleanup | SCHED-5b/5c | `core/sched/omni_generation_scheduler.py`、`omni_scheduling_coordinator.py`、`omni_ar_scheduler.py::_free_request` |

若描述只写模型症状，先从模型 owner 找到 payload producer/consumer；只有实际断点落在调度、
prefix cache 或 copy lifetime 时才把 Scheduler 加为 owner。

## SCHED-1a — prefix cache 的关键 key 必须显式声明，禁止抬 cap 或关缓存

skill 元数据：`fix-talker-truncated-prefill-prefix-cache-key-cap`，
modules=[worker_runner, model_executor]，status=active，run_count=54，2026-06-10 创建 / 07-11 最后使用。

- 症状：`tests/e2e/online_serving/test_qwen3_omni.py::test_mix_to_text_audio_001[default]`
  失败；stage-1（`StageEngineCoreProc_stage1_replica0`）死于
  `RuntimeError: The size of tensor a (6) must match the size of tensor b (9) at non-singleton dimension 0`，
  位置 `vllm_omni/model_executor/models/qwen3_omni/qwen3_omni.py::_get_talker_assistant_parts`
  （`input_embeds = assistant_text_hidden + assistant_codec_hidden`）。因 OmniServer fixture
  是 session 级、stage-1 已死，同文件其余用例随即全部 `EngineDeadError`，watchdog 杀
  pytest（rc=143）。shape 解码：`assistant_codec_hidden` 恒为 9 行；
  `assistant_text_hidden`==6（0 + 4 pad + 1 BOS + 1 zero-fill）意味着
  `thinker_embed[im_start_index:segment_end_index]` 为**空**——stage-0 发来的
  `embed.prefill` 远短于 prompt。
- 诊断（跨 stage 截断通用配方）：
  1. 在 stage-0 日志 `grep "Skipping mm prefix cache key"` —— 命中
     `hidden_states.layer_0` / `hidden_states.layer_24`（embeddings 层与
     accept_hidden_layer 层）即适用本规则。
  2. payload 遥测 `grep "_send_single_request"`：健康时 mix 测试所有请求 ~21–22 MB；
     损坏时首个请求 ~21 MB（cache miss），随后同 prompt 请求骤降 ~1.4 MB
     （prefix 命中、只剩后缀行）。
  3. 先归因再调试：与**上一次通过的 run** 同一测试日志对比
     （`rebase_logs/runs/<prev-run>/tests/00_omni_qwen3-omni_test.log`）；核对 vLLM 版本行
     `Initializing a V1 LLM engine (vX.Y...+g<sha>)` 是否一致——一致则回归在 vllm-omni
     树（合入的 origin/main 或模块 agent 提交）而**不是** vLLM bump；
     `git log -S"<告警文本>" --all` 快速定位引入提交。
- 根因链（首见于 vllm-omni #3689 / `57227dc7`）：测试用 `--stage-overrides` 强制打开
  stage-0/1 的 prefix caching；qwen3-omni thinker 把逐 token
  `hidden_states.layer_0`（embeddings）与 `hidden_states.layer_{accept_hidden_layer}`
  打进 thinker→talker payload；prefix 命中时只执行后缀 token，前缀行必须从
  `OmniTensorPrefixCache` 重建；#3689 加了逐 key 512 MiB cap
  （`_MAX_MM_CACHE_BYTES_PER_KEY`，为 qwen3-tts 类模型设的 OOM 防线）——大 KV cache
  下（如 L20X 682,896 token → 2048 维 bf16 每 key 2667.6 MiB）两个 layer key 被
  **静默丢弃**，prefix 命中的请求带着截断的 `embed.prefill` 在 talker 侧爆 shape。
- 修法（skill 的 4 处小改，模型声明豁免，沿既有
  `requires_full_prefix_cached_hidden_states` / `deferred_prefix_cache_mm_keys` 模式）：
  1. `vllm_omni/core/prefix_cache.py` —— `OmniTensorPrefixCache.__init__` 增
     `required_mm_cache_keys: set[str] | None`；`maybe_init_missing_mm_cache_keys`
     中该集合内的 key 绕过 cap（改打 `warning_once` 报实际 MiB，而不是跳过）。
  2. `vllm_omni/worker/gpu_model_runner.py` —— `initialize_metadata_builders` 构造
     cache 时传 `required_mm_cache_keys=set(getattr(getattr(self, "model", None),
     "required_prefix_cache_mm_keys", ()) or ())`。
  3. `qwen3_omni.py` thinker 分支 `__init__`：声明
     `self.required_prefix_cache_mm_keys = {"hidden_states.layer_0"}`，再取
     `accept_layer = getattr(talker_config, "accept_hidden_layer", None)`，仅当 `accept_layer is not None` 时加
     `f"hidden_states.layer_{int(accept_layer)}"`。
  4. `tests/core/test_prefix_cache.py` —— 单测把 cap monkeypatch 到 1 字节，断言
     required key 仍被缓存、可选超大 key 被跳过。
  - key 命名：`flatten_payload`（`vllm_omni/data_entry_keys.py`）把
    `{"hidden_states": {"layers": {N: t}}}` 展平成 `"hidden_states.layer_N"`，
    **声明展平后的名字**。
  - main @5c390096 现状：布尔合同 `requires_full_prefix_cached_hidden_states`
    （`gpu_ar_model_runner.py:603`，qwen3_tts/higgs_v3 talker 显式 False）与集合
    `deferred_prefix_cache_mm_keys`（:692/:730，模型声明如
    `qwen3_tts_talker.py:321` `{"codes.audio"}`）已在；skill 的 `required_*` 命名
    在该提交尚未出现——按 skill 的 Watch Out，该修复属 vllm-omni upstream，需提/跟
    upstream PR。
- 验证：`python -m pytest tests/core/test_prefix_cache.py -q` 全过；
  `CUDA_VISIBLE_DEVICES=0,1 python -m pytest -s -v
  tests/e2e/online_serving/test_qwen3_omni.py -m 'core_model' --run-level 'core_model'`
  → 4 passed；stage-0 日志出现 `... exceeds the 512.0 MiB cap ... but is required for
  downstream-stage correctness; allocating it on CPU anyway`，且 `_send_single_request`
  对**所有** mix 请求都 ~21 MB（不只是第一个）。
- 禁止：全局抬高/删除逐 key cap（那是别的模型的 OOM 防线）；在测试或 deploy 配置里
  关 prefix caching 掩盖正确性 bug；在 talker 侧容忍短 embed（payload 早已错了）。
- Watch out：下游 stage 消费**全 prompt 逐 token** mm 输出的模型，在 stage-0 可能开
  prefix caching 时都必须声明 required keys —— Qwen2.5-omni 今天不用 layer-capture
  机制，机制变了要复查；绕过 cap 的缓存住在主机内存（本例每 key ~2.6 GiB）——TB 级内存的 CI 主机
  可承受，小内存主机要标注。^[SK-fix-talker-truncated-prefill-prefix-cache-key-cap]

## SCHED-1b — prefix-cache passthrough 必须保留逐请求边界与载荷语义

- 触发：修改 `build_mm_cpu`、`to_payload_element`、prefix-cache merge/deferred payload，
  或 runner 对 combined multimodal output 的拆包。
- 强制：token-aligned tensor（首维等于本步 scheduled token 总数）按每个请求的
  `start:end` 切片；非 token-aligned tensor 给每个请求完整独立 clone；prefix-cache
  merge 中的 list（如 `codes.ref`）保持整表并逐请求 clone，直到 runner 用**原 batch
  index** `_unwrap_lists`。D2H 后每个嵌套 tensor leaf 必须在 CPU、detached、contiguous，
  并保持 dtype/shape/value；dict/list 与非 tensor leaf 的结构和值不变。
- 生命周期：abort/discard 必须删除 staged chunks，之后的 commit 是 no-op；同 req-id
  重用从空状态开始，不能混入旧 chunk。
- 禁止：把所有 passthrough tensor 一律按 token 切；在 merge 阶段提前按 downstream
  subset index 拆 list；用 float staging buffer 改写 int metadata；把本规则解释为后续 W2
  优化已经实现——`f24a6165` 只增加当前行为的 characterization tests。
- 验收：mixed hit/miss + 不等 scheduled length 同时覆盖 1-D/2-D token-aligned、多个
  非对齐 shape、per-request tensor list 和 int32/int8 metadata；修改一请求结果不影响
  其他请求或源值。另测 discard→late commit、discard→req-id reuse。^[PR #5310]

## SCHED-2a — 极小 max_num_batched_tokens 与并发 prefill 会挂死 GPU

skill 元数据：`gpu-hang-low-max-num-batched-tokens`，
modules=[online_serving, worker_runner]，status=active，run_count=38，2026-06-18 创建 / 07-11 最后使用。

- 触发：启动约 2s 后 GPU hang，NVIDIA watchdog 杀进程，日志只有
  `Received cancellation signal, interrupting`（无 Python 栈）；条件为并发请求 ≥5 且
  `max_num_batched_tokens < 256`（如 64）。
- 机制：upstream 调度器新增 `throttle_prefills` 后与极小 token 预算交互不良。
- 修法：小批路径测试用适中小值——`tests/e2e/online_serving/test_qwen3_omni_expansion.py`
  的 `get_batch_token_config`，两个 stage 一起改：
  `updates={"stages": {0: {"max_num_batched_tokens": 512}, 1: {"max_num_batched_tokens": 512}}}`，
  并注释"64 过小会挂 GPU；调度器再变需重估"。
- 验证边界：完整验证需  2×H100；skill 落盘时无卡，实际验证为 import 检查（已确认无语法错误）——这是
  **纯测试配置改动**，不碰产品代码。
- 禁止：把挂死当模型/驱动 bug 直接重试；用超大预算掩盖小批路径不测。
  ^[SK-gpu-hang-low-max-num-batched-tokens]

## SCHED-3a — rebase 前必须对照 live upstream 调度接口

- 触发：对齐 upstream vLLM 版本（rebase/分支合并）涉及 `vllm/v1/core/sched/`。
- 强制：对照 live upstream 源码核对本组件继承的接口（`schedule`/
  `update_from_output`/异步调度、kv-connector 统计等挂点）是否有签名、时序或语义
  变化，逐条登记后再改代码；曾发生 `kv_connector_stats` 提取时序在上游更新后错位、
  需要移到 `_update_from_kv_xfer_finished` 之后的案例（omni_ar_scheduler.py 与
  omni_generation_scheduler.py 都要改）。base `NewRequestData` 重包必须按 live dataclass
  字段无损复制后再附 Omni payload；共享 mixin 只集中机械 lifecycle，AR/generation 的
  admission、cached-payload 和 synthetic-abort 等差异用调用参数保留为显式本地策略。
- 禁止：只跑单测绿灯就认定调度语义未变；不能用缺少真实 mixin helper 的
  `SimpleNamespace`/`object.__new__` stub 绕过共享调用链，也不能手列一份会随 upstream
  schema 漂移的 base output/request 字段。
- 验收：枚举 live `NewRequestData.__dataclass_fields__` 逐字段断言 identity/equality，覆盖
  Omni fast path 不重建与 generation fallback；AR/generation 分别验证 pending-input、queue
  restore、finished-set/abort policy。直接调用 scheduler 方法的轻量 stub 必须继承 mixin 或
  显式绑定本次方法真实依赖，使断言确实到达目标分支。 ^[PR #5461]

## SCHED-4a — side-stream 复制必须拥有源 buffer 的完成期

- 触发：prefix-cache 异步写、side-stream D2H、persistent GPU buffer 或下一 step 会重写
  的 `slot_mapping`/hidden/mm tensor。
- 强制：源 tensor 在 copy event 完成前保持有效且不可被重写；使用显式 stream ordering、
  retain/`record_stream` 或消费屏障。drain/early-return 也必须完成或转移生命周期责任。
  单 pending-write 流水线中 event 未 ready 时 drain 必须不触碰 cache；ready 后恰好消费
  一次；调度第 N+1 次 write 前必须先消费第 N 次，不能覆盖 pending state。
- 禁止：仅同步目标 CPU tensor，却允许下一 step 复用源 GPU buffer；这会得到合法 shape
  但错误行内容。
- 验收：连续两 step 写入不同 sentinel，在人为延迟 side stream 下证明第一轮 CPU 结果
  不被第二轮覆盖；强制 event query false→true，断言 0→1→0 次 drain，并验证未显式
  drain 时下一次 schedule 仍先落盘上一轮。 ^[PR #4106] ^[PR #5310]

## SCHED-4b — pinned CPU 分配必须先判断 CUDA 能力

- 触发：CPU-only 测试、CUDA 不可用环境或异步 copy 可降级路径。
- 强制：根据 CUDA availability 选择 pinned/non-pinned allocation，再决定是否启用异步。
- 禁止：先无条件构造 pinned tensor，失败后才关闭 async path。
- 验收：CPU-only 环境能构造并走同步 fallback；CUDA 环境仍使用 pinned + async，两个
  分支产生相同内容。 ^[PR #4106]

## SCHED-5a — sampled-token logprobs 先校验再修改 request

- 触发：AR scheduler 消费 model-runner sampled tokens 和 `num_logprobs`，尤其是
  spec-decode 或 batched output slicing。
- 强制：按 request 切出 logprob rows，校验二维 shape、行数、第一 token 对齐和有限值；
  失败只将当前 request 置为 `FINISHED_ERROR`，不能先 append token 或污染同批 request。
  stop/EOS 截断后再按最终 emitted token 数重新 slice。
- 禁止：`logprobs` 缺失时静默跳过；用 truthiness 判断合法空输出；把 runner 的错位
  row 当作用户请求成功。
- 验收：覆盖 missing、wrong shape/count、token misalignment、NaN、spec-decode trim
  和同批健康 request 继续完成。

## SCHED-5b — stateful async-chunk request 必须占用调度容量

- 触发：模型在等待下一 chunk 时保留 runner state，或 full-payload connector 负责把下
  一段重新送入 generation stage。
- 强制：`retains_state_across_chunks` 为真时，把 connector 中等待 chunk 的 request
  计入 `max_num_seqs`；full-payload consumer 在 chunk 到达时重新进入 waiting queue，
  不要被 base scheduler 提前停放。
- 禁止：只按 `running` list 计数导致超额 admission；把 connector-fed chunk 当成 API
  streaming update；仅在 abort 路径释放 receiver。
- 验收：mixed batch 覆盖等待 chunk 的容量上限、full-payload requeue、normal finish
  的 receiver cleanup 和 abort/replica-loss cleanup。

## SCHED-5c — stage-0 final request 的 KV transfer 例外必须显式标记

- 触发：stage-0 的 text/final 输出通常不需要下游 KV，但 CFG companion 或其他终端
  payload 仍需要复用该 cache。
- 强制：用 `omni_force_kv_transfer` 等 request metadata 明确覆盖“final stage=0”的
  shortcut；scheduler、engine 和 companion tracker 使用同一个标记语义。
- 禁止：按 final stage id 静默跳过所有 stage-0 KV；只在 companion 的 producer 设置
  标记而不测试 scheduler 的 transfer decision。
- 验收：普通 stage-0-final request 不传 KV，标记 request 传 KV，且 metadata 在
  `OmniARScheduler._request_omits_kv_transfer_to_next_stage` 中可读回。

## SCHED-5d — CFG companion 必须成对推进，缺失时有限降级并终止等待

- 触发：Audex/扩散 CFG companion、双 waiting queue、不同 chunk 进度或 companion
  abort/split。
- 强制：不完整 pair 暂存并按 parent/companion 对齐进度；完成时一起收敛，缺失或拆分
  的 companion 只能走显式、有界的 fallback，并清理两侧状态。
- 禁止：只推进 parent 让 companion 永久停在 waiting；把缺 companion 当普通 batch
  请求静默放行；用无限等待掩盖 replica loss 或 abort。
- 验收：覆盖完整 pair、不同进度、missing/split、parent abort 和 companion abort，
  断言请求不会挂死、错误归属保持 request-local、队列和 connector state 都释放。

## SCHED-5e — pooling output decoder 必须覆盖两个 scheduler 且失败即为 request error

- 触发：pooling stage 配置 per-stage output decoder，或修改 `OmniARScheduler`、`OmniGenerationScheduler` 的 pooling output 完成路径。
- 强制：两个 scheduler 都经共享 mixin 在 terminal status 处理前调用 decoder；成功时把解码 payload 写入 `EngineCoreOutput`，失败时只将当前 request 置为 `FINISHED_ERROR`、保留错误原因并停止继续调度。
- 禁止：只在 AR scheduler 接 hook；decoder 异常 fail-open 为空成功；先完成请求再解码；把原始 pooler tensor 或错误 request 的 payload 发送给下游。
- 验收：分别覆盖 AR/generation scheduler 的成功、decoder 抛异常、无 decoder 和同批健康 request；断言成功 payload、`FinishReason.ERROR`、request-local 错误归属及无跨请求污染。
^[PR #4795]

## SCHED-5f — async-chunk 等待必须有可配置的截止时间

- 触发：async-chunk 请求进入 `WAITING_FOR_CHUNK`，或部署配置读取 `VLLM_OMNI_INPUT_WAIT_TIMEOUT_S`。
- 强制：统一校验超时值，拒绝负数和非有限值，`0` 仅作为显式禁用并记录 warning；chunk adapter 在请求停等时开始计时、每次收到 chunk 后重置，并由 scheduler 及时结束超时且仍在 `self.requests` 中的请求。
- 禁止：只保护 full-payload 的 `WAITING_FOR_INPUT`；让负数、`nan` 或 `inf` 静默关闭 deadline；按 stream 总生命周期而非 chunk 间 stall 时间计时；对已离开 scheduler 的请求调用 `finish_requests`。
- 验收：覆盖有效值、显式零值、负数和非有限值解析，覆盖 dropped terminal chunk、producer 无响应、chunk 到达后重置、请求完成/abort 清理及同批健康请求继续运行；断言超时请求为 `FINISHED_ERROR`，并确认模块 reload 不污染后续测试。^[PR #6033]

## SCHED-5g — resumable async-chunk 终态清理必须以 live queue 所有权为准

- 触发：resumable async-chunk 请求在一个流式 segment 结束时进入 `FINISHED_STOPPED`，但仍由 `running`、`waiting`、`skipped_waiting` 或 connector 隐藏队列持有，随后 session close、取消或其他路径调用 `finish_requests`。
- 强制：先物化可能被多层消费的 request-id iterator，并在 adapter 清理前快照 `skipped_waiting` 中承担流式等待计数的请求；只对仍有活队列所有权的目标 resumable 终态请求恢复状态，`skipped_waiting` 恢复为 `WAITING_FOR_STREAMING_REQ`，`running`/`waiting` 按实际队列对齐；running purge 必须限定本次 finish 集合，并确保 `_free_request`、coordinator 与 connector 清理恰好执行一次。
- 禁止：把任意已完成请求重新打开；对脱离所有 live queue、可能等待 deferred block free 的终态请求调用释放；全局清空 running 中无关的 resumable segment；重复消费单遍 request-id iterator，或因非流式 skipped 请求错误减少 streaming counter。
- 验收：AR 与 generation scheduler 均覆盖 hidden、`running`、`waiting`、`skipped_waiting`、脱离队列及无关 resumable 请求；断言状态、队列、计数、request map 和 active-stream capacity 正确，首次 finish 恰好释放、第二次无操作，并验证 generator request-id 输入。^[PR #6360]

## SCHED-6a — async discard 的计数单位必须与 stale drain 一致

- 触发：上游 scheduler 改动异步占位、stale output 或 streaming segment replacement。
- 强制：每个 discard site 用 `num_in_flight_tokens`（scheduled-token 单位）累加
  `num_stale_output_tokens`；每个迟到 frame 先按本次 `num_tokens_scheduled` 结算 in-flight 与 stale
  两个同单位 counter，再在 append/emit 前丢弃。placeholder rollback 与 stale drain 分开记账。
- 禁止：用 `num_output_placeholders` 初始化 stale counter；清零 placeholder 后仍让迟到输出进入
  placeholder/computed-token 的正常结果更新；把 scheduler 修复宣称为音频 WER 修复。
- 验收：AR 与 generation 路径覆盖多 token frame、prefill 无 placeholder、连续旧/新 segment，
  断言 stale counter 恰好归零且首个新 segment 输出不被吞；真实质量指标必须另行验证。^[PR #5976]

## 相关

## SCHED-6b — request-end full payload 是显式 admission capability

- 触发：新增或修改只在 request end 消费完整上游 sequence 的 stage。
- 强制：coordinator allowlist 与模型 capability 同步；完成前零传输，完成时只 enqueue 一次完整 sequence，
  consumer 使用 non-async-chunk topology。IndexTTS 2.5 的精确键是
  `("IndexTTS25S2MelDecoder", "indextts2_5_s2mel_decoder")`。
- 禁止：按模型名猜测、扩大到整个家族，或逐 token 重复搬运。
- 验收：allowlisted/non-allowlisted 对照、完成时一次传输、abort 无残留。^[PR #5957]

- 机制与边界见 [architecture](architecture.md)；跨 stage 数据面见
  [Distributed 组件](../distributed/_index.md)。

## SCHED-6c — full-payload allowlist 必须精确绑定最终 consumer 与 async wiring

- 触发：新增 async-chunk processor 或把某个 stage 加入 full-payload input allowlist。
- 强制：allowlist 使用精确的 `(model_arch, stage_key)` consumer 配对；Nemotron 的 `talker -> code2wav` 才能接收完整 code payload，`thinker -> talker` 保持 token-only；sync full-payload builder 与 async-chunk builder 必须分别接入同一真实 code2wav consumer。
- 禁止：按模型家族或 stage index 猜测 full-payload 能力；把 token-only 的 thinker→talker hop 放进 full-payload allowlist；让非 async deploy 逐 token搬运完整 code stack，或让 async 终端 chunk 缺少 finished/empty-terminal 语义。
- 验收：覆盖 allowlisted code2wav 与 non-allowlisted talker 对照，分别验证普通 deploy 的一次 request-end 全 payload、streaming deploy 的累计 chunk/终端 chunk、connector requeue 和 abort cleanup。
^[PR #5842]

