---
title: Agent Loop 与 Rail 装配 的职责、接口与配置
created: 2026-10-01
updated: 2026-10-01
type: guide
tags:
- jiuwenswarm
sources:
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_deep.py
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/Harness.md
---

# Agent Loop 与 Rail 装配 的职责、接口与配置

本页是该功能的基本知识入口，基线 `f0a69728c96b`。它连接源码契约与上游功能文档；详细字段和行为仍沿固定引用核对。

<!-- kb:knowledge owner=feature-harness facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 职责与边界

Harness 通过 Agent 循环、工具与生命周期 rail 组合运行行为。一个能力是否可用取决于装配参数、宿主 backend、权限与运行环境。 本页记录入口职责与边界；逐文件的类型、函数和依赖关系见同 owner 的源码接口记录。

源码与文档：[jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L1–L19672](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L1-L19672)；[docs/zh/Harness.md:L1–L626](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Harness.md#L1-L626)。

<!-- kb:knowledge owner=feature-harness facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 接口与调用入口（API）

可定位的实现声明包括 `get_runtime_tool_session_id()`；`init_permission_engine()`；`build_model_from_entry(mcc, mco)`；`parse_int(value, default)`；`parse_optional_int(value)`。这些是源码定位入口，具体公共用户操作沿功能文档查证；本页不把内部符号直接当成稳定 HTTP API。参数、返回类型、错误传播和生命周期应在所列实现与调用方一起核对。

源码与文档：[jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L1–L19672](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L1-L19672)；[docs/zh/Harness.md:L1–L626](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Harness.md#L1-L626)。

<!-- kb:knowledge owner=feature-harness facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 配置入口与生效条件

 实现中直接读取的环境变量名称包括 `PLAYWRIGHT_RUNTIME_MCP_ENABLED`、`BROWSER_RUNTIME_MCP_ENABLED`、`BROWSER_DRIVER`、`VISION_API_KEY`、`VISION_BASE_URL`；名称与实际部署值分开核对。 修改设置时还要检查配置加载位置与本功能的装配或连接时机，不能只由“保存成功”判断当前运行实例已经采用新值。

源码与文档：[jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L1–L19672](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L1-L19672)；[docs/zh/Harness.md:L1–L626](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Harness.md#L1-L626)。

<!-- kb:knowledge owner=feature-harness facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 设计取舍

**设计推断**：Rail 按生命周期组合规划、权限、上下文和工具，便于独立扩展执行能力；代价是注册顺序、重复注册、卸载和宿主服务注入会影响组合效果。源码有 Rail 类型并不代表当前模式或已安装 agent-core 提供了该能力。以上分析从所列接口与功能边界得出，不宣称作者曾评估所有替代方案。

源码与文档：[jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L1–L19672](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L1-L19672)；[docs/zh/Harness.md:L1–L626](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Harness.md#L1-L626)。

<!-- kb:knowledge owner=feature-harness facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 数据流与关联功能

Harness 通过 Agent 循环、工具与生命周期 rail 组合运行行为。一个能力是否可用取决于装配参数、宿主 backend、权限与运行环境。 联调时结合[Agent、Code 与 Team 模式](feature-modes.md)、[生命周期 Hooks 与扩展](../extensions-plugins/feature-hooks.md)、[子代理派发与验证](../agents-team/feature-subagents.md)的入口、数据归属和生效条件查证；这些关联页解释不同阶段，不能只凭一项成功判定整个链路完成。

源码与文档：[jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L1–L19672](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L1-L19672)；[docs/zh/Harness.md:L1–L626](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Harness.md#L1-L626)。

<!-- kb:knowledge owner=feature-harness facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 怎样验证

用最小 Agent 跑一轮模型与工具调用，核对生命周期事件和工具集合。按模式验证 rail 装配与卸载，覆盖缺少 backend、依赖版本不匹配及重复注册；再检查取消后的工具和资源清理。这些是建议的验收步骤，本页没有记录上游运行测试已执行或已通过。

源码与文档：[jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L1–L19672](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L1-L19672)；[docs/zh/Harness.md:L1–L626](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Harness.md#L1-L626)。
