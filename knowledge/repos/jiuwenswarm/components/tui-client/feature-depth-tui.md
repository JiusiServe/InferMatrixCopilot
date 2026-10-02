---
title: "TUI 对话与命令：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/index.ts:L17-L29, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/index.ts:L86-L92, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/tests/task-lifecycle-port.test.mjs:L1-L4, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/tests/task-lifecycle-port.test.mjs:L176-L193, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/tests/task-lifecycle-port.test.mjs:L195-L210]
feature: "tui"
entry_points: ["jiuwenswarm/channels/tui/frontend/src/index.ts"]
source_globs: ["jiuwenswarm/channels/tui/frontend/src/index.ts", "jiuwenswarm/channels/tui/*"]
---

# TUI 对话与命令：实现深读

[功能概览](feature-tui.md) · [owner 入口](_index.md)

<!-- kb:depth feature=tui facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8db4acbe1b2a9462dcc461a82639658681500f510344cdb151da4b592de0968e -->
**--url 默认值与 TTY 检查覆盖**
--url 在 parseArgs 中默认 "ws://127.0.0.1:19001/tui"，L92 再以 values.url ?? 同一默认值兜底。非交互环境（stdin/stdout 任一非 TTY）默认报错退出，但设置环境变量 JIUWENSWARM_TUI_HEADLESS（注释注明用于自动化测试）可跳过该检查。

来源：[jiuwenswarm/channels/tui/frontend/src/index.ts:L17–L29](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/index.ts#L17-L29), [jiuwenswarm/channels/tui/frontend/src/index.ts:L86–L92](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/index.ts#L86-L92)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/tui/frontend/src/index.ts","start":17,"end":29,"sha256":"e3dcca39c81378fd80f980cd53fc688807c9c8bf010d5a111da6c5362c57debe"},{"path":"jiuwenswarm/channels/tui/frontend/src/index.ts","start":86,"end":92,"sha256":"c4be983b89ab1643df16d1156a66760ec749fb604b8efa76a44c21a563cfe75c"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=tui facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e5c38aedf50eb99e0987a3bcf93511a3ccb06c510e54deacbde0c2ae25ea59e3 -->
**task-lifecycle-port.test.mjs 断言断连与并发下的取消行为（针对 dist 构建）**
入口是 jiuwenswarm/channels/tui/frontend/tests/task-lifecycle-port.test.mjs：node 顶层断言脚本（无测试框架），从 ../dist/core/supervision/task-lifecycle-port.js 导入被测实现并以 MockDeps 注入依赖。用例 10 置 MockDeps.connectionAlive=false，断言 cancelAndWaitForIdle 立即以 CancelError.code==="CANCEL_CONNECTION_LOST" 拒绝且 deps.sentInterrupts.length===0（已断连时不发送 interrupt）；用例 9 断言首个 waiter 未决期间第二次调用立即 reject CANCEL_ALREADY_PENDING。此处仅描述断言所锻炼的行为，不声称测试当次已运行通过。

来源：[jiuwenswarm/channels/tui/frontend/tests/task-lifecycle-port.test.mjs:L1–L4](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/tests/task-lifecycle-port.test.mjs#L1-L4), [jiuwenswarm/channels/tui/frontend/tests/task-lifecycle-port.test.mjs:L176–L193](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/tests/task-lifecycle-port.test.mjs#L176-L193), [jiuwenswarm/channels/tui/frontend/tests/task-lifecycle-port.test.mjs:L195–L210](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/tests/task-lifecycle-port.test.mjs#L195-L210)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":4,"path":"jiuwenswarm/channels/tui/frontend/tests/task-lifecycle-port.test.mjs","sha256":"b0ef9dbdfe036e178a1381f5631c3c7d77ddce7e6d436cef7225778e15d49076","start":1},{"end":193,"path":"jiuwenswarm/channels/tui/frontend/tests/task-lifecycle-port.test.mjs","sha256":"41d2eb2d3801c0b2e006c293b6a0a51e9a8e77f4d18e10f68e1291c401e29aac","start":176},{"end":210,"path":"jiuwenswarm/channels/tui/frontend/tests/task-lifecycle-port.test.mjs","sha256":"0e3c7d0438ae4c4510b21c75da6dec9fadab223756e2ebc8b3cc14d196a05ee8","start":195}],"trace":[]} -->
<!-- /kb:depth -->
