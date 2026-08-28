---
title: "vLLM-Omni 发布规则"
created: 2026-08-28
updated: 2026-08-28
type: index
tags: [vllm-omni, release]
sources: []
---

# vLLM-Omni 发布规则

## 什么时候查这里

- 准备发版、签收 release 门禁，或核对 CUDA/NPU/DI/需求完成度是否达标。

## 不放什么

- 仓库日常开发硬门禁；这些仍在根目录 [rules.md](../rules.md)。
- 通用测试方法或跨仓库 CI 纪律；这些放 [general/ci](../../../general/ci/_index.md)。
- 具体模型实现细节；这些放 [models](../models/_index.md)。

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| Release 前必须满足的门禁 | [发布规范](release.md) | UT/性能 Guide 与 CUDA/NPU/DI 等硬门槛 |
