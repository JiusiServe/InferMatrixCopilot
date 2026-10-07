---
title: "Web 资产发布流程（prepare/commit/轮询/提交锁）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/services/assetPublishApi.ts:L28-L38, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/hooks/useAssetPublish.ts:L39-L61, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/assetPublishState.ts:L7-L15, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/assetPublishState.ts:L47-L61, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/assetPublishErrors.ts:L13-L33, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/tests/assetPublishDrawer.test.mjs:L317-L331, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/assetPublishEvents.ts:L1-L4, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/services/assetPublishApi.ts:L10-L38, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/assetPublishState.ts:L23-L41, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/services/assetPublishApi.ts:L10-L19, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/services/assetPublishApi.ts:L27-L38, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/utils/gitcodeOAuth.ts:L32-L47, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/hooks/useAssetPublish.ts:L29-L30]
feature: "web-asset-publish-flow"
entry_points: ["jiuwenswarm/channels/web/frontend/src/hooks/useAssetPublish.ts"]
source_globs: ["jiuwenswarm/channels/web/frontend/src/hooks/useAssetPublish.ts", "jiuwenswarm/channels/web/frontend/src/types/assetPublish.ts", "jiuwenswarm/channels/web/frontend/src/features/assetPublication.ts", "jiuwenswarm/channels/web/frontend/src/features/assetPublishErrors.ts", "jiuwenswarm/channels/web/frontend/src/features/assetPublishEvents.ts", "jiuwenswarm/channels/web/frontend/src/features/assetPublishState.ts"]
---

# Web 资产发布流程（prepare/commit/轮询/提交锁）：实现深读

[功能概览](feature-web-asset-publish-flow.md) · [owner 入口](_index.md)

<!-- kb:depth feature=web-asset-publish-flow facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3c11fb91725fe2d3b64df464092cb57c393e33ac6017da5a03fdbb330eb1d69e -->
**updateSubmission 回调按活动提交过滤记录并设置提交锁**
useAssetPublish 的 updateSubmission 回调：若已有 activeSubmission 且其 operationId/draftId 均不匹配 next，则返回 false 不更新；否则按 publishOutcome 是否为 queued/uploading/unknown 设置 activeSubmission 与 submissionLocked，并把记录去重前插到 records。record 相关字段变化时通过 window 事件 'asset-publication-changed' 通知。

