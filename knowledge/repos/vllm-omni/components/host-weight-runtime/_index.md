---
title: "Host Weight Runtime"
created: 2026-08-23
updated: 2026-08-23
type: index
tags: [vllm-omni, components]
sources: ["PR #6419", vllm_omni/host_weight_runtime/]
confidence: high
---

# Host Weight Runtime

- 源码入口：`vllm_omni/host_weight_runtime/`。
- 主要职责：跨模型共享的 immutable host artifact、lease、filesystem store、typed outcome
  和 restore transaction；具体 diffusion producer/identity adapter 仍归 Diffusion owner。

## 什么时候查这里

- 修改 host-weight store、lease/lock、deny/quarantine、locality、fallback 或 restore transaction。
- 具体 diffusion layout/source identity 同时读取 [Diffusion DIFF-2d](../diffusion/rules.md)。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| typed failure、lease/store concurrency、restore transaction | [rules](rules.md) |
