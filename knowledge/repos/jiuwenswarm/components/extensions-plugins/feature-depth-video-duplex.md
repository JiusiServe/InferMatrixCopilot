---
title: "音视频双工扩展：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/video_duplex/backend/joyai_provider.py:L65-L79, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/video_duplex/backend/joyai_provider.py:L82-L89, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/video_duplex/backend/tasks/rail.py:L7-L23, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/video_duplex/backend/tasks/rail.py:L39-L59, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/video_duplex/backend/tasks/execution.py:L98-L126, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/video_duplex/tests/backend/test_video_live.py:L1632-L1647, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/video_duplex/backend/tasks/rail.py:L42-L47, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/video_duplex/backend/tasks/execution.py:L58-L70, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/video_duplex/backend/tasks/rail.py:L42-L53, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/video_duplex/backend/tasks/rail.py:L54-L65, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/video_duplex/backend/tasks/server_adapter.py:L13-L52]
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

<!-- kb:depth feature=video-duplex facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=915332ede5907c1156f63add2a7e447ff9b094216d2679af7c4bf74931906c6c -->
**task_checkpoint 回调路径：按 managed_task_request 匹配绑定后在模型调用前检查**
Root Agent 触发 before_model_call 后进入 task_checkpoint：从 ctx.extra 的 run_context.extra 取 managed_task_request，在 rail.managed_tasks 中按 request_id（无 id 时按 binding.root is ctx.agent）匹配绑定；before_model 阶段依次执行 capture_execution()、check()、before_model()，作用于该次模型调用。

