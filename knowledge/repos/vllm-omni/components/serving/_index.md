---
title: "Serving"
created: 2026-07-10
updated: 2026-09-05
type: index
tags: [vllm-omni, components, serving]
sources: []
---

# Serving

- 主要源码入口：`vllm_omni/entrypoints/`（cli、openai、openpi 及 omni/async_omni 入口）和 `vllm_omni/engine/`（orchestrator、stage engine core、stage pool/runtime、output processor）
- 源码校验：以上路径均已在 `main @ 58cb8de6` 验证存在
- 主要职责：用户入口、请求解析、在线服务和 engine 边界

## 什么时候查这里

- CLI、HTTP、OpenAI-compatible API 或 offline/online 请求行为不一致。
- 参数在入口处丢失、默认值改变，或请求没有进入预期 engine 路径。

## 不放什么

- 模型内部 attention、checkpoint 或 diffusion 算法问题。
- 通用 API 设计方法；这些放 `general/review/`。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 理解入口到 engine 的边界 | [architecture](architecture.md) |
| 根据 PR 描述直达 request contract、stage sampling constraints、streaming format、artifact readiness、factory lifecycle 或 metrics 的规则组与第一批源码 | [rules 与代码地图](rules.md) |
| Prometheus family、pipeline waiting/running gauge、stage/replica snapshot 或 collector lifecycle | [metrics 生命周期规则](rules-metrics.md) |
| upstream launcher shutdown、renderer warmup 与多 replica compile-cache 隔离 | [upstream 兼容规则](rules-upstream-compat.md) |
| stage/replica 死亡、request-local failure、readiness/liveness 或驱逐后 cleanup | [fault-isolation rules](rules-fault-isolation.md) |
| batched chat frontend fan-out、choice cardinality、whole-batch error/cancellation | [batch chat rules](rules-batch-chat.md) |
| engine startup/shutdown、stage lifecycle、acknowledged abort 的 shutdown race、full-duplex、CFG companion，或 opt-in event-driven orchestration / reader-poller reconcile / final-output drain | [engine 生命周期规则](rules-engine-lifecycle.md) |
| duplex stage-keyed segment state、跨 stage boundary/metadata 隔离 | [duplex 编排规则](rules-duplex-orchestration.md) |
| acknowledged abort 的 RPC ACK、queue/router shutdown race、cancellation cleanup 或 backpressure/timeout 保持 | [acknowledged abort 生命周期规则](rules-abort-lifecycle.md) |
| assembled FastAPI route 覆盖、method/path ownership 或 request-body forwarding | [app assembly 规则](rules-app-assembly.md) |
| stage config→EngineArgs projection、explicit `devices`、TP/local-DP/PP、replica layout 或 worker 创建前的 layout guard | [stage 启动与设备布局规则](rules-stage-startup.md) |
| 公开请求字段的校验、来源冲突、alias/extras 归一与 consumer view | [请求输入合同](rules-request-input.md) |
