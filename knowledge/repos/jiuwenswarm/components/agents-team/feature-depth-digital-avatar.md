---
title: "群聊数字分身与 owner 权限：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/avatar_rail.py:L43-L119, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/permissions/owner_scopes.py:L104-L114, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/avatar_rail.py:L121-L161, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/avatar_rail.py:L164-L170, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/permissions/owner_scopes.py:L117-L127, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/permissions/owner_scopes.py:L7-L11, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/permissions/owner_scopes.py:L170-L181, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/国内频道.md:L211-L215", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/permissions/test_owner_scopes_context.py:L31-L50, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/permissions/test_installed_permission_snapshot.py:L92-L103, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/permissions/owner_scopes.py:L150-L160]
feature: "digital-avatar"
entry_points: ["jiuwenswarm/agents/harness/common/rails/avatar_rail.py", "jiuwenswarm/agents/harness/common/rails/permissions/owner_scopes.py"]
source_globs: ["jiuwenswarm/agents/harness/common/rails/avatar_rail.py", "jiuwenswarm/agents/harness/common/rails/permissions/owner_scopes.py"]
---

# 群聊数字分身与 owner 权限：实现深读

[功能概览](feature-digital-avatar.md) · [owner 入口](_index.md)

<!-- kb:depth feature=digital-avatar facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fdc65e36f8e94f3fe2632775ffdede6fc9388c0867ead78eb2e39a2e231359e8 -->
**Rail 对 owner_scopes ContextVar 的耦合**
AvatarPromptRail 不持有自己的状态源，两个钩子都通过 TOOL_PERMISSION_CONTEXT.get() 读取 owner_scopes 模块设置的 PermissionContext；perm_ctx 为 None 时直接返回不注入。此外 current_permission_owner_scope 用 (channel_id, principal_user_id) 组成 "principal:{channel}:{user}" 令牌供 workspace 溯源，说明身份与工作区归属共用同一上下文，改动字段名会同时影响两处。

