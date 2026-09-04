---
title: "Diffusion worker observability rules"
created: 2026-09-05
updated: 2026-09-05
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #6307", vllm_omni/diffusion/worker/diffusion_worker.py, tests/diffusion/test_diffusion_worker_process_title.py]
confidence: high
---

# Diffusion worker observability rules

## DIFF-4o — worker 进程标题和日志前缀必须来自同一已初始化拓扑

- 触发：修改 `DiffusionWorker`/`WorkerProc` 启动、model-parallel 初始化，或 worker 的进程标题和日志装饰。
- 强制：early startup 先用通用 `DiffusionWorker` 标识；`initialize_model_parallel()` 完成后、模型加载前再次从 active group 生成同一个标识并同时交给 upstream `set_process_title(..., prefix="vLLM-Omni")` 与 `decorate_logs()`。按 DP、PP、SP、CFG、TP、FS（HSDP）顺序附加非 singleton group 的 `_<AXIS><rank_in_group>`；仅在 expert parallel enabled 时查询 EP 并附加它。所有 singleton 维度省略。
- 禁止：用 global rank 代替局部 topology rank；在 parallel state 可用前读取 group；仅更新 OS title 或仅更新日志前缀；因 optional `setproctitle` 缺失让 worker 启动失败；把该可观测性改动描述为 scheduling、通信、模型输出或性能路径变化。
- 验收：覆盖初始化前 generic 名称及不读取 group、singleton、DP/PP/SP/CFG/TP、standalone FS/HSDP、conditional EP、缺少 `setproctitle` 仍装饰日志，以及 Linux `ps` 可见 title；冷启动 `ps` polling 要有足够 wall-clock budget，避免 import 延迟造成 flaky test。此状态的 `get_fs_group` 依赖在随后 parallel-state 改版中会不兼容，属于本提交之后的边界，不能回写为本提交未实现。^[PR #6307]
