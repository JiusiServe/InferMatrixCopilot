---
title: "vLLM-Omni 审查指南"
created: 2026-07-10
updated: 2026-07-30
type: index
tags: [vllm-omni, review]
sources: []
---

# vLLM-Omni 审查指南

| 遇到什么 | 查看哪里 |
|---|---|
| 按 PR 描述先路由到精确 owner/model 代码地图，再用 changed files 校验范围 | [PR intent maintainer routing](maintainer-pattern-routing.md) |
| 审查模型适配 PR 的完整性 | [model adaptation guardrails](model-adaptation-guardrails.md) |
| Strict 审查注入的触发式检查单（streaming 生命周期、平台默认值影响面、依赖下界、CI marker 选择、测试有效性） | [strict review checklist](strict-review-checklist.md) |
| 判断新模型验证是否证明语义正确 | [model validation](model-validation.md) |
