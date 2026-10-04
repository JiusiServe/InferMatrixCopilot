---
title: "components-heartbeatpanel 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-heartbeatpanel 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/HeartbeatPanel/HeartbeatPagination.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=14b27b2c2118ba6866f9610c8e78ac031f50125c24d92a92789157a4798624c9 -->
**`jiuwenswarm/channels/web/frontend/src/components/HeartbeatPanel/HeartbeatPagination.tsx`**

- 源码声明的类型、组件或调用边界：`HEARTBEAT_PAGE_SIZE_OPTIONS`, `HEARTBEAT_PAGE_SIZE_DEFAULT`, `HeartbeatPaginationProps`, `HeartbeatPagination`, `pageSizeOptions`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useMemo } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { ChevronLeft, ChevronRight } from 'lucide-react';`；`import SimpleSelect from '../CronPanel/SimpleSelect';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/HeartbeatPanel/HeartbeatPagination.tsx#L1-L79)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/HeartbeatPanel/HeartbeatScheduleEditor.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0300980737e7843d366658b30dfe10dc9fdb359a42d6fa5939e93e0fb69132db -->
**`jiuwenswarm/channels/web/frontend/src/components/HeartbeatPanel/HeartbeatScheduleEditor.tsx`**

- 源码声明的类型、组件或调用边界：`HeartbeatScheduleEditorProps`, `KIND_TABS`, `TIMEZONE_SELECT_OPTIONS`, `HeartbeatScheduleEditor`, `minIntervalMinutes`, `intervalMinutes`, `cronError`, `nowStr`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useTranslation } from 'react-i18next';`；`import type { HeartbeatScheduleFormValue } from './heartbeatScheduleConvert';`；`import type { HeartbeatScheduleKind } from '../../types/heartbeat';`；`import { validateHeartbeatCronExpr } from './heartbeatCronValidation';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/HeartbeatPanel/HeartbeatScheduleEditor.tsx#L1-L128)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/HeartbeatPanel/HeartbeatStatusBadge.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5f8bb201e20137da69ac21f9ea9c6d84d7f88b8b6df05a2561b2239eeca73498 -->
**`jiuwenswarm/channels/web/frontend/src/components/HeartbeatPanel/HeartbeatStatusBadge.tsx`**

- 源码声明的类型、组件或调用边界：`HeartbeatStatusVariant`, `VARIANT_CLASS`, `HeartbeatStatusBadge`, `variant`, `Icon`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useTranslation } from 'react-i18next';`；`import type { HeartbeatJobStatus } from '../../types/heartbeat';`；`import { heartbeatStatusVariant, heartbeatStatusLabelKey, type HeartbeatStatusVariant } from './hear`；`import { RunningIcon, BoldRingIcon } from '../CronPanel/StatusBadge';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/HeartbeatPanel/HeartbeatStatusBadge.tsx#L1-L24)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/HeartbeatPanel/HeartbeatTaskDrawer.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e528142ba0d89d200b6872ed6c4e0cb015340d77fcfdff51cc19dae1296fa87f -->
**`jiuwenswarm/channels/web/frontend/src/components/HeartbeatPanel/HeartbeatTaskDrawer.tsx`**

- 源码声明的类型、组件或调用边界：`HeartbeatScheduleFormValue`, `NAME_MAX_LENGTH`, `PROMPT_MAX_LENGTH`, `HeartbeatTaskFormValue`, `emptyHeartbeatTaskForm`, `jobToHeartbeatTaskForm`, `HeartbeatTaskDrawerProps`, `HeartbeatTaskDrawer`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import type { HeartbeatConcurrencyPolicy, HeartbeatMeta, HeartbeatSessionDeletedPolicy, HeartbeatTas`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/HeartbeatPanel/HeartbeatTaskDrawer.tsx#L1-L225)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/HeartbeatPanel/heartbeatCronValidation.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1d615a76f20bebe1490a78b199ca3fa172890ad2b6eacd22e17a5b22f44445a7 -->
**`jiuwenswarm/channels/web/frontend/src/components/HeartbeatPanel/heartbeatCronValidation.ts`**

- 源码声明的类型、组件或调用边界：`validateHeartbeatCronExpr`, `trimmed`, `parts`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { validateCronExpr } from '../CronPanel/cronExprValidation.js';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/HeartbeatPanel/heartbeatCronValidation.ts#L1-L17)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/HeartbeatPanel/heartbeatScheduleConvert.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c06d9763e99d6e2c7087a62d208c4a07f532a3f88e56232a6aba5d9759933b3e -->
**`jiuwenswarm/channels/web/frontend/src/components/HeartbeatPanel/heartbeatScheduleConvert.ts`**

- 源码声明的类型、组件或调用边界：`HeartbeatScheduleFormValue`, `MIN_INTERVAL_SECONDS`, `emptyHeartbeatScheduleForm`, `epochSecondsToOnceLocal`, `d`, `pad`, `date`, `time`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { HeartbeatScheduleDTO, HeartbeatScheduleKind } from '../../types/heartbeat';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/HeartbeatPanel/heartbeatScheduleConvert.ts#L1-L80)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/HeartbeatPanel/heartbeatStatusText.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dc82165dbdec2c8816c002d067568778132b829c67656ac264e56c5031c6ac7e -->
**`jiuwenswarm/channels/web/frontend/src/components/HeartbeatPanel/heartbeatStatusText.ts`**

- 源码声明的类型、组件或调用边界：`HeartbeatStatusVariant`, `heartbeatStatusVariant`, `heartbeatStatusLabelKey`, `canHeartbeatRunNow`, `canHeartbeatToggleEnable`, `hasRemainingRuns`, `KNOWN_RUN_NOW_REJECT_REASONS`, `heartbeatRunNowMessageKey`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { HeartbeatJobStatus, HeartbeatRunStatus, HeartbeatScheduleDTO } from '../../types/heart`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/HeartbeatPanel/heartbeatStatusText.ts#L1-L93)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/HeartbeatPanel/index.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=72f60cb1e6795c2e9e279a7a81b2f24862a676797cf6746d2f0c456f8bc3b4a1 -->
**`jiuwenswarm/channels/web/frontend/src/components/HeartbeatPanel/index.tsx`**

- 源码声明的类型、组件或调用边界：`HeartbeatTaskFormValue`, `HeartbeatPanelProps`, `heartbeatJobToUI`, `formatHeartbeatTimestamp`, `d`, `HeartbeatPanel`, `sessionIdRef`, `loadAll`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useMemo, useRef, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import {`；`import { webRequest } from '../../services/webClient';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/HeartbeatPanel/index.tsx#L1-L664)。
<!-- /kb:file -->
