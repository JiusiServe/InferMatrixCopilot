---
title: "Web 前端中英双语 i18n 初始化：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/i18n/index.ts:L15-L27, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/i18n/index.ts:L1-L14, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/i18n/index.ts:L22-L27, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/i18n/index.ts:L1-L28, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/i18n/index.ts:L30-L30, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/tests/fixtures/settings-extension/extensionDemoMain.tsx:L17-L20, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/i18n/index.ts:L15-L28, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/tests/inputAreaPermissionMerge.test.mjs:L90-L94, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/tests/inputAreaPermissionMerge.test.mjs:L149-L161, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/tests/inputAreaPermissionMerge.test.mjs:L229-L247, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/i18n/index.ts:L1-L30]
feature: "web-i18n-zh-en"
entry_points: ["jiuwenswarm/channels/web/frontend/src/i18n/index.ts"]
source_globs: ["jiuwenswarm/channels/web/frontend/src/i18n/index.ts", "jiuwenswarm/channels/web/frontend/src/App.tsx"]
---

# Web 前端中英双语 i18n 初始化：实现深读

[功能概览](feature-web-i18n-zh-en.md) · [owner 入口](_index.md)

<!-- kb:depth feature=web-i18n-zh-en facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bd163e11a2497b6a60d1be119affe197757aa4561859ecefd77e1854739320d4 -->
**模块导入时链式注册插件并调用 init（配置结果未在所示行内确认）**
导入 i18next 实例后依次 .use(LanguageDetector)、.use(initReactI18next)，再以 zh/en 两个 translation 资源调用 init，完成语言检测与 React 绑定的配置；init 是否同步完成未在所示行内展示。

