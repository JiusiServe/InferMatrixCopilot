---
title: ACP 与 stdio 桥接 的职责、接口与配置
created: 2026-10-01
updated: 2026-10-01
type: guide
tags:
- jiuwenswarm
sources:
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/acp/stdio_client.py
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/ACP插件使用.md
---

# ACP 与 stdio 桥接 的职责、接口与配置

本页是该功能的基本知识入口，基线 `f0a69728c96b`。它连接源码契约与上游功能文档；详细字段和行为仍沿固定引用核对。

<!-- kb:knowledge owner=feature-acp facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 职责与边界

ACP 进程桥接负责外部请求、子进程环境和协议消息。stdio 线路协议与 Runtime 会话操作属于不同层，调试时应保留请求关联和取消语义。 本页记录入口职责与边界；逐文件的类型、函数和依赖关系见同 owner 的源码接口记录。

源码与文档：[jiuwenswarm/acp/stdio_client.py:L1–L13](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/acp/stdio_client.py#L1-L13)；[docs/zh/ACP插件使用.md:L1–L146](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/ACP%E6%8F%92%E4%BB%B6%E4%BD%BF%E7%94%A8.md#L1-L146)。

<!-- kb:knowledge owner=feature-acp facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 接口与调用入口（API）

此入口通过模块装配和客户端协议参与功能。这些是源码定位入口，具体公共用户操作沿功能文档查证；本页不把内部符号直接当成稳定 HTTP API。参数、返回类型、错误传播和生命周期应在所列实现与调用方一起核对。

源码与文档：[jiuwenswarm/acp/stdio_client.py:L1–L13](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/acp/stdio_client.py#L1-L13)；[docs/zh/ACP插件使用.md:L1–L146](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/ACP%E6%8F%92%E4%BB%B6%E4%BD%BF%E7%94%A8.md#L1-L146)。

<!-- kb:knowledge owner=feature-acp facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 配置入口与生效条件

 文档中的调用选项包括 `--python`，适用命令与前置条件沿文档确认。 修改设置时还要检查配置加载位置与本功能的装配或连接时机，不能只由“保存成功”判断当前运行实例已经采用新值。

源码与文档：[jiuwenswarm/acp/stdio_client.py:L1–L13](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/acp/stdio_client.py#L1-L13)；[docs/zh/ACP插件使用.md:L1–L146](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/ACP%E6%8F%92%E4%BB%B6%E4%BD%BF%E7%94%A8.md#L1-L146)。

<!-- kb:knowledge owner=feature-acp facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 设计取舍

**设计推断**：stdio 桥接让 IDE 复用本地 Gateway，无需额外 Agent 引擎；代价是子进程环境、线路消息与 Gateway 会话都需要正确启动。stdout 的协议消息和日志输出必须分开，主进程未就绪时不能由 IDE 插件安装成功推断连接已可用。以上分析从所列接口与功能边界得出，不宣称作者曾评估所有替代方案。

源码与文档：[jiuwenswarm/acp/stdio_client.py:L1–L13](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/acp/stdio_client.py#L1-L13)；[docs/zh/ACP插件使用.md:L1–L146](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/ACP%E6%8F%92%E4%BB%B6%E4%BD%BF%E7%94%A8.md#L1-L146)。

<!-- kb:knowledge owner=feature-acp facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 数据流与关联功能

ACP 进程桥接负责外部请求、子进程环境和协议消息。stdio 线路协议与 Runtime 会话操作属于不同层，调试时应保留请求关联和取消语义。 联调时结合[E2A 统一请求响应协议](feature-e2a.md)、[VS Code 客户端](../ide-clients/feature-vscode.md)、[交互式命令行](../gateway-channels/feature-cli.md)的入口、数据归属和生效条件查证；这些关联页解释不同阶段，不能只凭一项成功判定整个链路完成。

源码与文档：[jiuwenswarm/acp/stdio_client.py:L1–L13](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/acp/stdio_client.py#L1-L13)；[docs/zh/ACP插件使用.md:L1–L146](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/ACP%E6%8F%92%E4%BB%B6%E4%BD%BF%E7%94%A8.md#L1-L146)。

<!-- kb:knowledge owner=feature-acp facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 怎样验证

按文档先初始化和配置模型、启动 Gateway，再从 ACP Client 连接并完成一次请求。检查请求关联、流式输出、人工交互与取消，覆盖主进程未启动、子进程退出和环境路径错误。这些是建议的验收步骤，本页没有记录上游运行测试已执行或已通过。

源码与文档：[jiuwenswarm/acp/stdio_client.py:L1–L13](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/acp/stdio_client.py#L1-L13)；[docs/zh/ACP插件使用.md:L1–L146](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/ACP%E6%8F%92%E4%BB%B6%E4%BD%BF%E7%94%A8.md#L1-L146)。
