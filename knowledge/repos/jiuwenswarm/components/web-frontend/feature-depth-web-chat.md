---
title: "Web 对话与流式状态：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts:L1250-L1259, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts:L1261-L1276, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/A2UI.md:L72-L87, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts:L434-L448, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts:L291-L296, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/sessionInput.ts:L25-L43, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts:L515-L523, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts:L4343-L4352, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ChatPanel/MessageItem.tsx:L812-L837, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/a2ui/A2UIMessageContent.tsx:L159-L168, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/MarkdownRenderer.tsx:L97-L99]
feature: "web-chat"
entry_points: ["jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts"]
source_globs: ["jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts", "jiuwenswarm/channels/web/frontend/src/*"]
---

# Web 对话与流式状态：实现深读

[功能概览](feature-web-chat.md) · [owner 入口](_index.md)

<!-- kb:depth feature=web-chat facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1d112cc0b85988918f0076235ad454808975eac68ce4bd51ed4fba1893a8114a -->
**request 的薄封装契约**
useWebSocket 返回的 request<T>(method, params, options) 只是 webClient.request 的透传封装（回调内一行委托），调用方按统一 WS 请求帧使用 method（如 team.snapshot）加 params.session_id；reconcileTeamMembersFromSnapshot 展示了调用者义务：传入 timeoutMs: 5000 并自行捕获异常，失败时静默保留旧状态。

