---
title: "TUI 对话与命令：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/index.ts:L17-L29, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/index.ts:L86-L92]
---

# TUI 对话与命令：实现深读

[功能概览](feature-tui.md) · [owner 入口](_index.md)

<!-- kb:depth feature=tui facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8db4acbe1b2a9462dcc461a82639658681500f510344cdb151da4b592de0968e -->
**--url 默认值与 TTY 检查覆盖**
--url 在 parseArgs 中默认 "ws://127.0.0.1:19001/tui"，L92 再以 values.url ?? 同一默认值兜底。非交互环境（stdin/stdout 任一非 TTY）默认报错退出，但设置环境变量 JIUWENSWARM_TUI_HEADLESS（注释注明用于自动化测试）可跳过该检查。

来源：[jiuwenswarm/channels/tui/frontend/src/index.ts:L17–L29](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/index.ts#L17-L29), [jiuwenswarm/channels/tui/frontend/src/index.ts:L86–L92](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/index.ts#L86-L92)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/tui/frontend/src/index.ts","start":17,"end":29,"sha256":"e3dcca39c81378fd80f980cd53fc688807c9c8bf010d5a111da6c5362c57debe"},{"path":"jiuwenswarm/channels/tui/frontend/src/index.ts","start":86,"end":92,"sha256":"c4be983b89ab1643df16d1156a66760ec749fb604b8efa76a44c21a563cfe75c"}],"trace":[]} -->
<!-- /kb:depth -->
