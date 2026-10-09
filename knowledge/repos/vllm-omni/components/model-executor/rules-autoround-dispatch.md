---
title: "AutoRound NVFP4 method dispatch 合同"
created: 2026-10-09
updated: 2026-10-09
type: rule
tags: [vllm-omni, components]
sources: ["PR #7721"]
confidence: high
---

# AutoRound NVFP4 method dispatch 合同

## EXEC-AUTOROUND-NVFP4-1a — Omni INC 复用 upstream FP4 scheme 并保留 exclusion

- 触发：修改共享 OmniINCConfig 的 nv_fp 支持或 quant method selection。
- 强制：SUPPORTED_DTYPES 接纳 nv_fp；由 config_parser.resolve(layer,prefix) 判定 runtime layer，量化 LinearBase 使用 upstream CompressedTensorsW4A4Fp4 scheme 与 CompressedTensorsLinearMethod；excluded Linear 返回 UnquantizedLinearMethod，非 Linear 返回 None。保留 MXFP4/MXFP8 与 stage-prefix 映射的既有边界。
- 禁止：为同一 NVFP4 ABI 新写重复 linear/scheme；忽略 per-layer exclusion；在 CPU config 测试初始化真实 GPU kernel。
- 验收：真实 config/method selection 覆盖 int4/mxfp4/nvfp4 与 excluded/nonlinear，mock 仅隔离 kernel initialization；检查 scheme/method/packing 字段，GPU 数值与 checkpoint加载另走实测。 ^[PR #7721]
