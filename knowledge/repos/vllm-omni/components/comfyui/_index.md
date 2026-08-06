---
title: "ComfyUI vLLM-Omni"
created: 2026-08-06
updated: 2026-08-06
type: index
tags: [vllm-omni, components, serving]
sources: [apps/ComfyUI-vLLM-Omni/, tests/e2e/features/comfyui/, "PR #5756"]
confidence: high
---

# ComfyUI vLLM-Omni

- 源码入口：`apps/ComfyUI-vLLM-Omni/` 的 nodes、API client、types 和 example workflows。
- 源码校验：app 与 `tests/e2e/features/comfyui/` 已在 `v0.26.0 @ a4ea67a2` 验证存在。
- 主要职责：把 ComfyUI video-generation 节点输入校验并编译为 vLLM-Omni 的 T2VA、
  FL2VA 或 Ref2VA multipart 请求；服务端 endpoint 本身归 [Serving](../serving/_index.md)。

## 什么时候查这里

- 修改 ComfyUI 节点输入、reference 组合、mode 选择、multipart 字段或 client 请求。
- 用 [MiniMax H3](../../models/minimax-h3/_index.md) 验证 T2VA/FL2VA/Ref2VA workflow。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| frame/reference 互斥、mode 路由、multipart 字段 | [rules](rules.md) |

## 不放什么

- 通用 OpenAI-compatible request normalization 或 endpoint policy；这些属于 Serving。
- MiniMax H3 pipeline 内部的 packing、量化和 denoise 行为；这些属于模型 owner。
