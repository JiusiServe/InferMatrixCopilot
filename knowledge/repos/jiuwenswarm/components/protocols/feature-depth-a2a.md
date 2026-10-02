---
title: "A2A 接入与 AgentCard：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/protocol/a2a/a2a_connect.py:L284-L314, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/A2A.md:L51-L58, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/protocol/a2a/a2a_connect.py:L151-L188, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/A2A.md:L122-L125, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/A2A.md:L134-L152]
feature: "a2a"
entry_points: ["jiuwenswarm/gateway/channel_manager/protocol/a2a/a2a_connect.py"]
source_globs: ["jiuwenswarm/gateway/channel_manager/protocol/a2a/a2a_connect.py", "jiuwenswarm/gateway/channel_manager/protocol/a2a/*.py"]
---

# A2A 接入与 AgentCard：实现深读

[功能概览](feature-a2a.md) · [owner 入口](_index.md)

<!-- kb:depth feature=a2a facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9d3f9d150cf34cb0189ff350ef7368e6adc4fc7ccae105c507496ecc46d01c14 -->
**enabled 开关与 AgentCard 字段来源**
A2AChannel.start 在 config.enabled 为假时记日志 "[A2AChannel] disabled by config" 并不启动服务（默认关闭，文档 §3：A2A_SERVER_ENABLED 未设则关闭，端口默认 19100、路径 /a2a）。AgentCard 的 name/description/version 取自 config.app_name/app_description/app_version，supported_interfaces[0].url 由 config.host:port + rpc_path 拼出，capabilities 固定 streaming=True、push_notifications=False。

来源：[jiuwenswarm/gateway/channel_manager/protocol/a2a/a2a_connect.py:L284–L314](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/protocol/a2a/a2a_connect.py#L284-L314), [docs/zh/A2A.md:L51–L58](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/A2A.md#L51-L58)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/gateway/channel_manager/protocol/a2a/a2a_connect.py","start":284,"end":314,"sha256":"5190c6360c98ff7303a64a2982c0e1a886f3914d331ab0080e3641078cfc5643"},{"path":"docs/zh/A2A.md","start":51,"end":58,"sha256":"1dfc6a98f6b35ed2131426453c8dc0bc1b8733a4f6d5305c8f14bba389de830b"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=a2a facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f3839fe34c5d5090100d11080844257535f8a67845658aec07893fa718cf9cbc -->
**推理内容不进 artifact，仅作状态事件**
设计推断（非作者历史意图）：

推理消息永不写入 response artifact：config.expose_reasoning 为真时以 working 状态的 TaskStatusUpdateEvent 流式输出，part 由 message_to_a2a_parts(fallback_to_text=False) 生成；关闭时直接丢弃。推断：好处是调用方可借助 metadata 键 jiuwen_thought（对齐 Google ADK 的 adk_thought 惯例）结构化区分思考与正文，代价是纯 artifact 消费方看不到推理、且终态 reasoning 分支必须显式清空 response_parts 防泄漏。

来源：[jiuwenswarm/gateway/channel_manager/protocol/a2a/a2a_connect.py:L151–L188](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/protocol/a2a/a2a_connect.py#L151-L188), [docs/zh/A2A.md:L122–L125](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/A2A.md#L122-L125)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/gateway/channel_manager/protocol/a2a/a2a_connect.py","start":151,"end":188,"sha256":"ecebb28d438a77a08e9e9be3c22b355ced45f86a2aa9c604f42be34d3c2f6624"},{"path":"docs/zh/A2A.md","start":122,"end":125,"sha256":"93f754975fabffdec25b29de509ba73dd9ef80f072409ec22e4ab6f2aad98104"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=a2a facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fe15739c43677ada9618d994c37e8919f9d7518350b0f5849cb028b9da42d2e0 -->
**文档给出的本地验证命令**
docs/zh/A2A.md §8 给出针对 http://127.0.0.1:{A2A_SERVER_PORT:-19100}{A2A_SERVER_PATH:-/a2a} 的 curl 验证：非流式 method=SendMessage 与流式 method=SendStreamingMessage 的 JSON-RPC 请求，前置条件是 AgentServer、Gateway 均已启动且 A2A_SERVER_ENABLED=true。所提供的切片中没有该功能的自动化测试入口，此处仅记录文档约定的手工验证方式，不声称测试已运行或通过。

来源：[docs/zh/A2A.md:L134–L152](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/A2A.md#L134-L152)

<!-- kb:depth-proof {"evidence":[{"path":"docs/zh/A2A.md","start":134,"end":152,"sha256":"539c1fd6494415dc2daa5bb4dfc87e4837781a286c3fd8adb943977ab29d309c"}],"trace":[]} -->
<!-- /kb:depth -->
