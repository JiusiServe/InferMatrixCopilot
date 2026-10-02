---
title: "语音输入、回复朗读与停止：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts:L130-L146, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts:L83-L90, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts:L168-L178]
---

# 语音输入、回复朗读与停止：实现深读

[功能概览](feature-speech-interaction.md) · [owner 入口](_index.md)

<!-- kb:depth feature=speech-interaction facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1d8d106b20f87793cfb54e49b7301980d9b25d2abec2eea80c3d4bcf7e98564c -->
**录音失败丢弃、空转写报错与卸载清理**
recorder.onerror 置 discardRecordingRef = true、释放麦克风并回调 'Microphone recording failed'；onstop 在 discard 或 chunks 为空时直接返回、不转写。ASR 返回空文本时抛出 'ASR did not return any text' 并经 onError 传播。组件卸载的 cleanup 置 discardRecordingRef = true、停掉仍在 recording 的 recorder 并释放麦克风，防止卸载后触发转写。

来源：[jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts:L130–L146](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts#L130-L146), [jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts:L83–L90](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts#L83-L90), [jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts:L168–L178](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts#L168-L178)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts","start":130,"end":146,"sha256":"eae230b081e6efe824f1d6c3ead9edda083bae99cc4061acc8d3729f5e2a8e2d"},{"path":"jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts","start":83,"end":90,"sha256":"94909861272a6f455d2c92acc84ecd00f410cfec7b33b8492dc2941c3b5fea5c"},{"path":"jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts","start":168,"end":178,"sha256":"542bb16629f8246759cd2ba531e702457458c3fd8bafd6a18f51e5fa8559e53d"}],"trace":[]} -->
<!-- /kb:depth -->
