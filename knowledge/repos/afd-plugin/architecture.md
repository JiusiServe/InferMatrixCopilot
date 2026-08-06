---
title: "AFD plugin 仓库架构"
created: 2026-08-06
updated: 2026-08-06
type: architecture
tags: [afd-plugin, components]
sources:
  - "afd-plugin@a432692:README.md"
  - "afd-plugin@a432692:docs/design/module/index.md"
  - "afd-plugin@a432692:afd_plugin/**"
confidence: medium
---

# AFD plugin 仓库架构

## 职责和边界

AFD plugin 是 vLLM 的 Attention-FFN Disaggregation 外部插件。它拥有插件注册、AFD 配置、角色 worker/model runner、模型包装、connector、平台机制和窄兼容层；vLLM 仍拥有 API scheduler、基础设备初始化、KV cache 和普通输出路径。AFD 不修改 vLLM 源码树。

当前上游设计中只有 [plugin-boundary](components/plugin-boundary/_index.md) 标为 normative；其他模块设计仍是 draft。因此本页和各 component architecture 记录 `a432692` 的 v0.26 工作实现，不把 draft payload、factory、metadata 或 work-item surface 提升为长期扩展 API。

## 主要入口和依赖方向

```text
vllm.general_plugins -> register_afd()
  -> config / validation / worker selection
  -> Attention runtime ----+
  -> FFN runtime ----------+--> connectors --> CUDA / Ascend mechanisms
  -> model registration ---+--> model integration
  -> compatibility patches ----> pinned vLLM / vLLM-Ascend behavior
```

- [Plugin boundary](components/plugin-boundary/architecture.md) 是 CPU-safe 最低共享层。
- [Attention runtime](components/attention-runtime/architecture.md) 接收外部请求并保留 scheduler、KV 和输出职责。
- [FFN runtime](components/ffn-runtime/architecture.md) 是 connector 驱动的计算 daemon，不接收用户请求。
- [Connectors](components/connectors/architecture.md) 拥有跨角色传输、拓扑和通信资源。
- [Model integration](components/model-integration/architecture.md) 拥有角色感知构造、权重加载和前向计算。
- [Execution platforms](components/execution-platforms/architecture.md) 隔离 CUDA/Ascend graph、DBO/ubatching、profiling 和 native ops。
- [Compatibility](components/compatibility/architecture.md) 只适配受支持上游，不是 AFD-owned 功能的 catch-all。

## 数据怎样流动

1. vLLM 通过 `vllm.general_plugins` 调用 `register_afd()`，AFD 配置位于 `VllmConfig.additional_config["afd"]`。
2. 配置规范化按平台和 `role` 选择 Attention 或 FFN worker，并在创建通信资源前拒绝非法拓扑、connector 和 class path。
3. Attention 接收 API 请求，沿原生 scheduler/KV 路径构建 batch，把 AFD metadata 放入 `ForwardContext.additional_kwargs`。
4. 角色感知模型在拆分层完成 Attention 计算，经 connector 把 hidden states 和 transfer context 交给 FFN。
5. FFN daemon 计算 MLP/MoE 并返回结果；Attention 继续后续层、sampling 和用户响应。
6. runner 关闭 graph/profiler，connector 释放 process group 和 communicator，剩余设备/workspace teardown 仍由匹配上游 runtime 负责。

## 怎样验证

先运行 [仓库默认门禁](rules.md)，再按 [components 索引](components/_index.md) 选 focused unit tests。只有修改跨角色、connector、模型或平台行为时，才追加对应 GPU/NPU E2E 和精度证据。
