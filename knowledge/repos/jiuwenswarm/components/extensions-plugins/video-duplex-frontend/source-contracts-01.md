---
title: "video-duplex-frontend 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# video-duplex-frontend 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/frontend/TaskFullDuplexAction.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=36df93785b874006bf8453774242845199ffb026e9d47df000c53b6a2b4947b9 -->
**`jiuwenswarm/extensions/video_duplex/frontend/TaskFullDuplexAction.tsx`**

- 源码声明的类型、组件或调用边界：`parseEnabled`, `TaskFullDuplexAction`, `enabled`, `cancelled`, `retryTimer`, `load`, `handleClick`, `readySessionId`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect } from 'react';`；`import { AudioWaveform, LoaderCircle, Square } from 'lucide-react';`；`import type { ApplicationPluginTaskInputActionProps } from '../../../channels/web/frontend/src/appli`；`import { useTaskFullDuplexEnabled, setTaskFullDuplexEnabled } from '../../../channels/web/frontend/s`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/frontend/TaskFullDuplexAction.tsx#L1-L96)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/frontend/TaskFullDuplexRuntime.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9dcb4398265862c1c415b5629686609af9c988b88f4e5fe19ebb86b6b1e69f46 -->
**`jiuwenswarm/extensions/video_duplex/frontend/TaskFullDuplexRuntime.tsx`**

- 源码声明的类型、组件或调用边界：`VideoLivePanelHandle`, `WAIT_REASON_LABELS`, `PersistedTimelineEvent`, `historyQueues`, `timelineEventId`, `timestampSeconds`, `parsed`, `persistTimelineEvent`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useRef } from "react";`；`import type { ApplicationPluginTaskRuntimeProps } from "../../../channels/web/frontend/src/applicati`；`import { useTaskFullDuplexEnabled } from "../../../channels/web/frontend/src/features/taskFullDuplex`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/frontend/TaskFullDuplexRuntime.tsx#L1-L599)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/frontend/VideoDuplexSettings.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6a3daa25c7c44de37096f797aeb9861aeb2dc7f58d9c0f74f367ecef88d61d6c -->
**`jiuwenswarm/extensions/video_duplex/frontend/VideoDuplexSettings.tsx`**

