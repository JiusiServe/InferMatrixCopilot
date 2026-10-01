---
title: "content-adapters 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# content-adapters 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/content/adapters/arxiv.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=379aab5158dcb9a61e854c659721d042388c4db6bbac41f5e4e82e023c36643d -->
**`jiuwenswarm/channels/browser/frontend/src/content/adapters/arxiv.ts`**

- 源码声明的类型、组件或调用边界：`extractArxiv`, `parts`, `titleEl`, `title`, `authors`, `abstract`, `body`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/content/adapters/arxiv.ts#L1-L33)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/content/adapters/github.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=15b39d63fb27bc99f0e61d4d1d161f48e8bffd7c71f11ee7bca42cc3fae3b4df -->
**`jiuwenswarm/channels/browser/frontend/src/content/adapters/github.ts`**

- 源码声明的类型、组件或调用边界：`extractGitHub`, `title`, `parts`, `article`, `body`, `comments`, `desc`, `topics`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/content/adapters/github.ts#L1-L40)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/content/adapters/hackernews.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=52e9a4d7f91c22db511d53785c5aba9f829269307126da3dbe1856b0fc3d2e97 -->
**`jiuwenswarm/channels/browser/frontend/src/content/adapters/hackernews.ts`**

- 源码声明的类型、组件或调用边界：`extractHackerNews`, `url`, `extractItem`, `parts`, `titleEl`, `title`, `linkedUrl`, `subtext`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/content/adapters/hackernews.ts#L1-L82)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/content/adapters/pubmed.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f9659564f16b03f52ec0deb64db83291e51bc078158633bd30e244a192f49b20 -->
**`jiuwenswarm/channels/browser/frontend/src/content/adapters/pubmed.ts`**

- 源码声明的类型、组件或调用边界：`extractPubmed`, `parts`, `titleEl`, `title`, `authors`, `abstract`, `fullText`, `mesh`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/content/adapters/pubmed.ts#L1-L26)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/content/adapters/sec.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=20dc46c5daba28ed5a6bfad0f2e9ce0b6310d209c518ce3560afb28d7d992b02 -->
**`jiuwenswarm/channels/browser/frontend/src/content/adapters/sec.ts`**

- 源码声明的类型、组件或调用边界：`extractSec`, `title`, `parts`, `formContent`, `filingHeader`, `docBody`, `cloned`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/content/adapters/sec.ts#L1-L28)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/content/adapters/twitter.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=416ef71e1de2af8ccac45be23d0e28a308c9404395d25847207a03160599f63e -->
**`jiuwenswarm/channels/browser/frontend/src/content/adapters/twitter.ts`**

- 源码声明的类型、组件或调用边界：`extractTwitter`, `parts`, `title`, `articles`, `processed`, `textEl`, `text`, `authorEl`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/content/adapters/twitter.ts#L1-L47)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/content/adapters/wikipedia.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c7991ea470e5ff65c659090f3a7adedb529b6ae1e1b4766d27140207cca1ff3f -->
**`jiuwenswarm/channels/browser/frontend/src/content/adapters/wikipedia.ts`**

- 源码声明的类型、组件或调用边界：`extractWikipedia`, `titleEl`, `title`, `parts`, `content`, `clone`, `noiseSelectors`, `stopHeadings`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/content/adapters/wikipedia.ts#L1-L49)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/content/adapters/youtube.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0dbb11c7893e24550f1ed92d77b7292ffb2b3a09be52337818cfb5085164598a -->
**`jiuwenswarm/channels/browser/frontend/src/content/adapters/youtube.ts`**

- 源码声明的类型、组件或调用边界：`extractYouTube`, `parts`, `titleEl`, `title`, `channel`, `desc`, `transcript`, `extractTranscriptFromInitialData`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/content/adapters/youtube.ts#L1-L94)。
<!-- /kb:file -->
