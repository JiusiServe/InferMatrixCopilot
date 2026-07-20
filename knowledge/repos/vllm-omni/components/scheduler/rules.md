---
title: "Scheduler 规则"
created: 2026-07-16
updated: 2026-07-20
type: rule
tags: [vllm-omni, components, scheduler]
sources: ["vllm-omni-rebase-agent@122a9468:agent/skills/fix-talker-truncated-prefill-prefix-cache-key-cap/SKILL.md", "vllm-omni-rebase-agent@122a9468:agent/skills/gpu-hang-low-max-num-batched-tokens/SKILL.md", vllm_omni/worker/gpu_ar_model_runner.py, vllm_omni/core/prefix_cache.py, "PR #4106"]
---

# Scheduler 规则

只有 `SCHED-数字字母` 是可审计规则 ID。运营 runbook 以 rebase-agent 仓库为准，
本页是知识树沉淀快照（2026-07-16，agent @122a9468；skills 工作树含未提交遥测更新，
快照以工作树为准）。

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
  omni_generation_scheduler.py 都要改）。
- 禁止：只跑单测绿灯就认定调度语义未变（单测常用 `object.__new__` 绕过真实构造）。

## SCHED-4a — side-stream 复制必须拥有源 buffer 的完成期

- 触发：prefix-cache 异步写、side-stream D2H、persistent GPU buffer 或下一 step 会重写
  的 `slot_mapping`/hidden/mm tensor。
- 强制：源 tensor 在 copy event 完成前保持有效且不可被重写；使用显式 stream ordering、
  retain/`record_stream` 或消费屏障。drain/early-return 也必须完成或转移生命周期责任。
- 禁止：仅同步目标 CPU tensor，却允许下一 step 复用源 GPU buffer；这会得到合法 shape
  但错误行内容。
- 验收：连续两 step 写入不同 sentinel，在人为延迟 side stream 下证明第一轮 CPU 结果
  不被第二轮覆盖。 ^[PR #4106]

## SCHED-4b — pinned CPU 分配必须先判断 CUDA 能力

- 触发：CPU-only 测试、CUDA 不可用环境或异步 copy 可降级路径。
- 强制：根据 CUDA availability 选择 pinned/non-pinned allocation，再决定是否启用异步。
- 禁止：先无条件构造 pinned tensor，失败后才关闭 async path。
- 验收：CPU-only 环境能构造并走同步 fallback；CUDA 环境仍使用 pinned + async，两个
  分支产生相同内容。 ^[PR #4106]

## 相关

- 机制与边界见 [architecture](architecture.md)；跨 stage 数据面见
  [Distributed 组件](../distributed/_index.md)。
