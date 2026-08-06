---
title: "AFD model integration 入口"
created: 2026-08-06
updated: 2026-08-06
type: index
tags: [afd-plugin, components, model-integration, model-executor]
sources:
  - "afd-plugin@a432692:docs/design/module/model_integration.md"
---

# AFD model integration 入口

## 什么时候查这里

- 修改 AFD model registry alias、角色感知模块构造/权重加载、forward-context metadata 或 DeepSeek MoE handoff。
- 调查 Attention/FFN 为什么加载不同参数，或 gate 放置、dense/MoE 分流、async CAM 数据流。

## 不放什么

- worker 生命周期放 [Attention](../attention-runtime/_index.md) / [FFN](../ffn-runtime/_index.md)。
- connector payload/resource 放 [connectors](../connectors/_index.md)；DBO/graph yield 机制放 [execution-platforms](../execution-platforms/_index.md)。

## Owner 凭证

- 基线：`afd-plugin main @ a432692ed7d5dd6437a4755b530ee7aaf2685dad`。
- 主源码：`afd_plugin/model_executor/**`。
- 职责：模型注册、role-aware construction/loading、AFD metadata access 和 model-side Attention↔FFN 计算。
- 输入/输出：输入 checkpoint architecture、AFD role/config、forward metadata 和 connector payload；输出角色所需模块/参数与匹配的 hidden states/FFN result。
- 验证：`tests/unit/model_executor/**`、connector experts contract、GPU/NPU model 和 accuracy E2E。
- 影响：模型加载内存、MoE gate/experts、forward context、connector transfer 和精度。

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| 理解 registry、角色构造、metadata 和权重加载 | [architecture](architecture.md) | DeepSeek-oriented 当前实现 |
| 调查 caller 生命周期 | [Attention](../attention-runtime/architecture.md) / [FFN](../ffn-runtime/architecture.md) | runner-owned context 和 step |
| 调查 transfer state | [connectors](../connectors/architecture.md) | payload/context 与资源 owner |
