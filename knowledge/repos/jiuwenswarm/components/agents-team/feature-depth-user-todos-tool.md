---
title: "user_todos Personal Per-Channel Todo Tool：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/user_todo_tool.py:L17-L19, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/user_todo_tool.py:L109-L124, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/user_todo_tool.py:L270-L305, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/user_todo_tool.py:L208-L230, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/user_todo_tool.py:L246-L253, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/user_todo_tool.py:L13-L14, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/user_todo_tool.py:L194-L207, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/user_todo_tool.py:L114-L124]
feature: "user-todos-tool"
entry_points: ["jiuwenswarm/agents/harness/common/tools/user_todo_tool.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/user_todo_tool.py"]
---

# user_todos Personal Per-Channel Todo Tool：实现深读

[功能概览](feature-user-todos-tool.md) · [owner 入口](_index.md)

<!-- kb:depth feature=user-todos-tool facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4c3dc688de4b0f095af267d391e197564c08e61ef731c16690ce2ba89aa1228f -->
**create action appends a TodoItem and writes the channel's file**
With title set, _handle_user_todos parses the channel file, derives remind_at = due_at − 5 minutes only when due_at is truthy, remind_at is unset and parses via datetime.fromisoformat (parse failure yields ""), appends a TodoItem with uuid[:8] id and status/priority defaulting to PENDING/MEDIUM, writes the file, and returns success with the new todo dict.

来源：[jiuwenswarm/agents/harness/common/tools/user_todo_tool.py:L270–L305](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/user_todo_tool.py#L270-L305)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":305,"path":"jiuwenswarm/agents/harness/common/tools/user_todo_tool.py","sha256":"77867ab7c5279deea4923fb0d744eb4127d0faf54841b0ee4ea9188037ba1791","start":270}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=user-todos-tool facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6d44e9f2b391e86edd876ba8e9dd245bb53bb07db7e242c3b4b018fee416597f -->
**user_todos accepts a params object or dict and returns an operation result dict**
The @tool-decorated async function user_todos takes UserTodosParams (or a dict filtered to its dataclass fields) with action in list/get/create/update/delete/search, optional channel_id, and returns a Dict such as {"success": True, "todos": [...], "count": n} for list; the docstring notes channel_id defaults to the global channel id.

来源：[jiuwenswarm/agents/harness/common/tools/user_todo_tool.py:L208–L230](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/user_todo_tool.py#L208-L230), [jiuwenswarm/agents/harness/common/tools/user_todo_tool.py:L246–L253](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/user_todo_tool.py#L246-L253)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":230,"path":"jiuwenswarm/agents/harness/common/tools/user_todo_tool.py","sha256":"824a32a4599a5d399cc3d849608491cdb943c6930592c18c09e9a14c1a80c643","start":208},{"end":253,"path":"jiuwenswarm/agents/harness/common/tools/user_todo_tool.py","sha256":"11fb1488e0bd686c7e122d677960eed20b35a272b346e4c729ad8cf0cb59b5a1","start":246}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=user-todos-tool facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f04d32b19dba56d80f8f75f75dcfce56f112c11d3e5805de526fedea1cbbf711 -->
**Channel and workspace defaults: ContextVar channel "default", workspace "."**
Module defaults are _global_workspace_dir="." and a ContextVar channel_id defaulting to "default"; when params.channel_id is unset, _handle_user_todos falls back to _ctx_channel_id.get(), and todos live under <workspace>/memory/user_todos/<sanitized_cid>.md. Status/priority default to PENDING/MEDIUM on create.

来源：[jiuwenswarm/agents/harness/common/tools/user_todo_tool.py:L17–L19](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/user_todo_tool.py#L17-L19), [jiuwenswarm/agents/harness/common/tools/user_todo_tool.py:L109–L124](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/user_todo_tool.py#L109-L124)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":19,"path":"jiuwenswarm/agents/harness/common/tools/user_todo_tool.py","sha256":"798a35319df096e15bd0f9e9c0ee30094e1cfb42985e22eff1f80bb3a30b499d","start":17},{"end":124,"path":"jiuwenswarm/agents/harness/common/tools/user_todo_tool.py","sha256":"6d1cbdc964a1cc142532ad5650721bd2db61cb53a17dfee957a43ab133edefe2","start":109}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=user-todos-tool facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5c97deaf8cd43d2f4c7348bc1ec327a4d42a0a66c97a1eb3f62618d81691452d -->
**Registered via openjiuwen @tool as stateless=True; logging via jiuwenswarm logger**
The module imports the tool decorator from openjiuwen.core.foundation.tool.tool and logger from jiuwenswarm.common.utils (L13–L14). Registration uses stateless=True; the adjacent comment (L202–L205) states this is because the tool is a module-level singleton driven by set_global_workspace_dir/set_global_channel_id, so every agent shares one registration under its bare id — the comment's stated rationale, not runtime-verified here.

来源：[jiuwenswarm/agents/harness/common/tools/user_todo_tool.py:L13–L14](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/user_todo_tool.py#L13-L14), [jiuwenswarm/agents/harness/common/tools/user_todo_tool.py:L194–L207](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/user_todo_tool.py#L194-L207)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":14,"path":"jiuwenswarm/agents/harness/common/tools/user_todo_tool.py","sha256":"c19dd1f50a57ab2cccd742ceac79b98c720274564449c1686a9a50b1257f8d16","start":13},{"end":207,"path":"jiuwenswarm/agents/harness/common/tools/user_todo_tool.py","sha256":"470000b557d1fced21f1cca865394721ebeeb1061df7ca2596c4634b09fc56a3","start":194}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=user-todos-tool facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dd413cb45e702dd8e586cfec470724e48cefd711557b9208cedd83999d5697e0 -->
**Sanitization blocks path traversal but is not injective across channel ids**
设计推断（非作者历史意图）：

Benefit: _sanitize_channel_id strips path separators and special characters, preventing channel-id path traversal into other directories. Cost (inference): the substitution is many-to-one, so two distinct raw channel ids mapping to the same sanitized string would share one .md file; the shown code does not detect or prevent this collision.

来源：[jiuwenswarm/agents/harness/common/tools/user_todo_tool.py:L114–L124](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/user_todo_tool.py#L114-L124)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":124,"path":"jiuwenswarm/agents/harness/common/tools/user_todo_tool.py","sha256":"1dba462199be6e5b573fb7a8d9adafa12f71efe431681339a7c4602c88b926a2","start":114}],"trace":[]} -->
<!-- /kb:depth -->
