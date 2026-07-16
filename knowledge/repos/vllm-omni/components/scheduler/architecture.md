---
title: "Scheduler 共享架构"
created: 2026-07-16
updated: 2026-07-16
type: architecture
tags: [vllm-omni, components, scheduler]
sources: [docs/design/module/ar_module.md, vllm_omni/core/sched/omni_ar_scheduler.py, vllm_omni/core/sched/omni_scheduling_coordinator.py, vllm_omni/core/prefix_cache.py, vllm_omni/worker/gpu_ar_model_runner.py]
---

# Scheduler 共享架构

以下事实在 `main @ 5c390096` 复核；官方叙述见
`docs/design/module/ar_module.md`（含继承 classDiagram 与请求流转 flowchart）。

## 继承链（对 vLLM 的扩展方式）

- `OmniARScheduler(OmniSchedulerMixin, VLLMScheduler)` —— `vllm_omni/core/sched/omni_ar_scheduler.py:50`。
  `schedule()` 调 `super().schedule()` 后，把 base `NewRequestData` 重包成
  `OmniNewRequestData`，附上 `prompt_embeds` 与 `additional_information`（跨 stage
  载荷）；`update_from_output()` 保持 vLLM 原语义。异步变体
  `OmniARAsyncScheduler(OmniARScheduler, AsyncVLLMScheduler)`（:928）。
- `OmniGenerationScheduler(OmniSchedulerMixin, VLLMScheduler)`
  （`omni_generation_scheduler.py:42`）—— 非 AR/单步架构（Conv/LSTM、code2wav 等）的
  快路径：`schedule()` 一次性为请求分配全部输入 token（预算不足回退默认调度）；
  `update_from_output()` 单步后直接置 `FINISHED_STOPPED` 并 `_free_request`。
- `OmniSchedulerMixin`（`omni_scheduler_mixin.py:40`）承载两者共享的 omni 调度行为。

## 跨 stage KV transfer（调度面）

`KVCacheTransferData`（`omni_ar_scheduler.py:40`）是 AR scheduler 携带的跨 stage KV
迁移合同；调度器决定"何时可发/何时已就绪"，实际搬运由
[Distributed 组件](../distributed/_index.md)的 connector/KV-transfer 管理面执行。
真实案例（只链接不复制）：
[HunyuanImage3 KV reuse 事故](../../models/hunyuan-image3/incidents/2026-05-13-kv-reuse-orchestrator.md)
中 `omni_ar_scheduler.py` 的 kv_ready 发射与 `_mark_request_for_kv_transfer` 是根因链的一环。

## chunk / full-payload 输入等待

`OmniSchedulingCoordinator`（`omni_scheduling_coordinator.py`）管理
`WAITING_FOR_CHUNK` / `WAITING_FOR_INPUT` 状态转换，判定依据是
`OmniConnectorOutput` 的就绪信号——协调器**不直接**调用 connector 的 put/get
（数据面在 runner 的 `OmniConnectorModelRunnerMixin`，见
[Model Executor](../model-executor/architecture.md)）。模块 docstring 声明它取代了旧
`OmniChunkTransferAdapter` 的调度侧职责。

## Omni tensor prefix cache

`OmniTensorPrefixCache`（`core/prefix_cache.py:33`，含 `_PendingAsyncWrite` 异步写）
缓存逐 token 张量（如 thinker 的 `hidden_states.layer_N`），prefix 命中时只执行后缀
token，前缀行从缓存重建后拼入跨 stage payload。消费端合同：
`vllm_omni/worker/gpu_ar_model_runner.py:603` 读取模型的
`requires_full_prefix_cached_hidden_states`（默认 True；`qwen3_tts_talker.py:311`、
`higgs_audio_v3_talker.py:236` 显式声明 False）。该机制的失败模式与硬规则见
[rules](rules.md) 的 `SCHED-1a`。

## 与 orchestrator 的边界

调度器只负责单 stage 内的请求生命周期与跨 stage 载荷的调度面；逻辑请求在
stage 间的推进、路由与转发属于 `engine/orchestrator.py`
（[Serving](../serving/architecture.md)）。诊断跨 stage 问题时先分清
"调度面（这里）/数据面（distributed）/编排面（serving）"再下钻。

源码会变化，具体类名和行号在改代码前必须以目标仓库当前版本为准。
