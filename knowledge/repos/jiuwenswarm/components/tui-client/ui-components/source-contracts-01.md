---
title: "ui-components 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# ui-components 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/checkbox-list.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b891adc74c20758447901e63d1f20298207ed55ab0f5912acb22e2e34b9790c6 -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/checkbox-list.ts`**

- 源码声明的类型、组件或调用边界：`CheckboxItem`, `CheckboxGroup`, `FlatItem`, `CheckboxTheme`, `defaultTheme`, `CheckboxList`, `gi`, `ii`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import chalk from "chalk";`；`import { matchesKey } from "@mariozechner/pi-tui/dist/keys.js";`；`import { visibleWidth, wrapTextWithAnsi } from "@mariozechner/pi-tui";`；`import { padToWidth } from "../rendering/text.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/checkbox-list.ts#L1-L270)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/messages/content-components.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c8a3c9be4deb510966632ff9eebeeab4240bd6c409fef7fe547e7d8ca8a03ecd -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/messages/content-components.ts`**

- 源码声明的类型、组件或调用边界：`Component`, `renderAssistantLines`, `body`, `lines`, `lastIndex`, `renderThinkingLabel`, `label`, `focus`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { truncateToWidth, type Component } from "@mariozechner/pi-tui";`；`import type { HistoryItem } from "../../../core/types.js";`；`import { chalk, palette } from "../../theme.js";`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/messages/content-components.ts#L1-L145)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/messages/diff-component.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e96b051fd9e4bd782dff2012dc57a66499d71f0c8c66edad7a1130138a04cd2c -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/messages/diff-component.ts`**

- 源码声明的类型、组件或调用边界：`DiffComponent`, `lines`, `turns`, `gitDiff`, `innerWidth`, `hasTurns`, `hasGitDiff`, `trackedFiles`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { Component } from "@mariozechner/pi-tui";`；`import type { HistoryItem, FileDiff, GitDiffFile } from "../../../core/types.js";`；`import { palette } from "../../theme.js";`；`import { renderWrappedText } from "../../rendering/text.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/messages/diff-component.ts#L1-L126)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/messages/history-entry.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=939b58b6a28388910f37a0825b3c14d7558466dfae2ef2a3eb5905f9c79f29d7 -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/messages/history-entry.ts`**

- 源码声明的类型、组件或调用边界：`renderHistoryEntry`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { HistoryItem } from "../../../core/types.js";`；`import { renderCompactEntry } from "./render-compact-entry.js";`；`import { renderDetailedEntry } from "./render-detailed-entry.js";`；`import type { MessageRenderOptions, RenderedHistoryEntry } from "./types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/messages/history-entry.ts#L1-L15)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/messages/meta-components.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7e9217393c33fd95f7126a6d9dce13a9030c9d00930faf59c44563716e88054a -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/messages/meta-components.ts`**

- 源码声明的类型、组件或调用边界：`renderGroupedHelpView`, `lines`, `innerWidth`, `version`, `versionText`, `group`, `groupTitle`, `groupPadding`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { visibleWidth } from "@mariozechner/pi-tui";`；`import type { Component } from "@mariozechner/pi-tui";`；`import type { HistoryItem } from "../../../core/types.js";`；`import { palette } from "../../theme.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/messages/meta-components.ts#L1-L244)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/messages/presentation-rules.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3caf3ae97d9b48eaf0b76f42b1e3e4beb823e5f5aa125958a852e8ccac233b33 -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/messages/presentation-rules.ts`**

- 源码声明的类型、组件或调用边界：`COMPACT_EXPANDED_TOOL_NAMES`, `shouldExpandCompactToolGroup`, `shouldGapAfterEntry`, `shouldEmphasizeAssistantTransition`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { HistoryItem } from "../../../core/types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/messages/presentation-rules.ts#L1-L54)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/messages/render-compact-entry.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=642f46340450c803be155ba6a4c67b195698b24bd3ff4bfc62779016e1cb81a9 -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/messages/render-compact-entry.ts`**

