---
title: "jetbrains-plugin-src 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# jetbrains-plugin-src 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/ui/FixWithAiIntention.kt pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=30b10a947413054190ce8cbb7dbcbc7fbc374abdd9a69d469381150f8217e495 -->
**`jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/ui/FixWithAiIntention.kt`**

- 源码声明的类型、组件或调用边界：`FixWithAiIntention`, `getText`, `getFamilyName`, `startInWriteAction`, `isAvailable`, `invoke`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`package com.jiuwenswarm.plugin.ui`；`import com.intellij.codeInsight.intention.IntentionAction`；`import com.intellij.openapi.application.ApplicationManager`；`import com.intellij.openapi.editor.Editor`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/ui/FixWithAiIntention.kt#L1-L98)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/ui/StatusBarWidgetFactory.kt pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=79cce388797eeec4a90ccc19ea85a0cbb89b561ce225ab1af414255c41caee5b -->
**`jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/ui/StatusBarWidgetFactory.kt`**

- 源码声明的类型、组件或调用边界：`StatusBarWidgetFactory`, `getId`, `getDisplayName`, `isAvailable`, `createWidget`, `disposeWidget`, `canBeEnabledOn`, `JiuwenStatusBarWidget`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`package com.jiuwenswarm.plugin.ui`；`import com.intellij.openapi.project.Project`；`import com.intellij.openapi.util.Disposer`；`import com.intellij.openapi.wm.StatusBar`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/ui/StatusBarWidgetFactory.kt#L1-L122)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/ui/SwarmMapPanel.kt pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0d0295804224114e19ee3b1afd774bee572cf6b3337d3b6538b3fe45905a3840 -->
**`jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/ui/SwarmMapPanel.kt`**

- 源码声明的类型、组件或调用边界：`SwarmMapPanel`, `onMessage`, `onLoadEnd`, `postSnapshot`, `postDebug`, `injectBridge`, `readSwarmMapHtml`, `fallbackHtml`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`package com.jiuwenswarm.plugin.ui`；`import com.google.gson.Gson`；`import com.intellij.openapi.Disposable`；`import com.intellij.openapi.application.ApplicationManager`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/ui/SwarmMapPanel.kt#L1-L140)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/ui/SwarmMapToolWindowFactory.kt pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=370994a0e71e967b9a9bce1cc8a77bcb5699ab0503ea64c1ee0e0d2a699c525b -->
**`jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/ui/SwarmMapToolWindowFactory.kt`**

- 源码声明的类型、组件或调用边界：`SwarmMapToolWindowFactory`, `createToolWindowContent`, `shouldBeAvailable`, `getPanel`, `removePanel`, `openOrReveal`, `findChatPanel`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`package com.jiuwenswarm.plugin.ui`；`import com.intellij.openapi.diagnostic.logger`；`import com.intellij.openapi.project.Project`；`import com.intellij.openapi.wm.ToolWindow`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/ui/SwarmMapToolWindowFactory.kt#L1-L72)。
<!-- /kb:file -->
