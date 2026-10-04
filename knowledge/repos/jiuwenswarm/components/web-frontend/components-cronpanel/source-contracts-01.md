---
title: "components-cronpanel 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-cronpanel 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/CronPanel/ConfirmDialog.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=230768749e0bcfc4da28fc7ae17048e3d0b90ab6838bbdf543066326931bffcd -->
**`jiuwenswarm/channels/web/frontend/src/components/CronPanel/ConfirmDialog.tsx`**

- 源码声明的类型、组件或调用边界：`ConfirmDialogProps`, `ConfirmDialog`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useTranslation } from 'react-i18next';`；`import { X } from 'lucide-react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/CronPanel/ConfirmDialog.tsx#L1-L48)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/CronPanel/CronTaskDrawer.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bf200f6172afed68fe9b2aa5b3a5e8e671ff4e6fbac7c3daf4009f340993dae8 -->
**`jiuwenswarm/channels/web/frontend/src/components/CronPanel/CronTaskDrawer.tsx`**

- 源码声明的类型、组件或调用边界：`CRON_EFFECTIVE_DATE_UI_ENABLED`, `CRON_NAME_MAX_LENGTH`, `CRON_DESCRIPTION_MAX_LENGTH`, `CronTaskFormValue`, `emptyForm`, `jobToForm`, `templateToForm`, `CronTaskDrawerProps`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useState, ReactNode } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { X, Pencil } from 'lucide-react';`；`import ScheduleEditor from './ScheduleEditor';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/CronPanel/CronTaskDrawer.tsx#L1-L522)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/CronPanel/DatePicker.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5d404da559bd4a103e03313a19473105d464e8541e58770c65dd6e4bfa558774 -->
**`jiuwenswarm/channels/web/frontend/src/components/CronPanel/DatePicker.tsx`**

- 源码声明的类型、组件或调用边界：`DatePickerProps`, `buildMonthList`, `list`, `offset`, `d`, `parseFlexibleDate`, `m`, `date`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useRef, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { Calendar, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';`；`import { useClickOutside } from './useClickOutside';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/CronPanel/DatePicker.tsx#L1-L261)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/CronPanel/ModeSelector.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cdbdfd96bea8779090c5f5ef473d2096ec0cc9f58fdd5883b60fa77d9d004625 -->
**`jiuwenswarm/channels/web/frontend/src/components/CronPanel/ModeSelector.tsx`**

- 源码声明的类型、组件或调用边界：`ModeSelectorProps`, `ModeSelector`, `rootRef`, `menuPortalRef`, `handlePointerDown`, `updateMenuPosition`, `rect`, `currentMode`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useLayoutEffect, useRef, useState } from 'react';`；`import { createPortal } from 'react-dom';`；`import clsx from 'clsx';`；`import { useTranslation } from 'react-i18next';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/CronPanel/ModeSelector.tsx#L1-L149)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/CronPanel/ScheduleEditor.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e09b96d313b776df45cfb2470c75bdc09fd40e08ff118f2c586cd0d14d970f60 -->
**`jiuwenswarm/channels/web/frontend/src/components/CronPanel/ScheduleEditor.tsx`**

- 源码声明的类型、组件或调用边界：`ScheduleEditorProps`, `TopMode`, `PERIOD_KINDS`, `WEEKDAY_ITEMS`, `WEEK_OF_MONTH_OPTIONS`, `topModeOf`, `defaultForTopMode`, `intervalNumberTextOf`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useRef, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import SimpleSelect from './SimpleSelect';`；`import TimePicker from './TimePicker';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/CronPanel/ScheduleEditor.tsx#L1-L640)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/CronPanel/SimpleSelect.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a2d4ca0339ed949e4feb5a64b75cb0b7e6eaf61666ca0d38996b110208d614b3 -->
**`jiuwenswarm/channels/web/frontend/src/components/CronPanel/SimpleSelect.tsx`**

- 源码声明的类型、组件或调用边界：`SimpleSelectOption`, `SimpleSelectProps`, `SimpleSelect`, `rootRef`, `selected`, `isEmptySelection`, `selectedLabel`, `selectedTitle`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useRef, useState } from 'react';`；`import type { ReactNode } from 'react';`；`import { ChevronDown, Check } from 'lucide-react';`；`import { useClickOutside } from './useClickOutside';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/CronPanel/SimpleSelect.tsx#L1-L102)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/CronPanel/StatusBadge.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=934d18daefcd06d29db095a9bae0cf72b5e4d0abb7c68c746bab2246b1527b18 -->
**`jiuwenswarm/channels/web/frontend/src/components/CronPanel/StatusBadge.tsx`**

