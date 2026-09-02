---
title: "Diffusion multiprocess runtime 规则"
created: 2026-09-02
updated: 2026-09-02
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #5864", vllm_omni/diffusion/diffusion_engine.py, vllm_omni/diffusion/executor/multiproc_executor.py, vllm_omni/diffusion/inline_stage_diffusion_client.py, vllm_omni/diffusion/ipc.py, vllm_omni/diffusion/sched/request_scheduler.py, vllm_omni/diffusion/worker/diffusion_worker.py, tests/diffusion/test_async_output_worker.py, tests/diffusion/test_diffusion_engine.py, tests/diffusion/test_diffusion_ipc.py, tests/diffusion/test_inline_stage_diffusion_client.py, tests/diffusion/test_ipc_async.py, tests/diffusion/test_multiproc_engine_concurrency.py, tests/diffusion/test_result_pump.py]
confidence: high
---

# Diffusion multiprocess runtime 规则

## DIFF-1d — async output 的 compute 与 output-ready 必须分成两个可观察阶段

- 触发：把 diffusion D2H/SHM packing 移到 worker 后台线程，或修改 result pump、`collective_rpc`、
  batch output split。
- 强制：GPU compute 完成只释放下一次 forward；最终输出必须等 side-stream event、D2H 和 SHM packing
  完成后再 resolve。每个 worker-owned result queue 由唯一 pump reader 分发，batch 结果按 request 映射
  拆分；step-mode 保留同步路径。
- 禁止：在 compute-done 时把未完成 device tensor 当最终 artifact；让多个线程同读一个 result queue；
  用同步 `.cpu()` 掩盖 stream ordering 或让下一 step 重写源 buffer。
- 验收：覆盖 compute-done、output-ready、RPC error、batch split、queue cleanup 与非 CUDA/step-mode
  fallback。^[PR #5864]

## DIFF-1g — 每个 worker result queue 必须有唯一 reader 与显式 SHM owner

- 触发：request-mode worker result queue、async pump、multi-rank reply 或 tensor/NumPy SHM serialization。
- 强制：每个 worker 创建独立 result queue，executor 为每个 queue 建唯一 pump；RPC/output future 按
  envelope ID 路由，DP reply 保留 rank tag。递归 pack/unpack 必须覆盖 tagged/RPC envelope、nested
  dict/list/tuple、tensor 与大于 1MB 的 non-object ndarray；reader copy 后 close+unlink segment。
- 禁止：多个 worker 共写一个 queue 后假设 reply 不冲突；pump 与同步 caller 同读；object ndarray
  进入 raw SHM；只释放顶层 handle 而泄漏 nested segment。
- 验收：真实 spawn workers 各建 queue，传 nested tensor/video/audio ndarray，验证 tag/order/dtype/value，
  所有 pump 停止、queue 关闭、SHM name 不再可 attach。当前测试覆盖成功 round-trip；partial pack、
  unpack/copy 异常时已创建 segment 的回收仍缺 fault-injection。^[PR #5864]

## DIFF-1h — request-mode shutdown 必须幂等、有界且按 engine→task/IPC 顺序完成

- 触发：worker async-output thread、executor process cleanup、inline client 或 orchestrator pre-mark shutdown。
- 强制：worker 用 sentinel 停 async thread，并证明 thread 已停止后才 teardown 它仍可能访问的
  model/queue/SHM；executor 以全局 deadline join 全部 workers，统一 terminate survivors，再 join
  pumps/fail futures。inline client 区分 shutting-down 与
  shutdown-complete，在 lock 内先 close engine 再等待 thread-pool；调用方复用 sampling params 时在 task
  启动前同步 clone。
- 禁止：把 orchestrator 的 pre-mark 当作 teardown 已完成；每 worker 单独耗完整 timeout；先等待可能
  阻塞在 engine RPC 的 executor 再 close engine；二次 shutdown 重复释放。
- 验收：normal、worker shutdown exception、premarked、concurrent/repeated shutdown、blocked RPC、async
  output active 与 forced termination 都验证无 live thread/process/queue/SHM，future 到达终态。目标常量
  为 worker 15s 全局 join、5s terminate grace、async thread 10s、pump 2s；async thread 超时仍存活时
  虽保留 result queue，却仍先调用 `worker.shutdown()`，model teardown 可能与 live output thread 竞态，
  且没有后续强制 thread/SHM/queue 回收证明。final 2×B300 rerun提供一次普通 TP2 与
  DLO DP2 clean exit，但不替代 fault matrix。^[PR #5864]

## DIFF-2k — DLO AllGather DP wave 必须完整兼容或不可复用地 fail closed

- 触发：DLO+AllGather、DP>1 允许 concurrent request，或修改 multi-rank `execute_model` RPC。
- 强制：只在 DLO+AllGather+DP>1 放宽 single-request pipeline admission；preflight 复用完整
  `RequestBatchSamplingParamsKey`，另比较 canonical `extra_args` 并拒绝空 prompt。shape、CFG、denoise
  schedule、output count、LoRA 与任何 future control-flow 字段必须相同；prompt/token length 和
  seed/generator 可不同。multi-rank reply 按 `dp_rank` tag 排序，step mode 从
  `dp_rank * (TP*SP*PP*CFG)` 选择 replica primary result queue。
- 禁止：为凑 wave 静默改变用户 wait 配置；用 step count+extra_args 代替完整 key；partial collective
  timeout 后复用 process group。少于 DP 个 request 时 rank 以 `dp_rank % len(reqs)` 重复执行已有 request，
  只消费前 request-count 个排序输出；这是 correctness fallback 与额外计算，不得称为满 DP throughput。
- 验收：完整/partial wave、mismatch shape/CFG/steps/output/LoRA/extra_args、空 prompt、不同 seed/token
  length、rank tag 重排与 primary-rank topology 都覆盖；timeout 必须将 engine 标记失败、同步 shutdown
  并通知 failure callback。timeout 默认 600s 且在 import 时从 env 读取，不是 request deadline。final
  2×B300 evidence 覆盖 ordinary TP2 与 H3 DLO DP2 的错误 wave→同 engine recovery→无 active child；
  仍只绑定 eager+CUDNN exact topology，不能推广到一般 DP/SP 或替代 per-replica SP/mmap redesign。
  ^[PR #5864]
