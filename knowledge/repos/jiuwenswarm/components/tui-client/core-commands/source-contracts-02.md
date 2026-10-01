---
title: "core-commands 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# core-commands 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/compact.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f699b06b234d93bfad6ce834b5057e7ae22c8da24372af9c38454c80509d9eea -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/compact.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `CompactResponse`, `createCompactCommand`, `payload`, `result`, `stats`, `compactSummary`, `beforeK`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addInfo } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/compact.ts#L1-L75)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/config.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=221b340f3a741f57bbd119ede6ebcb45abadd3f03a8960f5c7ce463f7cd2c93d -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/config.ts`**

- 源码声明的类型、组件或调用边界：`CommandContext`, `COMPLETION_SCHEMA_TTL_MS`, `cachedSchemaKeys`, `cachedSchemaAt`, `ConfigItemSchema`, `FRONTEND_SCHEMA_KEYS`, `FRONTEND_SCHEMAS`, `getFrontendSchema`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addInfo, extractObject, formatValue } from "../helpers.js";`；`import { CommandKind, type CommandContext, type SlashCommand } from "../types.js";`；`import type { ThemeName } from "../../../ui/theme.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/config.ts#L1-L649)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/context.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3c979c524ec2ed3a2d3847c0edd9b198f1df600dd24444867e697825222ffe34 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/context.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `ContextUsagePayload`, `formatTokenCount`, `value`, `toLocale`, `renderBar`, `filled`, `clamped`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addInfo } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/context.ts#L1-L107)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/copy.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=82a503c9d672a71588dce793955b63e4bf44172836edd7e8ff1bcf4aef77d4d5 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/copy.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `getRecentAssistantMessages`, `texts`, `index`, `entry`, `text`, `createCopyCommand`, `arg`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { copyToClipboard } from "../clipboard.js";`；`import { addError, addInfo } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/copy.ts#L1-L60)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/cron.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=18cd069ce16633826fced9ac821ffa80a71ae7ceab38d0c6284fbf201e54d5d6 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/cron.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `CronJobPayload`, `CronJobListPayload`, `CronJobMetaPayload`, `TARGET_CHANNELS`, `cachedCronMeta`, `loadCronJobMeta`, `payload`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addInfo, parseArgs } from "../helpers.js";`；`import { CommandKind, type SlashCommand, type CommandContext } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/cron.ts#L1-L902)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/debug.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=625a597b828d528f2a94d6e25915ae4d3af0f3bf3137487b8f63c6b0f427e5bc -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/debug.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `EMPTY_PROMPT_MSG`, `createDebugCommand`, `prompt`, `requestId`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, makeItem } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/debug.ts#L1-L41)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/diff.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=82ca1dd31a5d710340a4db7c81d730ac0ad09476b4de9893756e4c23e4c79b88 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/diff.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `DiffPayload`, `createDiffCommand`, `payload`, `turns`, `gitDiff`, `parts`, `summary`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addDiff } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`；`import type { TurnDiff, GitDiffData } from "../../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/diff.ts#L1-L51)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/evolve.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5cccbe4eb4f73c3420651e693775817aac41b61fba445ed019dfd46fafcf24ac -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/evolve.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `EVOLUTION_SUPPORTED_MODES`, `unsupportedEvolutionModeMessage`, `createEvolveCommand`, `unsupportedMode`, `skillArg`, `text`, `requestId`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { makeItem, parseArgs } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`；`import type { ClientMode } from "../../modes.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/evolve.ts#L1-L181)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/exit.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=237c83c8f52edefb2be0960a079593df004fabab24be24fdb22b3405498d420d -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/exit.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `createExitCommand`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/exit.ts#L1-L15)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/expand.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=401698ee3c5ecb57d70cddfaaa7b2905fa376de84e079b8e95018754bd693a89 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/expand.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `EXPAND_SCOPES`, `createExpandCommand`, `scope`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { makeItem } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/expand.ts#L1-L32)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/export.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d87f71890627c5e911691150d3b6064779127f3dcfdfd35e79223b2edc771fe1 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/export.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `ensureTxtExtension`, `dir`, `base`, `finalBase`, `formatTimestamp`, `year`, `month`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { writeFileSync } from "node:fs";`；`import { basename, dirname, join, resolve } from "node:path";`；`import { copyToClipboard } from "../clipboard.js";`；`import { addError, addInfo } from "../helpers.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/export.ts#L1-L266)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/fold.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1a87cfe0bc05478ca7e57096ae9f04e3c4ef4cd1ec0b2ed6e5170405c5e16857 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/fold.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `FOLD_MODES`, `createFoldCommand`, `mode`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { makeItem } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/fold.ts#L1-L25)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/harmonyos-dev-init.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=19f0717104ff71242074d481cd80fc8b08842c28b4092a06400fddb41e50b061 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/harmonyos-dev-init.ts`**

- 源码声明的类型、组件或调用边界：`CommandContext`, `RuntimeCheck`, `CommandResult`, `KnowledgeMcpConfig`, `KnowledgeMcpStatus`, `KnowledgeMcpReport`, `HarmonyDevReport`, `McpListPayload`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addInfo } from "../helpers.js";`；`import { CommandKind, type CommandContext, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/harmonyos-dev-init.ts#L1-L661)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/harmonyos-project-init.prompts.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d28384137a7f6a45e012d6e875e65efe521e24e4b556bf386d3155ce30758aa2 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/harmonyos-project-init.prompts.ts`**

- 源码声明的类型、组件或调用边界：`RuntimeCheck`, `HarmonyModule`, `HarmonyProjectContext`, `promptValue`, `text`, `clipped`, `buildHarmonyOSProjectInitPrompt`, `project`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/harmonyos-project-init.prompts.ts#L1-L81)。
<!-- /kb:file -->