- 源码声明的类型、组件或调用边界：`shouldRenderInfoExpanded`, `meta`, `renderCompactEntry`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { HistoryItem } from "../../../core/types.js";`；`import {`；`import { CollapsedToolGroupMessageComponent, ToolGroupMessageComponent } from "../tools/index.js";`；`import type { MessageRenderOptions, RenderedHistoryEntry } from "./types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/messages/render-compact-entry.ts#L1-L79)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/messages/render-detailed-entry.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c4c359d3e0fd24a387e7c889f68179c92ead7625796b96db207264d5363f5d99 -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/messages/render-detailed-entry.ts`**

- 源码声明的类型、组件或调用边界：`renderDetailedEntry`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { HistoryItem } from "../../../core/types.js";`；`import {`；`import { CollapsedToolGroupMessageComponent, ToolGroupMessageComponent } from "../tools/index.js";`；`import type { MessageRenderOptions, RenderedHistoryEntry } from "./types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/messages/render-detailed-entry.ts#L1-L88)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/messages/shared.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0714200fce0a6972f1913132b2811f766a51f7bf16988f96c11fca9c4305bf7e -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/messages/shared.ts`**

- 源码声明的类型、组件或调用边界：`renderClaudeResponseLines`, `renderMediaItems`, `lines`, `item`, `kind`, `label`, `image`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { Image as TuiImage } from "@mariozechner/pi-tui";`；`import type { MediaItem } from "../../../core/types.js";`；`import { palette } from "../../theme.js";`；`import { prefixedLines, renderWrappedText, summarize } from "../../rendering/text.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/messages/shared.ts#L1-L46)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/messages/types.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=954954bee599c5be3553e0fc07491857ed4c8132aa7c2875132de9eaafd6d134 -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/messages/types.ts`**

- 源码声明的类型、组件或调用边界：`MessageRenderOptions`, `RenderedHistoryEntry`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/messages/types.ts#L1-L13)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/team-panel.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e60b62463703160f0b650f5abbcf74bd88abe036f0e0b1d18761710df3e9d5be -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/team-panel.ts`**

- 源码声明的类型、组件或调用边界：`TeamMemberSummary`, `compactMemberPreview`, `colorMemberLine`, `colorTreeContextLine`, `renderMemberTree`, `lines`, `leader`, `teammates`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { TeamMemberEvent, TeamMessageEvent, TeamTaskEvent } from "../../core/types.js";`；`import { padToWidth } from "../rendering/text.js";`；`import { palette } from "../theme.js";`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/team-panel.ts#L1-L432)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/team-shared.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=630f261baedd6af087294bd7c4033138a5b9f4eae5725db387f30e330c6c0ef2 -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/team-shared.ts`**

- 源码声明的类型、组件或调用边界：`TeamMemberSummary`, `truncate`, `formatElapsed`, `diff`, `seconds`, `minutes`, `hours`, `normalizeStatusValue`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { TeamMemberEvent, TeamMessageEvent, TeamTaskEvent } from "../../core/types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/team-shared.ts#L1-L200)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/team-status-pill.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0017c1542f2a87624478766ae8fa82e0942e4c0aa9d52d19e2e7f73cbc2ee937 -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/team-status-pill.ts`**

- 源码声明的类型、组件或调用边界：`renderTeamStatusPill`, `members`, `workingCount`, `parts`, `latestTask`, `content`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { TeamMemberEvent, TeamMessageEvent, TeamTaskEvent } from "../../core/types.js";`；`import { padToWidth } from "../rendering/text.js";`；`import { palette } from "../theme.js";`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/team-status-pill.ts#L1-L39)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/tools/tool-render-types.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f5195263b562371b88802e580f654f988571364b016eff709403e7fc4d43c70e -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/tools/tool-render-types.ts`**

- 源码声明的类型、组件或调用边界：`DetailedToolRenderOptions`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/tools/tool-render-types.ts#L1-L4)。
<!-- /kb:file -->
