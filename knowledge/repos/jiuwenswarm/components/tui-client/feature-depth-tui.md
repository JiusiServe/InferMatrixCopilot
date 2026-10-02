---
title: "TUI 对话与命令：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/index.ts:L17-L29, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/index.ts:L86-L92, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/tests/task-lifecycle-port.test.mjs:L1-L4, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/tests/task-lifecycle-port.test.mjs:L176-L193, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/tests/task-lifecycle-port.test.mjs:L195-L210, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/index.ts:L206-L225, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/TUI使用指南.md:L39-L46", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/index.ts:L100-L107, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/TUI使用指南.md:L13-L24", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/index.ts:L202-L244, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/app-state.ts:L733-L766, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/index.ts:L212-L244, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/app-state.ts:L98-L105, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/app-state.ts:L3636-L3647]
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

<!-- kb:depth feature=tui facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6aa78ce599354fcc95bcaf187e3a64236df600944b74426f1c525ddf19364100 -->
**closeUi 正常退出：closed 防重入后先通知再清理，最后 process.exit(exitCode 默认 0)**
closeUi 先检查 closed 守卫并置 closed=true，再 await user_exit 断连通知（错误被 catch 吞掉），随后 screen?.dispose、appState.stop()（若本地有挂起提问则以 "app stopped while awaiting input" reject，并 wsClient.disconnect()），最后 tui.stop() 与 process.exit(exitCode)。