来源：[jiuwenswarm/extensions/video_duplex/backend/tasks/rail.py:L7–L23](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/tasks/rail.py#L7-L23), [jiuwenswarm/extensions/video_duplex/backend/tasks/rail.py:L39–L59](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/tasks/rail.py#L39-L59)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":23,"path":"jiuwenswarm/extensions/video_duplex/backend/tasks/rail.py","sha256":"a816fbf8eec0a9169557a31b63ee077856d2276f928f3f80322bc36b5f4bdb7e","start":7},{"end":59,"path":"jiuwenswarm/extensions/video_duplex/backend/tasks/rail.py","sha256":"8828d7c66e3b6be8a03f61b532eb1bce4490801f119b358a1bd15a995085c672","start":39}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=video-duplex facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d63288d13cda3af961550e073a81e98d79cc60b75456ec24332c4bd1c3c0aa9d -->
**task_checkpoint 依赖 rail.managed_tasks：request_id 匹配、假值时回退 root 身份**
task_checkpoint 在 rail.managed_tasks 中按 binding.request_id == managed_task_request 匹配，request_id 为假值时回退按 binding.root is ctx.agent 匹配；该注册表由 bind_task_execution 经 adapter.task_execution_binding 填充，同 session_id 已占用时抛 RuntimeError("Task execution already bound")。

来源：[jiuwenswarm/extensions/video_duplex/backend/tasks/rail.py:L42–L47](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/tasks/rail.py#L42-L47), [jiuwenswarm/extensions/video_duplex/backend/tasks/execution.py:L58–L70](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/tasks/execution.py#L58-L70)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":47,"path":"jiuwenswarm/extensions/video_duplex/backend/tasks/rail.py","sha256":"e9e9f97aa092402bb64d8445144b7eec4c263d4267a9576c223a60cf9c766fc0","start":42},{"end":70,"path":"jiuwenswarm/extensions/video_duplex/backend/tasks/execution.py","sha256":"d86840a79385aafc4a28b474ebdceb46851e87004237148e12eb147cf9e76697","start":58}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=video-duplex facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9cddead1294b7aca72b2295fce42ce8e2ffa0ea1678543f9b35cec86498b2222 -->
**task_checkpoint：无匹配绑定且 managed_task_request 为真值才中止；root 匹配分支包装异常**
rail.managed_tasks 无匹配绑定时，仅当 managed_task_request 为真值才抛 AbortError("TASK_EXECUTION_BINDING_CLOSED")，为假值则直接 return；在 ctx.agent is checkpoint.root 的分支内，stage 调用抛出的异常被包装为 AbortError("TASK_CHECKPOINT_REJECTED", cause=exc) 后重抛。

来源：[jiuwenswarm/extensions/video_duplex/backend/tasks/rail.py:L42–L53](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/tasks/rail.py#L42-L53), [jiuwenswarm/extensions/video_duplex/backend/tasks/rail.py:L54–L65](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/tasks/rail.py#L54-L65)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":53,"path":"jiuwenswarm/extensions/video_duplex/backend/tasks/rail.py","sha256":"cde7fca781d3357801d0fa811e4d271c569abb3c6d9ebbd85d320a4b20d65b37","start":42},{"end":65,"path":"jiuwenswarm/extensions/video_duplex/backend/tasks/rail.py","sha256":"d1bf72307011eef943a798632e523bd907f185e39439851d154e9c0913015e36","start":54}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=video-duplex facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1eb423780bd1ab383b5ad58f2393cf1b93e11166235f0f4b0775634fa657f812 -->
**结算上报可转后台任务：不阻塞收尾，但失败仅记 warning（推断）**
设计推断（非作者历史意图）：

bind_task_execution 收尾时若 native_executions 未全部 done，report_settlement 改由 asyncio.create_task 后台执行；推断收益：请求方 finally 不必等待远端 close/settle；推断代价：该后台任务异常只触发 logger.warning('Task settlement acknowledgement failed: …')，不传播给原调用。

来源：[jiuwenswarm/extensions/video_duplex/backend/tasks/execution.py:L98–L126](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/tasks/execution.py#L98-L126)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":126,"path":"jiuwenswarm/extensions/video_duplex/backend/tasks/execution.py","sha256":"7b194e7bf9574eaeaf3f9a1d901aa06533a6cf855cfdd41e99fc4d8d9ce72bf8","start":98}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=video-duplex facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d891c76547e5d3639f072a6b230a00ebc868208ccc3d2af06f8b1179852a5d6c -->
**test_joyai_frame_handler_rejects_non_image_payload 运行时断言非图片载荷返回 BAD_REQUEST**
该 pytest.mark.asyncio 测试以 {'frame_data_url': 'not-an-image'} 直接调用 channel.handlers['video.joyai.frame']，并把 joyai_provider.request_frame 替换为被调即抛 AssertionError 的 fail_request；断言最后一个响应 code=='BAD_REQUEST'，即非图片载荷在触达 JoyAI 前被拒。

来源：[jiuwenswarm/extensions/video_duplex/tests/backend/test_video_live.py:L1632–L1647](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/tests/backend/test_video_live.py#L1632-L1647)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1647,"path":"jiuwenswarm/extensions/video_duplex/tests/backend/test_video_live.py","sha256":"ecd622866dc05f8261d6e86b6f373962a3ebbe93a80ba9197887dd47244a4821","start":1632}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->

<!-- kb:depth feature=video-duplex facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6fb8bcf8469ef312fe5dc3a15d955cbd1d29465308325d5fda2d468ffe237e16 -->
**VoiceTaskServerAdapter.methods 声明两方法；handle 分支的真值校验与返回契约**
methods 仅声明 VOICE_TASK_CHECKPOINT_ACK 与 VOICE_TASK_FILES；handle 按 req_method 分支：ACK 分支返回 accepted，另一分支要求 session 匹配 managed-task-[0-9a-f]{32} 且 execution_request_id 为真值，否则抛 ValueError("Invalid task execution identity")。其后 guard、user_id 校验与 flush_pending_writes(timeout=5) 仍可抛错中止返回；全部通过后仅收集该 execution_id 的 chat.file 记录为 files，并以 AgentResponse ok=True 延续原请求与渠道标识。

来源：[jiuwenswarm/extensions/video_duplex/backend/tasks/server_adapter.py:L13–L52](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/tasks/server_adapter.py#L13-L52)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":52,"path":"jiuwenswarm/extensions/video_duplex/backend/tasks/server_adapter.py","sha256":"2f1120e4c16c58b82a586ced4886cbe512cb5d7c37c2718ec75817aaab89379b","start":13}],"trace":[]} -->
<!-- /kb:depth -->