来源：[jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts:L1250–L1259](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts#L1250-L1259), [jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts:L1261–L1276](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts#L1261-L1276)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts","start":1250,"end":1259,"sha256":"bf4117e34735549561389b806a66134e20b61a9d1ec1936631e9f01a16ca46f2"},{"path":"jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts","start":1261,"end":1276,"sha256":"e882245310fbbbeb03e8e7e5472eb611a07f68e57e36278757164a111ffe9a1d"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-chat facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c3ab0517d8ce42fb6d16e2322b3919378002a7bd9a0f43545e89802234fa47e0 -->
**goal get 连续失败收敛为 unknown**
performGoalGet 中 requestGoalAction 抛错且重试次数耗尽（attempt >= GOAL_GET_RETRY_DELAYS_MS.length）时，不抛出异常，而是把 queryStatus 置 'unknown' 并清空 pendingAction 后返回；成功路径由 applyIncomingGoal 把 queryStatus 收敛回 'ok'。

来源：[jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts:L434–L448](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts#L434-L448), [jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts:L291–L296](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts#L291-L296)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts","start":434,"end":448,"sha256":"33159314babdee9de56b5f1e95fc14e23f7dae7469ce472faf8a900ea067c991"},{"path":"jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts","start":291,"end":296,"sha256":"08bd703f0c17b2a05aa2423b815d19981866b01ef1c59f4f10036732ffda74fe"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-chat facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b412e3e568bd6061b1ea2dd5045655a0c6da5ad3e481fd113d0c806f161b199a -->
**前端构建与 A2UI 默认值脚本**
文档给出的前端相关验证入口：`npm run build`（Web renderer 构建）与 `node scripts/test-a2ui-action-defaults.mjs`（校验 A2UI choice 默认值补齐），后端配套 `uv run pytest tests/unit_tests/a2ui tests/system_tests/test_a2ui_system_flow.py`。这些是文档记录的测试命令，本页未声明其在当前基线已通过。

来源：[docs/zh/A2UI.md:L72–L87](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/A2UI.md#L72-L87)

<!-- kb:depth-proof {"evidence":[{"path":"docs/zh/A2UI.md","start":72,"end":87,"sha256":"10102ee9679f19e5053a526920d32306f8b01573b525014eab74595bd2a2a8a7"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-chat facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=83021e8ae4381f79ca41de6b88d608a159df97aeda3fd2079300c9b3502b679a -->
**sendQueuedTaskInput：仅 agent 模式派发排队输入并预置处理态**
回调先读 useSessionStore 的 runtime mode，非 'agent' 即本地返回；claimTaskInput 认领不到该任务也返回；发起时若 isProcessing 为假，则 setProcessing(true) 并 setThinking(true)，随后取 activeExecutionId 经注入的 request 发出 'chat.send'。

来源：[jiuwenswarm/channels/web/frontend/src/features/sessionInput.ts:L25–L43](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/sessionInput.ts#L25-L43)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":43,"path":"jiuwenswarm/channels/web/frontend/src/features/sessionInput.ts","sha256":"612ccd232362e44a74533d7837940c0bcb092b658ee4a75789e92589bf2f08b7","start":25}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-chat facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1298124dca6a5d16360d0d993159c87287a2cfee51cda97dc1307a89f86a6837 -->
**resolveInterruptResumeMode：非空 team_name 优先于 runtime mode**
先定位会话：sessionId 匹配 currentSession，否则在 sessions 列表查找；team_name 去空白后非空直接返回 'team'，否则返回 normalizeAgentMode(runtimes[sessionId]?.mode)。效果：带团队名的会话中断恢复模式解析为 team，覆盖存储的 runtime mode。

来源：[jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts:L515–L523](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts#L515-L523)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":523,"path":"jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts","sha256":"3505230312662a9849c935fdeacc84b7a186099f7d19bdf0dd7ca94daca6161c","start":515}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-chat facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4418b9f008c4264b414ed777764436ef9e9b9441971854e7c9eff33a85267d6a -->
**chat.processing_status 回调依赖 chatStore 的 switchingMode/isLoadingHistory**
回调先经 shouldDropDuplicatedEvent 去重并跳过主动推荐 payload，再依赖 useChatStore.getRuntime(sessionId) 的 switchingMode 与 isLoadingHistory 标志：任一为真即丢弃本次更新；后果是切模式或加载历史期间会话处理状态不更新。

来源：[jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts:L4343–L4352](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts#L4343-L4352)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":4352,"path":"jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts","sha256":"aa5fac2ed97079957c4615de4540b9a16d19319eab5988f909178bd1cb679d19","start":4343}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-chat facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=240d5a6917ed2cec265a9a6b55c471e7f7718762c6b2434cd9f2696586257609 -->
**Markdown 预处理按 [content]/[markdown] 依赖复用；依赖不变时免重算，内容变化仍整段重算（推断）**
设计推断（非作者历史意图）：

助手流式与最终气泡均经 A2UIMessageContent，text part 用 MarkdownRenderer；其 useMemo 以 [content] 做 unescapeLiteralNewlines+repairCollapsedGfmTables，以 [markdown] 分行。推断收益：依赖不变的重渲染复用旧结果；代价：内容一变（如流式追加）仍对整段字符串重新预处理。

来源：[jiuwenswarm/channels/web/frontend/src/components/ChatPanel/MessageItem.tsx:L812–L837](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/MessageItem.tsx#L812-L837), [jiuwenswarm/channels/web/frontend/src/features/a2ui/A2UIMessageContent.tsx:L159–L168](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/a2ui/A2UIMessageContent.tsx#L159-L168), [jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/MarkdownRenderer.tsx:L97–L99](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/MarkdownRenderer.tsx#L97-L99)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":837,"path":"jiuwenswarm/channels/web/frontend/src/components/ChatPanel/MessageItem.tsx","sha256":"978cf5343913ab88eb8631368ffa465e12d6e2d5edf9dc866f0371ef164c3452","start":812},{"end":168,"path":"jiuwenswarm/channels/web/frontend/src/features/a2ui/A2UIMessageContent.tsx","sha256":"21b7611ec0bc9b83d74229250106db540303d3c9b08ce919b8a6a67826630516","start":159},{"end":99,"path":"jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/MarkdownRenderer.tsx","sha256":"93909eb7bc4a7ec063b4e8e3edc8b96d5093bb4b344b38ba0215148e15740678","start":97}],"trace":[]} -->
<!-- /kb:depth -->
