---
title: "jetbrains-plugin-src 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# jetbrains-plugin-src 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/client/SessionManager.kt pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=34aac2030ffc4111c267dc7bbec9f7cf1fcdaeff72e530ad96c831dcb524f0e8 -->
**`jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/client/SessionManager.kt`**

- 源码声明的类型、组件或调用边界：`val`, `SessionInfo`, `SessionManager`, `sessionId`, `sessionTitle`, `addSessionListener`, `removeSessionListener`, `dispose`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`package com.jiuwenswarm.plugin.client`；`import com.google.gson.Gson`；`import com.google.gson.JsonObject`；`import com.intellij.openapi.application.ApplicationManager`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/client/SessionManager.kt#L1-L343)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/client/WsClient.kt pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f3904aead48cf7ea6007e40ba087cf5e91478dc9f3a99af8e427a662bd802729 -->
**`jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/client/WsClient.kt`**

- 源码声明的类型、组件或调用边界：`class`, `WsClient`, `pingIntervalSec`, `client`, `buildClient`, `setPingInterval`, `ws`, `status`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`package com.jiuwenswarm.plugin.client`；`import com.google.gson.Gson`；`import com.google.gson.JsonObject`；`import com.intellij.openapi.Disposable`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/client/WsClient.kt#L1-L155)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/context/ContextCollector.kt pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3a1fe10962d83e367f1b20051ab43b2df9218f3dfeb28225514f4816a7d9ec65 -->
**`jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/context/ContextCollector.kt`**

- 源码声明的类型、组件或调用边界：`collect`, `collectProjectRules`, `collectMentionedFiles`, `gatherWorkspaceFiles`, `collectFilesFlat`, `buildProjectTree`, `buildProjectTreeInternal`, `readIdeData`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`package com.jiuwenswarm.plugin.context`；`import com.intellij.openapi.application.ReadAction`；`import com.intellij.openapi.editor.Editor`；`import com.intellij.openapi.editor.impl.DocumentMarkupModel`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/context/ContextCollector.kt#L1-L276)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/context/GitContextProvider.kt pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2316d20b5457ccd595f214361e06425a97134d8f16d823cb8a55a5c5572cbf76 -->
**`jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/context/GitContextProvider.kt`**

- 源码声明的类型、组件或调用边界：`collect`, `runGit`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`package com.jiuwenswarm.plugin.context`；`import com.intellij.openapi.project.Project`；`import java.io.File`；`import java.util.concurrent.TimeUnit`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/context/GitContextProvider.kt#L1-L64)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/editor/DiffApplier.kt pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=18ae244c08f92e87dc5121093c6bb08647c1bb18a25db40526708a140fddea23 -->
**`jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/editor/DiffApplier.kt`**

- 源码声明的类型、组件或调用边界：`handle`, `handleOnEdt`, `handleEditFile`, `handleStrReplaceEditor`, `handleWriteFile`, `askApproval`, `applyStrReplace`, `writeEntireFile`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`package com.jiuwenswarm.plugin.editor`；`import com.google.gson.JsonElement`；`import com.google.gson.JsonObject`；`import com.google.gson.JsonParser`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/editor/DiffApplier.kt#L1-L310)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/settings/JiuwenSwarmSettings.kt pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=88d7d6f692a0a529f4b3813abb15a22fb503cd44a355662658333417196fcc0a -->
**`jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/settings/JiuwenSwarmSettings.kt`**

- 源码声明的类型、组件或调用边界：`JiuwenSwarmSettings`, `State`, `host`, `port`, `channelId`, `defaultMode`, `autoConnect`, `autoApplyEdits`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`package com.jiuwenswarm.plugin.settings`；`import com.intellij.openapi.application.ApplicationManager`；`import com.intellij.openapi.components.PersistentStateComponent`；`import com.intellij.openapi.components.State`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/settings/JiuwenSwarmSettings.kt#L1-L126)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/settings/SettingsConfigurable.kt pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e33d30ee5b515c5097465eb0107d461130a11865b536776ad6e5920f7ac48815 -->
**`jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/settings/SettingsConfigurable.kt`**

