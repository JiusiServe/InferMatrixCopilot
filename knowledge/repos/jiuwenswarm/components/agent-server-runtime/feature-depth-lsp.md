---
title: "LSP 代码智能：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/Harness.md:L201-L204, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L30-L37, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/Harness.md:L73-L84, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L1670-L1672]
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

<!-- kb:depth feature=lsp facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=be49d3ed9f1c5ade6a62a6f5da331d456f7eea1a95b3c43fd1f29c65447f435b -->
**LSP 诊断为内层 ReAct 工具调用钩子的典型 Rail 用途（文档记载）；适配器侧定义 LspRail 构建方法**
docs/zh/Harness.md 记载 Rail 在生命周期节点注入能力而不替换主流程，并将 LSP 诊断列为内层 ReAct `before_tool_call`/`after_tool_call` 的典型用途；JiuwenSwarmCodeAdapter 定义 `_build_lsp_rail_via_config`，其 docstring 称构建带 project_dir 参数的 LspRail。

来源：[docs/zh/Harness.md:L73–L84](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Harness.md#L73-L84), [jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L1670–L1672](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_code.py#L1670-L1672)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":84,"path":"docs/zh/Harness.md","sha256":"08acc5cdd1c9783e61fa9f98bc5a2926bb16fc914a1616fc2ffa812aa2f9b964","start":73},{"end":1672,"path":"jiuwenswarm/server/runtime/agent_adapter/interface_code.py","sha256":"fe151ebc641618bf4997231280efb10395aa63ea158b1bb9af3bd2bb8c1359f5","start":1670}],"trace":[]} -->
<!-- /kb:depth -->
