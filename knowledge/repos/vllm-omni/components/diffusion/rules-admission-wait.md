---
title: "Diffusion admission wait rules"
created: 2026-08-10
updated: 2026-08-10
type: rule
tags: [vllm-omni, components, diffusion, scheduler]
sources: [docs/mkdocs/hooks/generate_argparse.py, vllm_omni/diffusion/data.py, vllm_omni/diffusion/diffusion_engine.py, vllm_omni/diffusion/sched/base_scheduler.py, vllm_omni/diffusion/sched/interface.py, vllm_omni/diffusion/sched/request_scheduler.py, vllm_omni/entrypoints/cli/serve.py, tests/diffusion/test_diffusion_engine.py, tests/diffusion/test_diffusion_engine_rpc_routing.py, tests/diffusion/test_diffusion_scheduler.py, tests/entrypoints/test_async_omni_diffusion_config.py, "PR #5843"]
---

# Diffusion admission wait rules

只有 `DIFFADM-数字字母` 是可审计规则 ID。request/step batching 的能力矩阵先查
[step and batching](step-and-batching.md)，本页只拥有 scheduling wave 之前的 coalescing wait。

## DIFFADM-1a — Scheduler 决定 wait policy，Engine 只执行条件等待

- 触发：修改 diffusion busy loop、scheduler interface、request-wave batching、DP concurrent
  coalescing 或 admission wait 配置。
- 强制：Engine 持有 condition 和 monotonic clock，向 scheduler 请求一次内部
  `_AdmissionWaitDecision`，循环中只观测 waiting count、刷新 `stable_since`、调用
  `should_end_admission_wait()`，并用最多 2ms 的 condition wait 响应新请求/stop。Base/step/custom
  scheduler 默认 no-wait；`RequestScheduler` 才拥有 static-wave coalescing policy。
- 禁止：在 Engine 重新编码 request scheduler 的 max-batch/stability 规则；对 step scheduler
  默认等待；用 sleep 代替 condition wait；等待期间释放后不重新读取 scheduler 状态。
- 验收：mock scheduler 证明 Engine 遵从 policy；Base/Step 返回 no-wait；RequestScheduler 分别
  覆盖 disabled、active、已有 running wave、serial capacity、full batch、stable window、deadline
  与 stop_event。RPC/abort 唤醒和 shutdown 仍不能被 admission wait 饿死。^[PR #5843]

## DIFFADM-1b — RequestScheduler 的等待只为可扩大的空闲 wave

- 触发：修改 `request_batch_max_wait_ms`、`max_num_seqs`、DLO DP concurrent 或 request queue
  admission。
- 强制：仅当 max wait > 0、`max_num_running_reqs > 1` 且没有 running request 时等待。deadline
  为 start + max wait；普通稳定窗是 `min(50ms, max_wait/5)`，DP concurrent 是
  `min(300ms, max_wait/2)`。waiting 达 max batch、非空队列在稳定窗内不再增长、或到 deadline
  任一成立即结束。
- 禁止：serial capacity 仍付固定延迟；running wave 期间等下一批；把 DP 较长稳定窗应用到普通
  request batching；把 `max_num_seqs>1` 当成 pipeline 自动支持融合——能力 gate 仍在 Engine init，
  DLO DP concurrency 是现有例外。
- 验收：对普通/DP 两种稳定窗做精确 decision 测试，并证明每次 waiting count 增长都会重置
  `stable_since`。测试 fixture 构造真实 `RequestScheduler` 时必须显式提供
  `request_batch_max_wait_ms`，否则后台 busy loop 的 `AttributeError` 会伪装成超时。^[PR #5843]

## DIFFADM-1c — wait duration 与内部 decision 都要防止 non-finite hot spin

- 触发：CLI/config 接受 admission duration，或 scheduler extension 改 decision 数据结构。
- 强制：CLI argparse 与 `OmniDiffusionConfig.__post_init__` 都只接受 finite non-negative float；
  `nan`、正负 `inf` 和负数在启动边界拒绝。内部 decision 保持私有，缩小第三方构造无效状态的
  接口面。
- 禁止：只校验 `< 0`（`nan` 会穿透并令 condition timeout 退化成 hot poll）；只在 CLI 校验而
  放过 Python/config factory；重新公开 decision 却没有验证 finite deadline/stable window 和正
  max batch。
- 验收：Python config 与 CLI 都覆盖 `nan|inf|-inf|negative|zero|finite positive`；docs argparse
  extraction 必须为自定义 type 提供安全 stub。当前私有 `_AdmissionWaitDecision` 自身没有
  `__post_init__` invariant validation，安全性依赖 only-in-tree scheduler producer；若重新导出或
  开放 extension，须补 deadline/stability/max-batch 非法值测试。^[PR #5843]
