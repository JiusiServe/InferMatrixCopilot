---
title: "LSP 代码智能：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/Harness.md:L201-L204, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L30-L37]
feature: "lsp"
entry_points: ["jiuwenswarm/server/runtime/agent_adapter/interface_code.py"]
source_globs: ["jiuwenswarm/server/runtime/agent_adapter/interface_code.py", "jiuwenswarm/agents/harness/common/rails/*"]
---

# LSP 代码智能：实现深读

[功能概览](feature-lsp.md) · [owner 入口](_index.md)

<!-- kb:depth feature=lsp facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bc490c8caf47bcecc3b2da99d123fc84f36999f365d3dd293d40039dcdc66cce -->
**LspRail 的生命周期契约**
LspRail 是 LSP 能力的生命周期入口：负责初始化 LSP subsystem，并把单一 `lsp` tool 注册到 Agent 的 ability manager。该 tool 是模型调用 LSP 的统一入口，接收操作类型、文件路径、行列位置或查询条件并返回结构化结果。

来源：[docs/zh/Harness.md:L201–L204](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Harness.md#L201-L204), [jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L30–L37](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_code.py#L30-L37)

<!-- kb:depth-proof {"evidence":[{"path":"docs/zh/Harness.md","start":201,"end":204,"sha256":"dc6a0db9914e5b6e83411e7bc72fcaa6cd77d5daa3f0e0fe88ab59a8a7a324a2"},{"path":"jiuwenswarm/server/runtime/agent_adapter/interface_code.py","start":30,"end":37,"sha256":"b9eb66bc7d9ebfcffd0f15d7abc68d52503a2d9d4670e25d70282837bc1e70eb"}],"trace":[]} -->
<!-- /kb:depth -->