来源：[jiuwenswarm/channels/web/frontend/src/hooks/useAssetPublish.ts:L39–L61](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/hooks/useAssetPublish.ts#L39-L61), [jiuwenswarm/channels/web/frontend/src/features/assetPublishState.ts:L7–L15](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/assetPublishState.ts#L7-L15)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":61,"path":"jiuwenswarm/channels/web/frontend/src/hooks/useAssetPublish.ts","sha256":"03a1257fbd9bfd841096980b20e9f2733089a06b13a0517d1ad645bfb518b2ba","start":39},{"end":15,"path":"jiuwenswarm/channels/web/frontend/src/features/assetPublishState.ts","sha256":"39867aefa122c69e656e4ffd4a1149705041f0f12743c7f37e35d242a71f7f0e","start":7}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-asset-publish-flow facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=da7edcf650bdf426f57a6491303246adad59c3a322628749f601a98637409691 -->
**assetPublishApi.commit 接受 (draft_id, request_id)；prepare 传 metadata、可选 target_asset_id 与 force**
commit 调用 request('commit', {draft_id, request_id}) 返回 PublishRecord；prepare 过滤空 tags，target_asset_id 仅在非空时携带，并显式传 force。调用方须提供幂等 request_id。

来源：[jiuwenswarm/channels/web/frontend/src/services/assetPublishApi.ts:L28–L38](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/assetPublishApi.ts#L28-L38)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":38,"path":"jiuwenswarm/channels/web/frontend/src/services/assetPublishApi.ts","sha256":"cf97661281a487f80dbb446bd43619b636096c74fc431da178d535e0265f66fb","start":28}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-asset-publish-flow facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b019fa85a18cd1f2774fed2b627e9e3ce6f983007d03ab1c2c9bd4be28441dee -->
**发布 RPC 默认 75 秒超时，localStatus 单独用 15 秒且不带 auth**
describe/prepare/commit/status/records 经共享 request 助手走 `assets.publish.*` 并统一注入 auth 与 `{ timeoutMs: 75_000 }`；仅 localStatus 直接调 webRequest，超时 15_000 且参数只含引用字段。

来源：[jiuwenswarm/channels/web/frontend/src/services/assetPublishApi.ts:L10–L38](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/assetPublishApi.ts#L10-L38)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":38,"path":"jiuwenswarm/channels/web/frontend/src/services/assetPublishApi.ts","sha256":"f6e8f535af9051d00e283c2bb17e10df1fd8415ed8b514c8e38b0778c92a02a0","start":10}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-asset-publish-flow facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7bf87297a5304c9589caeeb32408e6d6577b79be09ce06804f6986382a3dc526 -->
**definitiveCommitRejection 区分 'expired'/'rejected'，publishIssueKey 未知错误回落 'requestFailed'**
definitiveCommitRejection 仅在 code/message 字符串匹配 \bdraft_expired\b（不区分大小写）时返回 'expired'，匹配 invalid_draft、draft_not_found、publish_auth_required、auth_required、invalid_identifier、queue_full、target_conflict 时返回 'rejected'，否则 null。publishIssueKey 将错误码规范化（trim、'-'→'_'、大写）后查 SAFE_FAILURE_KEYS 白名单，未命中回落 'requestFailed'。

来源：[jiuwenswarm/channels/web/frontend/src/features/assetPublishState.ts:L47–L61](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/assetPublishState.ts#L47-L61), [jiuwenswarm/channels/web/frontend/src/features/assetPublishErrors.ts:L13–L33](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/assetPublishErrors.ts#L13-L33)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":61,"path":"jiuwenswarm/channels/web/frontend/src/features/assetPublishState.ts","sha256":"62eeb08e06161366109032827663027e772d6c2c54617fe70bedc9f27f8720f5","start":47},{"end":33,"path":"jiuwenswarm/channels/web/frontend/src/features/assetPublishErrors.ts","sha256":"d69fbf3d9c28b06213bb74dc305792ad4eafe473ef0ae32ffeacc2cec60a2290","start":13}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-asset-publish-flow facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2a488908239b8eb8b76d9437d3fe90e7011c3be0a3fa1efe83cde24c8b7943dc -->
**createCommitAttempt 并发去重换取固定 requestId 重试：成功结果被缓存，失败后会重新 send**
设计推断（非作者历史意图）：

收益：同一 attempt 实例内并发的 run() 共享同一个 pending Promise，成功后 completed 缓存让后续 run 直接返回已兑现值。成本：仅成功结果被缓存——send 拒绝后 finally 清空 pending，之后的 run 会用同一 requestId 再次调用 send，客户端本身并不阻止重复提交（推断：去重依赖服务端按 request_id 幂等）。

来源：[jiuwenswarm/channels/web/frontend/src/features/assetPublishState.ts:L23–L41](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/assetPublishState.ts#L23-L41)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":41,"path":"jiuwenswarm/channels/web/frontend/src/features/assetPublishState.ts","sha256":"7476b6dbb3a5536cff7736534cb31140a8f4a567533124908557ace2fc593481","start":23}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-asset-publish-flow facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2b2aa1b8a6f01c2696a44f5bb6d9bafff52ee69cd1b88fa0a7f64613b19da997 -->
**抽屉测试用桩 API 验证轮询完成后更新历史行（automated_runtime）**
assetPublishDrawer.test.mjs 用 assetPublishApi.describe/status 桩返回 queued→completed/pending_moderation，openAssetPublish 打开抽屉后等待约 2100ms，断言 'asset-publish-record' 文本匹配 /pending moderation/i。这是对抽屉运行时行为的自动化测试（API 已打桩），非本批内执行的声明。

来源：[jiuwenswarm/channels/web/frontend/tests/assetPublishDrawer.test.mjs:L317–L331](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/tests/assetPublishDrawer.test.mjs#L317-L331), [jiuwenswarm/channels/web/frontend/src/features/assetPublishEvents.ts:L1–L4](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/assetPublishEvents.ts#L1-L4)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":331,"path":"jiuwenswarm/channels/web/frontend/tests/assetPublishDrawer.test.mjs","sha256":"aed4e702fac29d9fe2d8c31f88c84d5c6ab2fe1eb3ad2702d3a308fc3ed2e0de","start":317},{"end":4,"path":"jiuwenswarm/channels/web/frontend/src/features/assetPublishEvents.ts","sha256":"b014884785519b05dbc90594c2a58cf88c1475f99bb675fe62f0bae68bc20d26","start":1}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-asset-publish-flow facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=764c49a552acf60d70d1c5232d70dd0d28eaa526d30a530b45085e13e487ec3b -->
**assetPublishApi 的 describe/prepare/commit/status/records 五方法经共享 request 注入 OAuth 凭据并依赖 sessionStorage 读取**
所示 assetPublishApi.ts 中 describe、prepare、commit、status、records 五个方法都经共享 request<T> 调 webRequest，方法名拼接为 `assets.publish.${method}`，并统一附加 auth（getStoredOAuthToken/getStoredOAuthProvider）与 timeoutMs 75_000。凭据读取依赖 sessionStorage：getStoredOAuthToken 读取异常时返回 null，getStoredOAuthProvider 仅在归一化为 'github' 时返回 'github'，否则（含异常）回退 'gitcode'。useAssetPublish.ts L29 以 `${provider}:${token || ''}` 构造作用域键，token 为 null 时用空字符串。此范围不含 localStatus 等未展示分支。

来源：[jiuwenswarm/channels/web/frontend/src/services/assetPublishApi.ts:L10–L19](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/assetPublishApi.ts#L10-L19), [jiuwenswarm/channels/web/frontend/src/services/assetPublishApi.ts:L27–L38](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/assetPublishApi.ts#L27-L38), [jiuwenswarm/channels/web/frontend/src/utils/gitcodeOAuth.ts:L32–L47](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/gitcodeOAuth.ts#L32-L47), [jiuwenswarm/channels/web/frontend/src/hooks/useAssetPublish.ts:L29–L30](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/hooks/useAssetPublish.ts#L29-L30)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":19,"path":"jiuwenswarm/channels/web/frontend/src/services/assetPublishApi.ts","sha256":"4c17f2a08ec9214aeb8ec5588a9529cbfe61c20e2d089e03db0a6a39f2cda156","start":10},{"end":38,"path":"jiuwenswarm/channels/web/frontend/src/services/assetPublishApi.ts","sha256":"4dc35764ab91fe32e93216fa4e9c531a012c116a5156a462243d8daa9f0ff7bb","start":27},{"end":47,"path":"jiuwenswarm/channels/web/frontend/src/utils/gitcodeOAuth.ts","sha256":"05d08b0b44c0bf7a6a4d9213ea13438783e0cfc9178a8dfdc3ceb9d9b6064270","start":32},{"end":30,"path":"jiuwenswarm/channels/web/frontend/src/hooks/useAssetPublish.ts","sha256":"8f3c15ff7b0d1686a3ef58d320da304bec97784cade188a8d2dcff750b373300","start":29}],"trace":[]} -->
<!-- /kb:depth -->
