---
title: 上下文压缩与卸载 的职责、接口与配置
created: 2026-10-01
updated: 2026-10-01
type: guide
tags:
- jiuwenswarm
sources:
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_deep.py
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/上下文压缩.md
feature: "context"
entry_points: ["jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py", "jiuwenswarm/server/runtime/agent_adapter/interface_deep.py"]
source_globs: ["jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py", "jiuwenswarm/server/runtime/agent_adapter/interface_deep.py", "jiuwenswarm/agents/harness/common/*"]
---

# 上下文压缩与卸载 的职责、接口与配置

本页是该功能的基本知识入口，基线 `f0a69728c96b`。它连接源码契约与上游功能文档；详细字段和行为仍沿固定引用核对。

<!-- kb:knowledge owner=feature-context facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 职责与边界

上下文管理减少长对话的输入负担。压缩摘要和工具结果卸载具有不同的可恢复性，不能承诺所有被压缩的信息都能通过卸载索引取回。 本页记录入口职责与边界；逐文件的类型、函数和依赖关系见同 owner 的源码接口记录。

源码与文档：[jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py:L1–L201](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py#L1-L201)；[jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L1–L19672](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L1-L19672)；[docs/zh/上下文压缩.md:L1–L380](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E4%B8%8A%E4%B8%8B%E6%96%87%E5%8E%8B%E7%BC%A9.md#L1-L380)。

<!-- kb:knowledge owner=feature-context facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 接口与调用入口（API）

此入口通过模块装配和客户端协议参与功能。这些是源码定位入口，具体公共用户操作沿功能文档查证；本页不把内部符号直接当成稳定 HTTP API。参数、返回类型、错误传播和生命周期应在所列实现与调用方一起核对。

源码与文档：[jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py:L1–L201](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py#L1-L201)；[jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L1–L19672](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L1-L19672)；[docs/zh/上下文压缩.md:L1–L380](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E4%B8%8A%E4%B8%8B%E6%96%87%E5%8E%8B%E7%BC%A9.md#L1-L380)。

<!-- kb:knowledge owner=feature-context facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 配置入口与生效条件

上游 YAML 示例的配置键包括 `react.context_engine_config.enabled`、`react.context_engine_config.enable_reload`、`react.context_engine_config.message_summary_offloader_config.messages_threshold`、`react.context_engine_config.message_summary_offloader_config.tokens_threshold`、`react.context_engine_config.message_summary_offloader_config.large_message_threshold`、`react.context_engine_config.message_summary_offloader_config.offload_message_type`、`react.context_engine_config.message_summary_offloader_config.messages_to_keep`、`react.context_engine_config.message_summary_offloader_config.keep_last_round`。这些是示例字段，不单独证明源码默认值或全部优先级。 修改设置时还要检查配置加载位置与本功能的装配或连接时机，不能只由“保存成功”判断当前运行实例已经采用新值。

源码与文档：[jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py:L1–L201](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py#L1-L201)；[jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L1–L19672](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L1-L19672)；[docs/zh/上下文压缩.md:L1–L380](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E4%B8%8A%E4%B8%8B%E6%96%87%E5%8E%8B%E7%BC%A9.md#L1-L380)。

<!-- kb:knowledge owner=feature-context facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 设计取舍

**设计推断**：普通摘要压缩减少上下文开销但有信息损失；大工具消息卸载保留索引可检索，代价是磁盘内容与 OFFLOAD 标记需要保持一致。两类机制的可恢复性不同，不能承诺普通压缩后的全部细节还能召回。以上分析从所列接口与功能边界得出，不宣称作者曾评估所有替代方案。

源码与文档：[jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py:L1–L201](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py#L1-L201)；[jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L1–L19672](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L1-L19672)；[docs/zh/上下文压缩.md:L1–L380](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E4%B8%8A%E4%B8%8B%E6%96%87%E5%8E%8B%E7%BC%A9.md#L1-L380)。

<!-- kb:knowledge owner=feature-context facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 数据流与关联功能

上下文管理减少长对话的输入负担。压缩摘要和工具结果卸载具有不同的可恢复性，不能承诺所有被压缩的信息都能通过卸载索引取回。 联调时结合[Agent Loop 与 Rail 装配](feature-harness.md)、[长期记忆](../agents-team/feature-memory.md)、[Debug Dump 与 OTel](../observability/feature-debug-trace.md)的入口、数据归属和生效条件查证；这些关联页解释不同阶段，不能只凭一项成功判定整个链路完成。

源码与文档：[jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py:L1–L201](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py#L1-L201)；[jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L1–L19672](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L1-L19672)；[docs/zh/上下文压缩.md:L1–L380](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E4%B8%8A%E4%B8%8B%E6%96%87%E5%8E%8B%E7%BC%A9.md#L1-L380)。

<!-- kb:knowledge owner=feature-context facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 怎样验证

构造长会话与大工具结果，分别触发摘要压缩和卸载，检查下一轮上下文与 OFFLOAD 检索。覆盖禁用、阈值边界和丢失卸载文件，验证用户关键要求保留并清楚区分不可召回的摘要内容。这些是建议的验收步骤，本页没有记录上游运行测试已执行或已通过。

源码与文档：[jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py:L1–L201](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py#L1-L201)；[jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L1–L19672](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L1-L19672)；[docs/zh/上下文压缩.md:L1–L380](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E4%B8%8A%E4%B8%8B%E6%96%87%E5%8E%8B%E7%BC%A9.md#L1-L380)。
