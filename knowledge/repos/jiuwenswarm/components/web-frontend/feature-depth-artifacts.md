---
title: "会话产物列表、预览与下载：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L23-L28, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/artifactCollection.ts:L95-L119, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/artifactCollection.ts:L75-L93, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L45-L64, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L105-L109, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L15-L21, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L49-L56, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L81-L84, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L45-L56, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/filePreviewModel.ts:L54-L57, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L105-L105, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/tests/artifactCollection.test.mjs:L1-L4, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/tests/artifactCollection.test.mjs:L42-L55, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/tests/artifactCollection.test.mjs:L71-L92, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/filePreviewModel.ts:L47-L67, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L99-L112]
feature: "artifacts"
entry_points: ["jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx", "jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/artifactCollection.ts", "jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/filePreviewModel.ts"]
source_globs: ["jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx", "jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/artifactCollection.ts", "jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/filePreviewModel.ts"]
---

# 会话产物列表、预览与下载：实现深读

[功能概览](feature-artifacts.md) · [owner 入口](_index.md)



<!-- kb:depth feature=artifacts facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0691d0c3ee9d7d920ef1ba99957ad9f6069e7929ce7a2c604e9272e296c48d57 -->
**handleDownload 的调用契约**
handleDownload 先用 artifactDownloadUrl(artifact) 解析地址，返回 null 时直接 return；在 pywebview 桌面环境下调用 window.pywebview.api.download_file(downloadUrl, artifact.name || 'download')，浏览器环境则动态创建 <a> 元素设置 href 与 download 属性模拟点击下载。调用方需保证 artifact 至少有 downloadUrl 或 path，否则按钮渲染为 disabled。

