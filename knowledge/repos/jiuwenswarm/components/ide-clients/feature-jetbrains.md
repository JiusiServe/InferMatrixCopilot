---
title: JetBrains 客户端 的职责、接口与配置
created: 2026-10-01
updated: 2026-10-01
type: guide
tags:
- jiuwenswarm
sources:
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/ide/jetbrains/JetBrains插件.md
---

# JetBrains 客户端 的职责、接口与配置

本页是该功能的基本知识入口，基线 `f0a69728c96b`。它连接源码契约与上游功能文档；详细字段和行为仍沿固定引用核对。

<!-- kb:knowledge owner=feature-jetbrains facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 职责与边界

JetBrains 客户端在 IDE 工具窗口中提供交互并连接服务。JVM 插件生命期与 Python 服务运行期不同，需要分别检查连接、工作区与资源收尾。 本页记录入口职责与边界；逐文件的类型、函数和依赖关系见同 owner 的源码接口记录。

源码与文档：[jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt:L1–L74](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt#L1-L74)；[docs/zh/ide/jetbrains/JetBrains插件.md:L1–L185](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/ide/jetbrains/JetBrains%E6%8F%92%E4%BB%B6.md#L1-L185)。

<!-- kb:knowledge owner=feature-jetbrains facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 接口与调用入口（API）

可定位的实现声明包括 `JiuwenSwarmService`；`scheduleAckRetry`；`dispose`；`instance`。这些是源码定位入口，具体公共用户操作沿功能文档查证；本页不把内部符号直接当成稳定 HTTP API。参数、返回类型、错误传播和生命周期应在所列实现与调用方一起核对。

源码与文档：[jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt:L1–L74](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt#L1-L74)；[docs/zh/ide/jetbrains/JetBrains插件.md:L1–L185](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/ide/jetbrains/JetBrains%E6%8F%92%E4%BB%B6.md#L1-L185)。

<!-- kb:knowledge owner=feature-jetbrains facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 配置入口与生效条件

配置与启用条件的权威入口是下列功能文档和实现的调用方。本页提供查证路由：先确认当前宿主、会话或运行模式，再检查文档中的操作条件与实现消费的输入；不把 UI 文案、文件名或方法名猜作可写配置键。 修改设置时还要检查配置加载位置与本功能的装配或连接时机，不能只由“保存成功”判断当前运行实例已经采用新值。

源码与文档：[jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt:L1–L74](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt#L1-L74)；[docs/zh/ide/jetbrains/JetBrains插件.md:L1–L185](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/ide/jetbrains/JetBrains%E6%8F%92%E4%BB%B6.md#L1-L185)。

<!-- kb:knowledge owner=feature-jetbrains facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 设计取舍

**设计推断**：JVM 插件通过工具窗口连接 Agent 服务并复用 IDE 的 diff、诊断和终端交互；代价是 IDE 项目、插件生命周期与 Python 后端运行期需要分别管理。流式聊天可用不代表 Alt+Enter 快速修复和文件修改路径也已接线。以上分析从所列接口与功能边界得出，不宣称作者曾评估所有替代方案。

源码与文档：[jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt:L1–L74](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt#L1-L74)；[docs/zh/ide/jetbrains/JetBrains插件.md:L1–L185](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/ide/jetbrains/JetBrains%E6%8F%92%E4%BB%B6.md#L1-L185)。

<!-- kb:knowledge owner=feature-jetbrains facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 数据流与关联功能

JetBrains 客户端在 IDE 工具窗口中提供交互并连接服务。JVM 插件生命期与 Python 服务运行期不同，需要分别检查连接、工作区与资源收尾。 联调时结合[项目、会话与历史管理](../agent-runtime/feature-projects-sessions.md)、[VS Code 客户端](feature-vscode.md)、[LSP 代码智能](../agent-server-runtime/feature-lsp.md)的入口、数据归属和生效条件查证；这些关联页解释不同阶段，不能只凭一项成功判定整个链路完成。

源码与文档：[jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt:L1–L74](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt#L1-L74)；[docs/zh/ide/jetbrains/JetBrains插件.md:L1–L185](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/ide/jetbrains/JetBrains%E6%8F%92%E4%BB%B6.md#L1-L185)。

<!-- kb:knowledge owner=feature-jetbrains facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 怎样验证

在一个 IDE 项目中验证聊天流、选中上下文、diff 审查与 Alt+Enter 操作。覆盖回退、Git 快捷操作、项目切换和连接中断，再确认关闭工具窗口或项目时相关订阅和资源收尾。这些是建议的验收步骤，本页没有记录上游运行测试已执行或已通过。

源码与文档：[jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt:L1–L74](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt#L1-L74)；[docs/zh/ide/jetbrains/JetBrains插件.md:L1–L185](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/ide/jetbrains/JetBrains%E6%8F%92%E4%BB%B6.md#L1-L185)。
