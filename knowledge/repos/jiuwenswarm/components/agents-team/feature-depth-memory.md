---
title: "长期记忆：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/config.py:L250-L281, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/config.py:L207-L247, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/dreaming/sweeper.py:L51-L71]
---

# 长期记忆：实现深读

[功能概览](feature-memory.md) · [owner 入口](_index.md)

<!-- kb:depth feature=memory facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=77b957382daa83913df3464e57995d0a0eca0feaf568ffd554aaab09febd8d6e -->
**记忆开关的模式相关默认值**
is_memory_enabled(mode) 经 _resolve_mode_memory 归一 mode 后读 modes.agent.memory.enabled 或 modes.code.memory.enabled：code 族（含 code.*、agent.code.*、team.code.*，判定复用 mode_matrix.is_code_profile_mode）缺省 enabled=True，agent 族缺省 False；配置读取抛异常时记 warning 并返回 False。另 DreamingConfig.load 中，环境变量 DREAMING_{MODE}_ENABLED 优先于 config.yaml 的 memory.dreaming.{mode}.enabled（默认 false），间隔默认 14400.0 秒且可被 DREAMING_INTERVAL 覆盖。

来源：[jiuwenswarm/agents/harness/common/memory/config.py:L250–L281](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/config.py#L250-L281), [jiuwenswarm/agents/harness/common/memory/config.py:L207–L247](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/config.py#L207-L247), [jiuwenswarm/agents/harness/common/memory/dreaming/sweeper.py:L51–L71](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/dreaming/sweeper.py#L51-L71)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/memory/config.py","start":250,"end":281,"sha256":"d0cf034249e3b6c660c35aeb9beb5fe3ce2aed6efd9adab36b125f4a3a760e74"},{"path":"jiuwenswarm/agents/harness/common/memory/config.py","start":207,"end":247,"sha256":"6a37a7a8a0f8b8979e9cfe0d146e7714c6128b3731291ab3f1f9999dcfd70538"},{"path":"jiuwenswarm/agents/harness/common/memory/dreaming/sweeper.py","start":51,"end":71,"sha256":"0d1637e0457ea0e80a363ed5e0385c45a806408d4a51a0e3c5961e2b4262ee87"}],"trace":[]} -->
<!-- /kb:depth -->
