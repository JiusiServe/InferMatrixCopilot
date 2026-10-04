---
title: Agent、Code 与 Team 模式 的职责、接口与配置
created: 2026-10-01
updated: 2026-10-01
type: guide
tags:
- jiuwenswarm
sources:
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/mode_catalog.py
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/mode_matrix.py
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/模式系统.md
feature: "modes"
entry_points: ["jiuwenswarm/runtime/mode_catalog.py", "jiuwenswarm/common/mode_matrix.py"]
source_globs: ["jiuwenswarm/runtime/mode_catalog.py", "jiuwenswarm/common/mode_matrix.py", "jiuwenswarm/server/runtime/agent_adapter/*.py"]
---

# Agent、Code 与 Team 模式 的职责、接口与配置

本页是该功能的基本知识入口，基线 `f0a69728c96b`。它连接源码契约与上游功能文档；详细字段和行为仍沿固定引用核对。

<!-- kb:knowledge owner=feature-modes facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 职责与边界

运行模式决定 Agent 的装配、工具和交互能力。模式名称与具体 rail、工具和宿主后端之间存在映射，显示模式与实际装配需要共同查证。 本页记录入口职责与边界；逐文件的类型、函数和依赖关系见同 owner 的源码接口记录。

源码与文档：[jiuwenswarm/runtime/mode_catalog.py:L1–L111](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/mode_catalog.py#L1-L111)；[jiuwenswarm/common/mode_matrix.py:L1–L483](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mode_matrix.py#L1-L483)；[docs/zh/模式系统.md:L1–L263](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%A8%A1%E5%BC%8F%E7%B3%BB%E7%BB%9F.md#L1-L263)。

<!-- kb:knowledge owner=feature-modes facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 接口与调用入口（API）

可定位的实现声明包括 `ModeCatalogError`；`RuntimeModeDescriptor [to_dict]`；`ModeCatalogResult [to_dict]`；`list_mode_capabilities()`；`resolve_mode_capability(requested)`。这些是源码定位入口，具体公共用户操作沿功能文档查证；本页不把内部符号直接当成稳定 HTTP API。参数、返回类型、错误传播和生命周期应在所列实现与调用方一起核对。

源码与文档：[jiuwenswarm/runtime/mode_catalog.py:L1–L111](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/mode_catalog.py#L1-L111)；[jiuwenswarm/common/mode_matrix.py:L1–L483](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mode_matrix.py#L1-L483)；[docs/zh/模式系统.md:L1–L263](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%A8%A1%E5%BC%8F%E7%B3%BB%E7%BB%9F.md#L1-L263)。

<!-- kb:knowledge owner=feature-modes facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 配置入口与生效条件

上游 YAML 示例的配置键包括 `modes.agent.memory.enabled`、`modes.agent.rails`、`modes.agent.tools`、`modes.code.rails`、`modes.code.tools`、`modes.code.embedding_config.model_name`、`modes.code.embedding_config.base_url`、`modes.code.embedding_config.api_key`。这些是示例字段，不单独证明源码默认值或全部优先级。 修改设置时还要检查配置加载位置与本功能的装配或连接时机，不能只由“保存成功”判断当前运行实例已经采用新值。

源码与文档：[jiuwenswarm/runtime/mode_catalog.py:L1–L111](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/mode_catalog.py#L1-L111)；[jiuwenswarm/common/mode_matrix.py:L1–L483](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mode_matrix.py#L1-L483)；[docs/zh/模式系统.md:L1–L263](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%A8%A1%E5%BC%8F%E7%B3%BB%E7%BB%9F.md#L1-L263)。

<!-- kb:knowledge owner=feature-modes facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 设计取舍

**设计推断**：canonical 模式统一运行时表示，兼容旧别名以降低客户端迁移成本；代价是 UI 名称、入口参数和实际工具装配需要经过归一化才能比较。plan 与普通执行能力有不同限制，模式切换必须核对宿主支持和会话生效边界。以上分析从所列接口与功能边界得出，不宣称作者曾评估所有替代方案。

源码与文档：[jiuwenswarm/runtime/mode_catalog.py:L1–L111](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/mode_catalog.py#L1-L111)；[jiuwenswarm/common/mode_matrix.py:L1–L483](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mode_matrix.py#L1-L483)；[docs/zh/模式系统.md:L1–L263](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%A8%A1%E5%BC%8F%E7%B3%BB%E7%BB%9F.md#L1-L263)。

<!-- kb:knowledge owner=feature-modes facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 数据流与关联功能

运行模式决定 Agent 的装配、工具和交互能力。模式名称与具体 rail、工具和宿主后端之间存在映射，显示模式与实际装配需要共同查证。 联调时结合[Agent Loop 与 Rail 装配](feature-harness.md)、[工具权限与安全治理](feature-permissions.md)、[Code 模式编码记忆](feature-coding-memory.md)的入口、数据归属和生效条件查证；这些关联页解释不同阶段，不能只凭一项成功判定整个链路完成。

源码与文档：[jiuwenswarm/runtime/mode_catalog.py:L1–L111](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/mode_catalog.py#L1-L111)；[jiuwenswarm/common/mode_matrix.py:L1–L483](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mode_matrix.py#L1-L483)；[docs/zh/模式系统.md:L1–L263](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%A8%A1%E5%BC%8F%E7%B3%BB%E7%BB%9F.md#L1-L263)。

<!-- kb:knowledge owner=feature-modes facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 怎样验证

分别提交旧别名与 canonical 模式，核对返回模式和实际工具、权限、记忆配置。验证不支持的模式组合与 plan 入口条件，并检查模式切换后的 rail 卸载与重新装配。这些是建议的验收步骤，本页没有记录上游运行测试已执行或已通过。

源码与文档：[jiuwenswarm/runtime/mode_catalog.py:L1–L111](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/mode_catalog.py#L1-L111)；[jiuwenswarm/common/mode_matrix.py:L1–L483](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mode_matrix.py#L1-L483)；[docs/zh/模式系统.md:L1–L263](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%A8%A1%E5%BC%8F%E7%B3%BB%E7%BB%9F.md#L1-L263)。
