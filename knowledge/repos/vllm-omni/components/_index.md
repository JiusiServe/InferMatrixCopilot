---
title: "vLLM-Omni 组件 owner"
created: 2026-07-10
updated: 2026-08-23
type: index
tags: [vllm-omni, components]
sources: []
---

# 组件 owner

仅在 PR 描述和 Direct 路由都不能确定 owner 时查本页。选中一个主要 owner 后直接进入
其 `rules.md`；只有真实调用链跨边界时才打开第二个 owner。

| Owner | 负责范围 | 直接入口 |
|---|---|---|
| [Configuration](configuration/_index.md) | deploy YAML、PipelineConfig、registry、字段归属、default 和 endpoint policy | [rules](configuration/rules.md) |
| [Serving](serving/_index.md) | 用户请求、OpenAI API、响应、AsyncOmni engine 生命周期 | [rules](serving/rules.md) |
| [Model Executor](model-executor/_index.md) | stage config/input、模型加载、worker、跨 stage 数据桥 | [rules](model-executor/rules.md) |
| [Diffusion](diffusion/_index.md) | diffusion pipeline、denoise、VAE/DiT、并行和 cache | [rules](diffusion/rules.md) |
| [Host Weight Runtime](host-weight-runtime/_index.md) | immutable host artifact、lease、filesystem store、typed outcome 与 restore transaction | [rules](host-weight-runtime/rules.md) |
| Distributed | connector、KV 迁移、collective、跨 stage 通信 | [index](distributed/_index.md) |
| [Scheduler](scheduler/_index.md) | 请求队列、token budget、KV transfer、prefix cache | [rules](scheduler/rules.md) |

需要解释稳定数据流时再进入对应 owner 的 `architecture.md`，不要把 architecture 当成
review 的默认前置阅读。
