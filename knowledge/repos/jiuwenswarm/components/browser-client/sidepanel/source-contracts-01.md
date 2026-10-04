---
title: "sidepanel 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# sidepanel 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/sidepanel/ChatBridge.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=15103e6e6d28a117fec16a803d4581646c2ba69b0b786cbf70b674a1b9712f0f -->
**`jiuwenswarm/channels/browser/frontend/src/sidepanel/ChatBridge.ts`**

- 源码声明的类型、组件或调用边界：`log`, `ChatBridge`, `ids`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { createLogger } from "@shared/logger";`；`import { MSG } from "@shared/constants";`；`import { SidePanelRequest, BackgroundReply } from "@shared/messages";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/sidepanel/ChatBridge.ts#L1-L138)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/sidepanel/ContextBar.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=83174cdef323ec0d0df5036c9f4adca3cc18ac51eacbe9b48fdaa1650a87cc3d -->
**`jiuwenswarm/channels/browser/frontend/src/sidepanel/ContextBar.ts`**

- 源码声明的类型、组件或调用边界：`LOW_EXTRACTION_THRESHOLD`, `PREVIEW_CHARS`, `ContextBar`, `i`, `chip`, `charCount`, `isLow`, `isPdf`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { PinnedPage } from "@shared/types";`；`import { t } from "@shared/i18n";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/sidepanel/ContextBar.ts#L1-L177)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/sidepanel/SessionExporter.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8d11b891977d3bd2c30ab7c60e58748d528167c6ec30b32cadc2eb0f54f526a3 -->
**`jiuwenswarm/channels/browser/frontend/src/sidepanel/SessionExporter.ts`**

- 源码声明的类型、组件或调用边界：`ExportPackage`, `exportSessionJson`, `pinnedPages`, `chatHistory`, `pkg`, `exportSessionMarkdown`, `pinnedPages`, `chatHistory`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { getPinnedPagesBySession, loadChatHistory } from "@shared/storage";`；`import { PinnedPage, ResearchSession, ChatEntry } from "@shared/types";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/sidepanel/SessionExporter.ts#L1-L126)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/sidepanel/SessionPicker.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fc6fd3b1c32ed24af008779627633a895fe5444069b122f75aabe031df6225fd -->
**`jiuwenswarm/channels/browser/frontend/src/sidepanel/SessionPicker.ts`**

- 源码声明的类型、组件或调用边界：`SessionPicker`, `id`, `active`, `item`, `i`, `session`, `item`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { ResearchSession } from "@shared/types";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/sidepanel/SessionPicker.ts#L1-L122)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/sidepanel/chat.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c638fe0cbff4062f57f639df737ab4982d6532f134726a9d3fc85aa91b3d322b -->
**`jiuwenswarm/channels/browser/frontend/src/sidepanel/chat.ts`**

- 源码声明的类型、组件或调用边界：`formatTime`, `addTurnDivider`, `last`, `d`, `makeCopyIcon`, `btn`, `addMessageFooter`, `footer`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { t } from "@shared/i18n";`；`import { getPinnedPagesBySession } from "@shared/storage";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/sidepanel/chat.ts#L1-L118)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/sidepanel/markdown.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d308912cc3729bc7389eaf30cb0c63edb082321cb5ba70057641c88a56e0bd52 -->
**`jiuwenswarm/channels/browser/frontend/src/sidepanel/markdown.ts`**

- 源码声明的类型、组件或调用边界：`escapeHtml`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/sidepanel/markdown.ts#L1-L141)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/sidepanel/privacy.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2ed6bb7102c4d86f8c1a8daa5b89a47d496528f19fcd2334e806f0a5b77ba8f6 -->
**`jiuwenswarm/channels/browser/frontend/src/sidepanel/privacy.ts`**

- 源码声明的类型、组件或调用边界：`privacyEl`, `privacyBody`, `privacyClose`, `openPrivacy`, `closePrivacy`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { t } from "@shared/i18n";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/sidepanel/privacy.ts#L1-L21)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/sidepanel/reader.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c81f9ef85102aa9362b93ad8402b5a492ffa938eaa3b417cc0c45b5ce1b8d2c9 -->
**`jiuwenswarm/channels/browser/frontend/src/sidepanel/reader.ts`**

- 源码声明的类型、组件或调用边界：`readerEl`, `readerBack`, `readerContent`, `openReader`, `resp`, `ctx`, `article`, `h1`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { MSG } from "@shared/constants";`；`import { t } from "@shared/i18n";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/sidepanel/reader.ts#L1-L51)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/sidepanel/search.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=097ff7d5ddeb3c8d57c96b0e0747bcd49d0012e8e374340a5e9843e3181fb333 -->
**`jiuwenswarm/channels/browser/frontend/src/sidepanel/search.ts`**

- 源码声明的类型、组件或调用边界：`searchEl`, `searchInput`, `searchResults`, `searchClose`, `openSearch`, `closeSearch`, `runSearch`, `q`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { t } from "@shared/i18n";`；`import { loadPinnedPages } from "@shared/storage";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/sidepanel/search.ts#L1-L77)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/sidepanel/sidepanel.html pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6ba52ea0a5e45545a54c4a3531f7065018ba1a737f45895ca4ed4dc899ed4f06 -->
**`jiuwenswarm/channels/browser/frontend/src/sidepanel/sidepanel.html`**

- 页面装配边界：body, script 标签；资源装载与宿主连接取决于对应属性和脚本实现。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/sidepanel/sidepanel.html#L1-L484)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/sidepanel/tour.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e96f07c5b7ec8d9eb11db5efc32dc32221fa38b1d2df4bdd75df9fa9c401dd8c -->
**`jiuwenswarm/channels/browser/frontend/src/sidepanel/tour.ts`**

- 源码声明的类型、组件或调用边界：`tourEl`, `tourTitle`, `tourBody`, `tourNext`, `tourPrev`, `tourSkip`, `tourDots`, `TOUR_STEPS`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { t } from "@shared/i18n";`；`import { hasSeenTour, markTourSeen } from "@shared/storage";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/sidepanel/tour.ts#L1-L71)。
<!-- /kb:file -->
