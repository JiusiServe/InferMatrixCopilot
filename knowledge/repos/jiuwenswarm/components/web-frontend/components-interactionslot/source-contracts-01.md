---
title: "components-interactionslot 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-interactionslot 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/InteractionSlot/AuthorizationPrompt.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c663d7f9f0b6f2e9d6c700efa87e4883f54f9e76b68c5d77a9d85178014517f7 -->
**`jiuwenswarm/channels/web/frontend/src/components/InteractionSlot/AuthorizationPrompt.tsx`**

- 源码声明的类型、组件或调用边界：`AuthSemantic`, `AuthorizationPromptProps`, `ACTION_ORDER`, `PROSE_CLS`, `ResolvedAction`, `optionSemantic`, `resolveAuthorizationActions`, `primary`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useMemo, useRef, useState } from 'react';`；`import { createPortal } from 'react-dom';`；`import { useTranslation } from 'react-i18next';`；`import ReactMarkdown from 'react-markdown';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/InteractionSlot/AuthorizationPrompt.tsx#L1-L327)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/InteractionSlot/InteractionPrompt.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=59299ef47a9dba5a52db8e9f70d86e70d2d924a9555c1da3fb8825cab2cbd730 -->
**`jiuwenswarm/channels/web/frontend/src/components/InteractionSlot/InteractionPrompt.tsx`**

- 源码声明的类型、组件或调用边界：`QaSummaryData`, `CUSTOM_OPTION_LABEL`, `MAX_PAGES`, `SKIPPED_ANSWER_TEXT`, `CANCELLED_ANSWER_TEXT`, `InteractionPromptProps`, `PageState`, `emptyPage`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useMemo, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import ReactMarkdown from 'react-markdown';`；`import remarkGfm from 'remark-gfm';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/InteractionSlot/InteractionPrompt.tsx#L1-L445)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/InteractionSlot/QaSummaryCard.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=570a07af7c457491fa72080f0dea76d354a1d2001e47b7cf278cbbaa756f0431 -->
**`jiuwenswarm/channels/web/frontend/src/components/InteractionSlot/QaSummaryCard.tsx`**

- 源码声明的类型、组件或调用边界：`QaSummaryCardProps`, `QaSummaryCard`, `data`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { FileText } from 'lucide-react';`；`import { parseQaSummaryContent } from './qaSummary';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/InteractionSlot/QaSummaryCard.tsx#L1-L52)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/InteractionSlot/index.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e35dc5afb99c0bcaf2225fe2d9ddb95c826dd2e30fd75d073c4794080640adcd -->
**`jiuwenswarm/channels/web/frontend/src/components/InteractionSlot/index.tsx`**

- 源码声明的类型、组件或调用边界：`InteractionSlotProps`, `InteractionSlot`, `activeSessionId`, `pending`, `kind`, `isAuth`, `variant`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useChatStore } from '../../stores';`；`import type { UserAnswer } from '../../types';`；`import { AuthorizationPrompt } from './AuthorizationPrompt';`；`import { InteractionPrompt } from './InteractionPrompt';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/InteractionSlot/index.tsx#L1-L51)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/InteractionSlot/permissionTextI18n.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e75080e85e3e0e436a96eb8ca8270b8a92efb00f174b56d8e5d68b186d72482d -->
**`jiuwenswarm/channels/web/frontend/src/components/InteractionSlot/permissionTextI18n.ts`**

- 源码声明的类型、组件或调用边界：`EXACT_MAP`, `RISK_LABEL_MAP`, `RISK_TITLE_RE`, `HEADER_PREFIX_RE`, `TOOL_AUTH_FALLBACK_RE`, `modeSuffixMatch`, `prefixMatch`, `label`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/InteractionSlot/permissionTextI18n.ts#L1-L132)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/InteractionSlot/promptRouting.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1adc7464e6ea3fc075c5f6a594290e926754c0c8b1ab16ee6a7f0a24894039bb -->
**`jiuwenswarm/channels/web/frontend/src/components/InteractionSlot/promptRouting.ts`**

- 源码声明的类型、组件或调用边界：`PromptKind`, `AUTHORIZATION_SOURCES`, `isEvolutionPrompt`, `rid`, `isPlanApprovalPrompt`, `isSkillPackagePrompt`, `classifyPrompt`, `firstOptions`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { AskUserQuestionPayload } from '../../types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/InteractionSlot/promptRouting.ts#L1-L94)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/InteractionSlot/qaSummary.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1e70a563f71f5155b727397e5cd43e721ce8a4db4936ade8d6f3c59983b8df73 -->
**`jiuwenswarm/channels/web/frontend/src/components/InteractionSlot/qaSummary.ts`**

- 源码声明的类型、组件或调用边界：`QA_SUMMARY_PREFIX`, `QaSummaryItem`, `QaSummaryData`, `MASKED_ANSWER`, `SENSITIVE_QUESTION_MARKERS`, `maskSensitiveSummary`, `buildQaSummaryContent`, `isQaSummaryContent`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/InteractionSlot/qaSummary.ts#L1-L68)。
<!-- /kb:file -->
