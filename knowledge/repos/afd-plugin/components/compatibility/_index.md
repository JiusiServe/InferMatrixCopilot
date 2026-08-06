---
title: "AFD compatibility 入口"
created: 2026-08-06
updated: 2026-08-06
type: index
tags: [afd-plugin, components, compatibility]
sources:
  - "afd-plugin@a432692:docs/design/module/compatibility_and_patches.md"
---

# AFD compatibility 入口

## 什么时候查这里

- 升级 vLLM/vLLM-Ascend，新增或刷新 monkey patch，修改 patch guard、应用时机或 non-AFD 分支。
- 调查最佳努力 patch 未安装、重复包装、版本警告或 NPU runtime adapter 行为。

## 不放什么

- CUDA/Ascend graph、DBO、profiler 和 native op 机制放 [execution-platforms](../execution-platforms/_index.md)。
- AFD-owned 角色、模型或 connector 功能不能因为便于 hook 而放进 compatibility。

## Owner 凭证

- 基线：`afd-plugin main @ a432692ed7d5dd6437a4755b530ee7aaf2685dad`。
- 主源码：`afd_plugin/compat/{__init__,vllm}.py`、`compat/npu/{__init__,feature_validation,runtime,runtime_config}.py`、`compat/patches/**`。
- 输入：上游版本/符号、AFD role/config 与已初始化的平台模块。
- 输出：版本受限的 upstream 行为适配，且 non-AFD 分支保留固定上游语义。
- 验证：`tests/unit/compat/**`、package/classpath tests、`test_npu_runtime.py`、`test_npu_mla_graph.py`。
- 影响：全局 vLLM 符号、EngineCore、config normalization 和 Ascend worker startup。

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| 理解 patch 库存和应用生命周期 | [architecture](architecture.md) | v0.26 当前实现 |
| 审查新 patch 或上游升级 | [rules](rules.md) | upstream-first 和 API drift 门禁 |
| 核对入口延迟加载 | [plugin-boundary](../plugin-boundary/architecture.md) | 通用注册与 Ascend bootstrap 分层 |
