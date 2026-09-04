---
title: "Diffusion 指标证据规则"
created: 2026-09-04
updated: 2026-09-04
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["Issue #5811", "PR #4755", "PR #6150", vllm_omni/diffusion/outputs.py, vllm_omni/diffusion/sched/diffusion_scheduler.py, vllm_omni/metrics/prometheus.py]
confidence: high
---

# Diffusion 指标证据规则

本页承载 image/diffusion 请求指标的测量边界和解释合同。服务端的发射、聚合与
replica 生命周期见 [Serving metrics rules](../serving/rules.md)；性能结论的证据门槛见
[performance evidence](../../benchmark/guides/performance-evidence.md)。

## DIFF-5a — diffusion metrics 的 per-step 计算必须保留请求步数

- 触发：修改 diffusion output formatter、sampling params metadata 或 diffusion metrics accumulation，使请求级 DiT execution time 需要按 denoising step 归一化。
- 强制：`format_diffusion_outputs()` 必须保留 `sampling_params.num_inference_steps` 并传入 stage stats；aggregator 保留该 scalar，仅在 execution time 与正步数同时存在时按 `exec_time / num_inference_steps` 观测 per-step metric。
- 禁止：丢弃请求步数、用 stage 总生成时间替代 DiT execution time，或把跨多个结果的 scalar 累加后再计算 per-step 值。
- 验收：覆盖完整 metadata、缺失/`None`/零步数、正步数、重复结果与零 execution time；分别断言 per-step 值精确、无效步数跳过且 scalar 不累加。^[PR #4755]

## DIFF-5b — diffusion 指标必须区分 service time、forward time 与 unavailable

- 触发：修改 diffusion scheduler admission、engine output `metrics`、profiler stage
  durations，或将这些值汇总到 Prometheus/benchmark snapshots。
- 强制：enqueue 到首次 `RUNNING` 的等待直接在 scheduler 测量；engine request time 从
  scheduler insertion 到收到 output，包含 scheduler wait、execution 和 async-output wait，
  但不含 preprocess/postprocess。只有 profiler `*.diffuse` duration 可用时才发射
  forward/denoise family；VAE、KV receive、peak memory 同样以实际 source 为前提。每个
  chunk 的 `*_ms` 先转秒再按 request 累加，per-step 仅在正 steps 下计算。
- 禁止：用 `stage_gen - exec` 反推 queue time；把 service-time-per-step 称为纯 GPU
  denoise；profiler 未启用时以 `0` 代替 unavailable，或让 benchmark snapshot 将缺失
  forward 值悄然显示为零。
- 验收：覆盖 queue admission、async output、profile on/off、缺失 KV/VAE/memory、正/零
  steps 和多 output 累加；benchmark consumer 也必须明确区分 unavailable 与实测零。
  PR #6150 的最后一项仍是未解决 inline finding，不能据其测试或实现推断速度、质量或
  模型效果。^[Issue #5811] ^[PR #6150]
