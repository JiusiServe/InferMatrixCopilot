---
title: "core-commands 源码接口与集成边界 04"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# core-commands 源码接口与集成边界 04

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/permissions.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=960496c2893724ddd4f07cbeb1d74789fb01cbb1b599345485bd1ebd4b318f47 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/permissions.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `VALID_LEVELS`, `RULE_MATCH_RE`, `PATTERN_WRAP_WIDTH`, `PATTERN_CONT_INDENT`, `wrapLongToken`, `lines`, `i`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addInfo, makeItem } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/permissions.ts#L1-L554)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/persist.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e78ec1dff30cc85c1ace448fb8de4b3bc846786fa34cadfb72e0e0a502792ba0 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/persist.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `normalizePersistContent`, `createPersistCommand`, `content`, `created`, `nextId`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { generateCreateToken } from "../../session-state.js";`；`import { addError, addInfo } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/persist.ts#L1-L51)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/plan.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=48d77bc949a4c9a49a045da0a3250f392d28b4e18c07c00013a415508afc15d6 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/plan.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `PLAN_TO_NORMAL`, `resolvePlanTarget`, `resolveNormalTarget`, `createPlanCommand`, `value`, `isPlan`, `exitPlan`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addInfo } from "../helpers.js";`；`import type { ClientMode } from "../../modes.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/plan.ts#L1-L95)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/plugin.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a5eeee4fb489b79100ce09d2cb43f00bf3ffa19e9a7b3ed984fe9c4f6da02b8c -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/plugin.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `PluginEntry`, `PluginListPayload`, `MarketPlaceItem`, `listPlugins`, `payload`, `plugins`, `enabled`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addInfo, flattenArrayPayload, parseArgs } from "../helpers.js";`；`import { CommandKind, type SlashCommand, type CommandContext } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/plugin.ts#L1-L290)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/recap.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=98932901e9aac4ea416e4af39eb73837355920a733074d1e20a1c5574447a80a -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/recap.ts`**

- 源码声明的类型、组件或调用边界：`CommandContext`, `RecapResponse`, `NO_TURN_MSG`, `FAILED_MSG`, `CANCELLED_MSG`, `waitForInterrupt`, `check`, `createRecapCommand`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addInfo } from "../helpers.js";`；`import { CommandKind, type CommandContext, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/recap.ts#L1-L82)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/reload-plugins.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ce8591cf52fc5af45f408f5f7824bec54661b371c6ff61e2cf72976840b1aa5a -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/reload-plugins.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `ReloadPluginsPayload`, `createReloadPluginsCommand`, `payload`, `message`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addInfo } from "../helpers.js";`；`import { CommandKind, type SlashCommand, type CommandContext } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/reload-plugins.ts#L1-L42)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/rename.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e526fb29836c624185435272f3b32f9038a65a2c40ce2c66e76919d680915e7b -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/rename.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `RenamePayload`, `createRenameCommand`, `value`, `payload`, `currentTitle`, `payload`, `message`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addInfo } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/rename.ts#L1-L63)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/resume.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=921773654f563706c32b70db81c8e08c068d049a1b7c26305e035c2d071e20a0 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/resume.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `SessionMeta`, `SessionListPayload`, `ResumeResumePayload`, `normalizeSessionId`, `trimmed`, `trimmed`, `sanitizeSessionList`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addInfo } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`；`import type { AccentColorName } from "../../../ui/theme.js";`；`import { isTeamMode, normalizeToClientMode } from "../../modes.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/resume.ts#L1-L279)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/review.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6133ea0473a1e3587acd0832855e2580c1dbeb8faac4eff1c9d677ba98c4a5d9 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/review.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `createReviewCommand`, `command`, `requestId`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { makeItem } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/review.ts#L1-L31)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/rewind.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0c44f8ac912f81f3aa476e4103f0e7bb9e4fb19258c92f729b7b21e34292a695 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/rewind.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `TurnFileChange`, `TurnInfo`, `ListTurnsPayload`, `RewindPayload`, `RestoreOption`, `GREEN`, `RED`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addCommandEcho, addError, addInfo, makeItem } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/rewind.ts#L1-L426)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/sandbox.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5236f9875df8190e202ad87a066485e260ed74da6eb7ba85db4053b40ad48bd2 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/sandbox.ts`**

- 源码声明的类型、组件或调用边界：`CommandContext`, `SandboxFileEntry`, `SandboxRuntime`, `SandboxEffectiveFiles`, `SandboxMount`, `SandboxResponse`, `SandboxProviderType`, `cachedProviderType`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addInfo } from "../helpers.js";`；`import { CommandKind, type CommandContext, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/sandbox.ts#L1-L413)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/security-review.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fcafa2510cb3fd05e1ceb82f9e41ece41ef2fcb6fb4b7bb6246581c52c2346dc -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/security-review.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `createSecurityReviewCommand`, `command`, `requestId`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { makeItem } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/security-review.ts#L1-L38)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/session.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=18094aed087e53f076a400eab4a975cd449bb3675a39c269dd62fe1287029b1f -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/session.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `createSessionCommand`, `payload`, `message`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addInfo } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/session.ts#L1-L37)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/sessions.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e54bd7d06120c41234eadd7d6a7ede6f0aa0b3f8ba2f49486c6f94ffb1e88191 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/sessions.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `createSessionsCommand`, `payload`, `items`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { flattenArrayPayload, formatValue, makeItem } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/sessions.ts#L1-L32)。
<!-- /kb:file -->
