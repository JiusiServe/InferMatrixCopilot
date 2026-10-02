---
title: "E2A 统一请求响应协议：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/e2a/acp/acp_tool_updates.py:L119-L148, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/e2a/acp/acp_tool_updates.py:L301-L310]
feature: "e2a"
entry_points: ["jiuwenswarm/common/e2a/models.py"]
source_globs: ["jiuwenswarm/common/e2a/models.py", "jiuwenswarm/common/e2a/*.py"]
---

# E2A 统一请求响应协议：实现深读

[功能概览](feature-e2a.md) · [owner 入口](_index.md)

<!-- kb:depth feature=e2a facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5a6a33383476b638e0279a043d62af82a39e80bb0cf8d7e35017fa3f334ac216 -->
**build_acp_tool_descriptor 的输入契约**
build_acp_tool_descriptor 的 tool_call_id 是唯一必填关键字参数；arguments 宽松接受 dict、JSON 字符串或其他类型，由 _normalize_arguments 归一为 dict（字符串解析失败或解析结果非 dict 时包装为 {"input": 原字符串}）。调用方只需给出原始工具名，别名与 kind 推断由函数内部完成。

来源：[jiuwenswarm/common/e2a/acp/acp_tool_updates.py:L119–L148](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/e2a/acp/acp_tool_updates.py#L119-L148), [jiuwenswarm/common/e2a/acp/acp_tool_updates.py:L301–L310](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/e2a/acp/acp_tool_updates.py#L301-L310)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/common/e2a/acp/acp_tool_updates.py","start":119,"end":148,"sha256":"bd150266786e3188b77a0b49ce48cc19903ac7f2e135e683636ad4b631da2213"},{"path":"jiuwenswarm/common/e2a/acp/acp_tool_updates.py","start":301,"end":310,"sha256":"48dcc0f5d82fe2edf556ff96de801c25817ccc6cd09fba69bcb45e5b7dab28a7"}],"trace":[]} -->
<!-- /kb:depth -->
