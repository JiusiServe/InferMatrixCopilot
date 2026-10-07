---
title: "AgentOS 沙箱创建与幂等对账：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/agentos/agentos_router/registry_client.py:L338-L339, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/agentos/agentos_router/registry_client.py:L495-L535, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/agentos/agentos_router/stale_cleanup.py:L22-L53, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/agentos/agentos_router/agent_manager.py:L406-L412, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/agentos/agentos_router/agent_manager.py:L507-L534, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/agentos/agentos_router/stale_cleanup.py:L61-L78, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/extensions/test_agentos_agent_manager.py:L127-L141]
feature: "agentos-sandbox-create-lifecycle"
entry_points: ["jiuwenswarm/extensions/agentos/agentos_router/router_client.py"]
source_globs: ["jiuwenswarm/extensions/agentos/agentos_router/router_client.py", "jiuwenswarm/extensions/agentos/agentos_router/agent_manager.py", "jiuwenswarm/extensions/agentos/agentos_router/config.py", "jiuwenswarm/extensions/agentos/agentos_router/stale_cleanup.py"]
---

# AgentOS 沙箱创建与幂等对账：实现深读

[功能概览](feature-agentos-sandbox-create-lifecycle.md) · [owner 入口](_index.md)

<!-- kb:depth feature=agentos-sandbox-create-lifecycle facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=69d177077512df500fd233207c2e57a4d8826af9238ebd0d5012eff27a6f43af -->
**RegistryClient.enabled 由 _base_url 决定，禁用时 list_instances 回退到本地 _registered_agents**
enabled 即 bool(self._base_url)。list_instances 在 not self.enabled 时不发 GET api/instances，而是把 _registered_agents 中的 info 转成 InstanceRecord 并用 _instance_matches 按 node/framework/kind/user/include_unhealthy 过滤后返回。

来源：[jiuwenswarm/extensions/agentos/agentos_router/registry_client.py:L338–L339](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/agentos/agentos_router/registry_client.py#L338-L339), [jiuwenswarm/extensions/agentos/agentos_router/registry_client.py:L495–L535](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/agentos/agentos_router/registry_client.py#L495-L535)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":339,"path":"jiuwenswarm/extensions/agentos/agentos_router/registry_client.py","sha256":"10bb154caed05508c7b10baa54bb999aa4d9ee0ec1f42e86fe25d5d7fe299147","start":338},{"end":535,"path":"jiuwenswarm/extensions/agentos/agentos_router/registry_client.py","sha256":"fdce90795d13d5b3171b18df4752bac7b115c7e50f4170e2b62404c1aba0b185","start":495}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=agentos-sandbox-create-lifecycle facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0d6077affadb8067dcf17900c2aa429eab146716b7ea89241ad45250158f314d -->
**cleanup_stale_sandboxes 依赖注入 YuanRong、Registry、AgentManager，registry.enabled 关闭即返回 0**
该函数以关键字参数注入 YuanrongFrontendAgentClient、RegistryClient 与 AgentManager；当 registry.enabled 为假时直接返回 0，不发起 list_instances，实例列举经由 registry.list_instances(include_unhealthy=True)。

来源：[jiuwenswarm/extensions/agentos/agentos_router/stale_cleanup.py:L22–L53](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/agentos/agentos_router/stale_cleanup.py#L22-L53)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":53,"path":"jiuwenswarm/extensions/agentos/agentos_router/stale_cleanup.py","sha256":"17ee54200c12f3d61ddf49a7ef8ccf3f23217103b7e721bfadc2e8154c4fb03b","start":22}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=agentos-sandbox-create-lifecycle facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b3a51c0eba8808c5214de57ef8be876a7363997774c4d38a896410a1cda09b84 -->
**等待创建时按状态抛 AgentCreatingTimeout/AgentDeleted/AgentCreateFailed；_mark_creator_failed 仅作用于仍是 owner 的 runtime**
创建等待路径在超时（含 AGENT_CREATING_TIMEOUT 消息）、runtime.is_deleted()、is_failed() 时分别抛 AgentCreatingTimeout、AgentDeleted、AgentCreateFailed。_mark_creator_failed 在锁内确认 _runtimes.get(key) 仍是 owner_runtime 才 mark_failed；对 asyncio.CancelledError 只记 WARNING 日志并直接 return，不 logger.exception。

来源：[jiuwenswarm/extensions/agentos/agentos_router/agent_manager.py:L406–L412](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/agentos/agentos_router/agent_manager.py#L406-L412), [jiuwenswarm/extensions/agentos/agentos_router/agent_manager.py:L507–L534](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/agentos/agentos_router/agent_manager.py#L507-L534)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":412,"path":"jiuwenswarm/extensions/agentos/agentos_router/agent_manager.py","sha256":"92645f7b9f6109b190ed9d406a91b6a56c232baae15716f52cdc44556354894d","start":406},{"end":534,"path":"jiuwenswarm/extensions/agentos/agentos_router/agent_manager.py","sha256":"da97e87bfc4a7a2250f840d74a884ce1a686fe5718aa27610d29d54ef587aebe","start":507}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=agentos-sandbox-create-lifecycle facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=59ae635021e0118bcb032b6a1567726cd6adfe4a3c74a406d8ebf31eda823079 -->
**清理循环逐条容错：单条失败不中断，但返回值只计尝试数**
设计推断（非作者历史意图）：

收益：单条 _cleanup_one 异常仅 logger.exception 后继续处理其余记录，启动期清理不会因一行坏数据而中断；代价（推断）：processed 统计的是尝试条数而非成功销毁数，调用方无法从返回值区分部分失败。is_closed 回调为真时提前 break。

来源：[jiuwenswarm/extensions/agentos/agentos_router/stale_cleanup.py:L61–L78](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/agentos/agentos_router/stale_cleanup.py#L61-L78)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":78,"path":"jiuwenswarm/extensions/agentos/agentos_router/stale_cleanup.py","sha256":"906de3e8e65555aedae53145ae72e164b109b0d34d6a15e5d9f484a6d6b7e6d6","start":61}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=agentos-sandbox-create-lifecycle facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8ebd2965aca5540f018c29b9cfeafb42c1d350cdd63fcd5994799d0d115f2b1a -->
**test_agent_manager_get_delete_and_list 运行时验证 get/删除/列举契约**
该 asyncio 测试先 get_or_create_agent("u1","jiuwenswarm")，断言 get_agent 返回的快照 info 与 created.info 相等且 list_user_agents 含该 agent_id；随后 delete_agent 并断言 get_agent 返回 None、list_user_agents 为空列表。断言覆盖 AgentManager 本身，属 helper 级运行时验证。

来源：[tests/unit_tests/extensions/test_agentos_agent_manager.py:L127–L141](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/extensions/test_agentos_agent_manager.py#L127-L141)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":141,"path":"tests/unit_tests/extensions/test_agentos_agent_manager.py","sha256":"7d95a51cae0787424f1461de2074bedcb268e88345be901a626ba5a1e4f3eb5b","start":127}],"trace":[],"validation_kind":"helper_unit"} -->
<!-- /kb:depth -->
