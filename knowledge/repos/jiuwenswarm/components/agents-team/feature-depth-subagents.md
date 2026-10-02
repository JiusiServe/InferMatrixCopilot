---
title: "子代理派发与验证：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/code_subagents.py:L111-L126, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/code_subagents.py:L137-L154, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/statusline_setup_agent.py:L89-L119]
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
