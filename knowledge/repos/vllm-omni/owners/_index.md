---
title: "vLLM-Omni 负责人"
created: 2026-08-11
updated: 2026-08-11
type: index
tags: [vllm-omni, models]
sources: []
---

# vLLM-Omni 负责人

## 什么时候查这里

- 需要确认关键模型、模块或工作主题由谁负责，找到对应 owner。
- 想在 review、debug 或 benchmark 时把问题路由到正确的人。

## 不放什么

- 模型代码入口、registry key 和别名；这些放
  [`models/catalog.md`](../models/catalog.md)。
- 单个模型的实现与运行细节；这些放 `models/<模型>/`。

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| 关键模型与 Owner 清单 | [model_owner](model_owner.md) | 模型 → 负责人对照表 |
