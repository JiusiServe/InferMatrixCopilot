---
title: "features-taskfullduplex 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# features-taskfullduplex 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/taskFullDuplex/featureFlag.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=40157629cf51a19f8b994d27f22b9b0028b9038cec19f1dbc7513de96bfc80ca -->
**`jiuwenswarm/channels/web/frontend/src/features/taskFullDuplex/featureFlag.ts`**

- 源码声明的类型、组件或调用边界：`enabled`, `listeners`, `setTaskFullDuplexEnabled`, `useTaskFullDuplexEnabled`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useSyncExternalStore } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/taskFullDuplex/featureFlag.ts#L1-L21)。
<!-- /kb:file -->
