---
title: "vLLM-Omni 文档"
created: 2026-07-10
updated: 2026-09-02
type: index
tags: [vllm-omni, docs]
sources: ["PR #5715", README.md, docs/configuration/README.md, docs/getting_started/installation/README.md, docs/getting_started/installation/gpu/cuda.inc.md, docs/getting_started/installation/npu/npu.inc.md]
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

## 发布与安装边界

- stable release 从 0.14 起跟随 upstream vLLM 的偶数 minor cadence；版本兼容按 matching
  major/minor 判断。`vLLM-Omni 0.26.x` 要求 `vLLM 0.26.x`，稳定 0.26.0 文档固定
  vLLM `v0.26.0`，configuration 链接也必须指向 0.26 文档，不能拿旧版本示例混用。
- CUDA 文档的 0.26 base image 是 `vllm/vllm-openai:v0.26.0`；NPU source install 另有
  平台专属 tuple：vLLM `v0.26.0` + vLLM-Ascend `releases/v0.26.0rc`。Review 明确没有把
  NPU 更新扩散到 MUSA/quickstart，因此各平台 pin 必须回到自己的安装页核对。
- README 将 full-duplex realtime serving 标为 experimental；公开说明、验收和支持承诺
  不能把它写成 stable feature。
