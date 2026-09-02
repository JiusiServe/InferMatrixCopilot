---
title: "Diffusion 平台运行时规则"
created: 2026-09-02
updated: 2026-09-02
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #6058", vllm_omni/diffusion/registry.py, vllm_omni/diffusion/worker/diffusion_worker.py, vllm_omni/platforms/musa/platform.py]
confidence: high
---

# Diffusion 平台运行时规则

本页承载 diffusion worker 与硬件 platform 之间的配置合同；模型自己的 kernel、数值与性能
结论仍归共享 layer/backend 或模型 owner。

## Direct 代码快速入口

| PR 描述在做什么 | 规则 | 第一批 live 源码 |
|---|---|---|
| IR-op priority、Inductor/eager 默认顺序、模型 hook 覆盖 | `DIFFPLAT-1a` | platform `get_default_ir_op_priority` → `diffusion_worker._resolve_ir_op_priority` → model `get_diffusion_ir_op_priority_func` |

## DIFFPLAT-1a — platform IR-op priority 必须区分 Inductor 与 eager

- 触发：平台新增或修改 `get_default_ir_op_priority()`，或 diffusion worker 改变 platform
  default 与模型 hook 的合并顺序。
- 强制：worker 先取当前 platform default，再让模型级 `get_diffusion_ir_op_priority_func()`
  做精确覆盖。MUSA 与 ROCm 的通用基线是：backend 为 `inductor` 且 compilation mode 非
  `NONE` 时只优先 `native`，否则按 `vllm_c → native`；返回值必须经
  `IrOpPriorityConfig.with_default()` 构造，使显式 per-op priority 仍可表达。
- 禁止：在 compile 路径优先可能产生不兼容 custom-call 的 `vllm_c`；把 CUDA 固定优先级、
  ROCm 的 AITER/RMSNorm 特例或单模型 override 泛化到 MUSA；仅凭实现与 ROCm 排序一致声称
  MUSA kernel 已验证。
- 验收：平台单测至少覆盖 Inductor enabled、mode `NONE`、非 Inductor backend，并由 worker
  测试断言 platform default 先于 model hook。PR #6058 没有新增自动测试或 MUSA runtime
  运行，当前证据只证明静态实现与现有 worker consumer 接通。^[PR #6058]
