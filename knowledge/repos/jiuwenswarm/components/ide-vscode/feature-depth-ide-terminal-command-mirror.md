---
title: "IDE 终端命令镜像执行：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt:L40-L47, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/ide/jetbrains/JetBrains插件.md:L13-L24", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts:L9-L18, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt:L23-L38, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt:L23-L65, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts:L20-L48, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts:L3-L18, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts:L34-L65, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt:L10-L38]
feature: "ide-terminal-command-mirror"
entry_points: ["jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts", "jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts"]
source_globs: ["jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts", "jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts", "jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt"]
---

# IDE 终端命令镜像执行：实现深读

[功能概览](feature-ide-terminal-command-mirror.md) · [owner 入口](_index.md)

<!-- kb:depth feature=ide-terminal-command-mirror facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e8aa7a01352867606e117dc310deb203eb26fe7e31bc47aeeb0499133ebc0e14 -->
**VS Code runCommand：模块级 activeTerminal 惰性建、复用并 show() 后 sendText**
runCommand 在模块级 activeTerminal 为空时创建名为 'JiuwenSwarm' 的终端，cwd 取传入值，否则回退第一个工作区文件夹（无工作区时为 undefined）；随后 activeTerminal.show() 并 sendText(command)，命令文本不在此分支解析或校验。

来源：[jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts:L3–L18](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts#L3-L18)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":18,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts","sha256":"675685d151d6d0d674dc4528abc8397f9f2205ba6722e0c64d390d5aff1fbfbc","start":3}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ide-terminal-command-mirror facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0a9430c9e8e6f0528e7081b7fef4bbb196e1d1bc54f3b3689c76ec7757d14a92 -->
**extractCommand/extractArguments：多形态 payload 解析，返回首个命中键的 trim 后字符串或 undefined**
extractCommand 取 extractArguments 结果、payload.arguments 或 payload 本身作为 args（非对象则返回 undefined），再取 command/cmd/shell_cmd/bash_command 中首个真值并 String(...).trim()。extractArguments 优先 tool_call.arguments，tool_call 为对象但无对象型 arguments 时返回 tool_call 本身（此时不再查 tool_input/input），否则依次取 tool_input、input。

来源：[jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts:L34–L65](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts#L34-L65)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":65,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts","sha256":"f83c28d4fc04a9d5d8eb51f3518c6e4545d2a943553e698da7eca67294f8b052","start":34}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ide-terminal-command-mirror facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=42f9fdf961c6e7b8881ad40fc0d5f89ffefaa81548c8211baa8112593eae0ca8 -->
**JetBrains runCommand 受设置 runCommandsInTerminal 守卫，文档默认为开**
Kotlin runCommand 在执行前检查 JiuwenSwarmSettings.instance().runCommandsInTerminal，为假即 return。JetBrains 设置文档列出「在 IDE 终端中运行命令」默认值为「开」。所示 VS Code runCommand 片段不读取任何配置项。

来源：[jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt:L40–L47](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt#L40-L47), [docs/zh/ide/jetbrains/JetBrains插件.md:L13–L24](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/ide/jetbrains/JetBrains%E6%8F%92%E4%BB%B6.md#L13-L24), [jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts:L9–L18](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts#L9-L18)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":47,"path":"jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt","sha256":"75dbf4bdc27ee94d3cf7a54398c72ef7f9a6c1438357c6a512ece970126b3cfe","start":40},{"end":24,"path":"docs/zh/ide/jetbrains/JetBrains插件.md","sha256":"2bffe3f2a25fc1c87cbb6c18afc87f75f789d6bd5ffe07c55fd52331f0eedbcc","start":13},{"end":18,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts","sha256":"ef91f1905eed913ee1dc8e6c599f86ee59a4edc1d5f482ba8472cd1d5347c5f2","start":9}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ide-terminal-command-mirror facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e171f22c6fee3d1fde4aeb68e2f34cfe0070f4e4d3af754098e3a5f4bb77c21f -->
**Kotlin 侧经反射耦合 TerminalView/ShellTerminalWidget；VS Code 侧依赖 vscode.window 终端 API**
Kotlin init 通过 Class.forName 解析 org.jetbrains.plugins.terminal.TerminalView 与 ShellTerminalWidget 的方法，编译期不依赖 Terminal 插件；VS Code 直接调用 vscode.window.createTerminal/show/sendText。Kotlin 还依赖 ToolWindowManager 取 "Terminal" 工具窗。

来源：[jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt:L23–L38](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt#L23-L38), [jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts:L9–L18](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts#L9-L18)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":38,"path":"jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt","sha256":"b11987b8c2018012b83bec809cab328c2e6dc2021610ce254656b03edb981d5d","start":23},{"end":18,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts","sha256":"ef91f1905eed913ee1dc8e6c599f86ee59a4edc1d5f482ba8472cd1d5347c5f2","start":9}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ide-terminal-command-mirror facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=56d344931daffc68734cadac135e38b93af242d0c9b46ac47b8d8045cc3da6a0 -->
**Kotlin 反射缺失或执行异常被捕获并降级为日志；VS Code dispose 吞掉异常**
Kotlin init 反射失败时记 LOG.info 并让 Method 保持 null，runCommand 随后因 tv/gi 等为 null 提前 return（终端集成禁用）；runCommand 体内异常被 catch 记 LOG.warn。VS Code disposeTerminal 用 try/catch 忽略 dispose 异常并将 activeTerminal 置 undefined。extractCommand 在无命令键时返回 undefined，由调用方决定后续。

来源：[jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt:L23–L65](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt#L23-L65), [jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts:L20–L48](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts#L20-L48)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":65,"path":"jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt","sha256":"bc992a69b354e0f2748d62c26062bde9de29270c46e126d5a3d7890eb25822b6","start":23},{"end":48,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts","sha256":"7cd7eba3347585fc14bc588abb7ed99da78678787057c6423355330a308bcb6a","start":20}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ide-terminal-command-mirror facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4b98698ca88624ed95e8948f5651d912da540817d0e2ceb6cfac93a126e34482 -->
**JetBrains 端反射调用 Terminal API：编译期解耦，代价是初始化失败即静默禁用**
设计推断（非作者历史意图）：

TerminalManager 在 init 中通过 Class.forName/getMethod 反射获取 TerminalView 与 ShellTerminalWidget 的方法句柄，任何 Exception 仅 LOG.info 后继续，runCommand 中任一句柄为 null 即直接 return。推断（非作者意图）：这使插件可在缺少 Terminal 插件时编译，但运行时集成失败只留下日志，命令镜像被静默跳过。

来源：[jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt:L10–L38](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt#L10-L38), [jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt:L40–L47](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt#L40-L47)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":38,"path":"jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt","sha256":"2b9d331429dafb0daa14e4bdde7052df37c15ab2e308a6cc91cdb610efc730c8","start":10},{"end":47,"path":"jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt","sha256":"75dbf4bdc27ee94d3cf7a54398c72ef7f9a6c1438357c6a512ece970126b3cfe","start":40}],"trace":[]} -->
<!-- /kb:depth -->
