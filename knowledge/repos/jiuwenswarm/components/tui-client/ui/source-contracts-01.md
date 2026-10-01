---
title: "ui 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# ui 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/app-screen.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=eecf8b4dbf1a93e244ded92164bf54e8ad60ab0f18df6c69686bda8ee335d4fd -->
**`jiuwenswarm/channels/tui/frontend/src/ui/app-screen.ts`**

- 源码声明的类型、组件或调用边界：`SelectItem`, `SelectListTruncatePrimaryContext`, `AutocompleteItem`, `AutocompleteProvider`, `Component`, `Focusable`, `SlashCommand`, `InstalledSkillEntry`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import {`；`import { spawnSync } from "node:child_process";`；`import * as fs from "node:fs";`；`import * as path from "node:path";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/app-screen.ts#L1-L10368)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/keymap.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=01369d787b7571c12ce37d3e48d90071e0835dd4a44aec0bcbf3956a4de5105c -->
**`jiuwenswarm/channels/tui/frontend/src/ui/keymap.ts`**

- 源码声明的类型、组件或调用边界：`lastInterruptTime`, `AppScreenKeymapDelegate`, `KeyBindingDisplay`, `runCtrlC`, `now`, `commandCancelled`, `runCtrlD`, `now`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { matchesKey } from "@mariozechner/pi-tui";`；`import type { KeybindingAction } from "../core/keybindings/actions.js";`；`import { resolveAction } from "../core/keybindings/resolver.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/keymap.ts#L1-L149)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/memory-view.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f796da5d5a6c3d907104b120559c95fddd9d2ba644fa41cb18fc331c83cd6e8c -->
**`jiuwenswarm/channels/tui/frontend/src/ui/memory-view.ts`**

- 源码声明的类型、组件或调用边界：`TUI`, `MemoryFile`, `memoryPathKey`, `resolved`, `errorCode`, `assertDirectoryWritable`, `assertFileWritable`, `fd`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import {`；`import { dirname, resolve } from "node:path";`；`import { type TUI, type SelectItem, SelectList } from "@mariozechner/pi-tui";`；`import { addInfo } from "../core/commands/helpers.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/memory-view.ts#L1-L699)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/screen-layout.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=24de6ce1721942a095ad0a95eb41bf1feed23887ce3496036b73d87ba285d37d -->
**`jiuwenswarm/channels/tui/frontend/src/ui/screen-layout.ts`**

- 源码声明的类型、组件或调用边界：`ScreenLayoutOptions`, `formatSubtaskStatus`, `formatElapsed`, `totalSeconds`, `minutes`, `seconds`, `formatTokenCount`, `renderRunningStatus`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { visibleWidth } from "@mariozechner/pi-tui";`；`import type { AppSnapshot } from "../app-state.js";`；`import { formatModeForDisplay, isTeamMode } from "../core/modes.js";`；`import { renderTeamPanel } from "./components/team-panel.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/screen-layout.ts#L1-L445)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/theme.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ecf58186b6617a60032eea2477557a8a65aca966d63b84ac721bcb7b1707a599 -->
**`jiuwenswarm/channels/tui/frontend/src/ui/theme.ts`**

- 源码声明的类型、组件或调用边界：`highlightLine`, `result`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import chalk from "chalk";`；`import type { EditorTheme, MarkdownTheme, SelectListTheme } from "@mariozechner/pi-tui";`；`import { loadTuiConfig, saveTuiConfig } from "../core/tui-config-store.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/theme.ts#L1-L354)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/transcript-entry-selection.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1d1cd2d9e60c652828e2988ed07ab30a76da71a61bac4c71804b3a25f1664491 -->
**`jiuwenswarm/channels/tui/frontend/src/ui/transcript-entry-selection.ts`**

- 源码声明的类型、组件或调用边界：`isTodoTool`, `normalized`, `filterTodoToolEntry`, `tools`, `SelectedTranscriptEntries`, `selectTranscriptEntries`, `entries`, `latestUserIndex`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { AppSnapshot } from "../app-state.js";`；`import type { HistoryItem, ToolCallDisplay } from "../core/types.js";`；`import { buildTranscriptEntries } from "../core/transcript-timeline.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/transcript-entry-selection.ts#L1-L114)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/transcript-renderer.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f96bba1e000f52c870293063c21940bd4f38c7136b3e0e72ff8487b153929f39 -->
**`jiuwenswarm/channels/tui/frontend/src/ui/transcript-renderer.ts`**

- 源码声明的类型、组件或调用边界：`renderPendingUserInput`, `lines`, `isToolEntry`, `computeHiddenToolIndices`, `hidden`, `runStart`, `runLength`, `flushRun`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { AppSnapshot } from "../app-state.js";`；`import type { HistoryItem } from "../core/types.js";`；`import { renderHistoryEntry } from "./components/messages/index.js";`；`import { shouldEmphasizeAssistantTransition } from "./components/messages/presentation-rules.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/transcript-renderer.ts#L1-L145)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/welcome.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2e2e5c23cc5d9de373874765522ab8ca0140b4def5d8a90204baf9752fc5a338 -->
**`jiuwenswarm/channels/tui/frontend/src/ui/welcome.ts`**

- 源码声明的类型、组件或调用边界：`PreferredLanguage`, `ART_TITLE_RAW`, `BG_MAGENTA`, `GRADIENT_COLORS`, `applyGradient`, `color`, `centerLine`, `lineWidth`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { visibleWidth, wrapTextWithAnsi } from "@mariozechner/pi-tui";`；`import { formatModeForDisplay } from "../core/modes.js";`；`import type { ConnectionStatus } from "../core/ws-client.js";`；`import { padToWidth } from "./rendering/text.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/welcome.ts#L1-L168)。
<!-- /kb:file -->
