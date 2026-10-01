---
title: "core-commands 源码接口与集成边界 03"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# core-commands 源码接口与集成边界 03

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/harmonyos-project-init.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d80b15f24c2a7eda1af5a76d78ebdf6d535f705d61dc232aef4508471ffc3309 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/harmonyos-project-init.ts`**

- 源码声明的类型、组件或调用边界：`CommandContext`, `HarmonyProjectContext`, `RuntimeCheck`, `ProjectInitReport`, `pathError`, `result`, `showProjectReport`, `context`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addInfo } from "../helpers.js";`；`import { CommandKind, type CommandContext, type SlashCommand } from "../types.js";`；`import { switchMode } from "./mode.js";`；`import { completeDirPath, switchProjectScope } from "./workspace-dir.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/harmonyos-project-init.ts#L1-L144)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/help.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c8ddfd0a38cfb940733163a72db9c955981bea999167e6a504d0c7d93abb14b0 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/help.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `COMMAND_GROUPS`, `getCommandGroup`, `createHelpCommand`, `commands`, `groupedCommands`, `ungroupedCommands`, `command`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { CommandKind, type SlashCommand, type SlashCommandListProvider } from "../types.js";`；`import { makeItem } from "../helpers.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/help.ts#L1-L96)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/history.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=81b78cbe5969ee047bfa30e2f74ed2aefc3f1e0ba8253e6e27e703e839cf6f16 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/history.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `createHistoryCommand`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/history.ts#L1-L15)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/hooks.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=191b717ed2a66d3a4e6eb453493213706e1ed917ece08a26acfe19ee8180279a -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/hooks.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `HookConfig`, `HookMatcherSummary`, `HookEventSummary`, `HooksListPayload`, `showHooksBrowser`, `payload`, `events`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addInfo, makeItem } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/hooks.ts#L1-L175)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/init.prompts.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0e814d1aa28ceea36861e91ed690165beb47d8effa8ff5ba0084d8144156bf22 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/init.prompts.ts`**

- 源码声明的类型、组件或调用边界：`ScopeKey`, `ExistingFiles`, `BuildInitPromptArgs`, `resolveLanguage`, `lang`, `buildInitPrompt`, `buildInitPromptEn`, `scopeLine`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { CommandContext } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/init.prompts.ts#L1-L244)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/init.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=73202e3f9d9679c9a6429abb78f6307e07bfeefeed2c1887278774204536766c -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/init.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `ExistingFiles`, `ScopeKey`, `ScopeOption`, `getScopeOptions`, `createInitCommand`, `language`, `rootDir`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { existsSync } from "node:fs";`；`import { join } from "node:path";`；`import { addError, addInfo } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/init.ts#L1-L227)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/keybindings.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e68ab148a65db337f8e8f3e4e6d7bc8fa9c2f0e38e068fdf65de93e0496baa2d -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/keybindings.ts`**

- 源码声明的类型、组件或调用边界：`CommandContext`, `KeybindingContextName`, `formatWarning`, `where`, `applyAndReport`, `warnings`, `openEditor`, `path`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { existsSync, mkdirSync, rmSync, writeFileSync } from "node:fs";`；`import { dirname } from "node:path";`；`import { addError, addInfo } from "../helpers.js";`；`import { CommandKind, type CommandContext, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/keybindings.ts#L1-L160)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/mcp.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e24a1125ed4407331d7e8fc3574e2ff8ee5c5bd26f0047c83e595502d43880e2 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/mcp.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `McpTransport`, `McpListItem`, `McpListPayload`, `McpShowPayload`, `VALID_TRANSPORTS`, `tokenize`, `re`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addInfo } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/mcp.ts#L1-L316)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/memory-path-utils.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cd0344304791392fe39175556426b591c0bc71ec71de5c593c42c771252cbebc -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/memory-path-utils.ts`**

- 源码声明的类型、组件或调用边界：`formatMemoryPathForDisplay`, `namespacedPath`, `getDisplayPath`, `fileSlashes`, `fileNorm`, `homeDir`, `homeDirSlashes`, `homeDirNorm`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { statSync } from "node:fs";`；`import { homedir } from "node:os";`；`import { dirname, join, parse, relative } from "node:path";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/memory-path-utils.ts#L1-L192)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/memory.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0d108a58e9416d92b46bdaf3f3b1c48663a2ab162be4a6312cd60e144fc68a60 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/memory.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `MemoryFile`, `MemoryEditResult`, `MemoryStatusResult`, `MemoryToggleResult`, `MemoryOpenResult`, `PROJECT_MEMORY_FILES`, `LOCAL_MEMORY_FILES`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { existsSync, mkdirSync, readdirSync, statSync, readFileSync, writeFileSync } from "node:fs";`；`import { homedir } from "node:os";`；`import { dirname, join, parse, relative } from "node:path";`；`import { addError, addInfo, makeItem } from "../helpers.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/memory.ts#L1-L1043)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/mode.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=799f705351653ba1feeb62f49b0aec3602fdf468750b63c13f6943ea43f4c688 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/mode.ts`**

- 源码声明的类型、组件或调用边界：`CommandContext`, `switchMode`, `currentMode`, `displayNextMode`, `answers`, `selected`, `MODE_ALIASES`, `resolveModeTarget`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { AutocompleteItem } from "@mariozechner/pi-tui";`；`import type { ClientMode } from "../../modes.js";`；`import { formatModeForDisplay, isTeamMode } from "../../modes.js";`；`import { makeItem } from "../helpers.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/mode.ts#L1-L159)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/model.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e323e0f7a2eae0683efbec576aede325c3d5beb3258768d66ea300fb34310b2c -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/model.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `ModelMeta`, `ModelListPayload`, `RESERVED_MULTIMODAL_MODEL_KEYS`, `isReservedMultimodalModelKey`, `createModelCommand`, `raw`, `parts`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addInfo } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/model.ts#L1-L231)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/new.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1087e34b2eb7448123a1019b2bdb936ad1cfcb45302f59148ee2696ba3457ad3 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/new.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `shouldPersistSessionFromArgs`, `parts`, `createNewCommand`, `persistSession`, `created`, `nextId`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { generateCreateToken } from "../../session-state.js";`；`import { parseArgs } from "../helpers.js";`；`import { makeItem } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/new.ts#L1-L44)。
<!-- /kb:file -->
