---
title: "afd-plugin"
created: 2026-08-05
updated: 2026-08-05
type: index
tags: [afd-plugin]
sources: ["vllm-project/afd-plugin:AGENTS.md", "vllm-project/afd-plugin:README.md", "vllm-project/afd-plugin:pyproject.toml", "vllm-project/afd-plugin:.github/workflows/cpu-only-ci.yml"]
---

# afd-plugin

- 上游仓库：`vllm-project/afd-plugin`
- 默认分支：`main`
- 适用范围：AFD 插件的兼容 patch、配置校验、connector/distributed、worker/runner、GPU/NPU native backend、单测和硬件 E2E review
- 仓库自己的 `AGENTS.md`、`CLAUDE.md`、`.agents/skills/run-e2e/SKILL.md`、CI 和脚本保持权威；这里仅保存 InferMatrixCopilot 的最小路由规则

## 什么时候查这里

- 当前 Git 仓库、GitHub URL 或 PR 目标是 `vllm-project/afd-plugin`。
- 需要判断 AFD PR 的 changed files 应读哪些仓库专属 review 规则。

## 不放什么

- 不放 vLLM-Omni 的模型、远端、benchmark 或 rebase 经验。
- 不复制 AFD 仓库完整 README、AGENTS 或 E2E skill；运行细节以目标仓库当前文件为准。
- 不记录本机 checkout 路径、硬件账号、模型 cache 或凭据。

## 当前入口

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| 开始任何 afd-plugin review、issue answer 或仓库初始化 | [硬门禁](rules.md) | AFD 仓库级默认规则 |
| 需要跨仓库 review 基础方法 | [general review](../../general/review/_index.md) | 通用审查入口 |

