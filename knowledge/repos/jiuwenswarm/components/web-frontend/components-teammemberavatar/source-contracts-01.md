---
title: "components-teammemberavatar 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-teammemberavatar 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/TeamMemberAvatar/index.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3e7f494e9a1e3f064b995890136f27dbb84ce7752246c8340f1d8ade0481114b -->
**`jiuwenswarm/channels/web/frontend/src/components/TeamMemberAvatar/index.tsx`**

- 源码声明的类型、组件或调用边界：`TeamMemberIdentity`, `TeamMemberAvatarProps`, `useTeamMemberIdentity`, `activeSessionId`, `teamMembers`, `id`, `known`, `TeamMemberAvatar`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import clsx from 'clsx';`；`import { useMemo } from 'react';`；`import { useChatStore } from '../../stores/chatStore';`；`import { useSessionStore } from '../../stores/sessionStore';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/TeamMemberAvatar/index.tsx#L1-L71)。
<!-- /kb:file -->
