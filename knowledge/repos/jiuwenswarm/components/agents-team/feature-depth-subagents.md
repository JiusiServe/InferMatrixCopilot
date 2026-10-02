---
title: "子代理派发与验证：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/code_subagents.py:L111-L126, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/code_subagents.py:L137-L154, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/statusline_setup_agent.py:L89-L119, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/code_subagents.py:L157-L174, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/code_subagents.py:L12-L17, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/subagent_compat.py:L24-L33, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/subagent_compat.py:L23-L43, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/permissions/test_auto_decision.py:L130-L148, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/permissions/test_auto_decision.py:L217-L222]
feature: "subagents"
entry_points: ["jiuwenswarm/agents/swarm/providers/code_subagents.py", "jiuwenswarm/agents/harness/common/tools/subagent_compat.py"]
source_globs: ["jiuwenswarm/agents/swarm/providers/code_subagents.py", "jiuwenswarm/agents/harness/common/tools/subagent_compat.py", "jiuwenswarm/agents/harness/common/rails/*"]
---

# 子代理派发与验证：实现深读

[功能概览](feature-subagents.md) · [owner 入口](_index.md)

<!-- kb:depth feature=subagents facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9eb413a46154f89bdf6ad56d9711126857f0098d00b7de3ebb1333f4c99a7f94 -->
**statusline 子代理构造链**
成员装配时，工厂 build_statusline_setup_agent(factory_kwargs, ctx) 先从 ctx.extras["_parent_model"] 读取父成员模型；模型存在时调用 build_statusline_setup_agent_config(model, workspace=..., sys_operation=parent_sys_operation(ctx), ...)，后者构造并返回带 AgentCard(id="jiuwenswarm.statusline-setup")、rails=[SysOperationRail()]、enable_task_loop=False 的 SubAgentConfig，并置 spec.factory_kwargs={"auto_create_workspace": False}。

调用路径：`jiuwenswarm/agents/swarm/providers/code_subagents.py`（`build_statusline_setup_agent`） → `jiuwenswarm/server/runtime/agent_adapter/statusline_setup_agent.py`（`build_statusline_setup_agent_config`）

