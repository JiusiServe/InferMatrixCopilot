---
title: "Kandinsky 6"
created: 2026-10-06
updated: 2026-10-06
type: index
tags: [vllm-omni, models, diffusion]
sources: ["PR #8537"]
confidence: high
---

# Kandinsky 6

本 owner 对应 `vllm_omni/diffusion/models/kandinsky6/` 与
`Kandinsky6TI2VAPipeline`；不能继承其他视频模型的请求、checkpoint 或缓存假设。

| 遇到什么 | 查看哪里 |
|---|---|
| Hub 分目录权重、音视频输出、参考图、请求缓存与 VAE patch parallel | [模型规则](rules.md) |

共享执行与输出协议查 [Diffusion owner](../../components/diffusion/_index.md)；
公开 HTTP 请求与帧数校验查 [Serving owner](../../components/serving/_index.md)。
