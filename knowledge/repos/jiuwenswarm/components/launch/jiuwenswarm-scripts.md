---
title: "scripts/ — 构建辅助与 WhatsApp 桥接脚本"
created: 2026-10-05
updated: 2026-10-05
type: architecture
tags: [jiuwenswarm]
sources: []
---

# scripts/ — 构建辅助与 WhatsApp 桥接脚本

该模块包含仓库的独立 Node 脚本：扫描 agent 目录生成 workspace/agent-data.json 文件清单（可配合 chokidar 监听增量重新生成），以及一个基于 Baileys 的 WhatsApp WebSocket 桥接服务。桥接脚本是可选的运行时服务，默认不随主程序启动，需手动运行。

**入口脚本**

- `jiuwenswarm/scripts/generate-agent-folders.js` — 定位 agent 根目录（$JIUWENSWARM_ROOT/agent 或 ../resources/agent），递归扫描并写入 workspace/agent-data.json
- `jiuwenswarm/scripts/whatsapp-bridge.js` — 启动 WhatsApp 桥接：Baileys 连接 + WebSocket 服务（默认 ws://127.0.0.1:19600/ws），扫码登录、收发消息

**关键文件**

- `jiuwenswarm/scripts/watch-folders.js` — 开发辅助：先执行一次生成脚本，再用 chokidar 监听 agent 目录（$JIUWENSWARM_DATA_DIR/agent 或 ~/.jiuwenswarm/agent，回退到 ../resources/agent），变化时重新生
- `jiuwenswarm/scripts/generate-agent-folders.js` — 按文件夹分组文件清单，_zh/_en 后缀去重、排序保证输出稳定，失败时写空 JSON
- `jiuwenswarm/scripts/whatsapp-bridge.js` — 环境变量 WA_BRIDGE_HOST/PORT/PATH、WA_AUTH_DIR、WA_PRINT_QR 控制行为；广播 status/qr/inbound 消息，处理 send 请求并返回 send_result，非登出断线时 4 秒重

**相关文档**

- `README_CN.md` — 了解仓库整体功能与安装使用入口
- `docs/README.md` — 文档总导航，查找脚本相关（如 WhatsApp 频道/agent 目录）的详细文档

**调用路径**

- `jiuwenswarm/scripts/`