- 源码声明的类型、组件或调用边界：`Provider`, `VoiceProtocol`, `SettingsValues`, `SettingsPayload`, `EMPTY_SETTINGS`, `SECRET_KEYS`, `secretPlaceholder`, `VideoDuplexSettingsProps`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { FormEvent, useEffect, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { LoaderCircle, Power, Save, Settings2 } from 'lucide-react';`；`import type { ApplicationPluginSettingsProps } from '../../../channels/web/frontend/src/applicationP`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/frontend/VideoDuplexSettings.tsx#L1-L252)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/duplex-capture.js pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8fbeb02d2ba13f012fe4a9b1a12e8c4101e7e192a1f28363d13b29ed4a0038a3 -->
**`jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/duplex-capture.js`**

- 源码声明的类型、组件或调用边界：`DuplexCaptureProcessor`, `channel`, `index`, `sample`, `ready`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/duplex-capture.js#L1-L25)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/duplex-playback.js pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=114ee85b0719ef6ab88c5b621ac228d663fbc1a7bbc27941221c6f475378c125 -->
**`jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/duplex-playback.js`**

- 源码声明的类型、组件或调用边界：`DuplexPlaybackProcessor`, `wasEmpty`, `output`, `target`, `chunk`, `count`, `remainingBeforeChunk`, `index`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/duplex-playback.js#L1-L156)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/index.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=46cf847bd2d8118d94e74576112633bf64068e1d1b84b757e99b8501d3817751 -->
**`jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/index.tsx`**

- 源码声明的类型、组件或调用边界：`VideoSource`, `CapturedFrame`, `ScreenSource`, `FRAME_INTERVAL_MS`, `MAX_FRAMES`, `MAX_SCREENS`, `MAX_FRAME_WIDTH`, `SCREEN_PREVIEW_FRAME_RATE`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { TASK_ACCEPTED_INSTRUCTIONS } from './taskPrompts';`；`import {`；`import {`；`import { useTranslation } from 'react-i18next';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/index.tsx#L1-L1434)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/joyaiPromptLifecycle.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8ac05eeb004e4eb82eaa843fb573228be1195a9955d1b8e06b5b6f8298fd71de -->
**`jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/joyaiPromptLifecycle.ts`**

- 源码声明的类型、组件或调用边界：`ClaimedJoyAIPrompt`, `PromptWaiter`, `PendingJoyAIPrompt`, `JoyAIPromptLifecycle`, `waiter`, `pending`, `settled`, `pending`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/joyaiPromptLifecycle.ts#L1-L84)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/joyaiProvider.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=adcf3ac01fb05b223ecfd32737a6133a318deec926f8c8d22d569ffed477edc9 -->
**`jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/joyaiProvider.ts`**

- 源码声明的类型、组件或调用边界：`ReplyLanguage`, `FRAME_POLL_INTERVAL_MS`, `RATE_LIMIT_BASE_COOLDOWN_MS`, `RATE_LIMIT_MAX_COOLDOWN_MS`, `FRAME_POLL_CLIENT_BUILD`, `isJoyAIRateLimit`, `candidate`, `message`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { normalizeReplyLanguage, type ReplyLanguage } from './replyLanguage';`；`import { webClient, webRequest } from '../../../../channels/web/frontend/src/services/webClient';`；`import { canPlayJoyAIResponse, JoyAITtsInterruptionState, JoyAIVoiceSession } from './joyaiVoice';`；`import { assistantSpeechText } from './searchPresentation';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/joyaiProvider.ts#L1-L583)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/joyaiToolContext.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ec7a7e450f33f393212fea5fad8c786207f78898c25f3f5b1b3e04168294c488 -->
**`jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/joyaiToolContext.ts`**

- 源码声明的类型、组件或调用边界：`JoyAIToolContextEntry`, `JoyAIToolContextBatch`, `MAX_PENDING_TOOL_RESULTS`, `MAX_ATTACHED_TOOL_RESULTS`, `MAX_TOOL_CONTEXT_CHARS`, `compact`, `normalized`, `rememberJoyAIToolContext`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/joyaiToolContext.ts#L1-L69)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/joyaiVoice.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7772833a8d84e8f95e6474cdff3c2ecd8be3d4ead254aa19563f6f76d11d4cc6 -->
**`jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/joyaiVoice.ts`**

- 源码声明的类型、组件或调用边界：`TARGET_RATE`, `PRE_ROLL_MS`, `MAX_TURN_MS`, `PCM_STREAM_START_BUFFER_MS`, `JoyAIVoiceCallbacks`, `readableError`, `canPlayJoyAIResponse`, `JoyAITtsInterruptionState`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { SileroVad, SpeechDetection } from '../../../../channels/web/frontend/src/utils/speechD`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/joyaiVoice.ts#L1-L444)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/qwenOmniProtocol.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b28a3a2ecd133538afada9e066c2580ed3df75bd53db037a9145f02bd768008f -->
**`jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/qwenOmniProtocol.ts`**

- 源码声明的类型、组件或调用边界：`QWEN_MAX_BASE64_IMAGE_BYTES`, `QWEN_SESSION_INSTRUCTIONS`, `QwenOmniSessionOptions`, `QwenOmniMediaBatch`, `QwenOmniMediaSnapshot`, `createQwenOmniSessionUpdate`, `createQwenOmniTextTurnEvents`, `createQwenOmniToolResultEvents`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { normalizeReplyLanguage, speakLanguageInstruction } from './replyLanguage.js';`；`import {`；`import type { RealtimeBrief } from './types.js';`；`import type { QwenOmniToolResultContext } from './qwenOmniTools.js';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/qwenOmniProtocol.ts#L1-L159)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/qwenOmniSession.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=da4166b889a7c39f693c269681181b6c49b438f6502a9dcfdb8584ee3397db0e -->
**`jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/qwenOmniSession.ts`**

- 源码声明的类型、组件或调用边界：`RealtimeDuplexConfig`, `RealtimeToolResult`, `RealtimeDuplexCallbacks`, `resolveRealtimeUrl`, `protocol`, `browserBase`, `base`, `createRealtimeDuplexSession`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { taskCancellationNotice, taskQuestionNotice } from './taskPrompts.js';`；`import {`；`import { getWsBase } from '../../../../channels/web/frontend/src/utils/env.js';`；`import type { RealtimeBrief } from './types.js';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/qwenOmniSession.ts#L1-L1022)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/qwenOmniTools.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3804c29039a1da8ebb4d648ab22d5e482163831a4d58d8d3230d069ca8334fc2 -->
**`jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/qwenOmniTools.ts`**

- 源码声明的类型、组件或调用边界：`QWEN_OMNI_DELEGATE_TOOL_NAME`, `QWEN_OMNI_LEGACY_RESEARCH_TOOL_NAME`, `QwenOmniFunctionCall`, `QWEN_OMNI_DELEGATE_ARGUMENT_NAMES`, `asRecord`, `parseQwenOmniFunctionCall`, `name`, `callId`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { TASK_OPERATION_INSTRUCTIONS, taskResultNotice } from './taskPrompts.js';`；`import type { RealtimeBrief } from './types.js';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/qwenOmniTools.ts#L1-L142)。
<!-- /kb:file -->
