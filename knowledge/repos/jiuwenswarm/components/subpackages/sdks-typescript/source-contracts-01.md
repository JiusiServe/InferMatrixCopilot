---
title: "sdks-typescript 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# sdks-typescript 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=sdks/typescript/src/index.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fccc8ac1b5f160da2b881e5fa73015523ec02f71b2b6b3fdb98f8192e21833dc -->
**`sdks/typescript/src/index.ts`**

- 源码声明的类型、组件或调用边界：`ChildProcessWithoutNullStreams`, `Event`, `JsonObject`, `QueryOperation`, `QueryResult`, `RunInput`, `RunResult`, `Workspace`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";`；`import { randomUUID } from "node:crypto";`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/typescript/src/index.ts#L1-L392)。
<!-- /kb:file -->

<!-- kb:file path=sdks/typescript/src/protocol.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5635d05a0c0c25983dc477b1209d25ac7140c334bee0397d7e5c7c7a3889ac5c -->
**`sdks/typescript/src/protocol.ts`**

- 源码声明的类型、组件或调用边界：`Json`, `JsonObject`, `Mode`, `Workspace`, `AgentDefinition`, `RunInput`, `QueryOperation`, `RuntimeErrorInfo`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/typescript/src/protocol.ts#L1-L219)。
<!-- /kb:file -->