来源：[jiuwenswarm/channels/tui/frontend/src/index.ts:L202–L244](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/index.ts#L202-L244), [jiuwenswarm/channels/tui/frontend/src/app-state.ts:L733–L766](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/app-state.ts#L733-L766)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":244,"path":"jiuwenswarm/channels/tui/frontend/src/index.ts","sha256":"b32fc89f69bdbeb9085bf0336b36e98df8f6dcd0b02970ed5cb25839ea17a188","start":202},{"end":766,"path":"jiuwenswarm/channels/tui/frontend/src/app-state.ts","sha256":"550db4e950cd957d8d7f7c293da21750b48df1f0a4bb29f988b84b976200269f","start":733}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=tui facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8f9ce08d90558282449ec45fe3d69e86e4187172232a7e0c8a06d340d213b8fa -->
**parseCliArgs 的默认值契约与 closeUi(exitCode=0) 的 closed 单次保证**
`parseCliArgs` 返回旗标值对象：`url` 默认 `ws://127.0.0.1:19001/tui`、`token`/`user-id` 默认空串、`persist-session` 默认 `false`、`session` 无默认、`help` 短参 `-h`；文档旗标表的 `--url/--token` 默认值与此一致。`closeUi(exitCode = 0)` 首次调用置 `closed=true`，重复调用直接返回。

来源：[jiuwenswarm/channels/tui/frontend/src/index.ts:L17–L29](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/index.ts#L17-L29), [jiuwenswarm/channels/tui/frontend/src/index.ts:L206–L225](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/index.ts#L206-L225), [docs/zh/TUI使用指南.md:L39–L46](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/TUI%E4%BD%BF%E7%94%A8%E6%8C%87%E5%8D%97.md#L39-L46)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":29,"path":"jiuwenswarm/channels/tui/frontend/src/index.ts","sha256":"e3dcca39c81378fd80f980cd53fc688807c9c8bf010d5a111da6c5362c57debe","start":17},{"end":225,"path":"jiuwenswarm/channels/tui/frontend/src/index.ts","sha256":"b6de4ca81c82518eebfc99043f3a1b9adbe6d74419f788d65c12deb2bc4a3a83","start":206},{"end":46,"path":"docs/zh/TUI使用指南.md","sha256":"f67f3f9d4cd1b5f6728f23089b4ffea7d7e8dd3e83c749b010f6389a4204a573","start":39}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=tui facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d6888d244788cec236c8af6a48bc797b7895b7b19a4eb344dae5350d301d06ce -->
**closeUi 与 crash（后者仅在未 closed 时）耦合 AppState.stop 完成前端清理**
index.ts 的两条退出路径都调用 appState.stop()；该方法通知 stop 订阅器（单个监听器抛错被忽略）、清除计时器与取消监听，并最后 wsClient.disconnect()，因此退出时的连接与定时器清理耦合在 app-state 实现内。

来源：[jiuwenswarm/channels/tui/frontend/src/index.ts:L212–L244](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/index.ts#L212-L244), [jiuwenswarm/channels/tui/frontend/src/app-state.ts:L733–L766](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/app-state.ts#L733-L766)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":244,"path":"jiuwenswarm/channels/tui/frontend/src/index.ts","sha256":"8ed5742c87bfa5b856ed29b41a1d8750c2ff63e0821e43be887c48784b06e1f1","start":212},{"end":766,"path":"jiuwenswarm/channels/tui/frontend/src/app-state.ts","sha256":"550db4e950cd957d8d7f7c293da21750b48df1f0a4bb29f988b84b976200269f","start":733}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=tui facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e1a489617c885ddcbd22ad5e4bfa1d6efba80cb1314fc6f32e538c66e57b251c -->
**断连通知抛错被 catch 吞掉、非法 URL 按本地处理、双窗口同 --session 被 Gateway 拒绝**
`closeUi` 内断连通知抛错被 `catch` 吞掉（注释 Best effort only），后续 `screen?.dispose()/appState.stop()` 照常执行，`tui.stop()` 重复失败同样忽略；`isRemoteUrl` 对无法解析的 URL `catch` 返回 `false` 视为本地；文档记载两个窗口同时用同一 `--session <id>` 启动会被 Gateway 以 `SESSION_IN_USE` 拒绝。

来源：[jiuwenswarm/channels/tui/frontend/src/index.ts:L100–L107](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/index.ts#L100-L107), [jiuwenswarm/channels/tui/frontend/src/index.ts:L206–L225](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/index.ts#L206-L225), [docs/zh/TUI使用指南.md:L13–L24](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/TUI%E4%BD%BF%E7%94%A8%E6%8C%87%E5%8D%97.md#L13-L24)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":107,"path":"jiuwenswarm/channels/tui/frontend/src/index.ts","sha256":"87f444429c7066a26a497762c6942330bf431dee581230bfcfe4e3a196de4958","start":100},{"end":225,"path":"jiuwenswarm/channels/tui/frontend/src/index.ts","sha256":"b6de4ca81c82518eebfc99043f3a1b9adbe6d74419f788d65c12deb2bc4a3a83","start":206},{"end":24,"path":"docs/zh/TUI使用指南.md","sha256":"8672277d1bd03cfa091a2a5ca6d00bd5d0ebad2b2f5d3a733a51480f034cdfa1","start":13}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=tui facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=89b60d7e7a9d2e4b42c6ab2ffb34f165956a8a326c39d2ed0f220e1abead3087 -->
**仅 "already active in another window" 走有界延迟重试：自愈瞬态占用竞争，代价是启动等待与其余失败直接传播**
设计推断（非作者历史意图）：

catch 分支仅当错误消息含 "already active in another window"、target 非 null 且 retryIndex 未超出 BOOT_SESSION_IN_USE_RETRY_DELAYS_MS（[100,200,400,800,800,800,800]，共 7 次）时按延迟 await 后重试，否则 throw error 原样传播；收益是启动期瞬态占用竞争可自愈，代价是重试累计等待且其他失败不重试。

来源：[jiuwenswarm/channels/tui/frontend/src/app-state.ts:L98–L105](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/app-state.ts#L98-L105), [jiuwenswarm/channels/tui/frontend/src/app-state.ts:L3636–L3647](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/app-state.ts#L3636-L3647)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":105,"path":"jiuwenswarm/channels/tui/frontend/src/app-state.ts","sha256":"0c3682acc454ababbcfefa4b7853fc18abfee6faeab68d5e5863694eacf12ba7","start":98},{"end":3647,"path":"jiuwenswarm/channels/tui/frontend/src/app-state.ts","sha256":"b2ee99736aeae01e576e35d45bd46bdb5371bd0053da03e74df2dac390e2f694","start":3636}],"trace":[]} -->
<!-- /kb:depth -->
