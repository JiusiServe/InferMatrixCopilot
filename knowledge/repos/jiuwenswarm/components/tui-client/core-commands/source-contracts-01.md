---
title: "core-commands 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# core-commands 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/CommandService.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=43e8507b4d8157a13fdccc3474cd2996d83457a3a1dc347c24892fb76074e7c6 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/CommandService.ts`**

- 源码声明的类型、组件或调用边界：`parseSlashCommand`, `trimmed`, `parts`, `currentCommands`, `command`, `parentCommand`, `pathIndex`, `canonicalPath`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { CommandContext, CommandSuggestion, SlashCommand } from "./types.js";`；`import { flattenArrayPayload, makeItem, parseArgs } from "./helpers.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/CommandService.ts#L1-L261)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/_placeholder.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=80306c10346f8d07d88682f1dc6a7b3550afe0068b8fc4d286f1ff16dd57a020 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/_placeholder.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `createPlaceholderCommand`, `message`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addInfo } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/_placeholder.ts#L1-L29)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/agents.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=06249696f1ec67acc6139dde5616cfc6120fa988bc7fdcef1bb517ad10693acb -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/agents.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `AgentDef`, `SOURCE_LABELS`, `formatSource`, `label`, `shadow`, `listAgents`, `payload`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { flattenArrayPayload, makeItem } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/agents.ts#L1-L414)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/auto-harness-issue-fix.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2e87273b382bee14ee99509692af2c36899b768a40dfba15fd845b6b186fb844 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/auto-harness-issue-fix.ts`**

- 源码声明的类型、组件或调用边界：`AutoHarnessIssueStageProgress`, `AutoHarnessIssueProgress`, `IssueFixTaskStatus`, `IssueFixWatchItem`, `IssueWatchArgs`, `IssueFixArgs`, `IssueWatchResult`, `PipelineNameResolver`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { parseArgs } from "../helpers.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/auto-harness-issue-fix.ts#L1-L683)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/auto-harness.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a872a17791d414afafcac4b01e5185a805455fbffcd8a66f33798ab3f0bd55eb -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/auto-harness.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `IssueListRow`, `IssueMatrixResult`, `PIPELINE_DISPLAY_NAMES`, `PIPELINE_DISPLAY_KEYS`, `PIPELINE_BACKEND_VALUES`, `resolvePipelineName`, `PIPELINE_OPTIONS`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addInfo, parseArgs } from "../helpers.js";`；`import { CommandKind, type SlashCommand, type CommandContext } from "../types.js";`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/auto-harness.ts#L1-L2704)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.prompts.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a4f0ee64d7fa2a012bf032b6e1be7c6d043e11ae11ac97fac603b5e7e17890ab -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.prompts.ts`**

- 源码声明的类型、组件或调用边界：`AutofixPrPlatform`, `BuildAutofixPrPromptArgs`, `AUTOFIX_PR_PROMPT_TEMPLATE`, `buildAutofixPrPrompt`, `tail`, `hint`, `target`, `prompt`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.prompts.ts#L1-L182)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.status.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9a01585e3bb536b17eabdcd6a854fa2cd7b2270c044b8a493853903bc0cd5617 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.status.ts`**

- 源码声明的类型、组件或调用边界：`GITCODE_V5`, `GITCODE_V2`, `BROWSER_UA`, `HTTP_TIMEOUT_MS`, `CMD_TIMEOUT_MS`, `ChecksVerdict`, `PrState`, `PrStatus`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { execFile } from "node:child_process";`；`import type { PreferredLanguage } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.status.ts#L1-L423)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/branch.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=192563c0538184b217eee0067c315a014c3d51eb9686952aa1fb12837706d2a9 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/branch.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `SessionForkPayload`, `createBranchCommand`, `hasMainConversation`, `message`, `customTitle`, `payload`, `forkSessionId`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addCommandEcho, addError, addInfo } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/branch.ts#L1-L79)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/btw.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9b6dcd0fa6ebaae336d6ad3833b3c118b10b1d6b75c2654ce93400f27da21e2a -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/btw.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `BtwResponse`, `NO_CONTEXT_MSG`, `FAILED_MSG`, `EMPTY_QUESTION_MSG`, `CANCELLED_MSG`, `createBtwCommand`, `question`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addInfo } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/btw.ts#L1-L110)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/cancel.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c100e992b5c229346331001e387dcd1527ab9fbb8a1eb5760dc499c8f66f39aa -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/cancel.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `createCancelCommand`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addInfo } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/cancel.ts#L1-L17)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/chrome.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=664e79784cba7e40500aba5a64b5d46865548dd872263693920f03b73666009a -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/chrome.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `createChromeCommand`, `message`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addInfo } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/chrome.ts#L1-L27)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/clear.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c955138f8b90a663d07af255b9824f38f1f8761c26e44c09d34be9fb5d6f2c15 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/clear.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `shouldPersistSessionFromArgs`, `parts`, `createClearCommand`, `persistSession`, `created`, `nextId`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { generateCreateToken } from "../../session-state.js";`；`import { addCommandEcho, addError, addInfo, parseArgs } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/clear.ts#L1-L50)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/collapse.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fa98d7bebef67732dc6487443af45a5ee7fc6fa6141c292d0907ce2826217483 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/collapse.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `COLLAPSE_SCOPES`, `createCollapseCommand`, `scope`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { makeItem } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/collapse.ts#L1-L32)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/color.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1c00c2b75a3c5bccc63691b97141489f5733a5069f45fd394b16a04451bfe6cb -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/color.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `AccentColorName`, `COLOR_OPTIONS`, `RESET_ALIASES`, `normalizeColorArg`, `createColorCommand`, `value`, `normalizedColor`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addInfo } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`；`import { getAccentColorOptions, type AccentColorName } from "../../../ui/theme.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/color.ts#L1-L60)。
<!-- /kb:file -->
