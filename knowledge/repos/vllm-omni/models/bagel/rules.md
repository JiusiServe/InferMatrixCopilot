---
title: "BAGEL 规则"
created: 2026-08-06
updated: 2026-08-06
type: rule
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/bagel/bagel_transformer.py, "PR #5775"]
confidence: high
---

# BAGEL 规则

只有 `BAGEL-数字字母` 是可审计规则 ID。

## Direct 代码快速入口

| PR 描述信号 | 规则组 | 第一批源码 |
|---|---|---|
| CFG branch、position IDs、multimodal RoPE、Lance | BAGEL-1a | `diffusion/models/bagel/bagel_transformer.py` 的 CFG input preparation → [Lance](../lance/_index.md) 继承调用链 |

## BAGEL-1a — CFG position IDs 按 RoPE rank 选择序列维

- 触发：BAGEL/Lance 组装 CFG branch position IDs，或改变 1-D 与 multimodal RoPE 的
  position-id rank。
- 强制：legacy 1-D position IDs 沿 `dim=0` 拼接；形状为 `(3, S)` 的 2-D multimodal
  RoPE position IDs 沿序列维 `dim=1` 拼接，并保留三个坐标行的顺序和值。
- 禁止：对两种 rank 固定使用同一个 concat dim；通过 flatten/squeeze 把 2-D 输入伪装成
  1-D；只验证 token 总数而不验证坐标行。
- 验收：BAGEL 1-D 与 Lance 2-D 各有 shape 和逐值断言；2-D 用不同坐标行和不同 branch
  长度，确保错误的 `dim=0` 会失败。 ^[PR #5775]

模型拓扑与 CFG 数据流见 [BAGEL architecture](architecture.md)；共享 diffusion 合同见
[Diffusion 规则](../../components/diffusion/rules.md)。