来源：[jiuwenswarm/channels/web/frontend/src/i18n/index.ts:L1–L28](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/i18n/index.ts#L1-L28)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":28,"path":"jiuwenswarm/channels/web/frontend/src/i18n/index.ts","sha256":"adfe4ebe2000f594ce6ceb0097a831bcd0f033091822f5ac6d9999ce5b59718c","start":1}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-i18n-zh-en facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=62a6fe0fa9b1e647ad4024a18f9ff5b67688e5d78228789c2a66cfb0018de173 -->
**契约仅为默认导出该 i18n 实例；扩展方可对 zh/en 追加 translation 资源包**
模块默认导出已配置的 i18n 实例（L30）。fixture 演示调用方用法：对 ['zh','en'] 逐语言 addResourceBundle(language, 'translation', bundle, true, false)，随后以 i18n.exists(key,{lng}) 校验两种语言键是否存在。

来源：[jiuwenswarm/channels/web/frontend/src/i18n/index.ts:L30–L30](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/i18n/index.ts#L30-L30), [jiuwenswarm/channels/web/frontend/tests/fixtures/settings-extension/extensionDemoMain.tsx:L17–L20](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/tests/fixtures/settings-extension/extensionDemoMain.tsx#L17-L20)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":30,"path":"jiuwenswarm/channels/web/frontend/src/i18n/index.ts","sha256":"a180a969718f39673c17692fa302df5186a1b73861ae8dd646d7cf2d1ebb5180","start":30},{"end":20,"path":"jiuwenswarm/channels/web/frontend/tests/fixtures/settings-extension/extensionDemoMain.tsx","sha256":"e6c03d3a5404827991d3b03f2af2c2201b00e84f9d2d01245c21c6200d1e824e","start":17}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-i18n-zh-en facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=727230cfb10fcfa359b74ce7ad126332e2aac3dda26fe2e389a535900b55e9ac -->
**detection 仅用 localStorage，未检出时默认中文**
detection.order 与 caches 均为 ['localStorage']，不支持 navigator；fallbackLng: 'zh'，supportedLngs: ['zh','en']，interpolation.escapeValue 为 false。即首次无 localStorage 的访客固定得到中文。

来源：[jiuwenswarm/channels/web/frontend/src/i18n/index.ts:L15–L27](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/i18n/index.ts#L15-L27)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":27,"path":"jiuwenswarm/channels/web/frontend/src/i18n/index.ts","sha256":"8cc6a31a20553a4619284089dc2d3732314b34ef54b2aea453f0ef4e1398f4b3","start":15}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-i18n-zh-en facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c573da3e3259660664e46261bec580e606871c27587f26a48834c9799930afc3 -->
**i18next + react-i18next + i18next-browser-languagedetector 三件套**
LanguageDetector 只负责 localStorage 检测（order 限定），initReactI18next 挂接 React；语言资源静态来自 ./locales/zh.json 与 en.json，随模块导入打包。

来源：[jiuwenswarm/channels/web/frontend/src/i18n/index.ts:L1–L14](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/i18n/index.ts#L1-L14)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":14,"path":"jiuwenswarm/channels/web/frontend/src/i18n/index.ts","sha256":"e27438afb14acb904e06ced9e30fa179e1d5fd9cb21376443915da4bbbc16cbc","start":1}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-i18n-zh-en facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b069aa236ced9763c1d345a9c3ba80db1456638432a1b4bb25bceba3b5b127f0 -->
**localStorage 未缓存语言时的回退：fallbackLng 为 zh**
detection.order 仅含 'localStorage'（L25），不会读取 navigator；注释（L23–L24）说明未手动选择语言时默认中文。结合 init 的 fallbackLng: 'zh'（L17），当 localStorage 中没有已缓存的语言时，初始化结果落在 zh 资源上。supportedLngs 限定为 ['zh','en']（L18）。

来源：[jiuwenswarm/channels/web/frontend/src/i18n/index.ts:L15–L28](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/i18n/index.ts#L15-L28)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":28,"path":"jiuwenswarm/channels/web/frontend/src/i18n/index.ts","sha256":"41d5a9515cd1ff966891e8184d85f94cad24e28d01c9b13bde0876339a231466","start":15}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-i18n-zh-en facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4061f748a232998300f09831f17d5614621d7f616403f8a8681a52b098a7db9e -->
**放弃 navigator 检测：避免英文闪烁 vs 牺牲浏览器语言偏好**
设计推断（非作者历史意图）：

（推断）收益：注释写明桌面 WebView2 常为 en-US，不用 navigator 可避免启动初期误显英文，且与后端 preferred_language 默认一致；代价：无 localStorage 的英文浏览器用户首次访问也会看到中文，需手动切换。

来源：[jiuwenswarm/channels/web/frontend/src/i18n/index.ts:L22–L27](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/i18n/index.ts#L22-L27)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":27,"path":"jiuwenswarm/channels/web/frontend/src/i18n/index.ts","sha256":"27bcdfe8b51a722cd6943a05246020f2341c38551049d56628f2cc8e4458af7b","start":22}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-i18n-zh-en facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5fc5d686e0c32f436f67b222f41f1a48ea106eea882af9c7adccdbb010e7869f -->
**现有 DOM 测试以 zh/en 运行打包后的 i18n 模块并断言 tooltip 文案已翻译（仅覆盖运行时翻译使用）**
tests/inputAreaPermissionMerge.test.mjs 导入打包产物中的生产 i18n 模块（i18n/index.js），mount 前调用 i18n.changeLanguage(language)，并对 'zh' 与 'en' 各跑一个用例；断言 tooltip.textContent 等于 i18n.t('chat.config.mode.clusterDesc') 且不等于未翻译键名。该测试验证切换语言后 t() 产出翻译文案，不覆盖 i18n 初始化的 fallbackLng/detection 默认路径。

来源：[jiuwenswarm/channels/web/frontend/tests/inputAreaPermissionMerge.test.mjs:L90–L94](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/tests/inputAreaPermissionMerge.test.mjs#L90-L94), [jiuwenswarm/channels/web/frontend/tests/inputAreaPermissionMerge.test.mjs:L149–L161](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/tests/inputAreaPermissionMerge.test.mjs#L149-L161), [jiuwenswarm/channels/web/frontend/tests/inputAreaPermissionMerge.test.mjs:L229–L247](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/tests/inputAreaPermissionMerge.test.mjs#L229-L247), [jiuwenswarm/channels/web/frontend/src/i18n/index.ts:L1–L30](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/i18n/index.ts#L1-L30)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":94,"path":"jiuwenswarm/channels/web/frontend/tests/inputAreaPermissionMerge.test.mjs","sha256":"396ab1ad4b7708ac9ce02b9424ea1fc02e027f3b754f985702f89d089d3a640d","start":90},{"end":161,"path":"jiuwenswarm/channels/web/frontend/tests/inputAreaPermissionMerge.test.mjs","sha256":"e074d1a71d663ab60a6b3a6f8b5b0cc92d97d0e3caa7d485d7e2f8f5132e0034","start":149},{"end":247,"path":"jiuwenswarm/channels/web/frontend/tests/inputAreaPermissionMerge.test.mjs","sha256":"77a74829f77f3b943fb08e170d54b85114f0fb4ffc697411164e2581d8044e14","start":229},{"end":30,"path":"jiuwenswarm/channels/web/frontend/src/i18n/index.ts","sha256":"686fb21994a85f1d8d2dba9bdfebd963482a479ab591f707cc27cb7b7fc7a566","start":1}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
