---
title: "已有 PR 自动修复：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts:L24-L40, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts:L140-L147, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.ts:L61-L68, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts:L21-L22, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts:L64-L69, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts:L5-L19, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts:L102-L110, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts:L1-L3, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts:L66-L69, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts:L140-L146, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts:L73-L138, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.status.ts:L179-L189, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts:L88-L100, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts:L102-L147, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/自动修复PR.md:L115-L130", "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/自动修复PR.md:L150-L154"]
feature: "autofix"
entry_points: ["jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.ts", "jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts"]
source_globs: ["jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr*.ts"]
---

# 已有 PR 自动修复：实现深读

[功能概览](feature-autofix.md) · [owner 入口](_index.md)

<!-- kb:depth feature=autofix facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c3a2978d901730cabc0f92c5f77669f5c663d81f89195da9872faeda1e21b2c9 -->
**PrWatchDeps.sendMessage 的离线契约**
注入的 sendMessage: (prompt: string) => string | null 返回 requestId，离线时返回 null；调用方 PrWatchController.runRound 据此决定是否计入轮数——null 不算一轮，由下一次已连接的 tick 重试。宿主必须遵守该契约，否则轮数保险丝会被离线期间虚假消耗。

来源：[jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts:L24–L40](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts#L24-L40), [jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts:L140–L147](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts#L140-L147)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts","start":24,"end":40,"sha256":"75e9dbc6fd93d86f701b4aff6ce793fb9960f891d130546466677a8bf269f80a"},{"path":"jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts","start":140,"end":147,"sha256":"c1d2cedca0648c9ee70ff4916745f027d7c7ad7338ebf66aca046d1b284abd74"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=autofix facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5b9cbd4c9cf8b83bd6fc2c4645f84107f0c0d3188112220f146f6400c69b7dcb -->
**--interval 的解析、下限与默认值**
命令侧用正则 (^|\s)--interval[=\s]+([\d.]+) 解析分钟数（支持小数），换算为毫秒后 Math.max(10_000, …)，即下限 10 秒；未提供时 intervalMs 为 undefined，PrWatchController 构造函数回退 DEFAULT_WATCH_INTERVAL_MS = 10 * 60_000（10 分钟），maxRounds 回退 DEFAULT_WATCH_MAX_ROUNDS = 12。

来源：[jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.ts:L61–L68](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.ts#L61-L68), [jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts:L21–L22](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts#L21-L22), [jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts:L64–L69](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts#L64-L69)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.ts","start":61,"end":68,"sha256":"bf16bb43d698e99aa23f98d2fc020ff7deec5a253a5417516eece03992fd4b6c"},{"path":"jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts","start":21,"end":22,"sha256":"94c1e0f1a85b811d2b5eb506c1c34f756ec35afbdbf17ce91d9d776f5c19b62d"},{"path":"jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts","start":64,"end":69,"sha256":"e6824008932c870f8e5fcf78f535777adb979a910ecb130fcaef2a0eb753f8e8"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=autofix facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ad3fa9ebf5a0e140a45f6c52801085230f14ec5cdc1d44117f36861b09d7624d -->
**setInterval 轮询 + isBusy 跳过，而非事件钩防重叠**
设计推断（非作者历史意图）：

源码注释明示选择「Deliberately simple」：用 setInterval 轮询，靠 ticking 标志与 deps.isBusy() 在忙碌时跳过本轮，而非接入回合结束事件。收益是纯客户端实现、无需后端/agentserver 配合；代价是轮次节奏受 interval 粒度限制，忙碌或离线期间检查被顺延（此代价分析为推断）。

来源：[jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts:L5–L19](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts#L5-L19), [jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts:L102–L110](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts#L102-L110)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts","start":5,"end":19,"sha256":"2b2ccf684267276e8522e9171b0657a5af2555cea62e1cf72ebb7b411db44546"},{"path":"jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts","start":102,"end":110,"sha256":"4096daaddd00e16be0238b145262cba07f45ef2b658d5c3a9d9af9b2c6be2911"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=autofix facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f671fa5ad57f940bb2bab8c55f003f5b425f9d3dde10d1dccc1a43457ba62062 -->
**start() 首轮后按 intervalMs 轮询；tick 仅在已连接且空闲时查状态，随后停止、熔断或再跑一轮**
start() 在 timer 为空且未 stopped 时先 runRound()，再 setInterval 每 intervalMs 调 tick()；tick() 需 !stopped、!ticking、isConnected() 且 !isBusy() 才 await checkStatus，shouldStop 即 stop(reason)，roundsRun≥maxRounds 熔断，否则 runRound()。

来源：[jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts:L73–L138](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts#L73-L138), [jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.status.ts:L179–L189](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.status.ts#L179-L189)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":138,"path":"jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts","sha256":"3ee840e43d3a8c083165968a4bae8f1f9eaea3558e164e93faca15c281c3376b","start":73},{"end":189,"path":"jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.status.ts","sha256":"8965b8884774dcf0cd974ab7f96a2c72d4c5380cdffa0301859bcc8b48d43161","start":179}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=autofix facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=209bc9d09bda40cfe3f3337d2a61d3d8f86f933880a3e453f0b050ca1d76f2a1 -->
**watch.ts 导入 status 的 checkPrStatus 与 prompts 的 buildAutofixPrPrompt；未注入 checkStatus 时回落真实实现**
构造器里 maxRounds = config.maxRounds ?? DEFAULT_WATCH_MAX_ROUNDS、checkStatus = deps.checkStatus ?? checkPrStatus、语言默认 "zh"；tick 的停止判断耦合返回值的 shouldStop，每轮发送则完全经注入的 deps.sendMessage 完成。

来源：[jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts:L1–L3](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts#L1-L3), [jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts:L66–L69](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts#L66-L69), [jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts:L140–L146](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts#L140-L146)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":3,"path":"jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts","sha256":"69f44e6e266a987c053292f3c8325ba2e62525731d72f244403dfa9ef0e50577","start":1},{"end":69,"path":"jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts","sha256":"f5e756d564f242569286212081a27410262832a63978277b269be204a438f1e1","start":66},{"end":146,"path":"jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts","sha256":"07a2e060d878c0041096ffad4690a53eb9c8a8c08ea3a9e4d1fe61fc69316f7e","start":140}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=autofix facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ba392e5e130979c9472f0ef0eb3121056b79ddcec933b8c3dfcdf9716b0e0f7f -->
**tick 守卫分支：状态检查抛错仅结束本轮，不停止 watch 等下一 tick 重试**
tick() 在 stopped、ticking、!isConnected() 或 isBusy() 时直接 return。checkStatus 抛异常被 catch 后仅 return，finally 清除 ticking，不调用 stop()，下个 interval 重试；status.shouldStop 才以 reason 停止，roundsRun ≥ maxRounds 触发保险丝停止，否则 runRound()，其仅在 sendMessage 返回 requestId 时计轮（null 不计）。

来源：[jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts:L88–L100](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts#L88-L100), [jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts:L102–L147](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts#L102-L147)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":100,"path":"jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts","sha256":"78a0379911aa5277d6351cb5e799d225c65fb29c4124e7a2e04bdbb0586dd9d0","start":88},{"end":147,"path":"jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts","sha256":"308ce24cff5ac5ea7625597a72b3c5f441352d38295e9fae5fceaf2bf395796f","start":102}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=autofix facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=683e1ad9994592063779923579a42454a141a6241192e15edac966402ac1a671 -->
**/autofix-pr --watch 的文档化人工验收（未执行）**
文档中的人工验收步骤（本轮未执行）：

文档化步骤（本轮未执行）：在 Code 模式、已跟踪文件无未提交改动且能定位到开放 PR 的前提下运行 /autofix-pr --watch（或 /autofix-pr <PR号> --watch）。文档预期可观察结果：立即先跑一轮且完整显示在会话里；上一轮仍在跑时复查直接跳过；WebSocket 断线时不硬发，掉线那次不计入轮数；--stop 停止。此处不声称修复或 CI 已通过。

来源：[docs/zh/自动修复PR.md:L115–L130](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E8%87%AA%E5%8A%A8%E4%BF%AE%E5%A4%8DPR.md#L115-L130), [docs/zh/自动修复PR.md:L150–L154](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E8%87%AA%E5%8A%A8%E4%BF%AE%E5%A4%8DPR.md#L150-L154)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":130,"path":"docs/zh/自动修复PR.md","sha256":"df7aa8e781a52e2b66c9a3b2a8b9c7d51a0f10bf0af361fc6f3f54fe74e67177","start":115},{"end":154,"path":"docs/zh/自动修复PR.md","sha256":"4a4e89a29618ff5ee4039a3dcba35c91ebf1dbdd32929021e932cc41c83aec15","start":150}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
