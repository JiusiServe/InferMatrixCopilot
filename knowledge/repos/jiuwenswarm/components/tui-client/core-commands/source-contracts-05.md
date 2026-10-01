---
title: "core-commands 源码接口与集成边界 05"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# core-commands 源码接口与集成边界 05

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/simplify.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1d925de0438f3f16ea74e04724fc5516ac50184f78c31c9e3ef1aa92c5b2f1fc -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/simplify.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `SimplifyResponse`, `createSimplifyCommand`, `target`, `payload`, `prompt`, `requestId`, `message`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addInfo } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/simplify.ts#L1-L94)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/skills.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ee421eb80f4539140f780854843a60bfe371a0ccdbe01f0e61762004253b0be1 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/skills.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `ONLINE_SKILL_SOURCES`, `SkillNetItem`, `MarketPlaceItem`, `listMarketplaces`, `payload`, `items`, `pollSkillNetInstall`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { flattenArrayPayload, makeItem } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/skills.ts#L1-L877)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/status.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c1382d0f153aa50d42c151a707fb021bac4d4a43653c140c3ca32ed3161ec179 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/status.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `MemoryWarning`, `StatusPayload`, `showOverview`, `mcpItems`, `sourceItems`, `warnings`, `showUsage`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addInfo } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`；`import type { SessionUsageSummary } from "../../../app-state.js";`；`import { formatModeForDisplay } from "../../modes.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/status.ts#L1-L182)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/statusline.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a8d399b444a3ec3f8da75abfe4843561ba427da3885ee1509d5da7e317ede2c2 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/statusline.ts`**

- 源码声明的类型、组件或调用边界：`StatusLineSetting`, `CommandContext`, `getStatusLineConfig`, `showCurrentConfig`, `sl`, `lines`, `stripOuterQuotes`, `trimmed`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { makeItem } from "../helpers.js";`；`import { loadTuiConfig, saveTuiConfig, type StatusLineSetting } from "../../tui-config-store.js";`；`import { CommandKind, type CommandContext, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/statusline.ts#L1-L283)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/swarmflow.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a3a76c6c880b240d1f0b0fd6ac94a1e610208fb17fa0da596d6f167265e314cc -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/swarmflow.ts`**

- 源码声明的类型、组件或调用边界：`ClientMode`, `SlashCommand`, `SwarmflowToggleTarget`, `BudgetValue`, `SwarmflowTogglePlan`, `parseSwarmflowEnabled`, `value`, `parseSwarmflowBudget`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addInfo, addError } from "../helpers.js";`；`import { formatModeForDisplay, isTeamMode, type ClientMode } from "../../modes.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/swarmflow.ts#L1-L273)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/swarmflows.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d08c63005a275d03f238261597869858ef500d082db34d4e48f797363592b467 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/swarmflows.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `createSwarmFlowsCommand`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addInfo } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/swarmflows.ts#L1-L22)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/switch.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f336c32c7b89b574d2f8e742d3d906961aeed14114ae743e093f30a5fcb58f34 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/switch.ts`**

- 源码声明的类型、组件或调用边界：`CommandContext`, `SWITCH_CANCEL_TIMEOUT_MS`, `ThirdAgentEntry`, `ThirdAgentListPayload`, `performSwitch`, `check`, `answers`, `selected`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { makeItem } from "../helpers.js";`；`import { HANDOFF_TARGET_CC_TUI } from "../../supervision/protocol.js";`；`import { CommandKind, type CommandContext, type SlashCommand } from "../types.js";`；`import type { PendingQuestionOption } from "../../event-handlers.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/switch.ts#L1-L275)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/teamskills.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7b8d1eedc0ef5db25618b91027b4926f3059c67f9c80b8e484a3c88cb0ccbeb4 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/teamskills.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `TeamSkillsPublishParams`, `TeamSkillsDeleteParams`, `TeamSkillsInitParams`, `TeamSkillsValidateParams`, `TeamSkillsPackParams`, `TeamSkillsInfoParams`, `TeamSkillsSearchParams`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { flattenArrayPayload, makeItem, parseArgs } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/teamskills.ts#L1-L810)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/theme.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0d9e173f6bac5264abb360ee1d590d4fba510bc10faf9d767939805dbbd92f53 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/theme.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `DISPLAY_OPTIONS`, `createThemeCommand`, `value`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addError, addInfo } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`；`import type { ThemeName } from "../../../ui/theme.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/theme.ts#L1-L46)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/usage.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4c2d5f220ee3e9ffacecf96ebb3e7b1abbdf666f2b4884400a7e814c8451b28e -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/usage.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `showUsage`, `summary`, `fmt`, `items`, `entry`, `createUsageCommand`, `message`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { addInfo, addError } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/usage.ts#L1-L54)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/view.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8e1a52a5a06c2e2c8d4c83a113f0ce47cc4fcb696be513a4203de7e3d5f900a7 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/view.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommand`, `createViewCommand`, `nextMode`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { makeItem } from "../helpers.js";`；`import { CommandKind, type SlashCommand } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/view.ts#L1-L23)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/workspace-dir.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=117c57792da972a773ee74c5896f388b4269ec9a6b25c6f0a7a4e3af3495d827 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/workspace-dir.ts`**

- 源码声明的类型、组件或调用边界：`CommandContext`, `completeDirPath`, `trimmed`, `input`, `searchDir`, `prefixFilter`, `d`, `entries`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { readdirSync, statSync } from "node:fs";`；`import { homedir } from "node:os";`；`import { basename, dirname, isAbsolute, join, resolve } from "node:path";`；`import { addError, addInfo } from "../helpers.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/workspace-dir.ts#L1-L318)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/clipboard.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8d3821abb3c86981f8b167802ccb2f99074d754af456dc77691b3d3445bf94c5 -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/clipboard.ts`**

- 源码声明的类型、组件或调用边界：`tryClipboardAsync`, `settled`, `child`, `timer`, `tryCommandAsync`, `settled`, `child`, `timer`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { spawn } from "node:child_process";`；`import { writeFileSync, unlinkSync } from "node:fs";`；`import { join } from "node:path";`；`import { tmpdir } from "node:os";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/clipboard.ts#L1-L243)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/commands/helpers.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5d314dc21793d55f6f041d9616c5baa07d24ad13b84702697d44ba23799f45ac -->
**`jiuwenswarm/channels/tui/frontend/src/core/commands/helpers.ts`**

- 源码声明的类型、组件或调用边界：`now`, `makeItem`, `id`, `addInfo`, `addError`, `addCommandEcho`, `addDiff`, `id`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { HistoryItem, DiffMeta } from "../types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/helpers.ts#L1-L75)。
<!-- /kb:file -->
