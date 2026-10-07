---
title: "IDE 单轮文件快照与回退（Rewind）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L32-L48, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L53-L64, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/settings/JiuwenSwarmSettings.kt:L36-L39, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/settings/JiuwenSwarmSettings.kt:L123-L125, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L55-L63, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L249-L255, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts:L929-L940, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L245-L257, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts:L929-L934, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L22-L24, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L41-L53]
feature: "ide-turn-rewind-snapshot"
entry_points: ["jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/ui/ChatToolWindow.kt", "jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts"]
source_globs: ["jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/ui/ChatToolWindow.kt", "jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts", "jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/settings/JiuwenSwarmSettings.kt"]
---

# IDE 单轮文件快照与回退（Rewind）：实现深读

[功能概览](feature-ide-turn-rewind-snapshot.md) · [owner 入口](_index.md)

<!-- kb:depth feature=ide-turn-rewind-snapshot facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7b0f7d522322d968fa1246b38ac859f84ac34c1a86ec60327d694aa0c75eac77 -->
**handleRewind：空快照直接返回，否则恢复、清空并回报 rewind_done**
handleRewind 先取 lastTurnSnapshots 的副本，若 size === 0 直接 return；否则 await performRewind，随后 clearLastTurnSnapshots，并按 failed 是否为 0 组装消息 postToWebview({type:'rewind_done', restored, failed})。performRewind 内对每个条目：originalContent === null 且文件存在时 fs.unlinkSync 删除；非 null 时走恢复原内容分支（该写回语句体未在展示范围内）。

来源：[jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts:L929–L940](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts#L929-L940), [jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L245–L257](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts#L245-L257)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":940,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts","sha256":"689272cccde9f37e38b32935f79b3b48784dba76bb598766ed0e9aa14f88d977","start":929},{"end":257,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts","sha256":"d34c578b0a04d4d223a5a0e987e266c02a5e23be5c582d4c5685eec3b8cc0050","start":245}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ide-turn-rewind-snapshot facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=75c804ec428748cb2223ab643bbd33ad3c33344a38d3668adc07472ece9becd5 -->
**模块导出三个快照生命周期函数，promoteSnapshots 返回是否存在可回退文件**
promoteSnapshots(): boolean 在 currentTurnSnapshots.size === 0 时返回 false，否则提升并返回 true；getLastTurnSnapshots(): Map<string, FileSnapshot> 返回拷贝；clearLastTurnSnapshots(): void 清空 lastTurnSnapshots；ensureSnapshot(filePath) 无返回值。

来源：[jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L32–L48](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts#L32-L48), [jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L53–L64](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts#L53-L64)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":48,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts","sha256":"d5aba3973aa00c041be8e47d6f9bbbe7a92ed8fd4ac6b8c61bb1a877957a1975","start":32},{"end":64,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts","sha256":"e093e90c87837e677f50e643d8c2a5b1cdf21ed9c96344c4427ca9a62571822a","start":53}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ide-turn-rewind-snapshot facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5f6d308b7f88fc615217d8363b6bf742026433718bd36bf72cc18ed82ec55d3a -->
**JetBrains 设置 rewindEnabled 默认 true，注释声明其用于快照/回退**
JiuwenSwarmSettings.State 中 rewindEnabled: Boolean = true，注释为 "When true, snapshot files before agent edits so the rewind feature can become restore them." 的意图性说明（原文：snapshot files before agent edits so the rewind feature can restore them）。所示片段没有消费该开关的代码，因此其 gating 效果在本证据内未确立。

来源：[jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/settings/JiuwenSwarmSettings.kt:L36–L39](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/settings/JiuwenSwarmSettings.kt#L36-L39), [jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/settings/JiuwenSwarmSettings.kt:L123–L125](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/settings/JiuwenSwarmSettings.kt#L123-L125)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":39,"path":"jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/settings/JiuwenSwarmSettings.kt","sha256":"78b609f7b5f4bd367be920d58ab115c6282e450a2aa2eb9ec2b828574ac28622","start":36},{"end":125,"path":"jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/settings/JiuwenSwarmSettings.kt","sha256":"e663d4320e64a473fadf9314f54366fb4c124975a0666fda32109092c131c516","start":123}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ide-turn-rewind-snapshot facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3afe63cfd014942878540588a6aa95c8e19f01ca1df1dc8107d04e7357ee0deb -->
**ChatPanel 的回退依赖 DiffApplier 的三个导出与模块级 Map 状态**
handleRewind 调用 DiffApplier.getLastTurnSnapshots()（返回新 Map 副本）、performRewind(snapshots) 和 clearLastTurnSnapshots()。快照状态是 DiffApplier.ts 模块级变量 currentTurnSnapshots / lastTurnSnapshots；ensureSnapshot 用同步 fs.existsSync/readFileSync 写入，ChatPanel 不自持快照。

来源：[jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts:L929–L934](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts#L929-L934), [jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L22–L24](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts#L22-L24), [jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L41–L53](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts#L41-L53)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":934,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts","sha256":"f9fa18f5af911542871da0b509a616034dbb4f405451986a383b0f6eb336d82c","start":929},{"end":24,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts","sha256":"3fa72ccda52ca12753f073ab8d84b56d228d1a586861061202f2d901d6fcbd92","start":22},{"end":53,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts","sha256":"b60f7dfa74c3e3d86887259391f3cd0240574a640bdf9ee38bcac3a53ed496ef","start":41}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ide-turn-rewind-snapshot facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c8c888feed6bc6adff301877ebdf35f45151bffde93cfa23bb024cfccd505aee -->
**读取失败时快照记为 null，回退会把现存文件当作本轮新建而删除**
设计推断（非作者历史意图）：

ensureSnapshot 的 catch 分支将 currentTurnSnapshots.set(filePath, null)；performRewind 对 null 快照在 fs.existsSync 为真时执行 unlinkSync。即读取异常与"编辑前不存在"不可区分，回退会删除该文件。

来源：[jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L55–L63](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts#L55-L63), [jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L249–L255](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts#L249-L255)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":63,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts","sha256":"5706c671b5ff45f33fa6f9c13cbe5e1293606483821d530ee1e7e0c59132d488","start":55},{"end":255,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts","sha256":"0497b8927f3434c4d7e077435e51f55b997cad9b5c3eed760d9325ed1b540da3","start":249}],"trace":[]} -->
<!-- /kb:depth -->
