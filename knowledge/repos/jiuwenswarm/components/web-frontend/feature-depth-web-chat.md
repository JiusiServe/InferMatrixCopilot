---
title: "Web 对话与流式状态：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts:L1250-L1259, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts:L1261-L1276, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/A2UI.md:L72-L87, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts:L434-L448, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts:L291-L296]
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
