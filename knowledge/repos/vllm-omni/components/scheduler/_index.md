---
title: "Scheduler（AR/生成请求调度）"
created: 2026-07-16
updated: 2026-07-16
type: index
tags: [vllm-omni, components, scheduler]
sources: [vllm_omni/core/sched/omni_ar_scheduler.py, vllm_omni/core/prefix_cache.py, docs/design/module/ar_module.md]
---

# Scheduler（AR/生成请求调度）

- 源码入口：`vllm_omni/core/sched/`（`omni_ar_scheduler.py`、`omni_generation_scheduler.py`、
  `omni_scheduler_mixin.py`、`omni_scheduling_coordinator.py`）和 `vllm_omni/core/prefix_cache.py`
- 源码校验：以上路径与下列类均已在 `main @ 5c390096` 验证存在：`OmniARScheduler`（:50）、
  `OmniARAsyncScheduler`（:928）、`KVCacheTransferData`（:40）、`OmniGenerationScheduler`（:42）、
  `OmniSchedulerMixin`（:40）、`OmniTensorPrefixCache`（prefix_cache.py:33）
- 官方设计文档：`docs/design/module/ar_module.md`（继承关系、请求流转图）
- 测试入口：`tests/core/`
- 主要职责：AR/生成 stage 的请求调度（继承 vLLM Scheduler）、跨 stage KV transfer 的调度面、
  chunk/full-payload 输入等待状态机、omni tensor prefix cache

## 什么时候查这里

- 调查请求调度、waiting/running 状态转换、`WAITING_FOR_CHUNK`/`WAITING_FOR_INPUT`。
- 排查跨 stage KV transfer 的调度侧（`KVCacheTransferData`、kv_ready）。
- 排查 `OmniTensorPrefixCache` 引起的跨 stage payload 截断或缓存 miss。

## 不放什么

- engine 编排（`engine/orchestrator.py`、stage pool/runtime）属于 [Serving](../serving/_index.md)。
- diffusion 的噪声调度/采样 scheduler（`vllm_omni/diffusion/sched/`）属于 [Diffusion](../diffusion/_index.md)。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 理解调度器继承链、KV transfer 与 prefix cache 语义 | [architecture](architecture.md) |
| 修改 prefix cache 关键 key、小 token 预算或对齐 upstream 调度接口 | [rules](rules.md) |
