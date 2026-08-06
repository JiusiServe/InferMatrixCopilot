---
title: "AFD Attention runtime 入口"
created: 2026-08-06
updated: 2026-08-06
type: index
tags: [afd-plugin, components, attention-runtime]
sources:
  - "afd-plugin@a432692:docs/design/module/attention_runtime.md"
---

# AFD Attention runtime 入口

## 什么时候查这里

- 修改 Attention worker/model runner、API 请求执行、KV/sampling 边界或 AFD forward metadata 安装。
- 调查请求进入 Attention 后如何交给 FFN，以及 control-plane/async CAM 分流。

## 不放什么

- FFN daemon 生命周期放 [ffn-runtime](../ffn-runtime/_index.md)。
- payload/process group 放 [connectors](../connectors/_index.md)；graph 和 native ubatching 放 [execution-platforms](../execution-platforms/_index.md)。

## Owner 凭证

- 基线：`afd-plugin main @ a432692ed7d5dd6437a4755b530ee7aaf2685dad`。
- 主源码：`afd_plugin/v1/worker/attention_model_runner.py`、`attention_worker.py`、`ubatch_wrapper.py` 及 NPU 对应 Attention 文件。
- 职责：拥有外部请求、scheduler/KV/sampling 角色适配、AFD metadata 安装与 FFN handoff；不拥有 connector 通信资源或模型参数。
- 输入/输出：输入 vLLM scheduled batch 和 Attention role config；输出发往 FFN 的 stage/layer 工作与最终用户响应。
- 验证：`test_attention_model_runner.py`、`test_npu_runtime.py`、GPU/NPU serving、accuracy 和 async CAM E2E。
- 影响：请求调度、KV cache、模型 forward、connector control metadata 和输出路径。

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| 理解初始化、请求和 control metadata 流 | [architecture](architecture.md) | v0.26 当前运行实现 |
| 调查模型内 handoff | [model-integration](../model-integration/architecture.md) | 角色感知层构造和 metadata consumer |
| 调查 graph/DBO | [execution-platforms](../execution-platforms/architecture.md) | 平台 wrapper、capture 和 replay |
