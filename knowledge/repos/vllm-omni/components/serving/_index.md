---
title: "Serving"
created: 2026-07-10
updated: 2026-09-03
type: index
tags: [vllm-omni, components, serving]
sources: []
---

# Serving

- 主要源码入口：`vllm_omni/entrypoints/`（cli、openai、openpi 及 omni/async_omni 入口）和 `vllm_omni/engine/`（orchestrator、stage engine core、stage pool/runtime、output processor）
- 源码校验：以上路径均已在 `main @ 596c16a5` 验证存在
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
| 根据 PR 描述直达 request contract、streaming format、artifact readiness、factory lifecycle 或 metrics 的规则组与第一批源码 | [rules 与代码地图](rules.md) |
| upstream launcher shutdown、renderer warmup 与多 replica compile-cache 隔离 | [upstream 兼容规则](rules-upstream-compat.md) |
| stage/replica 死亡、request-local failure、readiness/liveness 或驱逐后 cleanup | [fault-isolation rules](rules-fault-isolation.md) |
| batched chat frontend fan-out、choice cardinality、whole-batch error/cancellation | [batch chat rules](rules-batch-chat.md) |
| engine startup/shutdown 顺序、stage 生命周期、full-duplex 与 CFG companion | [engine 生命周期规则](rules-engine-lifecycle.md) |
