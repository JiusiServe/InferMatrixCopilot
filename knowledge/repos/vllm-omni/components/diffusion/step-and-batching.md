---
title: "Step 执行合同与 batching 模式"
created: 2026-07-16
updated: 2026-09-02
type: guide
tags: [vllm-omni, components, diffusion]
sources: ["PR #5599", docs/design/feature/diffusion_continuous_batching.md, docs/user_guide/diffusion/execution_modes.md, vllm_omni/diffusion/diffusion_engine.py, vllm_omni/diffusion/models/interface.py, vllm_omni/diffusion/sched/request_scheduler.py, vllm_omni/diffusion/sched/step_scheduler.py, vllm_omni/diffusion/worker/diffusion_model_runner.py, tests/diffusion/test_diffusion_engine.py, tests/diffusion/test_diffusion_step_pipeline.py]
---

# Step 执行合同与 batching 模式

官方设计入口已合并为 `docs/design/feature/diffusion_continuous_batching.md`，用户配置入口是
`docs/user_guide/diffusion/execution_modes.md`（`main @ 9f978923` 复核）。旧的 step、request
batching 设计页及两份用户指南已删除；迁移依赖 MkDocs redirects，不能继续把旧路径当 source。

## 两个开关组成四种配置，不是四个 engine mode

| `step_execution` | `max_num_seqs` | scheduler / 执行语义 |
|---|---:|---|
| false | 1 | `RequestScheduler`；一次完整 `forward()`，串行 request |
| false | >1 | `RequestScheduler`；兼容 request 融合为一次完整 `forward()` |
| true | 1 | `StepScheduler`；每个 tick 推进一个 request 的一个 denoise step |
| true | >1 | `StepScheduler`；兼容 request 共享 step wave，即 continuous batching |

前两行在 engine 中同属 `REQUEST_BATCH`，后两行同属 `STEP_BATCH`。`max_num_seqs>1` 只是容量，
不会自动赋予 pipeline 批处理能力。

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

request mode 的 `max_num_seqs>1` 要求 pipeline 显式声明 `supports_request_batch=True`，否则
engine 初始化失败（DLO DP concurrent 保留已有例外）。`request_batch_max_wait_ms` 的具体启停、
stable window 与 deadline 已归 `RequestScheduler`；见
[admission wait rules](rules-admission-wait.md)。它用首请求延迟换 batch formation。

## step capability 必须验证 grouped contract

`supports_step_execution=True` 只证明四段 stateful contract（`prepare_encode`、
`denoise_step(input_batch, *, states=...)`、`step_scheduler`、`post_decode`）存在，不证明
`denoise_step` 能处理多个 state。Qwen-Image 支持 grouped step；HunyuanImage3 只有 resolved
self-attention backend 为 `TORCH_SDPA` 时支持 grouped step；Helios 会拒绝 `len(states) != 1`，
因此必须使用 `--step-execution --max-num-seqs 1`。新增 pipeline 不能只凭 capability flag
宣称 continuous batching，须用两个重叠且兼容的真实请求覆盖 state 隔离、abort 与输出归属。

step mode 当前拒绝所有 diffusion cache backend，但这不等于拒绝 inter-stage KV transfer：
runner 对新 admission 先调用 `receive_multi_kv_cache_distributed()`，再 `prepare_encode()`，且有
顺序测试。限制描述必须区分这两个机制。

## output stream 是统一生命周期

streaming 与 non-streaming caller 都消费 `DiffusionEngine.step_streaming()` 对应的 per-request
queue；前者转发每个 chunk，后者 drain 后只返回最终结果。terminal scheduler result 负责完成
request state；consumer cancel/disconnect 删除 delivery queue，但 scheduler 仍须完成清理；
shutdown 给剩余 stream 发送 error。兼容 wrapper `step()` 与
`async_add_req_and_wait_for_response()` 已 deprecated，新集成应使用 streaming API。

## 相关

- 噪声调度/采样归 [Diffusion 组件](_index.md)；请求级排队语义见
  [Scheduler 组件](../scheduler/_index.md)（AR 侧对照）。
