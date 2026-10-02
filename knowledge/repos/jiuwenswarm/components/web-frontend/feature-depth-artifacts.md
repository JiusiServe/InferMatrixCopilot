---
title: "会话产物列表、预览与下载：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L23-L28, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/artifactCollection.ts:L95-L119, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/artifactCollection.ts:L75-L93, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L45-L64, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L105-L109, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L15-L21, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L49-L56, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L81-L84, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L45-L56, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/filePreviewModel.ts:L54-L57, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L105-L105]
feature: "artifacts"
entry_points: ["jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx", "jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/artifactCollection.ts", "jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/filePreviewModel.ts"]
source_globs: ["jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx", "jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/artifactCollection.ts", "jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/filePreviewModel.ts"]
---

# 会话产物列表、预览与下载：实现深读

[功能概览](feature-artifacts.md) · [owner 入口](_index.md)

<!-- kb:depth feature=artifacts facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=060c20b4e44e8a30e011492104f5504a1eb22556ea53c89dc8458e43a98fe856 -->
**从会话消息构建产物列表**
useSessionArtifacts 从 useChatStore 读取 activeSessionId 对应会话的 messages，经 useMemo 交给 buildArtifacts；buildArtifacts 遍历每条 message.fileItems，过滤无名或无资源的项后逐个调用 fileItemToArtifact 生成 ArtifactItem，再按 getFileIdentityKey 去重（冲突用 preferArtifact 合并），最后按 timestamp 降序返回数组供列表渲染。

调用路径：`jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx`（`useSessionArtifacts`） → `jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/artifactCollection.ts`（`buildArtifacts`） → `jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/artifactCollection.ts`（`fileItemToArtifact`）

来源：[jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx:L23–L28](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx#L23-L28), [jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/artifactCollection.ts:L95–L119](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/artifactCollection.ts#L95-L119), [jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/artifactCollection.ts:L75–L93](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/artifactCollection.ts#L75-L93)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx","start":23,"end":28,"sha256":"4062ef2d150be5e8b4ac2669b3a0b2d2b79127bd94a0e6c8fcd2ac99b5fda19c"},{"path":"jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/artifactCollection.ts","start":95,"end":119,"sha256":"999efec876d5cf0e6c2603c13dcae555ed14e423bf1d099ec7e70dfdc77b9bd9"},{"path":"jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/artifactCollection.ts","start":75,"end":93,"sha256":"da33d82df3f0799eff14877545259837cf62940ef0e8347b4525705491b60c92"}],"trace":[{"path":"jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx","symbol":"useSessionArtifacts","start":23,"end":28},{"path":"jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/artifactCollection.ts","symbol":"buildArtifacts","start":95,"end":103},{"path":"jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/artifactCollection.ts","symbol":"fileItemToArtifact","start":75,"end":93}]} -->
<!-- /kb:depth -->

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
