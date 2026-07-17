---
title: "Diffusion 并行策略总览"
created: 2026-07-16
updated: 2026-07-16
type: guide
tags: [vllm-omni, components, diffusion]
sources: [docs/design/feature/tensor_parallel.md, docs/design/feature/cfg_parallel.md, docs/design/feature/vae_parallel.md]
---

# Diffusion 并行策略总览

每种策略一篇官方 spec（`docs/design/feature/`，均在 `main @ 5c390096` 验证存在）：
`tensor_parallel.md`、`pipeline_parallel.md`、`sequence_parallel.md`、
`expert_parallel.md`、`cfg_parallel.md`（CFG 正负分支并行——与
[architecture 的 CFG companion 流](../../serving/architecture.md)相关）、
`hsdp.md`、`vae_parallel.md`。本页只做路由：读具体策略以对应 spec 为准。

- 源码：`vllm_omni/diffusion/distributed/`（distributed_vae、sp_plan、序列并行
  hooks）；策略在 `diffusion/registry.py::initialize_model` 初始化链中注入
  （sequence parallelism、patch-parallel、VAE slicing/tiling）。
- **配置入口是 config 组件**：`composable_parallel` 的声明式 per-stage 轴栈
  （tp/dp/pp/ep/stage_replica 已接线；sp/cfg/vae_pp/hsdp 为保留位）见
  [Config 组件](../../config/architecture.md)；stage 级 `tensor_parallel_size` 等
  字段见 deploy schema。
- 并行度 × 设备容量的启动验收硬规则在
  [Model Executor 规则](../../model-executor/rules.md)。
