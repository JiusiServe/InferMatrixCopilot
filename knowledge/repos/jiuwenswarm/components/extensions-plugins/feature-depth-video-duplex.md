---
title: "音视频双工扩展：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/video_duplex/backend/joyai_provider.py:L65-L79, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/video_duplex/backend/joyai_provider.py:L82-L89]
feature: "video-duplex"
entry_points: ["jiuwenswarm/extensions/video_duplex/backend/tasks/rail.py"]
source_globs: ["jiuwenswarm/extensions/video_duplex/backend/tasks/rail.py", "jiuwenswarm/extensions/video_duplex/*"]
---

# 音视频双工扩展：实现深读

[功能概览](feature-video-duplex.md) · [owner 入口](_index.md)

<!-- kb:depth feature=video-duplex facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=aadd61c205667425c68cc212bd705293f50fdbb2bb1286ad60261dd9bf76cb0e -->
**语音端点与原生通道判定**
voice_config 的 ASR/TTS WebSocket 地址按 VOICE_ASR_ENDPOINT（或 VOICE_TTS_ENDPOINT）> JOYAI_ASR_WS_URL（或 JOYAI_TTS_WS_URL）> 默认 ws://127.0.0.1:8994/ws/asr 与 ws://127.0.0.1:8992/ws/tts 解析。uses_native_voice_channel 仅在 video_live_mode == "joyai" 时可能为真：VOICE_PROTOCOL 非空则必须等于 "native_ws"，否则看 JOYAI_VOICE_PROVIDER（默认 "native"），值为 openai/openai_compatible/siliconflow 时返回 False。

来源：[jiuwenswarm/extensions/video_duplex/backend/joyai_provider.py:L65–L79](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/joyai_provider.py#L65-L79), [jiuwenswarm/extensions/video_duplex/backend/joyai_provider.py:L82–L89](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/joyai_provider.py#L82-L89)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/extensions/video_duplex/backend/joyai_provider.py","start":65,"end":79,"sha256":"64dbd210934c088fdeaeed64077f28e386b294ae7be1d913cd1dd8f57c5516e6"},{"path":"jiuwenswarm/extensions/video_duplex/backend/joyai_provider.py","start":82,"end":89,"sha256":"664dd5679c67f5816c9ca903b636d1244443dd94ed077cf84f30764f0506e7bb"}],"trace":[]} -->
<!-- /kb:depth -->
