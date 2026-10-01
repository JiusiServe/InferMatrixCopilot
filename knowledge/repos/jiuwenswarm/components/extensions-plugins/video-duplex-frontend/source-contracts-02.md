---
title: "video-duplex-frontend 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# video-duplex-frontend 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/replyLanguage.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=527b2895a8fc629f35c9d1dc93bb3d552ef63eded78d8f2003ca23c07460ff9c -->
**`jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/replyLanguage.ts`**

- 源码声明的类型、组件或调用边界：`ReplyLanguage`, `normalizeReplyLanguage`, `speakLanguageInstruction`, `preserve`, `announceLanguageInstruction`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/replyLanguage.ts#L1-L9)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/searchPresentation.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=719df92a87c10302da1e4189bba6b7b483398d47fa66d1f2fe346afb1a88d239 -->
**`jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/searchPresentation.ts`**

- 源码声明的类型、组件或调用边界：`cleanModelText`, `SearchStatusItem`, `searchAwareToolStatus`, `foreground`, `runningCount`, `background`, `assistantSpeechText`, `normalized`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { SearchJobPayload, SearchProgressJob } from './types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/searchPresentation.ts#L1-L106)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/taskPrompts.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b832f9b35b002d9693035458167263970c18500a963c8440fda9f607299ab54f -->
**`jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/taskPrompts.ts`**

- 源码声明的类型、组件或调用边界：`QWEN_OMNI_TOOL_INSTRUCTIONS`, `TASK_ACCEPTED_INSTRUCTIONS`, `TASK_OPERATION_INSTRUCTIONS`, `taskCancellationNotice`, `taskQuestionNotice`, `taskResultNotice`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { RealtimeBrief } from './types.js';`；`import { announceLanguageInstruction, normalizeReplyLanguage } from './replyLanguage.js';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/taskPrompts.ts#L1-L59)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/types.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5485f21771041e74260c3a709c28b4c743cef8469f0ef5ef66d24af61ce97902 -->
**`jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/types.ts`**

- 源码声明的类型、组件或调用边界：`ChatContextItem`, `RealtimeBrief`, `SearchJobPayload`, `SearchProgressEntry`, `SearchProgressJob`, `SearchJobState`, `AgentAction`, `VideoSessionConfig`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { FileDownloadItem } from '../../../../channels/web/frontend/src/types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/types.ts#L1-L120)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/videoSource.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5919e1c21812b69c7fef2f81720dc6820352e14b3ad5a114c7a7b2c7a770048d -->
**`jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/videoSource.ts`**

- 源码声明的类型、组件或调用边界：`RealtimeVideoFrame`, `RealtimeVideoFrameScheduler`, `latestBySource`, `latest`, `offset`, `index`, `frame`, `RealtimeVideoSource`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/frontend/VideoLivePanel/videoSource.ts#L1-L89)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/frontend/index.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e886f4dbc30b272bb631f2f081e45b518aa84a4c5e983c9e7f986b00db383057 -->
**`jiuwenswarm/extensions/video_duplex/frontend/index.tsx`**

- 源码声明的类型、组件或调用边界：`applicationPluginId`, `applicationPluginTaskInputAction`, `applicationPluginTaskRuntime`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { VideoLivePanel } from "./VideoLivePanel";`；`import { TaskFullDuplexAction } from "./TaskFullDuplexAction";`；`import { TaskFullDuplexRuntime } from "./TaskFullDuplexRuntime";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/frontend/index.tsx#L1-L8)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/frontend/taskDuplexJobs.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1aaba0242cdaaf7a0d14e9f4b8732c808357eaf57d296a5032a76363524df422 -->
**`jiuwenswarm/extensions/video_duplex/frontend/taskDuplexJobs.ts`**

- 源码声明的类型、组件或调用边界：`ConversationJob`, `TaskDuplexJobs`, `searchSessionId`, `jobId`, `searchSessionId`, `sessionId`, `previous`, `job`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { SearchJobPayload } from "./VideoLivePanel/types";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/frontend/taskDuplexJobs.ts#L1-L86)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/frontend/taskFullDuplexRuntimeStore.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fa6033ab91893b75baa8befcefaf16920bbd9b1f71f3eb0dff0d3c4199f2af09 -->
**`jiuwenswarm/extensions/video_duplex/frontend/taskFullDuplexRuntimeStore.ts`**

- 源码声明的类型、组件或调用边界：`TaskFullDuplexRuntimeState`, `TaskFullDuplexRuntimeSnapshot`, `controller`, `bindSession`, `snapshot`, `listeners`, `errorToast`, `publish`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useSyncExternalStore } from 'react';`；`import { toast } from '../../../channels/web/frontend/src/components/ui/Toast/toastStore';`；`import type { VideoLivePanelHandle } from './VideoLivePanel';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/frontend/taskFullDuplexRuntimeStore.ts#L1-L78)。
<!-- /kb:file -->
