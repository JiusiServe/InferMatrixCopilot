---
title: "vLLM-Omni 代码审查"
created: 2026-07-10
updated: 2026-07-31
type: index
tags: [vllm-omni, review]
sources: []
---

# vLLM-Omni 代码审查

默认从 PR title/body 直接进入 component/model owner；changed files 只校验范围。本目录
只放 vLLM-Omni 特有的审查方法，不再承担 owner 导航。

| 具体问题 | 查看哪里 |
|---|---|
| PR 描述如何路由精确 owner/model 代码地图 | [maintainer pattern routing](guides/maintainer-pattern-routing.md) |
| 模型适配是否漏掉必要链路 | [model adaptation guardrails](guides/model-adaptation-guardrails.md) |
| 模型验证是否证明语义正确 | [model validation](guides/model-validation.md) |
| 维护或浏览本目录 | [guides index](guides/_index.md) |
