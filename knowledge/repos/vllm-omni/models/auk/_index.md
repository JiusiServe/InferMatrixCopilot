---
title: "Tencent AuK / AuK-Flash"
created: 2026-10-06
updated: 2026-10-06
type: index
tags: [vllm-omni, models, diffusion]
sources: ["PR #7469", "PR #7881", "PR #8300", "PR #8328", "PR #8305"]
confidence: high
---

# Tencent AuK / AuK-Flash

本 owner 对应 `diffusion/models/auk/` 的 DiT/codec 与
`entrypoints/openai/tts_adapters/auk.py` 的 instruction-driven Speech API adapter。

| 遇到什么 | 查看哪里 |
|---|---|
| task shortcut、DiT graph/request context、codec tiling、reference latent cache 或 fused activation | [AuK 规则](rules.md) |

共享执行查 [Diffusion owner](../../components/diffusion/_index.md)；
Speech API 的公共输入与输出查 [Serving owner](../../components/serving/_index.md)。
