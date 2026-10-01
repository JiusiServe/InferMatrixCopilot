---
title: "ui-components 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# ui-components 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/todo-list.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=77c084f66e787931abe3228ca49675da975cf59965b332b4992dad9f6713c811 -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/todo-list.ts`**

- 源码声明的类型、组件或调用边界：`normalizeTodoText`, `trimmed`, `todoLabel`, `spinner`, `text`, `prefix`, `todoLine`, `prefix`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { TodoItem } from "../../core/types.js";`；`import { padToWidth } from "../rendering/text.js";`；`import { chalk, palette } from "../theme.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/todo-list.ts#L1-L98)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/tools/collapsed-tool-group-message.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=305e38408fab6a237cd23139c247dc2df72bf4df572b39d0e137fabcd3b7b0da -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/tools/collapsed-tool-group-message.ts`**

- 源码声明的类型、组件或调用边界：`CollapsedToolGroupMessageComponent`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { Component } from "@mariozechner/pi-tui";`；`import type { HistoryItem } from "../../../core/types.js";`；`import { renderCollapsedCompactSummaryLines } from "./compact-tool-renderers.js";`；`import { ToolGroupMessageComponent } from "./tool-group-message.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/tools/collapsed-tool-group-message.ts#L1-L34)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/tools/command-tool-renderers.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0fc22e7fb995efe875624b29c63f0c22f10169ed6a5300f1673d1778a9adf718 -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/tools/command-tool-renderers.ts`**

- 源码声明的类型、组件或调用边界：`firstNonEmptyLines`, `value`, `lines`, `renderRunTool`, `args`, `payload`, `command`, `lines`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ToolCallDisplay } from "../../../core/types.js";`；`import { palette } from "../../theme.js";`；`import { summarize } from "../../rendering/text.js";`；`import type { DetailedToolRenderOptions } from "./tool-render-types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/tools/command-tool-renderers.ts#L1-L174)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/tools/compact-tool-renderers.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c68e44c5b30e2599045b3085d3313292e268db2cc8a8c0769082499e89d816cc -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/tools/compact-tool-renderers.ts`**

- 源码声明的类型、组件或调用边界：`summarizeCompactHint`, `normalized`, `compactActionLabel`, `compactToolTitle`, `args`, `path`, `query`, `url`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ToolCallDisplay } from "../../../core/types.js";`；`import { palette } from "../../theme.js";`；`import { summarize } from "../../rendering/text.js";`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/tools/compact-tool-renderers.ts#L1-L192)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/tools/detailed-tool-renderers.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=50f3e41f74dc1f6bcb9e53246b44c9f3018a4661060a94aedce52a2360b42d9c -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/tools/detailed-tool-renderers.ts`**

- 源码声明的类型、组件或调用边界：`renderDetailedToolLines`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ToolCallDisplay } from "../../../core/types.js";`；`import { renderFetchTool, renderRunTool } from "./command-tool-renderers.js";`；`import {`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/tools/detailed-tool-renderers.ts#L1-L65)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/tools/file-tool-renderers.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dde799a9e40d1f696ab781f1aca1c9370375cba4f39667e76af7c4bf3181df79 -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/tools/file-tool-renderers.ts`**

- 源码声明的类型、组件或调用边界：`renderSessionTool`, `args`, `description`, `index`, `total`, `label`, `lines`, `previewLines`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ToolCallDisplay } from "../../../core/types.js";`；`import { palette } from "../../theme.js";`；`import { summarize } from "../../rendering/text.js";`；`import type { DetailedToolRenderOptions } from "./tool-render-types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/tools/file-tool-renderers.ts#L1-L326)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/tools/search-tool-renderers.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4cf1d9a8074e8730f465e1991d6bf189303d9c53ca67af19d4f60dceb903a71e -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/tools/search-tool-renderers.ts`**

