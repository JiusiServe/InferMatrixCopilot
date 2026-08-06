---
title: "MiniMax H3 规则"
created: 2026-08-06
updated: 2026-08-06
type: rule
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/minimax_h3/minimax_h3_transformer.py, tests/diffusion/models/minimax_h3/test_minimax_h3_quantization.py, tests/diffusion/models/minimax_h3/test_minimax_h3_quantization_quality.py, docs/user_guide/quantization/fp8.md, "PR #5737"]
confidence: high
---

# MiniMax H3 规则

只有 `H3-数字字母` 是可审计规则 ID。

## Direct 代码快速入口

| PR 描述信号 | 规则组 | 第一批源码 |
|---|---|---|
| online FP8、quant config、ignored layers、QKV/gate-up loader | H3-1a | `diffusion/models/minimax_h3/minimax_h3_transformer.py::{MiniMaxH3Transformer.__init__,load_weights}` → component quant-config resolution |

## H3-1a — online FP8 的量化边界与 checkpoint 变换顺序必须一起保持

- 触发：MiniMax H3 online FP8、`ignored_layers`、vLLM linear replacement，或 QKV/
  gate-up checkpoint loader 发生变化。
- 强制：condition projection、token refiner、DiT blocks 和 AdaLN linears 接收 resolved
  quant config；video/audio patch projection、timestep projection 与最终 video/audio output
  projection 保持全精度。grouped QKV reorder 和 fused gate/up split 必须先完成，再调用参数上
  当前生效的 vLLM `weight_loader`，以保留 online FP8 wrapper；`ignored_layers` 使用带完整
  runtime prefix 的模块名。
- 禁止：先绕过 wrapper 用 default loader 写入再做 layout 变换；把 FP32 输入/输出边界纳入
  online FP8；用 checkpoint 短名匹配 runtime `ignored_layers`；把 online FP8 与 layerwise
  offload 组合宣称为已支持。
- 验收：测试 quant-config prefix 与 ignored-layer 命中、QKV reorder、gate/up 分片和实际
  loader 调用顺序；从 component config 入口证明量化配置到达 transformer；BF16 对 FP8 的
  质量回归与峰值显存分别设门槛，且 layerwise offload 组合明确拒绝。 ^[PR #5737]

共享量化/loader 边界见 [Diffusion 规则](../../components/diffusion/rules.md)；配置解析见
[Configuration 规则](../../components/configuration/rules.md)。
