---
title: "Scheduler（AR/生成请求调度）"
created: 2026-07-16
updated: 2026-09-02
type: index
tags: [vllm-omni, components, scheduler]
sources: [vllm_omni/core/sched/omni_ar_scheduler.py, vllm_omni/core/sched/omni_generation_scheduler.py, vllm_omni/core/sched/omni_scheduler_mixin.py, vllm_omni/core/sched/output.py, vllm_omni/core/prefix_cache.py, docs/design/module/ar_runtime.md, docs/design/module/archive/ar_module.md]
---

# Scheduler（AR/生成请求调度）

- 源码入口：`vllm_omni/core/sched/`（`omni_ar_scheduler.py`、`omni_generation_scheduler.py`、
  `omni_scheduler_mixin.py`、`omni_scheduling_coordinator.py`）和 `vllm_omni/core/prefix_cache.py`
- 源码校验：以上路径与下列类均已在 `main @ 53b60bd9` 验证存在：`OmniARScheduler`（:73）、
  `OmniARAsyncScheduler`（:815）、`OmniGenerationScheduler`（:29）、
  `OmniSchedulerMixin`（:64）、`OmniTensorPrefixCache`（prefix_cache.py:33）
- 官方 draft source map：`docs/design/module/ar_runtime.md`；旧继承关系、请求流转图只在
  `docs/design/module/archive/ar_module.md` 保留，须对当前代码复核。
- 测试入口：`tests/core/`
- 主要职责：AR/生成 stage 的请求调度（继承 vLLM Scheduler）、跨 stage KV transfer 的调度面、
  chunk/full-payload 输入等待状态机、omni tensor prefix cache

## 什么时候查这里

- 调查请求调度、waiting/running 状态转换、`WAITING_FOR_CHUNK`/`WAITING_FOR_INPUT`。
- 排查跨 stage KV transfer 的调度侧（transfer criteria、request lifecycle、kv_ready）；
  serialized `KVCacheTransferData` 本体属于 [Distributed](../distributed/_index.md)。
- 排查 `OmniTensorPrefixCache` 引起的跨 stage payload 截断或缓存 miss。

## 不放什么

- engine 编排（`engine/orchestrator.py`、stage pool/runtime）属于 [Serving](../serving/_index.md)。
- diffusion 的噪声调度/采样 scheduler（`vllm_omni/diffusion/sched/`）属于 [Diffusion](../diffusion/_index.md)。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 理解调度器继承链、KV transfer 与 prefix cache 语义 | [architecture](architecture.md) |
| 按 PR 描述直达 prefix cache、token budget、upstream 接口或 side-stream 首批源码 | [rules / Direct 代码快速入口](rules.md#direct-代码快速入口) |
