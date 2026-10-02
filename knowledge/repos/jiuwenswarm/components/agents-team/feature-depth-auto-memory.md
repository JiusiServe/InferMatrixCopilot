---
title: "对话后自动记忆：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: ["openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/自动记忆.md:L21-L33", "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/自动记忆.md:L99-L105", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/auto_memory/prompts.py:L13-L30, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py:L236-L242, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py:L95-L189, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py:L372-L406]
---

# 对话后自动记忆：实现深读

[功能概览](feature-auto-memory.md) · [owner 入口](_index.md)

<!-- kb:depth feature=auto-memory facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2afb6dbc34ed02f337ec59a637338c150506f6683330c302e42188a1e363a0a8 -->
**启用开关与提取提示语言**
文档记载 agent 模式用顶层 auto_memory_enabled、code 模式用 modes.code.memory.auto_coding_memory，默认均为 false。提取提示词由 build_extract_memories_prompt(language="zh") 生成，language 参数默认值也是 "zh"。

来源：[docs/zh/自动记忆.md:L21–L33](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E8%87%AA%E5%8A%A8%E8%AE%B0%E5%BF%86.md#L21-L33), [docs/zh/自动记忆.md:L99–L105](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E8%87%AA%E5%8A%A8%E8%AE%B0%E5%BF%86.md#L99-L105), [jiuwenswarm/agents/harness/common/auto_memory/prompts.py:L13–L30](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_memory/prompts.py#L13-L30), [jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py:L236–L242](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py#L236-L242)

<!-- kb:depth-proof {"evidence":[{"path":"docs/zh/自动记忆.md","start":21,"end":33,"sha256":"8e9d5336d9b38797e2e5f3630a60b89e315a11ee052f8b0c085a92a0c9b460a8"},{"path":"docs/zh/自动记忆.md","start":99,"end":105,"sha256":"743fca33759b3374213b31f50fbf9d767aec1ae126c3bdb328a05bfb275234b1"},{"path":"jiuwenswarm/agents/harness/common/auto_memory/prompts.py","start":13,"end":30,"sha256":"b960a4ad01ada6138c8df9f854e90d8d8ae2c738206e8ba2ccdc42b39cedd729"},{"path":"jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py","start":236,"end":242,"sha256":"c2dd130f7582a19673a6accd8c20ff9627672718e2e5c461407bf50c8b2db78c"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=auto-memory facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e426f0219b66734edceda05d0f632b116ba36cd41c4287200926b9e3429072b4 -->
**对 AutoMemoryToolRestrictionRail 的运行时工具限制**
缓存共享子 Agent 继承父 Agent 的全部工具，靠 AutoMemoryToolRestrictionRail.before_tool_call 在每次工具执行前做许可判定：只放行只读工具、只读 bash、memory_dir 内的写/编辑和 coding_memory 读写，其余调用 _deny_tool 拒绝。

来源：[jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py:L95–L189](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py#L95-L189), [jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py:L372–L406](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py#L372-L406)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py","start":95,"end":189,"sha256":"7e13e495016363af40270f19d289af4b0b95fe836ea2079e40855341b43df9d9"},{"path":"jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py","start":372,"end":406,"sha256":"65705ea70265b73c5aa10cd4378323fd4df98d0a5b3263ee30171626646b959d"}],"trace":[]} -->
<!-- /kb:depth -->
