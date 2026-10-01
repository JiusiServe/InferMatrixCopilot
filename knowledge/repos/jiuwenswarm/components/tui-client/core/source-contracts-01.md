---
title: "core 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# core 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/app-state-helpers.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1d1118c8209c975450855ed4633631c307815e2114ffa2c9ec60fdefcdcc2647 -->
**`jiuwenswarm/channels/tui/frontend/src/core/app-state-helpers.ts`**

- 源码声明的类型、组件或调用边界：`createId`, `findLastIndex`, `index`, `item`, `isIgnorableHistoryRestoreError`, `message`, `TOOL_TIMEOUT_MS`, `computeTimeoutAt`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { applyToolResult, createToolCallDisplay } from "./history-parser.js";`；`import type { HistoryItem, ToolCallDisplay, ToolExecution } from "./types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/app-state-helpers.ts#L1-L162)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/attachments.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e875a27ea0bbe56fe8289ba4265693e5b3c1d7559be8b69e45a88fea7b265a41 -->
**`jiuwenswarm/channels/tui/frontend/src/core/attachments.ts`**

- 源码声明的类型、组件或调用边界：`IMAGE_MIME_TYPES`, `SUPPORTED_FILE_EXTENSIONS`, `AT_MENTION_RE`, `candidate`, `extractAgentMentions`, `results`, `quotedAgentRegex`, `match`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { basename, extname, resolve } from "node:path";`；`import type { FileAttachment } from "./protocol.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/attachments.ts#L1-L253)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/compression-formatters.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fd29409ba0341f9c451071f9876e3369cab28b6bf5fe801c6a529bba74675d7c -->
**`jiuwenswarm/channels/tui/frontend/src/core/compression-formatters.ts`**

- 源码声明的类型、组件或调用边界：`readNumber`, `formatNumber`, `n`, `formatPercent`, `n`, `formatCompressionUsage`, `parts`, `COMPRESSION_STARTED_LABELS`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/compression-formatters.ts#L1-L48)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/event-handlers.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=28efcb616921e6a1312b1b160baefc1dffc8b7d32c125d3190c953c775cf35bc -->
**`jiuwenswarm/channels/tui/frontend/src/core/event-handlers.ts`**

