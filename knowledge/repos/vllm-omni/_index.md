# vLLM-Omni

- 上游仓库：`vllm-project/vllm-omni`
- 适用范围：vLLM-Omni 的开发、测试、文档、模型、性能和远端验证

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
| 查看配置和开发入口 | [dev](dev/_index.md) | 开发和配置说明 |
| 处理分支、PR 和公开证据 | [git](git/_index.md) | 仓库专有 Git/PR 规则 |
| 跑 benchmark、profiling 或查历史结果 | [benchmark](benchmark/_index.md) | 性能入口 |
| 在远端验证仓库改动 | [remote](remote/_index.md) | 仓库专有远端策略 |
| 查看共享代码模块 | [components](components/_index.md) | diffusion、model-executor、serving |
| 查看支持模型 | [models](models/_index.md) | 模型架构与经验 |
