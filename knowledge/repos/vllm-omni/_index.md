---
title: "vLLM-Omni"
created: 2026-07-10
updated: 2026-07-29
type: index
tags: [vllm-omni]
sources: []
---

# vLLM-Omni

- 上游仓库：`vllm-project/vllm-omni`
- 常用分支：默认分支 `main`；对齐 upstream vLLM 的重构分支 `dev/vllm-align`
- 适用范围：vLLM-Omni 的开发、测试、文档、模型、性能和远端验证
- 组件源码映射需在使用前按目标仓库当前 `main` 重新验证

## 什么时候查这里

- 当前 Git 仓库或用户明确目标是 vLLM-Omni。

## 不放什么

- 跨仓库通用的方法。
- Jianghan 或其他仓库的规则。

## 当前入口

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| 开始任何 vLLM-Omni 修改、测试、远端或发布任务 | [硬门禁](rules.md) | 仅适用于 vLLM-Omni 的仓库规则 |
| 审查模型适配和仓库专有改动 | [review](review/_index.md) | vLLM-Omni 审查规则 |
| 查看 CI 规则和测试配置 | [ci](ci/_index.md) | vLLM-Omni CI |
| 查看文档和 RFC 状态 | [docs](docs/_index.md) | 仓库文档入口 |
| 调查仓库专有 bug、crash 或行为异常 | [debug](debug/_index.md) | 完成通用调试后的仓库二次路由 |
| 查看配置入口、字段归属和构造链路 | [Configuration 规则](components/configuration/rules.md) | 直接进入共享配置 owner 规则；owner 不明时才看组件职责地图 |
| 处理分支、PR 和公开证据 | [git](git/_index.md) | 仓库专有 Git/PR 规则 |
| 跑 benchmark、profiling 或查历史结果 | [benchmark](benchmark/_index.md) | 性能入口 |
| 在远端验证仓库改动 | [remote](remote/_index.md) | 仓库专有远端策略 |
| 对齐 upstream vLLM（rebase、API 漂移、波次） | [rebase](rebase/_index.md) | 上游对齐工作流与漂移登记 |
| 查看共享代码模块 | [components](components/_index.md) | configuration、diffusion、distributed、model-executor、scheduler、serving |
| 查看支持模型 | [models](models/_index.md) | 模型架构与经验 |
