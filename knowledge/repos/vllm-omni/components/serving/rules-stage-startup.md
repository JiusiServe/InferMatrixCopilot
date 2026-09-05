---
title: "Stage 启动与设备布局规则"
created: 2026-09-04
updated: 2026-09-04
type: rule
tags: [vllm-omni, components, serving]
sources: ["PR #6050", "PR #5445", "Issue #5003", "PR #5742", vllm_omni/engine/stage_init_utils.py, tests/engine/test_stage_device_layout.py]
confidence: high
---

# Stage 启动与设备布局规则

本页补充 [Serving 规则](rules.md) 的 stage 启动边界；stage 生命周期和子进程环境 scope
见 [engine 生命周期规则](rules-engine-lifecycle.md)。

## SERV-10a — stage config 到 EngineArgs 的投影必须显式且由 owner 进程物化

- 触发：修改 `stage_init_utils.py` 的 typed stage→`EngineArgs` projection、upstream config 字段映射或 stage startup 的终态配置构造。
- 强制：AR/generation 从 upstream config dataclass 与 `EngineArgs` 的交集生成 projection map，显式记录且只投影构造时提供的字段，并集中处理 `cache_dtype`→`kv_cache_dtype`、`policy`→`scheduling_policy`、`data_parallel_master_ip`→`data_parallel_address` 等 alias；`CompilationConfig`/`ProfilerConfig` 以具体 upstream object 复制传递，最终 `VllmConfig` 由 engine-owning process 物化，diffusion 保持既有固定 owner 与 projection surface。
- 禁止：维护会随 upstream schema 漂移的静态 allowlist；把 inherited defaults、runtime-owned `worker_cls`/`distributed_executor_backend`、topology-owned `scheduler_cls` 或 private API-process 字段静默送入 EngineArgs；显式提供但没有合法 projection 的字段不得被丢弃，也不得在 head process 解析设备、rank、端口或 backend。
- 验收：非默认 upstream 字段能在最终 EngineArgs 读回且 alias 正确，未显式提供的 inherited defaults 不出现；显式无 projection 字段抛出明确错误；typed projection 保留 compilation/profiler 的 concrete type，structured stage registration 可 msgpack 传输，并回归 legacy/structured effective parity。 ^[PR #6050]

## SERV-12a — 多副本 stage 省略 devices 时仍按 replica 数生成设备槽位

- 触发：修改 `split_devices_for_replicas()`、`compute_replica_layout()`、`StageRuntime._build_logical_stage_init_plans()`，或修改 stage 的 `num_replicas` 与可选 `devices` 语义。
- 强制：当 stage 未声明 `devices` 时，返回与有效 replica 数对应的 `None` 槽位（至少保留一个槽位），使 `replica_devices_map` 和启动计划可按每个 `replica_id` 索引；每个 replica 继承 launcher 的 `CUDA_VISIBLE_DEVICES`，显式设备配置继续按既有规则拆分。
- 禁止：因 `devices=None` 只返回单元素列表；让多副本 stage 的启动计划索引越界；将未声明设备误当成显式设备，或改变显式设备配置与既有 `ValueError` 语义。
- 验收：覆盖 1、2、4 副本的未声明设备拆分、三副本 `replica_devices_map` 以及 logical stage init plans 的全部 replica ID 和 `None` 设备值；回归显式设备拆分、模板/池模式及错误路径。^[PR #5445]

## SERV-12b — 显式 stage devices 必须在 worker 创建前匹配本地副本世界大小

- 触发：修改 `build_vllm_config()`、`_check_stage_device_layout()`、`get_stage_devices_per_replica()`、`split_devices_for_replicas()`、`compute_replica_layout()`，或修改 stage 的 `devices`、TP、DP、PP、`num_replicas` 解析与启动顺序。
- 强制：对声明 `runtime.devices` 的每个 LLM stage，在 `create_engine_config` 或 worker/executor 创建前，以同一公式验证并拆分设备：每个本地 replica 需要 `tensor_parallel_size × data_parallel_size_local × pipeline_parallel_size`；`data_parallel_size_local` 未设置时才回退到全局 DP，值为 `0` 的 head process 不做本地设备验证。显式列表可为单 replica template（恰为每副本大小）或完整 pool（该大小 × `num_replicas`）；未声明 `devices` 时保留 launcher 分配语义。仅当去掉 TP 后设备数恰好有效，错误才说明 top-level TP 会广播到全部 stage，并要求在每个 stage override 中一并设置 TP 与 `devices`；其他 TP/DP/PP/replica 不匹配给通用维度说明。
- 禁止：按集群全局 DP 校验本地 `runtime.devices`；让 guard 与 replica splitter 使用不同的每副本宽度；在 engine config/worker 启动后才暴露 `local rank ... out of bounds`；把 PP 或其他布局错误一律归因于 top-level TP；因为没有显式 devices 而拒绝 vLLM 的设备分配。
- 验收：覆盖 TP 广播的单卡 stage 在 engine-config/executor 前失败、匹配 TP/device 通过、未声明 devices 跳过、local-DP 小于 global-DP 与 local-DP=0、PP/local-DP 加多副本的 template 和 full-pool 拆分，以及 PP-only mismatch 不含 TP 专属 workaround。^[Issue #5003] ^[PR #5742]
