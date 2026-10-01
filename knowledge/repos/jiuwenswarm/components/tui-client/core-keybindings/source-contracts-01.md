---
title: "core-keybindings 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# core-keybindings 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/keybindings/actions.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=270912c70931b0368dd7a36c43ff59aace3de3b19161392194f3d245f817ed01 -->
**`jiuwenswarm/channels/tui/frontend/src/core/keybindings/actions.ts`**

- 源码声明的类型、组件或调用边界：`KEYBINDING_CONTEXTS`, `KeybindingContextName`, `KEYBINDING_CONTEXT_DESCRIPTIONS`, `KEYBINDING_ACTIONS`, `KeybindingAction`, `KEYBINDING_ACTION_DESCRIPTIONS`, `ACTION_SET`, `CONTEXT_SET`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/keybindings/actions.ts#L1-L165)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/keybindings/defaultBindings.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5a2d5ee508a63605796c25553d948c758a35a09328030268eab3188d0d781957 -->
**`jiuwenswarm/channels/tui/frontend/src/core/keybindings/defaultBindings.ts`**

- 源码声明的类型、组件或调用边界：`DEFAULT_BINDINGS`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { KeybindingBlock } from "./types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/keybindings/defaultBindings.ts#L1-L120)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/keybindings/reserved.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=00310ab73c686f685b4fb1141b7d895152d5e0950696cc4d2ae8ce2430199307 -->
**`jiuwenswarm/channels/tui/frontend/src/core/keybindings/reserved.ts`**

- 源码声明的类型、组件或调用边界：`ReservedShortcut`, `NON_REBINDABLE`, `VALID_MODIFIERS`, `SPECIAL_KEYS`, `SYMBOL_KEYS`, `isKnownBaseKey`, `normalizeKey`, `parts`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/keybindings/reserved.ts#L1-L82)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/keybindings/resolver.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1d3f37f805ebd0a2e62ef13ed9064eadf7998567a1fffd6773e12fdced4cadc3 -->
**`jiuwenswarm/channels/tui/frontend/src/core/keybindings/resolver.ts`**

- 源码声明的类型、组件或调用边界：`KeyId`, `current`, `lastMtimeMs`, `reloadResolver`, `mtimeMs`, `result`, `resolveAction`, `ctxMap`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { type KeyId, matchesKey } from "@mariozechner/pi-tui";`；`import type { KeybindingAction, KeybindingContextName } from "./actions.js";`；`import { getKeybindingsMtimeMs, loadKeybindings, startKeybindingsWatcher } from "./store.js";`；`import type { KeybindingWarning, ResolvedBindings } from "./types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/keybindings/resolver.ts#L1-L55)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/keybindings/store.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=524532281c64053e6bfbba4a0c161f56f12294fd65a6c364467b98f37495c8c3 -->
**`jiuwenswarm/channels/tui/frontend/src/core/keybindings/store.ts`**

- 源码声明的类型、组件或调用边界：`KeybindingAction`, `CONFIG_DIR`, `KEYBINDINGS_FILE`, `getKeybindingsPath`, `keybindingsFileExists`, `getKeybindingsMtimeMs`, `buildResolved`, `resolved`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { existsSync, mkdirSync, readFileSync, statSync, watch } from "node:fs";`；`import { homedir } from "node:os";`；`import { dirname, join } from "node:path";`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/keybindings/store.ts#L1-L302)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/keybindings/template.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b40666c37807d5e562a581dac464a0db8c0c98cd42730e09ba034425059e16cd -->
**`jiuwenswarm/channels/tui/frontend/src/core/keybindings/template.ts`**

- 源码声明的类型、组件或调用边界：`generateKeybindingsTemplate`, `file`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { DEFAULT_BINDINGS } from "./defaultBindings.js";`；`import type { KeybindingsFile } from "./types.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/keybindings/template.ts#L1-L17)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/core/keybindings/types.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=09bfd5fe777eaf00ed2427deba2d7de17e8873e5d4974865e334e6ac3a301d69 -->
**`jiuwenswarm/channels/tui/frontend/src/core/keybindings/types.ts`**

- 源码声明的类型、组件或调用边界：`KeybindingBlock`, `KeybindingsFile`, `ResolvedBindings`, `KeybindingWarning`, `LoadResult`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { KeybindingAction, KeybindingContextName } from "./actions.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/keybindings/types.ts#L1-L30)。
<!-- /kb:file -->
