---
title: "官方设计文档地图（docs/design/**）"
created: 2026-07-16
updated: 2026-09-02
type: guide
tags: [vllm-omni, docs]
sources: ["PR #5833", "PR #5839", docs/.nav.yml, docs/design/index.md, docs/design/ar_diffusion_pipeline_capability.md, docs/design/architecture_overview.md, docs/design/feature/diffusion_continuous_batching.md, docs/design/feature/distributed_layerwise_offload.md, docs/design/feature/omni_async_output_materialization.md, docs/design/feature/quantization.md, docs/user_guide/diffusion/execution_modes.md]
---

# 官方设计文档地图（docs/design/**）

`main @ 62bf8d63` 复核。官方 `docs/design/index.md` 与 `docs/.nav.yml` 按 architecture、runtime/stage、
communication、diffusion acceleration、infrastructure/performance 和 module 编排。本轮新增 DLO 与
quantization design，`cpu_offload_diffusion.md` 重命名为 `cpu_offload.md` 并保留 MkDocs redirect，
同时移除 `ray_based_execution.md`，即删除一项误导性的 supported-design surface。目标 pin 虽仍暴露
`vllm_omni/distributed/ray_utils/`、`worker_backend` 与 `ray_address`，但 diffusion executor 明确
`NotImplementedError("ray backend is not yet supported.")`，placement-group/actor helpers 也没有
live caller；这些残留不是 runtime support 证据。索引仍未列
`docs/design/ar_diffusion_pipeline_capability.md`；找 spec 时仍须检查 `docs/design/` 实际文件树。

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
| `feature/distributed_layerwise_offload.md` + `user_guide/diffusion/cpu_offload.md` | DLO 的 DP/SP/TP/HSDP compatibility、AllGather 与 rank-local loader 合同；部分组合仅有配置级验证 | [diffusion rule DIFF-2e](../components/diffusion/rules.md) |
| `feature/quantization.md` + `user_guide/quantization/overview.md` | diffusion quantization factory、component routing、checkpoint metadata 与验证边界 | [diffusion rule DIFF-2c](../components/diffusion/rules.md) |
| `metrics.md`、`qwen3_omni_tts_performance_optimization.md` | Prometheus 指标；TTS 性能优化实录 | [qwen-omni](../models/qwen-omni/architecture.md)（perf 部分） |
| `docs/configuration/*` | 配置 schema spec | [configuration](../components/configuration/architecture.md) |
| `docs/contributing/ci/*` | L1–L5 与 markers | [ci guides](../ci/guides/test-tiers.md) |
| `docs/contributing/model/*` | 加模型三条路径 | [adding-a-model](../components/configuration/adding-a-model.md) |