来源：[jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L45–L64](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx#L45-L64), [jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L105–L109](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx#L105-L109)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx","start":45,"end":64,"sha256":"9c1ffd3c779a7e670921e31bc2f01785dcab3da3abc4e89f2ae33eafcdf64cc3"},{"path":"jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx","start":105,"end":109,"sha256":"056fcc5ceedef685c48272ab91ebe547a206e0f3d5066ec49a28bd79173a20f5"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=artifacts facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f2198248f508344df259dbba63d0f4a1dc72f9f6f050b12ddcf61980bb2853c8 -->
**桌面端 pywebview 保存桥**
列表通过 DownloadCapableWindow 类型声明检测 window.pywebview.api.download_file，存在时经 executeDesktopSave 包装执行原生保存而非浏览器下载；点击条目还会先尝试 openFileInDesktopBrowser 把文件交给桌面浏览器打开。这使同一组件在 Web 与桌面壳下复用，但行为依赖宿主注入的桥接 API。

来源：[jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L15–L21](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx#L15-L21), [jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L49–L56](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx#L49-L56), [jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L81–L84](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx#L81-L84)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx","start":15,"end":21,"sha256":"7c1b7dff1a3752bd7b50cadaf5983d208a78cd9cc2e7377ae680d438b5b20d1f"},{"path":"jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx","start":49,"end":56,"sha256":"e578cb71906621ea07645f1f94302036c9d923399b6ca0c4ada5951e1566038e"},{"path":"jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx","start":81,"end":84,"sha256":"c1e8a1289ca3e3b19ac5f5dc5f16fe2651cb1a4a230b7b7fc6357ee1ac7556a1"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=artifacts facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e151db34deed0f32daa7ce5559197d9690dd68f958e73d55024deacbf19e35dd -->
**下载失败与不可下载项**
pywebview 桌面保存返回 'failed' 时用 window.alert 弹出 t('artifacts.downloadFailed') 提示且不再回退到浏览器下载；artifactDownloadUrl 返回 null 时 handleDownload 静默 return；既无 downloadUrl 也无 path 的条目下载按钮 disabled。

来源：[jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L45–L56](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx#L45-L56), [jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/filePreviewModel.ts:L54–L57](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/filePreviewModel.ts#L54-L57), [jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L105–L105](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx#L105-L105)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx","start":45,"end":56,"sha256":"0ae13c70de444e9272d3be802d9aa6482a1d26b56d4cad03a41d8c43b4fcc23e"},{"path":"jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/filePreviewModel.ts","start":54,"end":57,"sha256":"6ab19b764c81863b70daa41463f51e95ec92cef19dbec0bb59272f6e8f2122fb"},{"path":"jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx","start":105,"end":105,"sha256":"5ba1b87907ae44dc19f694153b1965b9e3174bf9624052ff625b915c54cbe850"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=artifacts facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3c0c769dc2a676abf0b61b6282049eabff46d36ad6718ff2ac311c0e46bfdcd0 -->
**无专属设置项；地址由 downloadUrl 优先于 path 的资源优先级与 inline=1 默认决定**
所示切片中产物功能没有独立开关或环境变量，行为由每项资源字段的优先级决定：artifactDownloadUrl 优先返回 downloadUrl，其次用 path 拼 /file-api/raw-file?path=<encodeURIComponent(path)>，两者皆无则返回 null；列表下载按钮正是在 !artifact.downloadUrl && !artifact.path 时 disabled。预览侧 inlineDownloadUrl 对非 blob:/data: 的 downloadUrl 默认追加 inline=1 并只返回 pathname+search；文本预览的 path 兜底为 /file-api/file-content?path=…&encoding=auto，二进制兜底为 raw-file。

来源：[jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/filePreviewModel.ts:L47–L67](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/filePreviewModel.ts#L47-L67), [jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L99–L112](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx#L99-L112)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":67,"path":"jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/filePreviewModel.ts","sha256":"cc3b6b7f0f83cde81123bb984dac2e7352d76dd79ffd082f5cb71e2f53753356","start":47},{"end":112,"path":"jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx","sha256":"dccc6a27268bdd4f46e021e88f35569d075bfd08f20b7030cdd8d35aa021a925","start":99}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=artifacts facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dbd52f78631dd632375cfe4d65b3ea53f2a0346086520769966cd96ac2450d55 -->
**检测到 pywebview download_file 即走桌面原生保存，失败告警后不再回退链接下载**
设计推断（非作者历史意图）：

（推断）handleDownload 在存在 window.pywebview.api.download_file 时调用 executeDesktopSave：收益是桌面宿主可接管为原生保存流程；代价是该分支返回 'failed' 时仅 window.alert 提示，随后第 55 行 return，跳过下方创建 a 标签点击的浏览器下载兜底（'cancelled' 结局不告警）。分支行为本身是所示代码的事实，收益/代价的取舍判断为本人分析，未见文档记载该意图。

来源：[jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L45–L64](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx#L45-L64)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":64,"path":"jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx","sha256":"9c1ffd3c779a7e670921e31bc2f01785dcab3da3abc4e89f2ae33eafcdf64cc3","start":45}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=artifacts facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0f3fbe501fc12061263ba4bc6ff43e177e9b32725eb0d2d9650ab00b73955afb -->
**node:test 断言 buildArtifacts 的过滤、token 归一与同身份去重**
入口是 tests/artifactCollection.test.mjs（node:test，从 ../node_modules/.cache/artifact-collection/artifactCollection.mjs 导入被测函数）。'rejects file entries without a display name or readable resource' 断言空白 name 与无可读资源的项被丢弃，且仅 token 的项 downloadUrl 归一为 /file-api/download?token=token-only；'duplicate file cards select the retained artifact with the same stable id' 用同 path 不同 token 的两条 assistant 消息断言 artifacts.length 为 1、id 与 fileArtifactId 一致且保留项取较新消息的 download_url。此处仅记录断言内容，不代表当前已运行通过。

来源：[jiuwenswarm/channels/web/frontend/tests/artifactCollection.test.mjs:L1–L4](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/tests/artifactCollection.test.mjs#L1-L4), [jiuwenswarm/channels/web/frontend/tests/artifactCollection.test.mjs:L42–L55](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/tests/artifactCollection.test.mjs#L42-L55), [jiuwenswarm/channels/web/frontend/tests/artifactCollection.test.mjs:L71–L92](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/tests/artifactCollection.test.mjs#L71-L92)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":4,"path":"jiuwenswarm/channels/web/frontend/tests/artifactCollection.test.mjs","sha256":"3723ef4eb4c0f69b3b57be3bb24cb5f237df357df649dcac4d2e5d70458d12be","start":1},{"end":55,"path":"jiuwenswarm/channels/web/frontend/tests/artifactCollection.test.mjs","sha256":"e394de4467b4315c729b1911dfebe8b146473af232657c401807832a05b60564","start":42},{"end":92,"path":"jiuwenswarm/channels/web/frontend/tests/artifactCollection.test.mjs","sha256":"005e51700af7ecdc8f41a2d842ab0e0919f4f25b13050abe0b7087fe5b64afd6","start":71}],"trace":[]} -->
<!-- /kb:depth -->
