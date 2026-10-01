---
title: "tui-client 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# tui-client 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/app-state.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b6746de3ceeab4e4e4957c3016ee7d9187fe906484b0c31e5ba2ab02552631f8 -->
**`jiuwenswarm/channels/tui/frontend/src/app-state.ts`**

- 源码声明的类型、组件或调用边界：`AppEventDelegate`, `PendingQuestion`, `PendingQuestionItem`, `UserAnswer`, `HarnessExtensionReady`, `HarnessActivateInteraction`, `ClientMode`, `EventFrame`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addInfo } from "./core/commands/helpers.js";`；`import { PrWatchController } from "./core/commands/builtins/autofix-pr.watch.js";`；`import type { CommandContext, PreferredLanguage } from "./core/commands/types.js";`；`import type {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/app-state.ts#L1-L3686)。
<!-- /kb:file -->
