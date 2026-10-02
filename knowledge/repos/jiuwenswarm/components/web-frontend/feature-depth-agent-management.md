---
title: "智能体资产管理与工作区浏览：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/index.tsx:L984-L1004, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts:L166-L207, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts:L166-L187, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts:L83-L108, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/tests/agentManagementClient.test.mjs:L42-L51, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts:L182-L203, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/tests/agentManagementClient.test.mjs:L4-L16, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts:L1-L45, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts:L327-L349, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/stores/agentCatalogStore.ts:L35-L42]
feature: "agent-management"
entry_points: ["jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/index.tsx", "jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts", "jiuwenswarm/channels/web/frontend/src/components/AgentPanel/index.tsx"]
source_globs: ["jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/index.tsx", "jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts", "jiuwenswarm/channels/web/frontend/src/components/AgentPanel/index.tsx"]
---

# 智能体资产管理与工作区浏览：实现深读

[功能概览](feature-agent-management.md) · [owner 入口](_index.md)

<!-- kb:depth feature=agent-management facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2a5c7cff822162c94da260ea25e1827749ac503cbe2cc6da009b86a5687bb479 -->
**installDefinition 的结果契约**
client.installDefinition 返回带 kind 字段的结果：调用方 handleInstall 在 result.kind === 'auth_required' 时抛出 t('agentManagement.states.authRequired') 中止流程；当安装因连接器未就绪抛出 AgentInstallPendingError 时，错误对象携带 pendingConnectors 列表，面板据此把任务入队等待连接完成后重试。调用方义务是捕获该错误类型而非当作普通失败。

