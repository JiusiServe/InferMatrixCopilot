---
title: "FACT/TIP 双轨经验：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/TTSE.md:L5-L7, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/eternal_conversation/coordinator.py:L166-L174]
feature: "ttse"
entry_points: ["jiuwenswarm/server/runtime/agent_adapter/interface_deep.py"]
source_globs: ["jiuwenswarm/server/runtime/agent_adapter/interface_deep.py", "jiuwenswarm/agents/harness/common/*"]
---

# FACT/TIP 双轨经验：实现深读

[功能概览](feature-ttse.md) · [owner 入口](_index.md)

<!-- kb:depth feature=ttse facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b2a66102b092be841ba0048242614b9cd31da1ee74cff01e4ea739339ece650c -->
**对 agent_observability 轨迹的强依赖**
TTSE 的轨迹归纳依赖 LLM/工具 span：开启 TTSE 时 Host 会像 Skill/Symphony 演进一样自动拉起 `agent_observability`（即使其 `enabled: false`），否则 `run_evolution` 因无轨迹而静默跳过。TTSERail 本体由 agent-core 提供，缺失时 Host 侧降级跳过。

来源：[docs/zh/TTSE.md:L5–L7](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/TTSE.md#L5-L7)

<!-- kb:depth-proof {"evidence":[{"path":"docs/zh/TTSE.md","start":5,"end":7,"sha256":"68cd874d8b963de656a56d511ff09faa2acc826f47ea5888632726d48430e141"}],"trace":[]} -->
<!-- /kb:depth -->