来源：[jiuwenswarm/agents/harness/common/rails/avatar_rail.py:L43–L119](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/avatar_rail.py#L43-L119), [jiuwenswarm/agents/harness/common/rails/permissions/owner_scopes.py:L104–L114](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/owner_scopes.py#L104-L114)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/rails/avatar_rail.py","start":43,"end":119,"sha256":"873c50b6d7cf43806f2be5f2efa541c47379c115b79aca41f20db42d622d8d4b"},{"path":"jiuwenswarm/agents/harness/common/rails/permissions/owner_scopes.py","start":104,"end":114,"sha256":"d33e51196e242042c253980e078559852fc72a51ff6f1f4ab0b87a22e303a577"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=digital-avatar facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=200c1db8833a954180a067f789d35eb4248d8156734e155530c5f2e23ec0b049 -->
**受限记忆工具的拒绝路径**
before_tool_call 中 enable_memory=False 且群聊数字分身时，write_memory/edit_memory/read_memory/memory_search/memory_get 五个工具全部经 _reject_tool 拒绝，返回 "[PERMISSION_DENIED] 记忆系统已禁用，禁止访问"；仅群聊数字分身（记忆可用）时只拒写工具，消息为 "[PERMISSION_DENIED] 群聊模式下禁止写入/编辑记忆文件"。_reject_tool 置 ctx.extra["_skip_tool"]=True 并直接写 tool_result 与 ToolMessage，跳过真实执行。

来源：[jiuwenswarm/agents/harness/common/rails/avatar_rail.py:L121–L161](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/avatar_rail.py#L121-L161), [jiuwenswarm/agents/harness/common/rails/avatar_rail.py:L164–L170](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/avatar_rail.py#L164-L170)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/rails/avatar_rail.py","start":121,"end":161,"sha256":"2e2554eed3abad6f6bd503b2a7e3d88a713064af08d4a07dcbbb392e4fe02a71"},{"path":"jiuwenswarm/agents/harness/common/rails/avatar_rail.py","start":164,"end":170,"sha256":"35cb51e1f67f0f5898bcb01b6cf9f19c5eec219a4a271e7ea1def744d7e1f40c"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=digital-avatar facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=94cc323e0ca4028790e4e08b5292447379deb77b047377510c047eff236bc09b -->
**AvatarPromptRail.before_tool_call 回调：无 perm_ctx 直接返回；禁记忆时拒五种记忆工具，仅群聊分身时拒写入**
回调以 ctx.inputs.tool_name 为输入，TOOL_PERMISSION_CONTEXT.get() 为 None 时直接 return。enable_memory=False 且 group_digital_avatar、avatar_mode 同真时，五种记忆工具（含 read_memory、memory_search、memory_get）被 _reject_tool："[PERMISSION_DENIED] 记忆系统已禁用，禁止访问"；否则 group_digital_avatar 且 avatar_mode 时仅 _MEMORY_WRITE_TOOLS 被拒："[PERMISSION_DENIED] 群聊模式下禁止写入/编辑记忆文件"。

来源：[jiuwenswarm/agents/harness/common/rails/avatar_rail.py:L121–L161](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/avatar_rail.py#L121-L161)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":161,"path":"jiuwenswarm/agents/harness/common/rails/avatar_rail.py","sha256":"2e2554eed3abad6f6bd503b2a7e3d88a713064af08d4a07dcbbb392e4fe02a71","start":121}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=digital-avatar facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=74c8beccb59b3e58c7e69fe93f06e1809d7cd0044a3b32427f8a82acda7eb75b -->
**check_avatar_permission 契约：返回 allow/deny，ask 降级为 deny，调用方入口 setup、finally cleanup**
check_avatar_permission(tool_name, tool_args, channel_id, session_id, *, permission_config, use_installed_permissions=False, installed_engine=None) 返回 "allow"/"deny"（ask 自动降级为 deny）；模块 docstring 要求入口调用 setup、finally 调 cleanup。

来源：[jiuwenswarm/agents/harness/common/rails/permissions/owner_scopes.py:L117–L127](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/owner_scopes.py#L117-L127), [jiuwenswarm/agents/harness/common/rails/permissions/owner_scopes.py:L7–L11](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/owner_scopes.py#L7-L11)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":127,"path":"jiuwenswarm/agents/harness/common/rails/permissions/owner_scopes.py","sha256":"c10e101d559a580a994bdf988c7e5d38b89a61efb8d6f3d02e6ea885e3c25d3b","start":117},{"end":11,"path":"jiuwenswarm/agents/harness/common/rails/permissions/owner_scopes.py","sha256":"cda2e6e4912df0a77868d69b7d61adec48495a72174c1d2b5c0c935fa9b6ba72","start":7}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=digital-avatar facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=08fb24e661cd228bb9f8e6963c18b5e8b188bf03cfe0590ed71c5971417f9f49 -->
**owner_scopes 按 channel+principal 查找；空或非 dict 配置默认 allow**
工具级别按 owner_scopes[channel_id][principal_user_id] 查找，owner_scopes 为空或非 dict 时默认 allow；启用需在飞书频道配置打开 group_digital_avatar 开关并配置 my_user_id/bot_name。

来源：[jiuwenswarm/agents/harness/common/rails/permissions/owner_scopes.py:L170–L181](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/owner_scopes.py#L170-L181), [docs/zh/国内频道.md:L211–L215](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%9B%BD%E5%86%85%E9%A2%91%E9%81%93.md#L211-L215)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":181,"path":"jiuwenswarm/agents/harness/common/rails/permissions/owner_scopes.py","sha256":"ce54e1651e28fa647c57a452a37c1847a483311850b2f555e13a16a981fa40bb","start":170},{"end":215,"path":"docs/zh/国内频道.md","sha256":"4adda0415aa91896bb3413ac545ffc07423de2d3014bdc02c0b5945ac9d11e7d","start":211}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=digital-avatar facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bdd8c5f72ca023ef859862759d1c3153d9f20a07a8416a7d6a594eb80a5b8629 -->
**check_avatar_permission 缺上下文或引擎不可用时一律 deny 的收益与代价（推断）**
设计推断（非作者历史意图）：

事实：perm_ctx 为 None 或 principal_user_id 为空、以及 use_installed_permissions 下 installed_engine 缺可调用 evaluate_global_policy_directly 时，均 return "deny"。推断收益：无有效分身上下文的工具调用不会放行；推断代价：入口未 setup 上下文或缺 principal 的合法调用同样被一律拒绝。

来源：[jiuwenswarm/agents/harness/common/rails/permissions/owner_scopes.py:L150–L160](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/owner_scopes.py#L150-L160)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":160,"path":"jiuwenswarm/agents/harness/common/rails/permissions/owner_scopes.py","sha256":"dbb2b50eac0370f50c2a8305979128270c39178bd44d6660da5a7f029e98d0a9","start":150}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=digital-avatar facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b1bf84d198a4e4a4ae8490a16d13553a6270047c3f1a84410f63e17960798ba5 -->
**运行时单测断言 owner scope 复位与场景钩子 owner_scopes 拒绝结果**
test_setup_permission_context_uses_non_avatar_principal_metadata 断言 scope 为 principal:web:principal-42、cleanup 后为空；场景钩子测试断言返回 reject 与 [PERMISSION_DENIED] 该工具未被授权 (owner_scopes: deny)。

来源：[tests/unit_tests/agentserver/permissions/test_owner_scopes_context.py:L31–L50](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/permissions/test_owner_scopes_context.py#L31-L50), [tests/unit_tests/agentserver/permissions/test_installed_permission_snapshot.py:L92–L103](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/permissions/test_installed_permission_snapshot.py#L92-L103)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":50,"path":"tests/unit_tests/agentserver/permissions/test_owner_scopes_context.py","sha256":"1b5709eff930f423e5711feb5a171db17453d9c9e42cdb45d7b581c41ef52365","start":31},{"end":103,"path":"tests/unit_tests/agentserver/permissions/test_installed_permission_snapshot.py","sha256":"28b9213a9a191a270bf54edd6e618a66235bb30bd3ccfc027ee602c5d56bab53","start":92}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
