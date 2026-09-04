---
title: "Diffusion worker observability rules"
created: 2026-09-05
updated: 2026-09-05
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #6722", vllm_omni/diffusion/worker/diffusion_worker.py, vllm_omni/diffusion/distributed/parallel_state.py, tests/diffusion/test_diffusion_worker_process_title.py, tests/diffusion/distributed/test_expert_parallel_layout.py]
confidence: high
---

# Diffusion worker observability rules

## DIFF-4w — worker title 与日志前缀必须共享已初始化的拓扑标识

- 触发：修改 `DiffusionWorker`/`WorkerProc` 启动、model-parallel 初始化、进程标题或日志装饰。
- 强制：early startup 保留通用 `DiffusionWorker`；`initialize_model_parallel()` 完成后、模型加载前，按 DP、PP、SP、CFG、TP、FS、RP、EP 顺序从 active group 的 `rank_in_group` 追加非 singleton 维度，并把同一名字同时交给 `set_process_title(..., prefix="vLLM-Omni")` 和 `decorate_logs()`。FS/RP 只在 HSDP 查询，RP 只在多 replica layout 查询；EP 只在 expert parallel enabled 时查询。
- 禁止：在 parallel state 可用前读 group；用 global rank 代替 topology local rank；让非 HSDP/非 EP 路径访问 FS/RP/EP；只更新 OS title 或日志之一；因 optional `setproctitle` 不可用让 worker 启动失败。
- 验收：覆盖初始化前 generic 名称且不读 group、singleton、省略规则、DP/PP/SP/CFG/TP、FS、multi-replica RP、conditional EP、缺少 `setproctitle` 仍装饰日志，以及 Linux `ps` 可见 title；本提交的验证边界为 unit/CPU Gloo，未提供本地 GPU 证据。^[PR #6722]
