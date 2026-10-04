---
title: "core-supervision 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# core-supervision 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/supervision/handoff-port.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=eab28b1ff9f19ac2c8d3585edd9cbd32a374230e841a4501411ae25e13a96ce2 -->
**`jiuwenswarm/channels/tui/frontend/src/core/supervision/handoff-port.ts`**

- 源码声明的类型、组件或调用边界：`LAUNCHER_EXIT_INTERNAL_ERROR`, `HandoffPortImpl`, `check`, `exitCode`, `parsed`, `handoffPayload`, `handoffMessage`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type {`；`import { HANDOFF_TARGET_CC_TUI } from "./protocol.js";`；`import type { SupervisionEnv } from "./supervised-env.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/supervision/handoff-port.ts#L1-L130)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/supervision/protocol.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=36a75d645dfab2a014121ce606f9065b6e9d3d83a5af93610effa99bdccb3490 -->
**`jiuwenswarm/channels/tui/frontend/src/core/supervision/protocol.ts`**

- 源码声明的类型、组件或调用边界：`HANDOFF_TARGET_CC_TUI`, `HandoffTarget`, `HandoffErrorCode`, `HandoffCheckResult`, `CancelErrorCode`, `CancelError`, `CancelAndWaitOptions`, `TaskLifecyclePort`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/supervision/protocol.ts#L1-L111)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/supervision/reauth-port.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=eb263e624fff522a8660d52c9b45f227fc443c02370acabb36c3b712474c1efe -->
**`jiuwenswarm/channels/tui/frontend/src/core/supervision/reauth-port.ts`**

- 源码声明的类型、组件或调用边界：`LAUNCHER_EXIT_INTERNAL_ERROR`, `ReauthenticationPortImpl`, `exitCode`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ReauthenticationPort, ReauthenticationReason, UiLifecyclePort } from "./protocol.js";`；`import type { SupervisionEnv } from "./supervised-env.js";`；`import type { HandoffPortImpl } from "./handoff-port.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/supervision/reauth-port.ts#L1-L71)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/supervision/supervised-env.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=217712247c4bad645c86dbd31138a8c5043fde8a5f2a0e6b07160b2e1a0dc9b0 -->
**`jiuwenswarm/channels/tui/frontend/src/core/supervision/supervised-env.ts`**

- 源码声明的类型、组件或调用边界：`SupervisionEnv`, `readSupervisionEnv`, `supervised`, `switchCcExitCode`, `reauthExitCode`, `ccTuiExecutable`, `parseExitCode`, `n`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/supervision/supervised-env.ts#L1-L43)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/supervision/task-lifecycle-port.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ee62bffc2bdbfe7f3948c0af5a7857276c0b58db0334c4bf6b85283effd9e7c2 -->
**`jiuwenswarm/channels/tui/frontend/src/core/supervision/task-lifecycle-port.ts`**

- 源码声明的类型、组件或调用边界：`CancelAndWaitOptions`, `Waiter`, `TaskLifecycleDeps`, `InterruptResultHandler`, `DEFAULT_TIMEOUT_MS`, `TaskLifecyclePortImpl`, `timeoutMs`, `showNotice`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { CancelError, type CancelAndWaitOptions, type TaskLifecyclePort } from "./protocol.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/supervision/task-lifecycle-port.ts#L1-L175)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/supervision/ui-lifecycle.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=32a640f60093e28f56d27262d99551e2945f0ad0d7ea953a573c8bfdd958d44c -->
**`jiuwenswarm/channels/tui/frontend/src/core/supervision/ui-lifecycle.ts`**

- 源码声明的类型、组件或调用边界：`UiLifecycleDeps`, `UiLifecyclePortImpl`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { UiExitReason, UiLifecyclePort } from "./protocol.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/supervision/ui-lifecycle.ts#L1-L86)。
<!-- /kb:file -->
