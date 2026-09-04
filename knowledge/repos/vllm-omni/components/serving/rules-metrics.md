---
title: "Serving metrics 生命周期规则"
created: 2026-09-05
updated: 2026-09-05
type: rule
tags: [vllm-omni, components, serving]
sources: ["PR #3576", "PR #4755", "PR #6549", vllm_omni/engine/async_omni_engine.py, vllm_omni/engine/orchestrator.py, vllm_omni/entrypoints/async_omni.py, vllm_omni/entrypoints/omni_base.py, tests/metrics/test_prometheus.py]
confidence: high
---

# Serving metrics 生命周期规则

## SERV-2a — 指标节流和 gauge 按 scheduler/stage/replica owner 隔离

- 触发：orchestrator 聚合多 stage/replica stats，或新增全局 throttle/gauge。
- 强制：节流状态按实际 producer owner 隔离；request 状态 cleanup 后再计算 waiting 等 gauge。
- 禁止：用一个全局时间戳让先上报的 replica 抑制其他 replica；在 pop/cleanup 前发布最终 gauge。
- 验收：同一窗口内两个 replica 都能上报；单请求完成并清理后 waiting=0。^[PR #3576]

## SERV-2b — collector 重建只保护本项目 family

- 触发：同进程重建 engine、注册 Prometheus collectors 或调整 unregister 行为。
- 强制：只保护需要跨实例保留的 `vllm:omni_*` family，并保留 upstream collector 的正常 unregister/cleanup。
- 禁止：把 upstream unregister 整体置空，导致重复 timeseries 注册。
- 验收：同进程连续创建/销毁两次 engine，无 duplicate-timeseries 错误且 Omni family 仍可采集。^[PR #3576]

## SERV-2c — stage metrics 只能在 result message 首次消费时累计

- 触发：修改 `OmniBase` 的 result message 去重、`accumulate_diffusion_metrics`、`on_stage_metrics` 或重试/流式结果处理。
- 强制：以每个请求的 `msg_id = id(result)` consumed 集合作为唯一门禁；仅在消息首次未消费时累计 diffusion metrics、处理 stage metrics，完成两项操作后再记录该消息已消费。
- 禁止：在轮询重试、重复回调或消息标记后再次累计同一 result；把同一消息误当作新的 denoising step，或绕过现有 consumed 生命周期清理。
- 验收：同一 result 重复处理只产生一次累计，两个 distinct result 各自产生一次；覆盖异常、重试与请求清理，确认 consumed 状态不会导致重复累计或遗留。^[PR #4755]

## SERV-2f — pipeline gauge 必须把 engine 内 scheduler queue 从 running 移到 waiting

- 触发：修改 `vllm_omni:num_requests_running` / `vllm_omni:num_requests_waiting`、orchestrator 的 stage/replica scheduler snapshot，或 `OmniBase` 的 request arrival、result/finalization、cleanup 发布点。
- 强制：`AsyncOmniEngine` 与 `Orchestrator` 共享 `_engines_waiting_counter`；每次更新或移除非负的 `(stage_id, replica_id)` waiting snapshot 后，orchestrator 将其和同步进该 counter。前端只能经 `_publish_request_gauges(total)` 发布：`dispatched` 取 `_running_counter`（缺失时取 `total`），`engine_waiting` clamp 到 `[0, dispatched]`，`running = dispatched - engine_waiting`，`waiting = max(0, total - dispatched) + engine_waiting`。请求到达、stage result（包括 finalization 的 `total - 1` race 语义）和 cleanup 后都必须刷新，因此 cleanup 后的总数会覆盖尚未 pop 时的临时发布。
- 禁止：把 orchestrator 已 dispatch、但仍在 stage scheduler queue 的请求报作 running；分散复制公式；让负值、过期/竞态 snapshot 或 engine waiting 大于 dispatched 产生负 gauge；在 final request 仍在 `request_states` 时丢掉既有 `total - 1` 防止 waiting 卡为 1 的语义。
- 限制：该实现求的是各 `(stage, replica)` 最新 waiting snapshot 的**和**，并不按 request ID 去重；代码和 PR #6549 的 3-dispatched/2-queued 测试只证明单一 queue 的拆分，未证明同一 pipeline request 不会同时落在多个 snapshot。因此该值是受 clamp 保护的 scheduler-queue occupancy，不应声称是精确的全局唯一请求数。PR #6549 唯一 review thread 仅确认 `engines_` 名称用于区分 frontend 与 engine waiting，未处理该 cardinality 问题。
- 验收：用真实 Prometheus scrape 覆盖 3 个已 dispatch、其中 2 个 engine scheduler waiting，精确断言 running=1、waiting=2；同时覆盖 arrival、普通/最终 stage result、cleanup、replica removal 和 snapshot 的负值/超 dispatched 值，确认既有 finalization race 语义不变。^[PR #6549]
