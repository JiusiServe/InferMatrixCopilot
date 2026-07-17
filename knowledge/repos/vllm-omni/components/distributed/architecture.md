---
title: "Distributed 共享架构"
created: 2026-07-16
updated: 2026-07-16
type: architecture
tags: [vllm-omni, components, distributed]
sources: [docs/design/feature/disaggregated_inference.md, vllm_omni/distributed/omni_connectors/connectors/base.py, vllm_omni/distributed/omni_connectors/factory.py, vllm_omni/distributed/omni_connectors/kv_transfer_manager.py, vllm_omni/engine/stage_engine_startup.py]
---

# Distributed 共享架构

以下事实在 `main @ 5c390096` 复核；官方叙述见
`docs/design/feature/disaggregated_inference.md` 与 `docs/design/feature/omni_connectors/` 逐后端 spec。

## Connector 合同

`OmniConnectorBase`（`connectors/base.py:12`）：抽象 `put(from_stage, to_stage,
put_key, data)` / `get(...)`；类属性 `supports_raw_data`（:18，默认 False）——RDMA
类后端置 True 以跳过 `OmniSerializer` 序列化。当前所有后端为 D2H2D
（device→host→device）模式。

## 六个后端与选择矩阵（factory.py 注册名）

| 场景 | 后端（注册名） | 备注 |
|---|---|---|
| 单机 | `SharedMemoryConnector`（:71） | 未指定 connector 时自动配置 |
| 跨机 TCP | `MooncakeStoreConnector`（:59） | 需 Mooncake Master + metadata server |
| 跨机 RDMA（最快） | `MooncakeTransferEngineConnector`（:106） | RDMA/TCP 直传 + 托管内存池 |
| 跨机 RDMA（Mori） | `MoriTransferEngineConnector`（:117) | Mori IOEngine |
| Yuanrong | `YuanrongConnector`（:83）/`YuanrongTransferEngineConnector`（:94） | 数据面/传输引擎两形态 |

## KV 迁移管理面

`OmniKVTransferManager`（`kv_transfer_manager.py:341`，同文件 `OmniKVCacheConfig`
:121）统一管理跨 stage 的 OmniConnector 与 KV cache 迁移（E/P/D/G 解耦部署中
connector 位于 stage 边界）。调度侧的"何时可发/何时就绪"合同
（`KVCacheTransferData`）在 [Scheduler](../scheduler/architecture.md)；数据面的
runner 挂点在 [Model Executor](../model-executor/architecture.md) 的
`OmniConnectorModelRunnerMixin`。chunk 流式传输的适配层在
`transfer_adapter/chunk_transfer_adapter.py`。

## 协调与负载均衡

`omni_coordinator/`：`OmniCoordinator` 接收 stage 副本事件；`load_balancer.py`
的 `LoadBalancer`（:39）三个实现——`RandomBalancer`（:64）、`RoundRobinBalancer`
（:74）、`LeastQueueLengthBalancer`（:102）——供 stage pool 的副本路由使用。

## ZMQ 路由与端口分配

每个 `(stage_id, replica_id)` 路由需要 3 个端口（handshake/input/output），由
`OmniMasterServer._allocate_route_locked`（`stage_engine_startup.py:254`）分配。
历史坑：跨路由端口未去重导致 flaky `EADDRINUSE`（详见
[connector pitfalls](connector-pitfalls.md)）。

源码会变化，具体类名和行号在改代码前必须以目标仓库当前版本为准。
