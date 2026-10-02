---
title: "Worktree 隔离工作：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L1860-L1870, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L1845-L1862, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L1848-L1852, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L1860-L1862, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L1845-L1870, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L1857-L1870, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L1845-L1860, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L44-L63]
feature: "worktree"
entry_points: ["jiuwenswarm/server/runtime/agent_adapter/interface_code.py"]
source_globs: ["jiuwenswarm/server/runtime/agent_adapter/interface_code.py", "jiuwenswarm/agents/harness/common/rails/*"]
---

# Worktree 隔离工作：实现深读

[功能概览](feature-worktree.md) · [owner 入口](_index.md)

<!-- kb:depth feature=worktree facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=23e5fcc71f1e0d4690a0cdf2677d048c34643908cab9bf2aa0d8df1f38e49522 -->
**构造失败降级为禁用**
WorktreeRail 构造抛出任意 Exception 时被 except Exception 捕获，仅记录一条包含异常信息的 warning（"WorktreeRail create failed"），随后返回 None，不缓存失败状态——下一次调用会重新尝试构造。

来源：[jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L1860–L1870](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_code.py#L1860-L1870)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/server/runtime/agent_adapter/interface_code.py","start":1860,"end":1870,"sha256":"18043274369a327dc1ddb9c3a92db2e5c2eaacb8d2edc77683a8465d3f3de580"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=worktree facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bfe97cfc5e0e49d6cda8a3edc04cf2dc1673d6ada0e7ef8e95b071427b02d0cc -->
**_build_worktree_rail_via_config：缓存命中即返回旧实例，未命中才构建 WorktreeRail 并写入缓存**
进入方法先查 `self._worktree_rail`：非空则记录 reuse cached instance 日志并 return 该缓存实例；为空则进入 try，以 `WorktreeRail(config=WorktreeConfig(enabled=True))` 构建并赋给 `self._worktree_rail`，可见片段止于该赋值。

来源：[jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L1845–L1862](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_code.py#L1845-L1862)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1862,"path":"jiuwenswarm/server/runtime/agent_adapter/interface_code.py","sha256":"dbe2c1972348f40ea6bfd80b9469108a2e63d36083ceb44be6aea7021024b2fb","start":1845}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=worktree facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=00222606190e5077ef4d93ca3445c75cc4446533fa4c3dc100da26dfa70321d2 -->
**_build_worktree_rail_via_config 返回 WorktreeRail | None；构造异常不缓存、下次调用重试**
契约：self._worktree_rail 已非 None 时直接返回缓存实例；否则构造 WorktreeRail、赋值缓存后返回；构造抛异常时仅记录 warning 并返回 None，缓存保持未设置，因此下一次调用会重试构造。调用方必须处理 None 返回值。

来源：[jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L1845–L1870](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_code.py#L1845-L1870)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1870,"path":"jiuwenswarm/server/runtime/agent_adapter/interface_code.py","sha256":"51a7f19af6e89b9ad900428c4573de33520338b18a7fbf1bc6a5554c1a6ecacf","start":1845}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=worktree facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=79ff117175d8153ad14856b9d2333464cf921d1628991874f067242ecd58f5ad -->
**code 模式 WorktreeRail 仅设置 enabled=True，其余 WorktreeConfig 保持库默认（docstring 声明）**
docstring（1852–1854）声明构造 WorktreeConfig 时只设置 enabled=True，其余选项保持 openjiuwen 库默认，直至引入配置 schema；所示方法内首个守卫是 1857–1859 的缓存命中（_worktree_rail is not None）直接 return 旧实例，不再进入 1860 起的 try 构造路径。

来源：[jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L1845–L1860](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_code.py#L1845-L1860), [jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L44–L63](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_code.py#L44-L63)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1860,"path":"jiuwenswarm/server/runtime/agent_adapter/interface_code.py","sha256":"88aa54d4037f711152bfb2fbd457ab0a0b48c19d842f9ba56e5276d426ed7d52","start":1845},{"end":63,"path":"jiuwenswarm/server/runtime/agent_adapter/interface_code.py","sha256":"197498067d612c9c424fcb85ffb0ef2e834a8b408effaa2da1d1db5901ab30c9","start":44}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=worktree facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=51d49299ea0d5383e50485a93332e6eb0d3d229d700517c3d25cd6bdb181987a -->
**直接实例化库侧 WorktreeRail；docstring 称仓库根由运行时 cwd 经 find_canonical_git_root 解析**
代码直接实例化库的 `WorktreeRail`/`WorktreeConfig`；docstring 称 WorktreeManager 用 `find_canonical_git_root` 从运行时 cwd 解析仓库根，而 agent cwd 在 init 时被 Workspace 锚到 project_dir，因此 worktree 落在用户真实仓库之下。

来源：[jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L1848–L1852](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_code.py#L1848-L1852), [jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L1860–L1862](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_code.py#L1860-L1862)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1852,"path":"jiuwenswarm/server/runtime/agent_adapter/interface_code.py","sha256":"32e9804a23d55916edaad09f53d642e91e914786ed9ff849a47016958763c141","start":1848},{"end":1862,"path":"jiuwenswarm/server/runtime/agent_adapter/interface_code.py","sha256":"4834060a17d0411fe035232e1c388087754495606486da36b16674ecb0d7144c","start":1860}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=worktree facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4a4a329d3bc3abdb53b1f405ec8d69e0af6a76308940c4b0c84809375d7a3dc1 -->
**收益：缓存命中避免重复构造 WorktreeRail；成本：构造异常被吞为 warning+None（推理）**
设计推断（非作者历史意图）：

推理：缓存命中分支（L1857–L1859）使重复调用无需重建 WorktreeRail；成本是 except Exception（L1868–L1870）吞掉所有构造异常，仅留 warning 日志与 None 返回，失败原因不向调用方传播。均限定于本片段实现，未断言任何调用方行为。

来源：[jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L1857–L1870](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_code.py#L1857-L1870)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1870,"path":"jiuwenswarm/server/runtime/agent_adapter/interface_code.py","sha256":"7f29b0745d01ea12c8637ad12766d69b2ceb77cc9c914ac78de393b61d1f89c8","start":1857}],"trace":[]} -->
<!-- /kb:depth -->
