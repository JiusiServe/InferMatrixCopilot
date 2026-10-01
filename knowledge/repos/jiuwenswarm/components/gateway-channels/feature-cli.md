---
title: 交互式命令行 的职责、接口与配置
created: 2026-10-01
updated: 2026-10-01
type: guide
tags:
- jiuwenswarm
sources:
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/cli/main.py
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/命令行指令.md
---

# 交互式命令行 的职责、接口与配置

本页是该功能的基本知识入口，基线 `f0a69728c96b`。它连接源码契约与上游功能文档；详细字段和行为仍沿固定引用核对。

<!-- kb:knowledge owner=feature-cli facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 职责与边界

终端入口负责命令解析、网关连接和事件展示。用户命令与 Agent 工具调用经过不同的入口，不能用相同名字推断相同的执行权限。 本页记录入口职责与边界；逐文件的类型、函数和依赖关系见同 owner 的源码接口记录。

源码与文档：[jiuwenswarm/cli/main.py:L1–L11](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/cli/main.py#L1-L11)；[docs/zh/命令行指令.md:L1–L357](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%91%BD%E4%BB%A4%E8%A1%8C%E6%8C%87%E4%BB%A4.md#L1-L357)。

<!-- kb:knowledge owner=feature-cli facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 接口与调用入口（API）

此入口通过模块装配和客户端协议参与功能。这些是源码定位入口，具体公共用户操作沿功能文档查证；本页不把内部符号直接当成稳定 HTTP API。参数、返回类型、错误传播和生命周期应在所列实现与调用方一起核对。

源码与文档：[jiuwenswarm/cli/main.py:L1–L11](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/cli/main.py#L1-L11)；[docs/zh/命令行指令.md:L1–L357](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%91%BD%E4%BB%A4%E8%A1%8C%E6%8C%87%E4%BB%A4.md#L1-L357)。

<!-- kb:knowledge owner=feature-cli facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 配置入口与生效条件

 文档中的调用选项包括 `--mode`、`--session`、`--cwd`、`--project-dir`、`--trusted-dir`、`--gateway-url`，适用命令与前置条件沿文档确认。 修改设置时还要检查配置加载位置与本功能的装配或连接时机，不能只由“保存成功”判断当前运行实例已经采用新值。

源码与文档：[jiuwenswarm/cli/main.py:L1–L11](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/cli/main.py#L1-L11)；[docs/zh/命令行指令.md:L1–L357](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%91%BD%E4%BB%A4%E8%A1%8C%E6%8C%87%E4%BB%A4.md#L1-L357)。

<!-- kb:knowledge owner=feature-cli facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 设计取舍

**设计推断**：终端 CLI 提供单次提问、会话复用和 REPL，适合轻量终端操作；代价是连接状态、事件渲染和退出码必须协调。Gateway 控制指令会被网关拦截，不能把它们与 Agent 自己解释的文本命令混为同一执行入口。以上分析从所列接口与功能边界得出，不宣称作者曾评估所有替代方案。

源码与文档：[jiuwenswarm/cli/main.py:L1–L11](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/cli/main.py#L1-L11)；[docs/zh/命令行指令.md:L1–L357](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%91%BD%E4%BB%A4%E8%A1%8C%E6%8C%87%E4%BB%A4.md#L1-L357)。

<!-- kb:knowledge owner=feature-cli facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 数据流与关联功能

终端入口负责命令解析、网关连接和事件展示。用户命令与 Agent 工具调用经过不同的入口，不能用相同名字推断相同的执行权限。 联调时结合[机器执行与本地 CLI](feature-process-cli.md)、[TUI 对话与命令](../tui-client/feature-tui.md)、[Agent、Code 与 Team 模式](../agent-server-runtime/feature-modes.md)的入口、数据归属和生效条件查证；这些关联页解释不同阶段，不能只凭一项成功判定整个链路完成。

源码与文档：[jiuwenswarm/cli/main.py:L1–L11](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/cli/main.py#L1-L11)；[docs/zh/命令行指令.md:L1–L357](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%91%BD%E4%BB%A4%E8%A1%8C%E6%8C%87%E4%BB%A4.md#L1-L357)。

<!-- kb:knowledge owner=feature-cli facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 怎样验证

核对命令行模式参数、会话复用和两种输出模式；验证断连、Ctrl+C 和错误退出码。对控制指令确认网关改变会话或模式后，普通消息使用新状态且旧运行正确取消。这些是建议的验收步骤，本页没有记录上游运行测试已执行或已通过。

源码与文档：[jiuwenswarm/cli/main.py:L1–L11](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/cli/main.py#L1-L11)；[docs/zh/命令行指令.md:L1–L357](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%91%BD%E4%BB%A4%E8%A1%8C%E6%8C%87%E4%BB%A4.md#L1-L357)。
