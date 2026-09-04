---
title: "SANA-Video 规则"
created: 2026-09-05
updated: 2026-09-05
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #5861", vllm_omni/diffusion/models/sana_video/pipeline_sana_video.py, vllm_omni/diffusion/models/sana_video/pipeline_sana_video_i2v.py, vllm_omni/diffusion/models/sana_video/transformer_sana_video.py, tests/diffusion/models/sana_video/]
confidence: high
---

# SANA-Video 规则

## SANA-1a — native SANA Video 只支持 TP/CFG 的 {1,2} 矩阵

- 触发：native SANA Video TP/CFG、transformer layout、I2V 或 Diffusers adapter topology 变更。
- 强制：TP/CFG 各只 `{1,2}`，TP2×CFG2 valid；SP/text-encoder TP/PP/HSDP load 前 reject，Diffusers adapter reject native TP/CFG。TP 用 QKV column/output row、distributed RMSNorm global sumsq/local weights，GLUMB packed `[value;gate]` 每 segment slice 后 local chunk2/reduction。CFG1 batch neg/pos 后 slice；CFG2 mixin branch gather/combine FP32。uninitialized group serial，initialized broken group errors propagate；I2V first frame/mask 不变。
- 禁止：TP>2/CFG>2、cache/offload/step/support/perf claim。
- 验收：CPU topology/layout 与 tiny multiprocess TP/CFG matrix；A800 数字仅该环境观察。^[PR #5861]