- 源码声明的类型、组件或调用边界：`renderGlobTool`, `args`, `payload`, `parsedValue`, `pattern`, `lines`, `root`, `payloadMatchLines`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ToolCallDisplay } from "../../../core/types.js";`；`import { palette } from "../../theme.js";`；`import { summarize } from "../../rendering/text.js";`；`import type { DetailedToolRenderOptions } from "./tool-render-types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/tools/search-tool-renderers.ts#L1-L326)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/tools/tool-group-message.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1c538c1f214753dc43722175d4c32643e8487ff15e1ef8f242344390692147cd -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/tools/tool-group-message.ts`**

- 源码声明的类型、组件或调用边界：`ToolGroupMessageComponent`, `lines`, `allTools`, `tools`, `visibleTools`, `hiddenCount`, `tool`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { Component } from "@mariozechner/pi-tui";`；`import type { HistoryItem } from "../../../core/types.js";`；`import { renderCompactToolLines, renderHiddenToolsLine } from "./compact-tool-renderers.js";`；`import { renderDetailedToolLines } from "./detailed-tool-renderers.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/tools/tool-group-message.ts#L1-L49)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/tools/tool-kind-utils.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0ed85f3dcbc5de4e8b01e6b0c377d4102bcb368e77ad5189e393a16a88970e17 -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/tools/tool-kind-utils.ts`**

- 源码声明的类型、组件或调用边界：`summarizePath`, `parts`, `summarizeToolArguments`, `obj`, `normalized`, `pattern`, `root`, `keys`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ToolCallDisplay } from "../../../core/types.js";`；`import { summarize } from "../../rendering/text.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/tools/tool-kind-utils.ts#L1-L226)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/tools/tool-line-renderers.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b41615ae943f72e7b41cb3a2a9add21d1e57d7f2a59153aa83cb3ba12aa487ec -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/tools/tool-line-renderers.ts`**

- 源码声明的类型、组件或调用边界：`TOOL_BODY_PREFIX`, `TOOL_BODY_CONTINUATION`, `TOOL_TAIL_PREFIX`, `TOOL_TAIL_CONTINUATION`, `TOOL_EXPAND_HINT`, `MAX_STRUCTURED_LINES_COLLAPSED`, `MAX_STRUCTURED_LINES_EXPANDED`, `toolPrefix`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ToolCallDisplay } from "../../../core/types.js";`；`import { palette } from "../../theme.js";`；`import { prefixedLines, renderWrappedText } from "../../rendering/text.js";`；`import { isToolRunning } from "./tool-kind-utils.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/tools/tool-line-renderers.ts#L1-L170)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/tools/tool-render-shared.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=87c044892500185c7f91ca73db7432d3b265d2f41c569922378bed7bc495140e -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/tools/tool-render-shared.ts`**

- 源码声明的类型、组件或调用边界：`MAX_VISIBLE_TOOLS`, `summarizeStructuredPayload`, `parsed`, `keys`, `summarizeToolResultByKind`, `normalized`, `lines`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { summarize } from "../../rendering/text.js";`；`import { isPlainObject, tryParseStructuredText } from "./tool-structured-data.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/tools/tool-render-shared.ts#L1-L39)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/components/tools/tool-structured-data.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c32babb71648488a395d7b1be6599352c529d9dd7daee2ecec8bd3eb79ecc13c -->
**`jiuwenswarm/channels/tui/frontend/src/ui/components/tools/tool-structured-data.ts`**

- 源码声明的类型、组件或调用边界：`normalizePythonLiteralToJson`, `normalized`, `formatStructuredValue`, `output`, `append`, `visit`, `parsed`, `compactLines`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ToolCallDisplay } from "../../../core/types.js";`；`import { summarize } from "../../rendering/text.js";`；`import { getStringArg, isEditTool, isWriteTool } from "./tool-kind-utils.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/components/tools/tool-structured-data.ts#L1-L307)。
<!-- /kb:file -->