- 源码声明的类型、组件或调用边界：`StatusBadgeProps`, `RunningIcon`, `BoldRingIcon`, `StatusBadge`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useTranslation } from 'react-i18next';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/CronPanel/StatusBadge.tsx#L1-L58)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/CronPanel/TemplateClusterIcon.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=045f601285f02dffe8958b7ffb0763436b30d05d21869e9a88e313c0a4ce5748 -->
**`jiuwenswarm/channels/web/frontend/src/components/CronPanel/TemplateClusterIcon.tsx`**

- 源码声明的类型、组件或调用边界：`TemplateClusterIcon`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/CronPanel/TemplateClusterIcon.tsx#L1-L27)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/CronPanel/TimePicker.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=56a4c32d4aaa23992e5bf41424f45a14f976854ab0baf989b4a6e4e5503f18c0 -->
**`jiuwenswarm/channels/web/frontend/src/components/CronPanel/TimePicker.tsx`**

- 源码声明的类型、组件或调用边界：`HOURS`, `MINUTES`, `TimePickerProps`, `TimePicker`, `rootRef`, `pick`, `disabled`, `disabled`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useRef, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { Clock } from 'lucide-react';`；`import { useClickOutside } from './useClickOutside';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/CronPanel/TimePicker.tsx#L1-L106)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/CronPanel/constants.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=41ab95df78a15560862cdfe6611739353805cfe842cc3aaa2fa9bbacecdca77d -->
**`jiuwenswarm/channels/web/frontend/src/components/CronPanel/constants.ts`**

- 源码声明的类型、组件或调用边界：`TIMEZONE_OPTIONS`, `CRON_TEMPLATES`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { CronTemplateUI } from '../../types/cron';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/CronPanel/constants.ts#L1-L44)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/CronPanel/cronExprValidation.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a4496221aa89b7d38dd5d80b682c184cad81022f6e9113f0f8ee81ab1b296c40 -->
**`jiuwenswarm/channels/web/frontend/src/components/CronPanel/cronExprValidation.ts`**

- 源码声明的类型、组件或调用边界：`isValidCronField`, `parts`, `part`, `step`, `rangeValid`, `num`, `getFieldError`, `isValidCronRange`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { normalizeWeekAlphas } from './cronWeekAlpha.js';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/CronPanel/cronExprValidation.ts#L1-L115)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/CronPanel/cronMode.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f683400d4d1c57f2fa41f67ab9fbfbb08bc490a9bcfdbf344c267f7e6f71db8e -->
**`jiuwenswarm/channels/web/frontend/src/components/CronPanel/cronMode.ts`**

- 源码声明的类型、组件或调用边界：`isTeamCronModeValue`, `value`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/CronPanel/cronMode.ts#L1-L19)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/CronPanel/cronProjectDisplay.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f9c59f793f8c7b858ae3b4206aa7f5110e845d7b5373d4c0790da9a8dc3a33f6 -->
**`jiuwenswarm/channels/web/frontend/src/components/CronPanel/cronProjectDisplay.ts`**

- 源码声明的类型、组件或调用边界：`CronProjectLike`, `isDefaultLikeProject`, `resolveCronJobProjectName`, `project`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/CronPanel/cronProjectDisplay.ts#L1-L31)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/CronPanel/cronWakeOffset.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=957507410aefb62b7a2dd161777cb9d9a1761adcb9e35c87d4e25761435897e5 -->
**`jiuwenswarm/channels/web/frontend/src/components/CronPanel/cronWakeOffset.ts`**

- 源码声明的类型、组件或调用边界：`WAKE_OFFSET_MAX_MINUTES`, `normalizeWakeOffsetSeconds`, `n`, `wakeOffsetSecondsToMinutes`, `wakeOffsetMinutesToSeconds`, `minutes`, `clamped`, `normalizeWakeOffsetMinutesInput`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/CronPanel/cronWakeOffset.ts#L1-L37)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/CronPanel/cronWeekAlpha.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=132c546adc2a3f164aa0705db1be3c8fd5e0ef928f20bc552a7ef43e80ef92bd -->
**`jiuwenswarm/channels/web/frontend/src/components/CronPanel/cronWeekAlpha.ts`**

- 源码声明的类型、组件或调用边界：`WEEK_DOW_ALPHA_TO_NUM`, `WEEK_DOW_ALPHA_PATTERN`, `normalizeWeekAlphas`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/CronPanel/cronWeekAlpha.ts#L1-L24)。
<!-- /kb:file -->
