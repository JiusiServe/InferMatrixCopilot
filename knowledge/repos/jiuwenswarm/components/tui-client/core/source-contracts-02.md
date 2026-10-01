---
title: "core 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# core 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/workflows.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bc84782a70226a0e12e383fdc94a86c0b24b21b12f1187ba47c7169de55f4c3e -->
**`jiuwenswarm/channels/tui/frontend/src/core/workflows.ts`**

- 源码声明的类型、组件或调用边界：`WorkflowStatus`, `WorkflowAgentActivity`, `WorkflowNodeType`, `WorkflowBudget`, `WorkflowAgentPart`, `WorkflowAgent`, `WorkflowPhase`, `WorkflowRun`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/workflows.ts#L1-L849)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/ws-client.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b4e29b6066dc6f094795f5e03369e376867474404b4ff6b9edb246ee1d4da7e3 -->
**`jiuwenswarm/channels/tui/frontend/src/core/ws-client.ts`**

- 源码声明的类型、组件或调用边界：`FrameHandler`, `ConnectionStatus`, `PendingRequest`, `WsClient`, `ws`, `frame`, `timer`, `listener`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import WebSocket from "ws";`；`import type { Frame, ReqFrame, ResFrame } from "./protocol.js";`；`import { isResFrame } from "./protocol.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/ws-client.ts#L1-L266)。
<!-- /kb:file -->
