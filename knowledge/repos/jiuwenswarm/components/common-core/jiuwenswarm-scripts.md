---
title: "开发辅助脚本（scripts/）"
created: 2026-10-05
updated: 2026-10-05
type: architecture
tags: [jiuwenswarm]
sources: []
---

# 开发辅助脚本（scripts/）

存放仓库的开发辅助 Node.js 脚本：扫描 agent 资源目录生成文件夹索引并在开发时监听变更、把 WhatsApp 消息桥接到 WebSocket 频道。它们不属于运行时核心，而是生成产物与联调工具。

**入口文件**

- `jiuwenswarm/scripts/generate-agent-folders.js` — 遍历 agent 资源目录（可用环境变量覆盖根路径），把各语言后缀的 Markdown 文件归组并输出排序后的文件夹索引数据。
- `jiuwenswarm/scripts/whatsapp-bridge.js` — 连接 WhatsApp（@whiskeysockets/baileys）并通过 WebSocket 服务转发消息，带二维码终端打印、状态广播与自动重连。

**其他关键文件**

- `jiuwenswarm/scripts/watch-folders.js` — 开发模式下的监听器：用 chokidar 监视 agent 目录（环境变量或仓库回退路径），变更时以子进程重新执行生成脚本。

**相关文档**

- `docs/README.md`

**Routes**

- `jiuwenswarm/scripts/`
