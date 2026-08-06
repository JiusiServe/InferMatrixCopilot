---
title: "AFD execution platforms 入口"
created: 2026-08-06
updated: 2026-08-06
type: index
tags: [afd-plugin, components, execution-platforms]
sources:
  - "afd-plugin@a432692:docs/design/module/execution_platforms.md"
---

# AFD execution platforms 入口

## 什么时候查这里

- 修改 CUDA/Ascend worker 平台机制、CUDA/ACL Graph、DBO/ubatching、forward context、profiler、native op 或 build/package。
- 调查 graph key/state、stream/context 恢复、MLA Full Graph、CANN op 可用性或当前 connector 支持组合。

## 不放什么

- connector topology/process group 放 [connectors](../connectors/_index.md)。
- 全局 upstream 符号替换和 patch guard 放 [compatibility](../compatibility/_index.md)。

## Owner 凭证

- 基线：`afd-plugin main @ a432692ed7d5dd6437a4755b530ee7aaf2685dad`。
- 主源码：`compat/profiler.py`、`compat/npu/{forward_context,ops,profiler}.py`、`v1/worker/{cuda_graph,dbo}.py`、`v1/worker/npu/{forward_context,mla_graph,npu_ubatch_wrapper,ubatch_utils,ubatching}.py`、`csrc/**`、`setup.py`、`MANIFEST.in`。
- 职责：平台 class 策略、graph/DBO 协调、stream/context、profiler、native operator discovery/build/package。
- 输入/输出：输入 AFD role/config、stage token metadata 和 connector state；输出平台 forward context、graph cache/replay、ubatch 结果和 native op 调用。
- 验证：graph/DBO/NPU MLA/runtime、profiler、Ascend ops/build 单测与匹配硬件 E2E。
- 影响：两个 role、connector shape/control state、设备内存、性能和打包产物。

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| 理解 CUDA/Ascend、graph/DBO、MLA 和 native op | [architecture](architecture.md) | v0.26 当前平台矩阵 |
| 调查 connector state 来源 | [connectors](../connectors/architecture.md) | control/data plane 和资源 owner |
| 审查 Ascend global patch | [compatibility](../compatibility/rules.md) | upstream-first 与 non-AFD 回归 |
