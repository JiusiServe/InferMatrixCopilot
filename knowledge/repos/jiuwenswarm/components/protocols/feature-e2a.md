---
title: E2A 统一请求响应协议 的职责、接口与配置
created: 2026-10-01
updated: 2026-10-01
type: guide
tags:
- jiuwenswarm
sources:
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/e2a/models.py
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/E2A-protocol.md
---

# E2A 统一请求响应协议 的职责、接口与配置

本页是该功能的基本知识入口，基线 `f0a69728c96b`。它连接源码契约与上游功能文档；详细字段和行为仍沿固定引用核对。

<!-- kb:knowledge owner=feature-e2a facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 职责与边界

统一信封保留请求身份、方法与参数，并用响应结构承载流式和最终结果。外部协议投影与内部业务方法有不同的命名和状态边界。 本页记录入口职责与边界；逐文件的类型、函数和依赖关系见同 owner 的源码接口记录。

源码与文档：[jiuwenswarm/common/e2a/models.py:L1–L492](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/e2a/models.py#L1-L492)；[docs/zh/E2A-protocol.md:L1–L404](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/E2A-protocol.md#L1-L404)。

<!-- kb:knowledge owner=feature-e2a facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 接口与调用入口（API）

可定位的实现声明包括 `utc_now_iso()`；`IdentityOrigin`；`E2AProvenance`；`E2AFileRef`；`E2AAuth`。这些是源码定位入口，具体公共用户操作沿功能文档查证；本页不把内部符号直接当成稳定 HTTP API。参数、返回类型、错误传播和生命周期应在所列实现与调用方一起核对。

源码与文档：[jiuwenswarm/common/e2a/models.py:L1–L492](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/e2a/models.py#L1-L492)；[docs/zh/E2A-protocol.md:L1–L404](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/E2A-protocol.md#L1-L404)。

<!-- kb:knowledge owner=feature-e2a facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 配置入口与生效条件

该源码入口的构造或调用参数包括 `envelope`；它们是调用参数，不自动等同于全仓持久配置键。 修改设置时还要检查配置加载位置与本功能的装配或连接时机，不能只由“保存成功”判断当前运行实例已经采用新值。

源码与文档：[jiuwenswarm/common/e2a/models.py:L1–L492](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/e2a/models.py#L1-L492)；[docs/zh/E2A-protocol.md:L1–L404](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/E2A-protocol.md#L1-L404)。

<!-- kb:knowledge owner=feature-e2a facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 设计取舍

**设计推断**：E2A 在 Gateway 后统一请求身份与业务载荷，减少每个 AgentServer 入口理解原始平台 JSON 的负担；代价是协议映射必须保留关联与来源。业务 method 与 ACP 线路 method 有不同含义，兼容字段迁移不能丢失原始请求语义。以上分析从所列接口与功能边界得出，不宣称作者曾评估所有替代方案。

源码与文档：[jiuwenswarm/common/e2a/models.py:L1–L492](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/e2a/models.py#L1-L492)；[docs/zh/E2A-protocol.md:L1–L404](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/E2A-protocol.md#L1-L404)。

<!-- kb:knowledge owner=feature-e2a facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 数据流与关联功能

统一信封保留请求身份、方法与参数，并用响应结构承载流式和最终结果。外部协议投影与内部业务方法有不同的命名和状态边界。 联调时结合[A2A 接入与 AgentCard](feature-a2a.md)、[ACP 与 stdio 桥接](feature-acp.md)、[Web 对话与流式状态](../web-frontend/feature-web-chat.md)的入口、数据归属和生效条件查证；这些关联页解释不同阶段，不能只凭一项成功判定整个链路完成。

源码与文档：[jiuwenswarm/common/e2a/models.py:L1–L492](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/e2a/models.py#L1-L492)；[docs/zh/E2A-protocol.md:L1–L404](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/E2A-protocol.md#L1-L404)。

<!-- kb:knowledge owner=feature-e2a facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 怎样验证

用 Web、ACP 和平台消息构造同一业务请求，核对规范化后的身份、params、来源与响应关联。覆盖旧 metadata 兼容、序列化往返、流式和最终结果，检查 method 映射不混用协议层名称。这些是建议的验收步骤，本页没有记录上游运行测试已执行或已通过。

源码与文档：[jiuwenswarm/common/e2a/models.py:L1–L492](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/e2a/models.py#L1-L492)；[docs/zh/E2A-protocol.md:L1–L404](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/E2A-protocol.md#L1-L404)。
