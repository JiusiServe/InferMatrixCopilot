---
title: "components-cronpanel 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-cronpanel 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/CronPanel/index.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ebbb45ef93fc9529b7ac491611858bd1b9ee5c3b6cec031964ab8ec033891ec8 -->
**`jiuwenswarm/channels/web/frontend/src/components/CronPanel/index.tsx`**

- 源码声明的类型、组件或调用边界：`CronTaskFormValue`, `PAGE_SIZE_OPTIONS`, `DEFAULT_PAGE_SIZE`, `buildPageList`, `pages`, `start`, `end`, `p`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';`；`import { createPortal } from 'react-dom';`；`import { useTranslation } from 'react-i18next';`；`import { ChevronDown, ChevronLeft, ChevronRight, TrendingUp, Newspaper, Briefcase } from 'lucide-rea`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/CronPanel/index.tsx#L1-L1864)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/CronPanel/scheduleConvert.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2d6d8fe89cd113e560cd26a43befaca5c4d5d60ea78d87dd3a876fd4432186e5 -->
**`jiuwenswarm/channels/web/frontend/src/components/CronPanel/scheduleConvert.ts`**

- 源码声明的类型、组件或调用边界：`pad2`, `parseTime`, `match`, `h`, `m`, `isWildcard`, `parseSingleInt`, `parseIntList`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { CronSchedule } from '../../types/cron';`；`import { normalizeWeekAlphas } from './cronWeekAlpha';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/CronPanel/scheduleConvert.ts#L1-L307)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/CronPanel/useClickOutside.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f1d1f9444ce698ad76b509b261591e000c259b3448b8baec4c216271c101f4c9 -->
**`jiuwenswarm/channels/web/frontend/src/components/CronPanel/useClickOutside.ts`**

- 源码声明的类型、组件或调用边界：`RefObject`, `useClickOutside`, `handlePointerDown`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, type RefObject } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/CronPanel/useClickOutside.ts#L1-L14)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/CronPanel/xiaoyiCronTarget.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d5e79acd35a8631849d7f6ce60b60ecef911094e7cd2e2556db1e413ac0286a5 -->
**`jiuwenswarm/channels/web/frontend/src/components/CronPanel/xiaoyiCronTarget.ts`**

- 源码声明的类型、组件或调用边界：`hasXiaoyiPushApiId`, `conf`, `apps`, `item`, `isCronTargetOptionDisabled`, `enabled`, `id`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/CronPanel/xiaoyiCronTarget.ts#L1-L54)。
<!-- /kb:file -->
