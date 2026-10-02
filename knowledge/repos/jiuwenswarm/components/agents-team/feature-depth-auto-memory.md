---
title: "对话后自动记忆：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: ["openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/自动记忆.md:L21-L33", "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/自动记忆.md:L99-L105", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/auto_memory/prompts.py:L13-L30, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py:L236-L242, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py:L95-L189, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py:L372-L406, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py:L294-L312, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py:L327-L345, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py:L400-L424, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py:L231-L279, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py:L169-L187, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py:L5-L23]
feature: "auto-memory"
entry_points: ["jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py"]
source_globs: ["jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py", "jiuwenswarm/agents/harness/common/auto_memory/*"]
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

<!-- kb:depth feature=auto-memory facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a007578b4a701f614d4ab4a72414deacc862fbf9208a87b2fdd4fc1212f40475 -->
**缓存共享分支：`_instance` 守卫通过后构造子代理，并把转换后的 history 传入 create_new_context_engine**
父 `_instance` 为 None 时记录 error 并 return；否则以 `max_context_message_num=None`、`default_window_round_num=None` 构造 ContextEngineConfig，子代理以 `rails=subagent_rails` 建立，history 经 `_convert_messages_to_base_messages` 转换后作为 `messages=` 传给 `sub_agent.create_new_context_engine`，得到 new_session_id。

来源：[jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py:L294–L312](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py#L294-L312), [jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py:L327–L345](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py#L327-L345), [jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py:L400–L424](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py#L400-L424)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":312,"path":"jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py","sha256":"52f7e4c86884c84c9a1205b8e9d1488c272ba78681a5c1d9e7bf8a99e32f5c8c","start":294},{"end":345,"path":"jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py","sha256":"a89de6510f8f62d609d681b6a7a37e3f38819e55eeff5c6f57206736ba11b29a","start":327},{"end":424,"path":"jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py","sha256":"e6f97cda2763273636f711fe36e8c6ed068fe2387dfed4f972e52519dbaa000e","start":400}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=auto-memory facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3c5c6b395c3143a953620f89208a71c886464b954636c6b055acf4e7c3458f72 -->
**`_is_in_memory_dir(tool_args) -> bool`：路径先取 `file_path` 再取 `path`，仅当 `relative_to(self.memory_dir)` 成功才返回 True**
入参为工具参数字典；路径取 `file_path`，为空再取 `path`，两者皆空返回 False。绝对路径直接 resolve，相对路径按 `self.memory_dir` 拼接后 resolve；`relative_to` 成功返回 True，ValueError 或其他异常返回 False。调用方义务：`coding_memory_write`/`coding_memory_edit` 仅当返回 True 才放行。

来源：[jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py:L231–L279](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py#L231-L279), [jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py:L169–L187](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py#L169-L187)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":279,"path":"jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py","sha256":"858dc533c0b5b68a22f89bbe4ef6528a7a9b71808f23d62c7939483f836f626a","start":231},{"end":187,"path":"jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py","sha256":"38d157f79cc7fe47544bf4366e4ebada158ae26547d8a8f31a4cc0395ac3ef31","start":169}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=auto-memory facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fc5fdf94606358fe219ff6bb3944203b717c8091731372e5ae260faafb550f6c -->
**父适配器无 `_instance` 时记 error 并本地 return；`_is_in_memory_dir` 解析异常返回 False 使工具被拒**
触发条件是 `getattr(parent_agent, "_instance", None)` 为 None：记录 `[auto_memory] Parent adapter has no _instance, cannot proceed` 后 return，仅终止本次本地分支，不是进程退出码。路径解析抛出任何异常时 `_is_in_memory_dir` 记 warning 并返回 False。

来源：[jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py:L294–L312](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py#L294-L312), [jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py:L231–L279](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py#L231-L279)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":312,"path":"jiuwenswarm/agents/harness/common/auto_memory/extraction_runner.py","sha256":"52f7e4c86884c84c9a1205b8e9d1488c272ba78681a5c1d9e7bf8a99e32f5c8c","start":294},{"end":279,"path":"jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py","sha256":"858dc533c0b5b68a22f89bbe4ef6528a7a9b71808f23d62c7939483f836f626a","start":231}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=auto-memory facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8dc42a7c3157b7266b1197f39934b6cf462c65364d51b6b074fd82cc275ca98c -->
**子代理继承父工具以共享缓存（docstring 所述收益），代价是允许清单之外的任何工具一律落入拒绝分支**
设计推断（非作者历史意图）：

模块 docstring 称子代理继承父工具可共享缓存、由运行时限制防止越权使用；对应的成本是允许清单之外的任何工具都进入 deny 分支并记录 warning。收益为文档陈述，非所示运行时验证。

来源：[jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py:L5–L23](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py#L5-L23), [jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py:L169–L187](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py#L169-L187)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":23,"path":"jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py","sha256":"2ee6ae6e29039de549b381765ecdb2eb465a47406f8d4a0448dc481167cccd37","start":5},{"end":187,"path":"jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py","sha256":"38d157f79cc7fe47544bf4366e4ebada158ae26547d8a8f31a4cc0395ac3ef31","start":169}],"trace":[]} -->
<!-- /kb:depth -->
