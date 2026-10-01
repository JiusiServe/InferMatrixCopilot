---
title: "config 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# config 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/config/chatConfig.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=10d4a790a5de167715a5f929772f748c49e684d9b72b6d07d3c440d20402c94a -->
**`jiuwenswarm/channels/web/frontend/src/config/chatConfig.tsx`**

- 源码声明的类型、组件或调用边界：`ChatOptionDef`, `ClusterModeIcon`, `SingleAgentModeIcon`, `DefaultPermissionIcon`, `SafeAccessPermissionIcon`, `AGENT_MODE_OPTIONS`, `PERMISSION_OPTIONS`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { CircleAlert } from 'lucide-react';`；`import type { AgentMode, Permission } from '../types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/config/chatConfig.tsx#L1-L63)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/config/permissionProfiles.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=660cae9eb4a7c18d4bb09d29d897401ea3b45ac3e790cc06d59878912a766878 -->
**`jiuwenswarm/channels/web/frontend/src/config/permissionProfiles.ts`**

- 源码声明的类型、组件或调用边界：`PERMISSION_OPTIONS`, `permissionOptionsForMode`, `effectivePermissionProfile`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { AgentMode, Permission } from '../types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/config/permissionProfiles.ts#L1-L12)。
<!-- /kb:file -->
