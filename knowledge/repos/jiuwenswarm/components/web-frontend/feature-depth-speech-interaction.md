---
title: "语音输入、回复朗读与停止：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts:L130-L146, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts:L83-L90, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts:L168-L178, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts:L107-L124, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts:L72-L94, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts:L76-L85, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/utils/tts.ts:L89-L111, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/taskAsr/featureFlag.ts:L3-L21, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts:L2-L2, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts:L76-L90, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/utils/tts.ts:L5-L5, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/utils/tts.ts:L94-L111, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/README.md:L45-L48]
feature: "speech-interaction"
entry_points: ["jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts", "jiuwenswarm/channels/web/frontend/src/features/taskAsr/featureFlag.ts", "jiuwenswarm/channels/web/frontend/src/utils/tts.ts", "jiuwenswarm/channels/web/frontend/src/hooks/useSpeech.ts"]
source_globs: ["jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts", "jiuwenswarm/channels/web/frontend/src/features/taskAsr/featureFlag.ts", "jiuwenswarm/channels/web/frontend/src/utils/tts.ts", "jiuwenswarm/channels/web/frontend/src/hooks/useSpeech.ts"]
---

# 语音输入、回复朗读与停止：实现深读

[功能概览](feature-speech-interaction.md) · [owner 入口](_index.md)

<!-- kb:depth feature=speech-interaction facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1d8d106b20f87793cfb54e49b7301980d9b25d2abec2eea80c3d4bcf7e98564c -->
**录音失败丢弃、空转写报错与卸载清理**
recorder.onerror 置 discardRecordingRef = true、释放麦克风并回调 'Microphone recording failed'；onstop 在 discard 或 chunks 为空时直接返回、不转写。ASR 返回空文本时抛出 'ASR did not return any text' 并经 onError 传播。组件卸载的 cleanup 置 discardRecordingRef = true、停掉仍在 recording 的 recorder 并释放麦克风，防止卸载后触发转写。

