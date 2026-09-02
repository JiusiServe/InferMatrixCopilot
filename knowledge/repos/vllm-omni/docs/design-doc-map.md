---
title: "官方设计文档地图（docs/design/**）"
created: 2026-07-16
updated: 2026-09-02
type: guide
tags: [vllm-omni, docs]
sources: [docs/design/index.md, docs/design/architecture_overview.md, docs/design/feature/diffusion_continuous_batching.md, docs/design/feature/omni_async_output_materialization.md, docs/user_guide/diffusion/execution_modes.md]
---

# 官方设计文档地图（docs/design/**）

`main @ 9f978923` 复核。注意：官方 `docs/design/index.md` 只列了子集（Architecture
Overview、4 篇 feature、metrics、3 篇 module）；**完整树比索引大得多**——
`feature/` 下还有 async_chunk、cache_dit、teacache、prefix_caching、7 篇并行策略、
`omni_connectors/` 逐后端 spec 等未入索引的文档，找 spec 时直接 `ls docs/design/feature/`。

| 官方文档 | 一句话 | 知识树 owner |
|---|---|---|
| `architecture_overview.md` | 三类模型拓扑（DiT 主/AR 主/AR+DiT）、OmniRouter/EntryPoints/AR/Diffusion/OmniConnector、E/P/D/G 解耦、CFG companion 流 | [serving](../components/serving/architecture.md) + [distributed](../components/distributed/architecture.md) |
| `module/async_omni_architecture.md` | 五层运行时（API→Engine→Orchestration→Communication→Execution），ZMQ + janus 队列，Qwen3-Omni worked example | [serving](../components/serving/architecture.md)、[qwen-omni](../models/qwen-omni/architecture.md) |
| `module/ar_module.md` | AR 模块继承链与请求流转 | [scheduler](../components/scheduler/architecture.md) + [model-executor](../components/model-executor/architecture.md) |
| `feature/omni_async_output_materialization.md` | AR decode 关键路径外的异步 D2H 与 Omni payload 构造；含 live connector ownership、平台验证范围和同步 fallback | [model-executor](../components/model-executor/_index.md) |
| `module/dit_module.md` | Diffusion 引擎/调度/worker/pipeline/加速组件 | [diffusion](../components/diffusion/architecture.md) |
| `module/entrypoint_module.md` | **stub（"update soon"）——上游文档缺口** | [serving](../components/serving/_index.md) |
| `feature/disaggregated_inference.md` + `omni_connectors/*` | connector 选择矩阵与逐后端 spec | [distributed](../components/distributed/connector-backends.md) |
| `feature/diffusion_continuous_batching.md` + `user_guide/diffusion/execution_modes.md` | 合并后的开发者设计与用户配置入口：request/step 执行、两种 batching、统一 output stream | [diffusion](../components/diffusion/step-and-batching.md) |
| `feature/async_chunk.md` | 跨 stage 分块流式 | [distributed](../components/distributed/async-chunk.md) |
| `feature/cache_dit.md`、`teacache.md`、`prefix_caching.md` | 缓存加速 | [diffusion](../components/diffusion/cache-acceleration.md) |
| `feature/{tensor,pipeline,sequence,expert,cfg,vae}_parallel.md`、`hsdp.md` | 并行策略 | [diffusion](../components/diffusion/parallelism.md) |
| `feature/ray_based_execution.md` | Ray vs MP 后端、多机集群 | [serving](../components/serving/_index.md)（暂无专页） |
| `metrics.md`、`qwen3_omni_tts_performance_optimization.md` | Prometheus 指标；TTS 性能优化实录 | [qwen-omni](../models/qwen-omni/architecture.md)（perf 部分） |
| `docs/configuration/*` | 配置 schema spec | [configuration](../components/configuration/architecture.md) |
| `docs/contributing/ci/*` | L1–L5 与 markers | [ci guides](../ci/guides/test-tiers.md) |
| `docs/contributing/model/*` | 加模型三条路径 | [adding-a-model](../components/configuration/adding-a-model.md) |
