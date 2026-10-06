---
title: "Attention execution-path 能力规则"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #7379"]
confidence: high
---

# Attention execution-path 能力规则

## DIFF-ATTN-CONTRACT-1a — capability 必须描述实际执行路径和已证明的编译边界

- 触发：修改 `resolve_execution_path`、attention metadata normalization、FA4 custom op 或支持/编译模式声明。
- 强制：resolver 使用执行时同一有效 metadata，包括 layer 加入的 KV-cache dtype、并行策略与 HSDP 外边界。FA4 的迁移声明限于 CUDA/BF16、非因果、无 mask/packing/paged-KV/piecewise/量化/并行或外边界的 dense 路径；确认 Q/K/V dtype 和 device 一致、Q/K head dim 相同并通过 FA4 自身维度 validator。fake 输出最后一维取 V，保持输出 contiguous。
- 禁止：只看 Q 就声明兼容 Q/K/V；把 CPU vendor-kernel doubles 当作 NPU/ROCm 数值或 compiler 支持；validator 缺失仍标 `SUPPORTED`。未知 mask 语义仍是 `UNMIGRATED`，实际 UNKNOWN dispatch 可以读取 mask 值，不能宣称该路径没有 device→host 同步。
- 验收：覆盖混合 dtype/device、非法 head dim、validator 缺失、有效 KV dtype 与各外边界；FA4 以真实 kernel/eager/FP32 SDPA 对照 fullgraph 输出并核对 fake shape；NPU/ROCm wrapper 测试通过仍保持未迁移，直到目标硬件验证完成。^[PR #7379]
