---
title: "AFD connectors 入口"
created: 2026-08-06
updated: 2026-08-06
type: index
tags: [afd-plugin, components, connectors, distributed]
sources:
  - "afd-plugin@a432692:docs/design/module/connector_contracts.md"
---

# AFD connectors 入口

## 什么时候查这里

- 修改 connector factory/base、payload、topology、process group、control plane 或 CUDA/CAM/CAMP2P transport。
- 调查 rank 映射、同步/异步 step 选择、pending state、partial-init cleanup 或跨 role 失败。

## 不放什么

- worker daemon 生命周期放 [ffn-runtime](../ffn-runtime/_index.md)；请求协调放 [attention-runtime](../attention-runtime/_index.md)。
- graph、DBO、native op build 和 profiler 放 [execution-platforms](../execution-platforms/_index.md)。

## Owner 凭证

- 基线：`afd-plugin main @ a432692ed7d5dd6437a4755b530ee7aaf2685dad`。
- 主源码：`afd_plugin/connectors/**`、`afd_plugin/distributed/**`。
- 职责：factory/schema、world/rank 映射、control/data plane、payload/state 和 connector-owned communication 资源。
- 输入/输出：输入 AFD config、role rank、stage/layer tensor/context；输出跨 role payload、work item 或匹配的 FFN result。
- 验证：`tests/unit/connectors/**`、`tests/unit/distributed/**`、GPU/NPU TP 和 async CAM E2E。
- 影响：Attention/FFN 协调、graph shape state、进程组、communicator 和 shutdown。

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| 理解 factory、拓扑、payload 和生命周期 | [architecture](architecture.md) | 三类 connector 当前合同 |
| 核对 role runtime 如何消费 control/work item | [Attention](../attention-runtime/architecture.md) / [FFN](../ffn-runtime/architecture.md) | caller 生命周期 |
| 核对平台支持组合 | [execution-platforms](../execution-platforms/architecture.md) | graph/DBO/quantization 矩阵 |
