---
title: "vLLM-Omni 入口"
created: 2026-07-10
updated: 2026-09-02
type: index
tags: [vllm-omni]
sources: []
---

# vLLM-Omni

上游：`vllm-project/vllm-omni`。开始任何任务先遵守
[仓库硬规则](rules.md)。

## Review 最短路径

PR title/body 先选择 owner；changed files 只校验实际范围。Direct 已返回精确
`quick_map` 时，不再读取本页、组件总表或模型总表。

| PR 声明目标 | 直接 owner |
|---|---|
| PipelineConfig、YAML、registry、default、endpoint policy | [configuration rules](components/configuration/rules.md) |
| HTTP/OpenAI request、response、endpoint、engine lifecycle | [serving rules](components/serving/rules.md) |
| checkpoint、tokenizer、processor、stage input/handoff | [model-executor rules](components/model-executor/rules.md) |
| diffusion pipeline、denoise、VAE/DiT、图像生成 | [diffusion rules](components/diffusion/rules.md) |
| host-weight artifact、lease、filesystem store、restore transaction | [host-weight rules](components/host-weight-runtime/rules.md) |
| Buildkite、硬件 lane、CI guard、xdist/shared fixture | [CI rules](ci/rules.md) |
| connector、collective、跨 stage 通信 | [distributed](components/distributed/_index.md) |
| queue、token budget、prefix cache、调度 | [scheduler rules](components/scheduler/rules.md) |
| 明确模型名或 registry key | 直接查看 [models 目录](models/_index.md) |

owner 仍不明确时才看 [components 职责表](components/_index.md)；模型别名不确定时才查
[`models/catalog.md`](models/catalog.md)。

## 工作主题

| 任务 | 入口 |
|---|---|
| PR 审查专项 | [review](review/_index.md) |
| CI 和测试配置 | [ci](ci/_index.md) |
| 文档和 RFC | [docs](docs/_index.md) |
| bug 和行为异常 | [debug](debug/_index.md) |
| Git、PR、rebase | [git](git/_index.md)、[upstream rebase](rebase/_index.md) |
| benchmark / profiling | [benchmark](benchmark/_index.md) |
| ComfyUI、示例 app 和客户端适配 | [tooling](tooling/_index.md) |
| 远端验证 | [remote](remote/_index.md) |
| 关键模型与负责人 | [owners](owners/_index.md) |
