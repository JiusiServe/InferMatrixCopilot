---
title: "SeedVR2"
created: 2026-10-06
updated: 2026-10-06
type: index
tags: [vllm-omni, models, diffusion]
sources: ["PR #8102"]
confidence: high
---

# SeedVR2

本 owner 对应 `diffusion/models/seedvr2/` 的 restoration pipeline、admission 与
model-specific long-video route hook。

| 遇到什么 | 查看哪里 |
|---|---|
| restoration clip budget、长视频动态窗口、时序拼接、作业取消与文件生命周期 | [SeedVR2 规则](rules.md) |

共享模型加载与并行执行查 [Diffusion owner](../../components/diffusion/_index.md)；
公共 HTTP 装配查 [Serving owner](../../components/serving/_index.md)。
