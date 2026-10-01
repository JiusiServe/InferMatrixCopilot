---
title: "core-commands 源码接口与集成边界 06"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# core-commands 源码接口与集成边界 06

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/registry.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=43860821efb4d1109aea9941f0967e4edcf7bbd86267f34eb636bc29d1944f37 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/registry.ts`**

- 源码声明的类型、组件或调用边界：`BuiltinCommandsOptions`, `isHarmonyOSCommandsEnabled`, `createBuiltinCommands`, `commands`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { SlashCommand } from "./types.js";`；`import { createBranchCommand } from "./builtins/branch.js";`；`import { createBtwCommand } from "./builtins/btw.js";`；`import { createClearCommand } from "./builtins/clear.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/registry.ts#L1-L143)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/types.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=39f903b444f9f6769b0b5c19cbad5662e46ac14da3fa1bbfa5fb70aaa887dd6b -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/types.ts`**

- 源码声明的类型、组件或调用边界：`ConnectionStatus`, `PreferredLanguage`, `StatusViewTab`, `CommandKind`, `CommandSuggestion`, `CommandContext`, `SlashCommand`, `SlashCommandListProvider`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { HistoryItem, TeamMessageEvent } from "../types.js";`；`import type { AccentColorName, ThemeName } from "../../ui/theme.js";`；`import type { PendingQuestionItem, UserAnswer } from "../event-handlers.js";`；`import type { FileAttachment } from "../protocol.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/types.ts#L1-L201)。
<!-- /kb:file -->