来源：[jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts:L130–L146](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts#L130-L146), [jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts:L83–L90](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts#L83-L90), [jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts:L168–L178](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts#L168-L178)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts","start":130,"end":146,"sha256":"eae230b081e6efe824f1d6c3ead9edda083bae99cc4061acc8d3729f5e2a8e2d"},{"path":"jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts","start":83,"end":90,"sha256":"94909861272a6f455d2c92acc84ecd00f410cfec7b33b8492dc2941c3b5fea5c"},{"path":"jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts","start":168,"end":178,"sha256":"542bb16629f8246759cd2ba531e702457458c3fd8bafd6a18f51e5fa8559e53d"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=speech-interaction facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2e19c0701794688f9e2d5443af6d6270ff535602f89ec6a399c08a2c58ff6403 -->
**useTaskAsr：startRecording 带守卫取麦克风，transcribe 转写后经 onTranscript 回传**
startRecording 在 `!isSupported || isRecording || isTranscribing` 时直接 return，否则 getUserMedia（echoCancellation/noiseSuppression/autoGainControl 全开），未挂载则停轨道；transcribe(blob) 对 `!blob.size || !mountedRef.current` 静默 return，经 blobBase64 以 `task.asr.transcribe`（timeoutMs 130_000）转写，trim 非空文本经 onTranscript 回调。

来源：[jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts:L107–L124](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts#L107-L124), [jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts:L72–L94](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts#L72-L94)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":124,"path":"jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts","sha256":"a9732783c2cb2f0883fc7f3d424370d2d59c8f023b19287f31ade2d2ec25d676","start":107},{"end":94,"path":"jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts","sha256":"9f0147974db83cd1e189c4ca726bb8126532b062dc4ac954d7c2c3e5973242ec","start":72}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=speech-interaction facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=209eca359dcf3f5c66039eafecd2d83e43b332d92e0a4e6d30ec4ca420c9a9a6 -->
**task.asr.transcribe 与 tts.synthesize 的请求参数、超时与返回契约**
transcribe 发送 `{ audio_base64, mime_type: blob.type || 'audio/webm' }`，选项 `{ timeoutMs: 130_000 }`，结果取 `response.text?.trim()`；fetchTtsAudio 发送 `{ text }`（可选 `session_id`）并透传 AbortSignal 调 `tts.synthesize`，空文本或请求出错时返回 null 而非抛出。

来源：[jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts:L76–L85](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts#L76-L85), [jiuwenswarm/channels/web/frontend/src/utils/tts.ts:L89–L111](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/tts.ts#L89-L111)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":85,"path":"jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts","sha256":"0341cf1ff77bf36ad86cd871230877f3c4fbc34104c14ad11ddaa7655bfb5bfb","start":76},{"end":111,"path":"jiuwenswarm/channels/web/frontend/src/utils/tts.ts","sha256":"333deb041ba5f7a3096580d97a394435bb11da3eccfd77b9707a0bc324308f7b","start":89}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=speech-interaction facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=49b63ca2f21d8a2830f20ad196cdfd03dfb42bb99dd49d4dc60a833732f98cbc -->
**Task ASR 开关：模块级默认 false，getServerSnapshot 恒返回 true**
模块级 `enabled = false` 起始；`setTaskAsrEnabled(next)` 值未变时直接 return，变化时遍历 listeners 通知；`useTaskAsrEnabled` 经 useSyncExternalStore 读取 `enabled`，getServerSnapshot 固定返回 true。

来源：[jiuwenswarm/channels/web/frontend/src/features/taskAsr/featureFlag.ts:L3–L21](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/taskAsr/featureFlag.ts#L3-L21)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":21,"path":"jiuwenswarm/channels/web/frontend/src/features/taskAsr/featureFlag.ts","sha256":"8f53bfbbdc5400a8bda9533e825f36eba1d74dd688c8db156eb0921de5c04d29","start":3}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=speech-interaction facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a902776ab53caf75c0d5e3da7aa499b708fbac2fe0992522e096c7604bec1f16 -->
**ASR 与 TTS 复用 webClient 的 webRequest，错误传播路径不同**
两条语音路径共用 services/webClient 的 webRequest：transcribe 发 'task.asr.transcribe'（audio_base64、mime_type，timeoutMs 130_000），fetchTtsAudio 发 'tts.synthesize'（trim 后文本，可选 session_id 与 signal）。抛错时 ASR 在 mountedRef 为真时经 onError 上报；TTS 捕获后 console.warn 并返回 null。

来源：[jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts:L2–L2](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts#L2-L2), [jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts:L76–L90](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts#L76-L90), [jiuwenswarm/channels/web/frontend/src/utils/tts.ts:L5–L5](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/tts.ts#L5-L5), [jiuwenswarm/channels/web/frontend/src/utils/tts.ts:L94–L111](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/tts.ts#L94-L111)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":2,"path":"jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts","sha256":"99ba9766afc8eee1a1659678c569ef4ae4b28fc65499fe98855857bc4a601f04","start":2},{"end":90,"path":"jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts","sha256":"c7002a21d263b1756b3304d12b6484322ff98fc29916d3cd72eb3d0f59c544ce","start":76},{"end":5,"path":"jiuwenswarm/channels/web/frontend/src/utils/tts.ts","sha256":"5b2a0836646f12de65145eacd19222d3328a45e4f3b97fec168d2f382be02b9d","start":5},{"end":111,"path":"jiuwenswarm/channels/web/frontend/src/utils/tts.ts","sha256":"ac55a33da34f32fc05157b53026303068b869e2ff980c5738657258789b325e3","start":94}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=speech-interaction facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=df97e53c157055229425a770e949fb2c881fdc8c0c8857e7036bb5b1acc5fb31 -->
**useTaskAsr 的 transcribe：mountedRef 守卫换来卸载后不触发回调与状态更新，迟到的转写文本在该分支被跳过**
设计推断（非作者历史意图）：

transcribe 在 `!blob.size || !mountedRef.current` 时直接返回；成功路径 `if (mountedRef.current) onTranscriptRef.current(text)` 与 finally 中的 `setIsTranscribing` 受同一守卫。推断收益：组件卸载后不再触发回调或状态更新；推断代价：卸载后才返回的转写文本在此分支被跳过，不经此路径送达。

来源：[jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts:L72–L94](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts#L72-L94)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":94,"path":"jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts","sha256":"9f0147974db83cd1e189c4ca726bb8126532b062dc4ac954d7c2c3e5973242ec","start":72}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=speech-interaction facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ad1eb0241a64b013379f165833bdfd1ded6f5e53c05d9f9ba5c4865b6a39af55 -->
**README 45–48 行文档化的语音交互手动步骤（未执行）**
文档中的人工验收步骤（本轮未执行）：

README 45–48 行记录手动操作与预期结果：点击麦克风按钮进行语音输入（STT）；鼠标悬停在 AI 回复上显示朗读按钮（TTS）；语音输入时可随时打断 AI 处理。本文按文档化手动流程引用该步骤，未执行。

来源：[jiuwenswarm/channels/web/frontend/README.md:L45–L48](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/README.md#L45-L48)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":48,"path":"jiuwenswarm/channels/web/frontend/README.md","sha256":"d2e3030dc0ab2f940c12313c2d79a4668ab7e6377d864935a2be66e5004f5b0b","start":45}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