来源：[jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/index.tsx:L984–L1004](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/index.tsx#L984-L1004)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/index.tsx","start":984,"end":1004,"sha256":"bc1189ecfb029ebdb2dfb5e83bb01d4b31de3378eed784486ff122f428b9c5cb"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=agent-management facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cde429882a1ed1250c89b07df6ba34bcff3b61951e036fb2fa84a2e745515dcf -->
**listSkillOptions 在 includeTeamMarketplace 且提供回调时先返回基础列表，后台再拉团队市场**
listSkillOptions 先以 with_installed:true 调 skills.list，过滤 source!=='mcp' 后归一化；当 includeTeamMarketplace 且传入 onTeamMarketplaceLoaded 时立即返回基础列表，并在 setTimeout(0) 中请求 skills.swarmskillshub.recommend（top_k:500、cache_mode:'prefer_cache'、timeoutMs:30000），success 非 false 才回调合并列表与 cache。

来源：[jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts:L166–L207](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts#L166-L207)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":207,"path":"jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts","sha256":"c744e6136273418a67105bedbd11000ca68f1bb255780f77af54e420c013463e","start":166}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=agent-management facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1e2014986b3d82c7b671a78264ae3a74804a0bcc3eaed0310fdb7c35a07a0f28 -->
**listSkillOptions 默认 options={}：未传 includeTeamMarketplace 不请求 Hub**
options 默认为空对象：未传 includeTeamMarketplace 时直接返回 skills.list 的归一结果，不发起 Hub 请求；传了它但未传 onTeamMarketplaceLoaded 时保持旧的同 await 合并路径，且 teamMarketplace.success===false 时只返回本地列表。

来源：[jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts:L166–L187](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts#L166-L187)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":187,"path":"jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts","sha256":"9a86da46f0bc14d617582df149776be34d16491dee434f24f6d136f9c4beff44","start":166}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=agent-management facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=aaba0d54fba551cbaa948837070e2bbbf1eacefe5065b56f644fadd1796f6768 -->
**client 依赖 agentCatalogStore：删除/安装 webRequest 成功后失效目录，导入仅在 payload.id 非空时**
client.ts 导入 invalidateAgentCatalog，并在 'agent_templates.delete' 与 'agent_templates.install' 的 await webRequest 成功后调用，store 随即置 catalog=null、status='idle' 并递增 revision；'agent_templates.import_local' 仅当 payload.id 非空才失效，为空则抛 code 'agent_import_empty' 的 AgentManagementError 并跳过失效。

来源：[jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts:L1–L45](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts#L1-L45), [jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts:L327–L349](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts#L327-L349), [jiuwenswarm/channels/web/frontend/src/stores/agentCatalogStore.ts:L35–L42](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/agentCatalogStore.ts#L35-L42)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":45,"path":"jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts","sha256":"fa918ed052fcd1255339cd0ad3b5d41f55245d71e9bf5d8e723020b34ce0d374","start":1},{"end":349,"path":"jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts","sha256":"cb802b24451c6d454dcde4b0337ee9062961d3ab1675faf6911d12e8c2f3f24e","start":327},{"end":42,"path":"jiuwenswarm/channels/web/frontend/src/stores/agentCatalogStore.ts","sha256":"e032bda86e8c468f2f6cabbe9651f08c1c078db18b97c65360a1dfba4485a872","start":35}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=agent-management facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7dec208482342c87bc922db139b91b1621334a95496d929e790188ccfee79a19 -->
**标签补全失败时 allSettled 丢弃失败项，卡片按原 tags 原样返回**
触发：某卡片 tags 为空且 agent_templates.show 抛错（或返回空 template，抛 code 'agent_detail_empty'）；守护分支：Promise.allSettled 仅收 status==='fulfilled' 且 tags.length>0 的结果；恢复：未补全卡片保持原 tags（如 []）返回，不向上抛错。

来源：[jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts:L83–L108](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts#L83-L108), [jiuwenswarm/channels/web/frontend/tests/agentManagementClient.test.mjs:L42–L51](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/tests/agentManagementClient.test.mjs#L42-L51)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":108,"path":"jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts","sha256":"f59f2524c226617f85989ac1658612137b4cadbaa5d2aadb989cd5d2969d11d7","start":83},{"end":51,"path":"jiuwenswarm/channels/web/frontend/tests/agentManagementClient.test.mjs","sha256":"150c2055932be3f41575201314244203fb7643080c81c5eece1eab51fff5eb73","start":42}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=agent-management facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=52c115d475d8b0ff2666d3e63843cc927306133b35dda6dea251fd5c98fb8431 -->
**渐进式团队市场让选择器即刻可用，代价是 Hub 失败被静默吞掉**
设计推断（非作者历史意图）：

收益（推断）：基础列表先返回，慢速 Hub 不阻塞选择器（与 189 行注释一致）；成本（推断）：该路径 Hub 请求失败只进 .catch(() => {})，onTeamMarketplaceLoaded 收不到失败通知，调用方无法区分『无市场数据』与『市场故障』。

来源：[jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts:L182–L203](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts#L182-L203)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":203,"path":"jiuwenswarm/channels/web/frontend/src/features/agentManagement/client.ts","sha256":"cc62eee4f82509bc47f66842db5a3bd26ca70ec2b3f5559f5545253d6205c8ab","start":182}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=agent-management facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=395f2cd61c654022644a3bd0532b1b5877979469b5ec2965f215e8d10b1651a0 -->
**node:test 用例运行 esbuild 打包后的真实 client 并断言标签降级保留**
用例先以 esbuild 打包 src/features/agentManagement/client.ts 与 services/webClient.ts 并动态导入，把 webClient.request stub 为 detail 请求抛 'Remote detail is unavailable'，断言 listCatalog({enrichTags:true}) 仍返回 items[0].id==='cached'、tags 深等于 [] 且 cache 元数据保留。

来源：[jiuwenswarm/channels/web/frontend/tests/agentManagementClient.test.mjs:L4–L16](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/tests/agentManagementClient.test.mjs#L4-L16), [jiuwenswarm/channels/web/frontend/tests/agentManagementClient.test.mjs:L42–L51](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/tests/agentManagementClient.test.mjs#L42-L51)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":16,"path":"jiuwenswarm/channels/web/frontend/tests/agentManagementClient.test.mjs","sha256":"fe3adcae9b137e884b890a547fbbee991ba97e03b5ece4eeca6183c3035ec609","start":4},{"end":51,"path":"jiuwenswarm/channels/web/frontend/tests/agentManagementClient.test.mjs","sha256":"150c2055932be3f41575201314244203fb7643080c81c5eece1eab51fff5eb73","start":42}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
