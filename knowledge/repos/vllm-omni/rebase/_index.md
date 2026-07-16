---
title: "Rebase（对齐 upstream vLLM）"
created: 2026-07-16
updated: 2026-07-16
type: index
tags: [vllm-omni, rebase]
sources: [".buildkite/rebase-pipeline.yaml", "vllm-omni-rebase-agent@122a9468:agent/config.py"]
---

# Rebase（对齐 upstream vLLM）

把 vllm-omni 对齐到新版 upstream vLLM 的周期性工作：专用分支 `dev/vllm-align`、
专用管线 `.buildkite/rebase-pipeline.yaml`（`main @ 5c390096` 验证存在）、专职
自动化（rebase-agent 仓库——运营系统在那里，本主题只沉淀领域知识）。

## 什么时候查这里

- 做/排查 upstream 对齐（rebase、模块波次、API 漂移适配、对齐分支 CI）。

## 不放什么

- 单组件产品 bug → `components/<模块>/`；CI 结构与环境坑 → `ci/`；
  分支/PR 机制 → `git/`。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 工作流：分支、波次、模块→upstream 映射、失败路由 | [workflow](workflow.md) |
| 上游 API 漂移模式（serving/调度/测试侧） | [upstream API drift](upstream-api-drift.md) |
| 上游 API 漂移模式（权重/显存/运行时侧） | [drift：加载与运行时](upstream-api-drift-loading.md) |
