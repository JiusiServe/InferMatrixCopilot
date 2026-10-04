---
title: "components-membertaskdrawer 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-membertaskdrawer 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/MemberTaskDrawer/index.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=40ae88d0b396f86f64d04bed5ef73594f0649d87c65b16d2711845603b8a2838 -->
**`jiuwenswarm/channels/web/frontend/src/components/MemberTaskDrawer/index.tsx`**

- 源码声明的类型、组件或调用边界：`MemberTaskDrawerProps`, `getMemberRole`, `roles`, `key`, `ChevronIcon`, `TaskStatusIcon`, `CollapsibleTaskGroupProps`, `CollapsibleTaskGroup`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useState, useMemo } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { useChatStore, useTodoStore, useSessionStore } from '../../stores';`；`import { TeamMemberAvatar } from '../TeamMemberAvatar';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/MemberTaskDrawer/index.tsx#L1-L289)。
<!-- /kb:file -->
