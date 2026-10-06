---
title: "VoxCPM2 NPU estimator graph 规则"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, models, model-executor]
sources: ["PR #7275"]
confidence: high
---

# VoxCPM2 NPU estimator graph 规则

## VOXCPM2-NPU-1a — NPU graph 只包装已加载 LocDiT estimator 的 exact tensor 调用

- 触发：修改 NPU VoxCPM2 platform adapter、constructor patch、estimator forward 或 platform resolution。
- 强制：模型构造/权重加载完成后，NPU adapter 幂等包装 `feat_decoder.estimator.forward(x,mu,t,cond,dt)`，使用 `NPUExactGraphRunner` 的 exact-input gate 和有限 graph budget（本提交为 8）；不支持必要 NPU graph APIs 时保留 eager。CFM solver、request-local噪声、feature encode 与 VAE decode 保持各自原路径，不能把 estimator graph 等同完整 decode graph。`graph_tools` 只在真正 NPU worker setup 延迟导入；访问 platform 时使用模块当前值，避免 inspection import 初始化 NPU或保存未解析 sentinel。CUDA unified decode graph 的 scheduler deferral 仍由 CUDA capability 选择。
- 禁止：在模型 inspection 子进程提前初始化 NPU；重复 constructor patch 或重复包装 estimator；把 NPU fast path塞进硬件 YAML 或修改共享 runtime knobs 来假冒统一能力；把 CPU mock 或单次 Atlas A2观察当成真实 NPU parity/通用性能证明。
- 验收：CPU contract 验证延迟 import、幂等 patch、正确五 tensor wiring、unsupported API eager 和 NPU 不触发 CUDA waiting deferral；真实 NPU 另核对 estimator eager/replay 数值、exact signature miss、graph budget 与多请求 seed/生命周期。^[PR #7275]
