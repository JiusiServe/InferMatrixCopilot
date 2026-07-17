---
title: "Step 执行合同与 batching 模式"
created: 2026-07-16
updated: 2026-07-16
type: guide
tags: [vllm-omni, components, diffusion]
sources: [docs/design/feature/diffusion_step_execution.md, docs/design/feature/diffusion_request_level_batching.md, docs/design/feature/diffusion_continuous_batching.md]
---

# Step 执行合同与 batching 模式

官方 spec：`docs/design/feature/diffusion_{step_execution,request_level_batching,continuous_batching}.md`
（`main @ 5c390096` 复核）。

## step_execution 不是通用开关

`step_execution=True`（serving：`--step-execution`）只对实现了
`vllm_omni/diffusion/models/interface.py` 中**分段有状态合同**的 pipeline 生效；
它是"作者实现合同 + 用户 opt-in 旋钮"的两层结构——给新 pipeline 加支持要按该
接口实现，不要当成 runtime 配置随手打开。

## 两种 batching，别混

- **request-level batching**：对**兼容**的等待请求组成一个调度波，跑一次完整
  pipeline `forward()`（静态批）。设计动机：不把多个逻辑请求耦合进一个 request
  对象——请求身份、abort/错误处理、逐请求元数据保持清晰，同时对突发并发流量仍
  只发一次融合前向。每个 `OmniDiffusionRequest` 仍是单 prompt + 单 request_id。
- **continuous batching（实验）**：叠在 `step_execution=True` 之上——step 化把长
  denoise 循环拆成调度器可见的单元，运行时得以在 denoise step 之间接纳其他兼容
  请求、共享同一 denoise 前向。收益在低 MFU/突发场景（吞吐与设备利用率）；
  **不保证单请求延迟收益**。基础 step 合同不变，改动集中在 scheduler 与 runner 层
  （`vllm_omni/diffusion/sched/`、`worker/`）。

## 相关

- 噪声调度/采样归 [Diffusion 组件](../_index.md)；请求级排队语义见
  [Scheduler 组件](../../scheduler/_index.md)（AR 侧对照）。
