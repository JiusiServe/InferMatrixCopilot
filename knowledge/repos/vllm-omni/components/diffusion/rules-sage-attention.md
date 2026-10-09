---
title: "SageAttention3 FP4 dispatch 合同"
created: 2026-10-09
updated: 2026-10-09
type: rule
tags: [vllm-omni, components]
sources: ["PR #7740"]
confidence: high
---

# SageAttention3 FP4 dispatch 合同

## DIFF-SAGE3-1a — SageAttention3 注册与输入资格分别验证

- 触发：修改 SageAttention3 wrapper、custom op、dispatch 或支持声明。
- 强制：custom op 不声明输入 mutation；vendor 会原地中心化 K，故传入 clone。真实与 fake 输出保持相同 shape/dtype/device/layout，实际输出 contiguous；能力 metadata 覆盖实现接纳的 head dimension 64/128/256，但只对已验证 64/128 路径宣称 FP4，256 可能派发 SDPA。dtype/layout/hardware 资格在 kernel 前处理。
- 禁止：让 vendor 改写 caller K；把 op 注册、未迁移平台 advisory 或 D256 接纳等同 FP4 已执行；伪造 SM120 或未测设备保证。
- 验收：核对 K 未修改、fake/meta 合同、实际 dispatch 与 unsupported-input 失败边界；真实 CUDA 数值/性能证据单独绑定 GPU、输入布局和最终 head。 ^[PR #7740]
