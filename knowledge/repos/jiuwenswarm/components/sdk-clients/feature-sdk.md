---
title: Python 与 TypeScript SDK 的职责、接口与配置
created: 2026-10-01
updated: 2026-10-01
type: guide
tags:
- jiuwenswarm
sources:
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:sdks/python/src/jiuwenswarm_sdk/client.py
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:sdks/README.md
feature: "sdk"
entry_points: ["sdks/python/src/jiuwenswarm_sdk/client.py"]
source_globs: ["sdks/python/src/jiuwenswarm_sdk/client.py", "sdks/*"]
---

# Python 与 TypeScript SDK 的职责、接口与配置

本页是该功能的基本知识入口，基线 `f0a69728c96b`。它连接源码契约与上游功能文档；详细字段和行为仍沿固定引用核对。

<!-- kb:knowledge owner=feature-sdk facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 职责与边界

每次 SDK 调用创建一个 jiuwenswarm-process，等待 Runtime 清理和进程退出，不保留运行中的 Runtime。SDK 不导入 Agent 引擎，也不自行建立网关网络客户端；两种语言共享过程协议，但需要分别核对调用时限、取消与异常处理。

源码与文档：[sdks/python/src/jiuwenswarm_sdk/client.py:L1–L356](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/python/src/jiuwenswarm_sdk/client.py#L1-L356)；[sdks/README.md:L1–L148](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/README.md#L1-L148)。

<!-- kb:knowledge owner=feature-sdk facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 接口与调用入口（API）

Python `Client.query` 和 `Client.run` 以及 TypeScript Client 通过一次性子进程的管道交换消息。`on_event` 接收版本化事件；`on_interaction` 返回原始 answers 数组，缺少回调时抛出 InteractionRequired 并取消、清理。ASK 由宿主用户作决定，SDK 不把交互扁平化为自动批准。

源码与文档：[sdks/python/src/jiuwenswarm_sdk/client.py:L1–L356](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/python/src/jiuwenswarm_sdk/client.py#L1-L356)；[sdks/README.md:L1–L148](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/README.md#L1-L148)。

<!-- kb:knowledge owner=feature-sdk facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 配置入口与生效条件

`Client` 的 command 是 argv，cwd/env 控制子进程工作区和环境；调用方分别设置 Runtime timeout 与 SDK deadline。Python 使用 `deadline_seconds`，TypeScript 使用 `deadlineMs`/AbortSignal。取消、超时与交互答复都作用于同一个子进程，不自动重启重试。

源码与文档：[sdks/python/src/jiuwenswarm_sdk/client.py:L1–L356](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/python/src/jiuwenswarm_sdk/client.py#L1-L356)；[sdks/README.md:L1–L148](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/README.md#L1-L148)。

<!-- kb:knowledge owner=feature-sdk facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 设计取舍

**设计推断**：薄客户端为每次调用创建一次子进程，不另建 Agent 引擎或网络服务，使进程清理边界明确；代价是调用之间无法复用活 Runtime，也不会自动重试。Runtime timeout 与 SDK deadline 含义不同，取消和人工交互由调用方提供而非默认自动批准。以上分析从所列接口与功能边界得出，不宣称作者曾评估所有替代方案。

源码与文档：[sdks/python/src/jiuwenswarm_sdk/client.py:L1–L356](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/python/src/jiuwenswarm_sdk/client.py#L1-L356)；[sdks/README.md:L1–L148](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/README.md#L1-L148)。

<!-- kb:knowledge owner=feature-sdk facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 数据流与关联功能

SDK 封装协议类型与客户端通信，让外部程序管理会话和事件。两种语言的客户端需要遵守同一线路契约，但不能仅由类型相似推断重连或错误处理完全一致。 联调时结合[机器执行与本地 CLI](../gateway-channels/feature-process-cli.md)、[E2A 统一请求响应协议](../protocols/feature-e2a.md)、[工具权限与安全治理](../agent-server-runtime/feature-permissions.md)的入口、数据归属和生效条件查证；这些关联页解释不同阶段，不能只凭一项成功判定整个链路完成。

源码与文档：[sdks/python/src/jiuwenswarm_sdk/client.py:L1–L356](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/python/src/jiuwenswarm_sdk/client.py#L1-L356)；[sdks/README.md:L1–L148](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/README.md#L1-L148)。

<!-- kb:knowledge owner=feature-sdk facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 怎样验证

分别在 Python 与 TypeScript 调用 query 和 run，核对版本化事件、最终结果与子进程退出。覆盖缺少交互回调、超时、AbortSignal 或取消、启动失败和 Runtime 错误，检查失败后没有残留进程或隐式重试。这些是建议的验收步骤，本页没有记录上游运行测试已执行或已通过。

源码与文档：[sdks/python/src/jiuwenswarm_sdk/client.py:L1–L356](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/python/src/jiuwenswarm_sdk/client.py#L1-L356)；[sdks/README.md:L1–L148](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/README.md#L1-L148)。
