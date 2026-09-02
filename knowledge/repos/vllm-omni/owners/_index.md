---
title: "vLLM-Omni 负责人"
created: 2026-08-11
updated: 2026-09-02
type: index
tags: [vllm-omni, models]
sources: [.github/CODEOWNERS, docs/community/governance.md]
---

# vLLM-Omni 负责人

## 什么时候查这里

- 需要确认关键模型、模块或工作主题由谁负责，找到对应 owner。
- 想在 review、debug 或 benchmark 时把问题路由到正确的人。

## 不放什么

- 模型代码入口、registry key 和别名；这些放
  [`models/catalog.md`](../models/catalog.md)。
- 单个模型的实现与运行细节；这些放 `models/<模型>/`。
- 上游完整 path owner 或 committer 人员快照；人员会变动，路径审查负责人以目标 pin 的
  `.github/CODEOWNERS` 为准，committer 身份与职责以 `docs/community/governance.md` 为准。
  本目录只保留确有独立维护价值的模型路由，不把两份权威清单复制成易过期表格。

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| 按 changed path 找 review owner | 上游 `.github/CODEOWNERS` | 权威且随 pin 变化；按 GitHub CODEOWNERS pattern 匹配，不从本地人员表推断 |
| 确认 committer 身份与公开职责 | 上游 `docs/community/governance.md` | governance roster 是角色权威来源，不等同于每条 path 的 required reviewer |
| 关键模型与 Owner 清单 | [model_owner](model_owner.md) | 模型 → 负责人对照表 |
