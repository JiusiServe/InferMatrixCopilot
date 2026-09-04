---
title: "Diffusion 并行策略总览"
created: 2026-07-16
updated: 2026-09-05
type: guide
tags: [vllm-omni, components, diffusion]
sources: [docs/design/feature/tensor_parallel.md, docs/design/feature/cfg_parallel.md, docs/design/feature/vae_parallel.md, "PR #6340", vllm_omni/diffusion/distributed/a2a_permute.py, vllm_omni/diffusion/attention/parallel/ulysses.py]
---

# Diffusion 并行策略总览

每种策略一篇官方 spec（`docs/design/feature/`，均在 `main @ 5c390096` 验证存在）：
`tensor_parallel.md`、`pipeline_parallel.md`、`sequence_parallel.md`、
`expert_parallel.md`、`cfg_parallel.md`（CFG 正负分支并行——与
[architecture 的 CFG companion 流](../serving/architecture.md)相关）、
`hsdp.md`、`vae_parallel.md`。本页只做路由：读具体策略以对应 spec 为准。

- 源码：`vllm_omni/diffusion/distributed/`（distributed_vae、sp_plan、序列并行
  hooks）；策略在 `diffusion/registry.py::initialize_model` 初始化链中注入
  （sequence parallelism、patch-parallel、VAE slicing/tiling）。
- **配置入口是 config 组件**：`composable_parallel` 的声明式 per-stage 轴栈
  （tp/dp/pp/ep/stage_replica 已接线；sp/cfg/vae_pp/hsdp 为保留位）见
  [Configuration](../configuration/architecture.md)；stage 级 `tensor_parallel_size` 等
  字段见 deploy schema。
- strict Ulysses 可显式设置 `ulysses_a2a_permute=true` 使用 SymmMem permute-free A2A；它默认关闭，
  advanced-UAA 与 AllGather 不走该 path；strict Ulysses+Ring 的 Ulysses leg 可用。workspace/capture/shutdown 与硬件 parity 门禁见
  [DIFF-4x](rules-system-runtime.md#diff-4x-symmmem-ulysses-a2a-只能显式启用并保持-workspace-生命周期闭合)，
  配置投影见 [VOMNI-CFG-1q](../configuration/rules-diffusion-parallel-transport.md#vomni-cfg-1q-symmmem-ulysses-transport-开关必须完整投影且默认关闭)。^[PR #6340]
- 并行度 × 设备容量的启动验收硬规则在
  [Model Executor 规则](../model-executor/rules.md)。
