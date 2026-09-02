---
title: "官方设计文档地图（docs/design/**）"
created: 2026-07-16
updated: 2026-09-02
type: guide
tags: [vllm-omni, docs]
sources: ["PR #5139", "PR #5833", "PR #5839", docs/.nav.yml, docs/design/index.md, docs/design/module/, docs/design/module/archive/README.md, docs/design/ar_diffusion_pipeline_capability.md, docs/design/architecture_overview.md, docs/design/feature/diffusion_continuous_batching.md, docs/design/feature/distributed_layerwise_offload.md, docs/design/feature/omni_async_output_materialization.md, docs/design/feature/quantization.md, docs/user_guide/diffusion/execution_modes.md]
---

# 官方设计文档地图（docs/design/**）

`main @ fd0e9218` 复核。官方 `docs/design/index.md` 与 `docs/.nav.yml` 按 architecture、feature、
infrastructure/performance 和 21 个 module 页面编排。module frontmatter 的 owner、代码路径、依赖与
验证路径可作 review 首跳 source map；但本批页面全部是 `status: draft`，其中 invariant 编号也明确
只是 candidate，不能覆盖当前代码与测试。尤其 `module/vllm_omni_config.md` 是
`deferred-pending-refactor`，没有稳定 precedence、环境变量捕获、canonical config 或 invariant namespace。

旧四页已移入 `module/archive/` 并从导航移除，只能作为历史叙述；有用结论须先与当前代码/测试复核。
上游刻意没有为旧 URL 留 redirect，因此外部深链会 404。owner 与 `required_reviewers` 是不同角色，
不能用 document steward/technical owner 冒充独立验证批准。

此前 #5833/#5839 增加 DLO 与 quantization design；`cpu_offload_diffusion.md` 重命名为
`cpu_offload.md` 且保留 MkDocs redirect，并删除误导性的 `ray_based_execution.md`。目标 pin 仍有
`distributed/ray_utils/`、`worker_backend`、`ray_address`，但 diffusion executor 明确报 Ray backend
尚未支持，placement-group/actor helpers 也没有 live caller，不能据残留宣称 runtime support。
`docs/design/ar_diffusion_pipeline_capability.md` 仍未列入索引，找 spec 时还须检查实际文件树。

| 官方文档 | 一句话 | 知识树 owner |
|---|---|---|
| `architecture_overview.md` | 三类模型拓扑（DiT 主/AR 主/AR+DiT）、OmniRouter/EntryPoints/AR/Diffusion/OmniConnector、E/P/D/G 解耦、CFG companion 流 | [serving](../components/serving/architecture.md) + [distributed](../components/distributed/architecture.md) |
| `module/{entrypoints,vllm_omni_config,input_output_modality_contracts,error_contracts,engine_orchestration,stage_runtime,omni_connector,model_integration,ar_runtime}.md` | serving/config/I-O/error/engine/stage/connector/model/AR 的 draft ownership 与 source map；candidate invariant 尚非规范 | 对应 [serving](../components/serving/_index.md)、[configuration](../components/configuration/_index.md)、[distributed](../components/distributed/_index.md)、[scheduler](../components/scheduler/_index.md)、[model-executor](../components/model-executor/_index.md) |
| `feature/omni_async_output_materialization.md` | AR decode 关键路径外的异步 D2H 与 Omni payload 构造；含 live connector ownership、平台验证范围和同步 fallback | [model-executor](../components/model-executor/_index.md) |
| `module/diffusion/{index,diffusion_runtime,diffusion_model_integration,continuous_batching,parallelism,offloader}.md` | diffusion draft module 边界与首跳路径 | [diffusion](../components/diffusion/architecture.md) |
| `module/{execution_platforms,cache_management,quantization,observability,profiling,benchmarking}.md` | 横切模块的 draft owner/source map | 对应组件 owner；行为仍以代码和测试为准 |
| `module/archive/{async_omni_architecture,ar_module,dit_module,entrypoint_module}.md` | 历史快照，不是 active contract；旧路径无 redirect | 仅作 provenance，改动路由到 active module 页 |
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
