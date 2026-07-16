---
title: "Distributed（跨 stage 通信与数据搬运）"
created: 2026-07-16
updated: 2026-07-16
type: index
tags: [vllm-omni, components, distributed]
sources: [vllm_omni/distributed/omni_connectors/, vllm_omni/distributed/omni_coordinator/, docs/design/feature/disaggregated_inference.md]
---

# Distributed（跨 stage 通信与数据搬运）

- 源码入口：`vllm_omni/distributed/omni_connectors/`（`connectors/` 6 个后端、
  `factory.py`、`kv_transfer_manager.py`、`transfer_adapter/`、`utils/`）和
  `vllm_omni/distributed/omni_coordinator/`（协调器与 load balancer）
- 知识面另覆盖跨 stage ZMQ 路由/端口分配（`vllm_omni/engine/stage_engine_startup.py::OmniMasterServer`）
  ——组件划分服务知识归属，与 manifest 运行时粒度不同
- 源码校验：以上路径与下列锚点均已在 `main @ 5c390096` 验证存在：
  `OmniConnectorBase`（connectors/base.py:12）、`OmniKVTransferManager`
  （kv_transfer_manager.py:341）、`LoadBalancer` 三实现（load_balancer.py:39/64/74/102）、
  `OmniMasterServer._allocate_route_locked`（stage_engine_startup.py:254）
- 官方设计文档：`docs/design/feature/disaggregated_inference.md` +
  `docs/design/feature/omni_connectors/`（逐后端 spec）
- 测试入口：`tests/distributed/`

## 什么时候查这里

- 跨 stage 数据传不动、损坏、乱序或 `Address already in use` 类启动失败。
- 选择/配置 connector 后端（单机 SHM、跨机 Mooncake/Mori/Yuanrong）。
- 排查 KV cache 跨 stage 迁移的数据面（`OmniKVTransferManager`）。

## 不放什么

- 调度侧的 KV/输入等待状态机属于 [Scheduler](../scheduler/_index.md)。
- 请求编排与 stage 生命周期属于 [Serving](../serving/_index.md)。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 理解 connector 合同、6 后端、KV 迁移管理与负载均衡 | [architecture](architecture.md) |
| 已修过的 connector/端口产品坑 | [connector pitfalls](connector-pitfalls.md) |
