---
title: TUI 对话与命令 的职责、接口与配置
created: 2026-10-01
updated: 2026-10-01
type: guide
tags:
- jiuwenswarm
sources:
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/index.ts
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/TUI使用指南.md
feature: "tui"
entry_points: ["jiuwenswarm/channels/tui/frontend/src/index.ts"]
source_globs: ["jiuwenswarm/channels/tui/frontend/src/index.ts", "jiuwenswarm/channels/tui/*"]
---

# TUI 对话与命令 的职责、接口与配置

本页是该功能的基本知识入口，基线 `f0a69728c96b`。它连接源码契约与上游功能文档；详细字段和行为仍沿固定引用核对。

<!-- kb:knowledge owner=feature-tui facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 职责与边界

终端 UI 展示会话、命令、运行事件和人工交互。TUI 局部指令与发给后端的 slash 指令在不同位置解析，因此连接成功并不证明每条命令由同一组件实现。 本页记录入口职责与边界；逐文件的类型、函数和依赖关系见同 owner 的源码接口记录。

源码与文档：[jiuwenswarm/channels/tui/frontend/src/index.ts:L1–L276](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/index.ts#L1-L276)；[docs/zh/TUI使用指南.md:L1–L780](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/TUI%E4%BD%BF%E7%94%A8%E6%8C%87%E5%8D%97.md#L1-L780)。

<!-- kb:knowledge owner=feature-tui facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 接口与调用入口（API）

可定位的实现声明包括 `parseCliArgs`；`isRemoteUrl`；`buildUiLifecycle`；`notifyDisconnectBeforeExit`；`closeUi`。这些是源码定位入口，具体公共用户操作沿功能文档查证；本页不把内部符号直接当成稳定 HTTP API。参数、返回类型、错误传播和生命周期应在所列实现与调用方一起核对。

源码与文档：[jiuwenswarm/channels/tui/frontend/src/index.ts:L1–L276](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/index.ts#L1-L276)；[docs/zh/TUI使用指南.md:L1–L780](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/TUI%E4%BD%BF%E7%94%A8%E6%8C%87%E5%8D%97.md#L1-L780)。

<!-- kb:knowledge owner=feature-tui facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 配置入口与生效条件

 文档中的调用选项包括 `--session`、`--url`、`--token`、`--help`、`--budget`、`--project`，适用命令与前置条件沿文档确认。 修改设置时还要检查配置加载位置与本功能的装配或连接时机，不能只由“保存成功”判断当前运行实例已经采用新值。

源码与文档：[jiuwenswarm/channels/tui/frontend/src/index.ts:L1–L276](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/index.ts#L1-L276)；[docs/zh/TUI使用指南.md:L1–L780](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/TUI%E4%BD%BF%E7%94%A8%E6%8C%87%E5%8D%97.md#L1-L780)。

<!-- kb:knowledge owner=feature-tui facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 设计取舍

**设计推断**：TUI 将本地 UI 指令与后端控制指令分层解析，便于处理终端专有交互；代价是命令排障需要先判断解析位置。同 Gateway 可以承载多个窗口，但同 session 同时占用受到限制；增加窗口不等于创建独立后端实例。以上分析从所列接口与功能边界得出，不宣称作者曾评估所有替代方案。

源码与文档：[jiuwenswarm/channels/tui/frontend/src/index.ts:L1–L276](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/index.ts#L1-L276)；[docs/zh/TUI使用指南.md:L1–L780](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/TUI%E4%BD%BF%E7%94%A8%E6%8C%87%E5%8D%97.md#L1-L780)。

<!-- kb:knowledge owner=feature-tui facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 数据流与关联功能

终端 UI 展示会话、命令、运行事件和人工交互。TUI 局部指令与发给后端的 slash 指令在不同位置解析，因此连接成功并不证明每条命令由同一组件实现。 联调时结合[交互式命令行](../gateway-channels/feature-cli.md)、[单机多实例](../launch/feature-instances.md)、[已有 PR 自动修复](feature-autofix.md)的入口、数据归属和生效条件查证；这些关联页解释不同阶段，不能只凭一项成功判定整个链路完成。

源码与文档：[jiuwenswarm/channels/tui/frontend/src/index.ts:L1–L276](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/index.ts#L1-L276)；[docs/zh/TUI使用指南.md:L1–L780](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/TUI%E4%BD%BF%E7%94%A8%E6%8C%87%E5%8D%97.md#L1-L780)。

<!-- kb:knowledge owner=feature-tui facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 怎样验证

在交互式 TTY 验证连接、消息流和审批，再检查非 TTY 的启动行为。开启两个窗口核对独立会话，尝试占用同一 session 验证冲突；分别测试本地 slash 指令与发往 Gateway 的命令。这些是建议的验收步骤，本页没有记录上游运行测试已执行或已通过。

源码与文档：[jiuwenswarm/channels/tui/frontend/src/index.ts:L1–L276](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/index.ts#L1-L276)；[docs/zh/TUI使用指南.md:L1–L780](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/TUI%E4%BD%BF%E7%94%A8%E6%8C%87%E5%8D%97.md#L1-L780)。