来源：[jiuwenswarm/agents/swarm/providers/code_subagents.py:L137–L154](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/code_subagents.py#L137-L154), [jiuwenswarm/server/runtime/agent_adapter/statusline_setup_agent.py:L89–L119](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/statusline_setup_agent.py#L89-L119)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/swarm/providers/code_subagents.py","start":137,"end":154,"sha256":"7da4a50bf3720942f85ff6d46e6e2e51c4d25cc160c05be5ab54fddc92d70cc4"},{"path":"jiuwenswarm/server/runtime/agent_adapter/statusline_setup_agent.py","start":89,"end":119,"sha256":"d29b0aa0a1071c04b1a3ccb6bbcee46f86a9c743d9a93a089bf6c20fa523e4a1"}],"trace":[{"path":"jiuwenswarm/agents/swarm/providers/code_subagents.py","symbol":"build_statusline_setup_agent","start":137,"end":154},{"path":"jiuwenswarm/server/runtime/agent_adapter/statusline_setup_agent.py","symbol":"build_statusline_setup_agent_config","start":89,"end":119}]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=subagents facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d59a8d994b0651678ab5f4fcbc1a910c7ed679e51b4ed7cb1ef0596531b7d7a8 -->
**code_agent 复用共享 CodingMemoryRail**
build_code_agent 从 ctx.extras[CODING_MEMORY_EXTRAS_KEY] 取主代理的 CodingMemoryRail 实例；由于向 build_code_agent_config 传 rails 会覆盖默认，必须显式把 SysOperationRail() 与共享 rail 一起传入，否则 code_agent 会丢失系统操作工具。这是 swarm 成员与主代理记忆一致的耦合点。

来源：[jiuwenswarm/agents/swarm/providers/code_subagents.py:L111–L126](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/code_subagents.py#L111-L126)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/swarm/providers/code_subagents.py","start":111,"end":126,"sha256":"e60bb9732f17d1faefd66901238dce07347018dd1c11b7a7b05f045c9cbfcd6a"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=subagents facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3ce204552e65aa9ce96a2802883d00a0473854a7a39b6a5a293be9dac5abf5c9 -->
**rails 覆盖必须显式携带默认项**
设计推断（非作者历史意图）：

推断：build_code_agent 向 build_code_agent_config 传 rails 时会整体覆盖默认 rail 集，因此共享的 CodingMemoryRail 必须与 SysOperationRail() 一起显式传入；收益是子代理复用主代理的编码记忆，代价是任何新增默认 rail 都要同步维护这里的列表，否则静默丢失。

来源：[jiuwenswarm/agents/swarm/providers/code_subagents.py:L111–L126](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/code_subagents.py#L111-L126)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/swarm/providers/code_subagents.py","start":111,"end":126,"sha256":"e60bb9732f17d1faefd66901238dce07347018dd1c11b7a7b05f045c9cbfcd6a"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=subagents facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8db4a43b31f217ee2e80828792036b9ff2362299644da55cea621856f4b1cb3a -->
**CompatibleSubagentControl.resume(subagent_id)：仅当已恢复、状态为 PENDING_INIT 且找到实例时才改写返回状态**
先 await super().resume(subagent_id)；若 not restored、result.status.kind 非 PENDING_INIT，或 self._manager.find(subagent_id) 为 None，则原样返回 super() 的结果。找到实例后若实时 agent_status() 已非 PENDING_INIT，返回 replace(result, status=current)；仍为 PENDING_INIT 时才 await instance.status.set(SubagentStatus.completed()) 并返回 replace(result, status=idle)（行内注释：COMPLETED 映射为公开 idle 态）。

来源：[jiuwenswarm/agents/harness/common/tools/subagent_compat.py:L23–L43](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/subagent_compat.py#L23-L43)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":43,"path":"jiuwenswarm/agents/harness/common/tools/subagent_compat.py","sha256":"059d8bd610ed341314eae7906fbf563a5b44230f273f3243aaabd3e526420474","start":23}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=subagents facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=abc8f0f00f7f281a2b122cfb9ca510574e26909818b7ff4c6d56e22ed0b9922c -->
**BrowserAgentInput 默认值：max_iterations、language 缺省 en、workspace_root 缺省 ./**
max_iterations 默认 DEFAULT_BROWSER_AGENT_MAX_ITERATIONS；language 由 code_runtime_language 解析、缺省 "en"；workspace_root 由 _workspace_root 解析、缺省 "./"；session_id 取自构建上下文，模块 docstring 称由其派生的 browser_key 让每个成员获得独立浏览器。

来源：[jiuwenswarm/agents/swarm/providers/code_subagents.py:L157–L174](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/code_subagents.py#L157-L174), [jiuwenswarm/agents/swarm/providers/code_subagents.py:L12–L17](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/code_subagents.py#L12-L17)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":174,"path":"jiuwenswarm/agents/swarm/providers/code_subagents.py","sha256":"e31da538728724c608838490b17f45cb16deddf861cdf6251fdf9beaf58e83a5","start":157},{"end":17,"path":"jiuwenswarm/agents/swarm/providers/code_subagents.py","sha256":"c11fca4d51f7ef288de2c44c7f4858376ad1b7cb21095720a3984953628f0ad4","start":12}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=subagents facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=14365026c8553a460855c1ee59ef846d587572dafd113d8cd73e846ad9820a4a -->
**resume 未恢复、非 PENDING_INIT 或找不到实例时原样透传**
触发：not result.restored 或状态非 PENDING_INIT，或 self._manager.find(subagent_id) 返回 None；对应守卫分支直接返回原 result，不做 idle 改写，也不在此抛出异常。

来源：[jiuwenswarm/agents/harness/common/tools/subagent_compat.py:L24–L33](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/subagent_compat.py#L24-L33)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":33,"path":"jiuwenswarm/agents/harness/common/tools/subagent_compat.py","sha256":"52c83dcfca3ed976ed111e04b1a48a581d3c0adb6634ace4248dd601368f0b40","start":24}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=subagents facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8b3ecf8e44921be6a87f155ede8aa4ef34f2411c83a634e55a00556d0247d1e8 -->
**helper 单测：terminal_internal_route 对 subagent 控制 tool 的条件放行**
断言仅覆盖判定 helper：subagent_runtime_control_verified=True 时 terminal_internal_route 对 subagent_list/send_input/close/resume 返回 level=='allow'、reason=='canonical_internal_action_allow'；未传该证明时对 subagent_list 返回 None。facts 为直接构造，未运行真实子代理派发。

来源：[tests/unit_tests/agentserver/permissions/test_auto_decision.py:L130–L148](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/permissions/test_auto_decision.py#L130-L148), [tests/unit_tests/agentserver/permissions/test_auto_decision.py:L217–L222](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/permissions/test_auto_decision.py#L217-L222)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":148,"path":"tests/unit_tests/agentserver/permissions/test_auto_decision.py","sha256":"fb064507f1635c00851d1887d853a73f640a5ddf26f0fc3c5144fe159a44656f","start":130},{"end":222,"path":"tests/unit_tests/agentserver/permissions/test_auto_decision.py","sha256":"7fb81c83f44a965a4399f86172e6785633061cdb19fe46fd5307775e10f6439f","start":217}],"trace":[],"validation_kind":"helper_unit"} -->
<!-- /kb:depth -->
