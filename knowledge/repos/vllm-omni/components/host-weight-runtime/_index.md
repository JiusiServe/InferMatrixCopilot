---
title: "Host Weight Runtime"
created: 2026-08-23
updated: 2026-09-04
type: index
tags: [vllm-omni, components]
sources: ["PR #6419", "PR #6486", "PR #6591", vllm_omni/host_weight_runtime/]
confidence: high
---

# Host Weight Runtime

- 源码入口：`vllm_omni/host_weight_runtime/`。
- 主要职责：跨模型共享的 immutable host artifact、lease、filesystem store、typed outcome
  和 restore transaction；transport 可在 lease 生命周期内注册 immutable mapping，但具体 diffusion
  producer、identity adapter 与 DLO selection 仍归 Diffusion owner。

## 什么时候查这里

- 修改 host-weight store、lease/lock、deny/quarantine、locality、fallback 或 restore transaction。
- 具体 diffusion layout/source identity 同时读取 [Diffusion DIFF-2d](../diffusion/rules-checkpoint-loading.md)。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| typed failure、lease/store concurrency、single-take carrier、restore transaction | [rules](rules.md) |