- 源码声明的类型、组件或调用边界：`SettingsConfigurable`, `panel`, `modeLabel`, `modeCode`, `getDisplayName`, `createComponent`, `isModified`, `apply`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`package com.jiuwenswarm.plugin.settings`；`import com.intellij.openapi.options.Configurable`；`import com.intellij.ui.components.JBCheckBox`；`import com.intellij.ui.components.JBLabel`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/settings/SettingsConfigurable.kt#L1-L168)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/swarm/SwarmState.kt pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bd5a079f4738654a3158c328abeb1e3c8f1a592330315ee9b4e4d108dc660dc3 -->
**`jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/swarm/SwarmState.kt`**

- 源码声明的类型、组件或调用边界：`LaneFeedEntry`, `at`, `AgentLane`, `displayName`, `role`, `status`, `executionStatus`, `currentTaskId`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`package com.jiuwenswarm.plugin.swarm`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/swarm/SwarmState.kt#L1-L49)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/swarm/SwarmStateManager.kt pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5221b0ff87ef58e5ecaa64a9a36e9a865f430c25bd49b7b3b14eeb7d98a4a8dd -->
**`jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/swarm/SwarmStateManager.kt`**

- 源码声明的类型、组件或调用边界：`SwarmStateManager`, `sessionId`, `teamName`, `lastEventAt`, `applyTeamEvent`, `normalizeEvent`, `normalizeLaneStatus`, `applyToolCall`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`package com.jiuwenswarm.plugin.swarm`；`import com.google.gson.Gson`；`import com.google.gson.JsonObject`；`import com.intellij.openapi.diagnostic.logger`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/swarm/SwarmStateManager.kt#L1-L421)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0d888ae8cd3f74014f4887d5c73846482fd1dca5e9864ea806a08aaf9d6ae82b -->
**`jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt`**

- 源码声明的类型、组件或调用边界：`terminalViewClass`, `getInstanceMethod`, `getWidgetsMethod`, `createWidgetMethod`, `executeCommandMethod`, `runCommand`, `extractCommand`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`package com.jiuwenswarm.plugin.terminal`；`import com.intellij.openapi.diagnostic.logger`；`import com.intellij.openapi.project.Project`；`import com.intellij.openapi.wm.ToolWindowManager`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt#L1-L79)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/ui/Actions.kt pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=853b16ce63c695e0bb74d5adda03976b31e1c49550eb44246323d5c9bfe6c8e3 -->
**`jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/ui/Actions.kt`**

- 源码声明的类型、组件或调用边界：`NewSessionAction`, `getActionUpdateThread`, `actionPerformed`, `update`, `SendSelectionAction`, `getActionUpdateThread`, `actionPerformed`, `update`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`package com.jiuwenswarm.plugin.ui`；`import com.intellij.openapi.actionSystem.ActionUpdateThread`；`import com.intellij.openapi.actionSystem.AnAction`；`import com.intellij.openapi.actionSystem.AnActionEvent`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/ui/Actions.kt#L1-L77)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/ui/ChatToolWindow.kt pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b4db1ec34c0b95e803b026bd9877e37aa67044fbb7296c1ad6e2db9098efd8e7 -->
**`jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/ui/ChatToolWindow.kt`**

- 源码声明的类型、组件或调用边界：`ChatToolWindowFactory`, `createToolWindowContent`, `shouldBeAvailable`, `addFallback`, `ChatPanel`, `lastRequestId`, `activeModel`, `historyLoadedForSession`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`package com.jiuwenswarm.plugin.ui`；`import com.google.gson.Gson`；`import com.google.gson.JsonObject`；`import com.google.gson.JsonParser`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/ui/ChatToolWindow.kt#L1-L1069)。
<!-- /kb:file -->
