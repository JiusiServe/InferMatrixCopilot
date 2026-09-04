---
title: "vLLM-Omni 文档"
created: 2026-07-10
updated: 2026-09-05
type: index
tags: [vllm-omni, docs]
sources: ["PR #5715", "PR #6029", "PR #6858", .claude/skills/readme.md, README.md, docs/configuration/README.md, docs/contributing/README.md, docs/getting_started/installation/README.md, docs/getting_started/installation/gpu/cuda.inc.md, docs/getting_started/installation/npu/npu.inc.md]
---

# vLLM-Omni 文档

## 什么时候查这里

- 编写或核验 vLLM-Omni 文档、RFC 和仓库专有公开说明。

## 不放什么

- 跨仓库通用的文档方法；先看 `general/docs/`。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 判断 RFC 是否仍在进行 | [RFC status](rfcs/_index.md) |
| 找上游官方设计文档与其知识树 owner | [design-doc map](design-doc-map.md) |
| generated example URL/nav、supported-model recipe 与硬件证据 | [generation and support rules](generation-and-support-rules.md) |
| contributor agent workflow、repository skill catalog 与信任边界 | [repository skill rules](repository-skills.md) |

## 发布与安装边界

- stable 0.28 文档将 vLLM-Omni `0.28.x` 与 vLLM `0.28.x` 对齐，configuration/env links 指向
  v0.28；这只是 release-documentation guidance，不能从 README highlights 推出 runtime/model support。
- NPU A2/A3 installation examples 使用 aligned vLLM-Ascend v0.28.0 images；latest-main 安装仍在该
  aligned container 内进行。CUDA nightly `nightly` 是 rolling tag，`nightly-<commit>` 为 reproducible
  commit tag，文档称只保留 newest 14。各 tag/image 的 live availability 仍须发布时核验。^[PR #6858]
- README 将 full-duplex realtime serving 标为 experimental；公开说明、验收和支持承诺
  不能把它写成 stable feature。
