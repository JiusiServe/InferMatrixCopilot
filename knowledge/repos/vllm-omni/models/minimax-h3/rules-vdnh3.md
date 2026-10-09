---
title: "MiniMax-H3 VDNH3 checkpoint 与请求合同"
created: 2026-10-09
updated: 2026-10-09
type: rule
tags: [vllm-omni, models]
sources: ["PR #8439"]
confidence: high
---

# MiniMax-H3 VDNH3 checkpoint 与请求合同

## MMH3-5a — VDNH3 metadata、attention 与请求资格必须成套校验

- 触发：修改 VDNH3 turbo artifact loader、hybrid attention 或 turbo request admission。
- 强制：artifact 必须提供非空 turbo_num_steps，按实际权重 shape/kind 转换 hybrid attention 并校验；serve partition 限于 fl2va，VDNH3_ATTN 与对应 checkpoint 成套加载。请求必须命中允许 task，不支持 LoRA，steps 匹配 metadata，sampler 仅缺省/euler；metadata 提供 expected shift 且请求显式给 shift 时校验一致。
- 禁止：从 checkpoint 名推断固定 8 步、DMD 身份或未校验的 base HF revision；硬编码未经 metadata 支持的 shift 数字；把 loader smoke 当作 full-model quality 已通过。
- 验收：覆盖缺 metadata、错误 weight shape/kind、task/LoRA/steps/sampler/shift 拒绝与合法路径；真实视频音频质量和性能另绑定 checkpoint、GPU、head 与 workload。 ^[PR #8439]
