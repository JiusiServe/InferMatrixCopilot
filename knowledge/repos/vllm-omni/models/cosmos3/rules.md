---
title: "Cosmos3 规则"
created: 2026-07-20
updated: 2026-07-31
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #5001"]
confidence: high
---

# Cosmos3 规则

只有 `COSMOS-数字字母` 是可审计规则 ID。

## Direct 代码快速入口

| PR 描述信号 | 规则组 | 第一批源码 |
|---|---|---|
| Cosmos3/Edge、layerwise offload、专有 block | COSMOS-1a | `diffusion/registry.py::_DIFFUSION_MODELS`；`diffusion/models/cosmos3/transformer_cosmos3_edge.py::Cosmos3EdgeVFMTransformer` |
| Distilled、SDE scheduler、`t_list` | COSMOS-1b | `diffusion/models/cosmos3/pipeline_cosmos3.py::Cosmos3OmniDiffusersPipeline` 及 scheduler config consumer |
| seed/generator、逐步噪声 | COSMOS-2a | `pipeline_cosmos3.py::Cosmos3OmniDiffusersPipeline` 的 request-local sampling 路径 |
| `guidance=0`、request extra | COSMOS-2b | `model_extras/cosmos3.py` → pipeline sampling params |
| online/offload/HSDP/VAE parallel 支持声明 | COSMOS-3a | capability 文档/recipe → 对应公开入口与实现路径 |

若描述只写 Cosmos3，先从 registry 的 class key 进入 pipeline；只有命中共享 RNG、graph
或 offload 机制时再加 [Diffusion owner](../../components/diffusion/rules.md)。

## COSMOS-1a — Edge 的 offload 声明覆盖全部专有 block

- 触发：修改 Edge transformer 层级、layerwise offload 或 component discovery。
- 强制：Edge 新增/重命名 block 时同步更新 offload block 声明，并验证启用 offload 后
  每个目标 block 都发生预期迁移。
- 禁止：从常规 transformer 的声明推断 Edge 自动覆盖。
- 验收：结构测试枚举 Edge block 与 offload 声明集合，真实 smoke 证明无遗漏驻留。 ^[PR #5001]

## COSMOS-1b — Distilled checkpoint 强制 stochastic scheduler 合同

- 触发：scheduler `_class_name` 或 checkpoint config 表明 distilled 变体。
- 强制：验证 `fixed_step_sampler_config.sample_type=sde` 且 `t_list` 非空；缺失立即失败。
- 禁止：静默使用普通 scheduler/default，使 distilled 输出“能跑但语义错”。
- 验收：有效 distilled config 选择正确 scheduler；sample type 或 timestep 缺失分别有
  fail-fast 测试。 ^[PR #5001]

## COSMOS-2a — 逐步重加噪只使用请求本地 generator

- 触发：pipeline 在 scheduler step 中生成额外噪声或根据 seed 重建 generator。
- 强制：generator 从 request sampling params 传入每次随机操作，并确认当前 diffusers 版本
  的 scheduler 真正消费该参数。
- 禁止：调用 `torch.manual_seed`/global RNG 实现逐请求确定性；并发请求会互相改状态。
- 验收：交错执行两个不同 seed 的请求与各自单独运行结果一致；相同 seed 可重复。 ^[PR #5001]

## COSMOS-2b — guidance=0.0 必须原样到达 consumer

- 触发：request/dataclass 初始化 guidance 或其他允许零值的字段。
- 强制：仅以 `is None` 判断未提供；保留显式 `0.0` 并沿 request → sampling params →
  pipeline 断言。
- 禁止：`value or default`、truthy sentinel。
- 验收：未提供使用默认，`0.0` 保持零，普通正值保持不变，三类测试都到 consumer。 ^[PR #5001]

## COSMOS-3a — 支持表中的每个能力都有独立证据

- 触发：声明 Edge/Distilled、online、offload、HSDP、VAE parallel 或公开 checkpoint 支持。
- 强制：每个勾选项绑定可运行命令、checkpoint、输出和对应路径测试；未发布 checkpoint
  不得提前标完整支持。
- 禁止：用 offline unit test 支撑 online/HSDP/offload 多项 claim。
- 验收：公开矩阵逐项引用当前 head 证据；pending 项明确未验证或暂不声明。 ^[PR #5001]

共享 RNG/graph 规则见 [Diffusion rules](../../components/diffusion/rules.md)；公开证据分层见
[model adaptation guardrails](../../review/guides/model-adaptation-guardrails.md)。
