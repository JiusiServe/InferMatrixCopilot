---
title: "IDE 终端命令镜像执行（VS Code 扩展与 JetBrains 插件）"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts:L5-L18, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt:L49-L61, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts:L408-L418]
feature: "ide-terminal-command-mirror"
entry_points: ["jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts", "jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts"]
source_globs: ["jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts", "jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts", "jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt"]
---

# IDE 终端命令镜像执行（VS Code 扩展与 JetBrains 插件）

<!-- kb:knowledge owner=feature-ide-terminal-command-mirror facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**支持的镜像行为与终端复用**

功能将 agent 的 `bash`/`run_command` 工具调用镜像到用户可见的 IDE 终端，展示实时输出。VS Code 端按会话复用单个名为 JiuwenSwarm 的终端，首次命令时惰性创建，每次执行前 `show()` 前置；JetBrains 端同样按终端标题 "JiuwenSwarm" 查找既有 widget，不存在时调用 `createLocalShellWidget(project.basePath, "JiuwenSwarm")` 新建，执行后把 Terminal 工具窗口带到前台。

Sources / 来源：[jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts:L5–L18](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts#L5-L18), [jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt:L49–L61](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/terminal/TerminalManager.kt#L49-L61)

<!-- kb:knowledge owner=feature-ide-terminal-command-mirror facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**验证**

Inference / 设计推断（非作者历史意图）：

所示文件片段中未包含针对 TerminalManager 或命令镜像路径的测试代码；ChatPanel 中的 `this.debug(\`TERM  → ${cmd}\`)` 调试日志是运行时确认命令提取与镜像触发点的可观测入口。无法据此判断仓库其他位置是否存在相关测试。

Sources / 来源：[jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts:L408–L418](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts#L408-L418)

