---
title: "群聊数字分身与 owner 权限：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/avatar_rail.py:L43-L119, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/permissions/owner_scopes.py:L104-L114, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/avatar_rail.py:L121-L161, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/avatar_rail.py:L164-L170]
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
