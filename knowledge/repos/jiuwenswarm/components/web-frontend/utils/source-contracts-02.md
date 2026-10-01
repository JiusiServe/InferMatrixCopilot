---
title: "utils 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# utils 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/skillPackageFile.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=72e1eed467ae067e9df5edad204133abb243f8f5d9ecdb54e054f52d0c969f3b -->
**`jiuwenswarm/channels/web/frontend/src/utils/skillPackageFile.ts`**

- 源码声明的类型、组件或调用边界：`SkillPackageFileLike`, `isSkillPackageFile`, `candidates`, `candidate`, `base`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/skillPackageFile.ts#L1-L23)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/svgDimensions.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=56cee11b175384d55ceac548e6c94b040ca4d9b4c199eaf149827c6e93ca337d -->
**`jiuwenswarm/channels/web/frontend/src/utils/svgDimensions.ts`**

- 源码声明的类型、组件或调用边界：`parseSvgViewBox`, `viewBox`, `parts`, `parsePixelAttribute`, `trimmed`, `n`, `getSvgNaturalWidth`, `viewBox`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/svgDimensions.ts#L1-L62)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/swarmflowAdvisory.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a22b997f15fc8dd5fc00c4c346a887adacd3801a94d637cb4bac1930e50c6c77 -->
**`jiuwenswarm/channels/web/frontend/src/utils/swarmflowAdvisory.ts`**

- 源码声明的类型、组件或调用边界：`SWARMFLOW_ADVISORY_SPAN`, `stripSwarmflowAdvisory`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/swarmflowAdvisory.ts#L1-L12)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/symphonyCommandDisplay.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=86a2c9a1326181a056ed6cb8ad16833375594a8625ccb5e00838635300aebe12 -->
**`jiuwenswarm/channels/web/frontend/src/utils/symphonyCommandDisplay.ts`**

- 源码声明的类型、组件或调用边界：`SymphonyCommandAction`, `SymphonyCommandLabel`, `VALUE_OPTIONS`, `SYMPHONY_COMMAND_TOOLS`, `tokenizeShell`, `tokens`, `current`, `quote`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`path: path && path !== '.' && path !== '/' ? shorten(path) : undefined,`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/symphonyCommandDisplay.ts#L1-L474)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/teamMemberAvatar.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8a009bf3286950ff7a021a09dc6e7d19543b572e943660c95ea746dc46021c52 -->
**`jiuwenswarm/channels/web/frontend/src/utils/teamMemberAvatar.ts`**

- 源码声明的类型、组件或调用边界：`TEAM_MEMBER_AVATARS`, `HUMAN_MEMBER_AVATARS`, `CLI_AGENT_AVATARS`, `CLI_AGENT_AVATAR_BACKGROUND`, `TEAM_MEMBER_BACKGROUND_COLORS`, `FNV_OFFSET_BASIS`, `FNV_PRIME`, `TeamMemberAvatarKind`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import teamLeaderAvatar from '../assets/teamleader.svg';`；`import userInTeamAvatar from '../assets/user-in-team.svg';`；`import teamAvatar2 from '../assets/Team-2.svg';`；`import teamAvatar3 from '../assets/Team-3.svg';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/teamMemberAvatar.ts#L1-L191)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/textEditCommands.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6f6a5e2682541a0ce15966be9c7c05abc4b8e57f03cf0635bd1b822ecb0b1c2d -->
**`jiuwenswarm/channels/web/frontend/src/utils/textEditCommands.ts`**

- 源码声明的类型、组件或调用边界：`DesktopLocalFilesEventDetail`, `NON_TEXT_INPUT_TYPES`, `SELECTION_INPUT_TYPES`, `TextEditTarget`, `isTextInputElement`, `type`, `isContentEditableElement`, `value`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import {`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/textEditCommands.ts#L1-L373)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/timestamp.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=95587c08a837b352e30dabdb21542bf82c40f6bcfb258e694f4de7378a951519 -->
**`jiuwenswarm/channels/web/frontend/src/utils/timestamp.ts`**

- 源码声明的类型、组件或调用边界：`VALID_YEAR_MIN`, `VALID_YEAR_MAX`, `yearOfEpochMs`, `looksLikePlausibleEpochMs`, `year`, `normalizeNumericEpoch`, `asMillis`, `parseTimestampToMs`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/timestamp.ts#L1-L67)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/tts.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8a6fb118af2278d0dc4810ad28ebf32f995bc2cd4fe9f2dc607b846fcf52c385 -->
**`jiuwenswarm/channels/web/frontend/src/utils/tts.ts`**

- 源码声明的类型、组件或调用边界：`TtsResponse`, `TTS_STOP_EVENT`, `CODE_BLOCK_RE`, `INLINE_CODE_RE`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { webRequest } from '../services/webClient';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/tts.ts#L1-L139)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/userId.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ede37cec76ee7a3d4b1eb78414c447ac409893aea4c01e92b9e6583e71f105a3 -->
**`jiuwenswarm/channels/web/frontend/src/utils/userId.ts`**

- 源码声明的类型、组件或调用边界：`USER_ID_STORAGE_KEY`, `readFromQuery`, `raw`, `readFromStorage`, `raw`, `writeToStorage`, `resolveUserId`, `fromQuery`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/userId.ts#L1-L66)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/uuid.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=398670e8cccbb61f7989f72392ea17a6902892cc71f26a41ecfa72f5f917d5b6 -->
**`jiuwenswarm/channels/web/frontend/src/utils/uuid.ts`**

- 源码声明的类型、组件或调用边界：`generateUuidV4`, `bytes`, `hex`, `prefixedMessageId`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/uuid.ts#L1-L31)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/writeClipboard.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2a5bcfdc61c5f069501213211b8bd5668192804ba88a6fd9797624bb9f088c59 -->
**`jiuwenswarm/channels/web/frontend/src/utils/writeClipboard.ts`**

- 源码声明的类型、组件或调用边界：`writeClipboard`, `exec`, `el`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/writeClipboard.ts#L1-L48)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/wsEventDedup.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=88011f6e677e427bf0585e32d4072445d445daf5ac47717bf84df024cf6e62e2 -->
**`jiuwenswarm/channels/web/frontend/src/utils/wsEventDedup.ts`**

- 源码声明的类型、组件或调用边界：`stringifyPayloadForDedup`, `serialized`, `makeEventDedupKey`, `payloadSessionId`, `payloadEventType`, `payloadRequestId`, `nestedToolCall`, `toolCallId`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/wsEventDedup.ts#L1-L66)。
<!-- /kb:file -->