- 源码声明的类型、组件或调用边界：`ContextCompressionStats`, `HistoryItem`, `JsonObject`, `SubtaskState`, `TeamMemberEvent`, `TeamMessageEvent`, `TeamTaskEvent`, `TodoItem`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import {`；`import { normalizeFinalContent } from "./final-content.js";`；`import {`；`import type { EventFrame } from "./protocol.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/event-handlers.ts#L1-L1566)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/final-content.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=55cc2fe478aa864a013469f93e64ea63fe913d3dfd6718384c54273a12001be9 -->
**`jiuwenswarm/channels/tui/frontend/src/core/final-content.ts`**

- 源码声明的类型、组件或调用边界：`decodeQuotedPythonLikeString`, `normalizeFinalDisplayText`, `normalizeFinalContent`, `rawContent`, `trimmed`, `parsed`, `singleQuoted`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/final-content.ts#L1-L49)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/history-parser.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6938326b961fe79b8deb50a1a4d0ddc4d1db415c99728e4fe47557c5190e4d76 -->
**`jiuwenswarm/channels/tui/frontend/src/core/history-parser.ts`**

- 源码声明的类型、组件或调用边界：`mergeAssistantFragmentContents`, `p`, `withoutLast`, `last`, `sortAssistantGroupByTime`, `ta`, `tb`, `sameAssistantTurn`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { normalizeFinalContent } from "./final-content.js";`；`import type { EventFrame } from "./protocol.js";`；`import type { HistoryItem, InfoMeta, JsonValue, MediaItem, ToolCallDisplay } from "./types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/history-parser.ts#L1-L993)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/modes.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=59dd7262239d9d25e3e7961c209ac60b06972a516c63ecf77a8245b34d8637e3 -->
**`jiuwenswarm/channels/tui/frontend/src/core/modes.ts`**

- 源码声明的类型、组件或调用边界：`ClientMode`, `isClientMode`, `LEGACY_MODE_TO_NEW`, `normalizeToClientMode`, `isTeamMode`, `formatModeForDisplay`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/modes.ts#L1-L75)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/pasted-text.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d744aedc1313b83a0ec505984a27dc5859b98b53e80c8f0b5bcaa0f44968276d -->
**`jiuwenswarm/channels/tui/frontend/src/core/pasted-text.ts`**

- 源码声明的类型、组件或调用边界：`PASTED_TEXT_MARKER_RE`, `PASTED_TEXT_LINE_THRESHOLD`, `PASTED_TEXT_CHAR_THRESHOLD`, `stripBracketedPasteMarkers`, `normalizePastedText`, `countPastedTextLines`, `shouldCollapsePastedText`, `formatPastedTextMarker`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/pasted-text.ts#L1-L37)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/plan-entry-source.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f4d82528a92d5083bc5911ee2cbe445a58e66d7af02098e44c6444b2411d3cd9 -->
**`jiuwenswarm/channels/tui/frontend/src/core/plan-entry-source.ts`**

- 源码声明的类型、组件或调用边界：`PLAN_ENTRY_SOURCE_SLASH_COMMAND`, `PLAN_ENTRY_SOURCE_PLAN_TOGGLE`, `PLAN_ENTRY_SOURCES`, `PlanEntrySource`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/plan-entry-source.ts#L1-L46)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/protocol.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=79b011c0f65a054424fc71b451edd3fec674fb584f7b099fddc27b6acd4db188 -->
**`jiuwenswarm/channels/tui/frontend/src/core/protocol.ts`**

- 源码声明的类型、组件或调用边界：`FileAttachment`, `ReqFrame`, `ResFrame`, `EventFrame`, `Frame`, `isResFrame`, `isEventFrame`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/protocol.ts#L1-L49)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/session-state.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fbda29491565571b4fad3d467ab5e19e1a09d559e204fd0910a7d224f2c2cde2 -->
**`jiuwenswarm/channels/tui/frontend/src/core/session-state.ts`**

- 源码声明的类型、组件或调用边界：`generateCreateToken`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import crypto from "node:crypto";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/session-state.ts#L1-L5)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/statusline-runner.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7af52aeb64e2a545cc873caab76cd3ce8724ff795346a7612ec7af374ed83771 -->
**`jiuwenswarm/channels/tui/frontend/src/core/statusline-runner.ts`**

- 源码声明的类型、组件或调用边界：`ChildProcess`, `StatusLineShellInvocation`, `PathExists`, `gitBashCandidates`, `candidates`, `pathDirs`, `dir`, `findGitBash`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { execFile, type ChildProcess } from "node:child_process";`；`import { existsSync } from "node:fs";`；`import { win32 } from "node:path";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/statusline-runner.ts#L1-L74)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/transcript-timeline.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=de238aa9190215b2230db6e73cd4fb19ae68aa0298ac7167457cac31684b314e -->
**`jiuwenswarm/channels/tui/frontend/src/core/transcript-timeline.ts`**

- 源码声明的类型、组件或调用边界：`TimelineItem`, `toTimestampMs`, `ts`, `compareTimelineItems`, `aValid`, `bValid`, `buildTimelineItems`, `messageItems`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { HistoryItem, ToolExecution } from "./types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/transcript-timeline.ts#L1-L247)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/tui-config-store.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c17413ec570e6c5900fa6aa3d1070f2bb7312b3beda7ab4edb14fcf4543320e3 -->
**`jiuwenswarm/channels/tui/frontend/src/core/tui-config-store.ts`**

- 源码声明的类型、组件或调用边界：`CONFIG_DIR`, `CONFIG_FILE`, `StatusLineSetting`, `TuiConfig`, `loadTuiConfig`, `raw`, `saveTuiConfig`, `existing`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";`；`import { homedir } from "node:os";`；`import { join } from "node:path";`；`import type { ThemeName } from "../ui/theme.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/tui-config-store.ts#L1-L67)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/tui-trusted-dirs-store.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fc7fc8f1e45e099fd3f71903543997fe74197b6440966eac0e0518e1081661f9 -->
**`jiuwenswarm/channels/tui/frontend/src/core/tui-trusted-dirs-store.ts`**

- 源码声明的类型、组件或调用边界：`_trustedDirsByProject`, `normalizePath`, `trimmed`, `expanded`, `resolved`, `migrateLegacyFormat`, `raw`, `projectCwd`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { readdirSync, statSync } from "node:fs";`；`import { homedir } from "node:os";`；`import { resolve } from "node:path";`；`import { loadTuiConfig, saveTuiConfig } from "./tui-config-store.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/tui-trusted-dirs-store.ts#L1-L336)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/types.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cd54e6551b4272e5f99832b92c748f963d98f23579353899ff0564a24500bba7 -->
**`jiuwenswarm/channels/tui/frontend/src/core/types.ts`**

- 源码声明的类型、组件或调用边界：`StreamingState`, `JsonPrimitive`, `JsonValue`, `JsonObject`, `MediaItem`, `SystemMeta`, `InfoMeta`, `ToolCallDisplay`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/types.ts#L1-L272)。
<!-- /kb:file -->
