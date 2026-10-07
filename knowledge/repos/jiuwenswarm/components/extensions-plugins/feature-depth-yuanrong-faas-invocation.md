---
title: "YuanRong FaaS 函数调用（非流式 + SSE 流式）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/yuanrong_frontend_client.py:L1880-L1908, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/agent_client/extension.py:L31-L60, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/yuanrong_frontend_client.py:L969-L971, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/yuanrong_frontend_client.py:L1936-L1943]
feature: "yuanrong-faas-invocation"
entry_points: ["jiuwenswarm/extensions/yuanrong_frontend_client.py"]
source_globs: ["jiuwenswarm/extensions/yuanrong_frontend_client.py", "jiuwenswarm/extensions/clawee.py", "jiuwenswarm/extensions/agent_client/extension.py"]
---

# YuanRong FaaS 函数调用（非流式 + SSE 流式）：实现深读

[功能概览](feature-yuanrong-faas-invocation.md) · [owner 入口](_index.md)

<!-- kb:depth feature=yuanrong-faas-invocation facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2b5107f0054c2987062e1c87d679f9ea36a8e6d80bb116693925597d1b0e2198 -->
**send_request_stream 输入 E2AEnvelope、产出 AgentResponseChunk；error 项产出错误块，exception 项抛 RuntimeError**
输入是 E2AEnvelope；产出为 AgentResponseChunk，request_id/channel_id 优先取 chunk 自身字段、兜底 e2a_to_agent_request 的值。"error" 项产出 payload={"error": text or "invoke stream failed"} 且 is_complete=False 的块；"exception" 项直接 raise RuntimeError(f"invoke stream failed: {text}")。调用方需消费异步迭代器并在 RuntimeError 上做自身错误处理。

来源：[jiuwenswarm/extensions/yuanrong_frontend_client.py:L1880–L1908](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/yuanrong_frontend_client.py#L1880-L1908)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1908,"path":"jiuwenswarm/extensions/yuanrong_frontend_client.py","sha256":"0d6c512d2a7ac00256f43b395e031b6747a04eb9dc6582b395290e713b3d8e30","start":1880}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=yuanrong-faas-invocation facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9b0e19fc58bcc519001b841a5c31006be5bbfe74db6b660190cd942aef8eca1b -->
**gateway.agent_client.type=yuanrong 时必填两项，其余有默认值**
type 默认 "websocket"（非 yuanrong 返回 [] 不注册）；yuanrong 模式下 frontend_endpoint 与 function_version_urn 缺失抛 ValueError；concurrency 默认 1、invoke_timeout_s 默认 60.0、agent_timeout_s 默认 300.0、agent_namespace 默认 "default"。

来源：[jiuwenswarm/extensions/agent_client/extension.py:L31–L60](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/agent_client/extension.py#L31-L60)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":60,"path":"jiuwenswarm/extensions/agent_client/extension.py","sha256":"b07b90dbd7bab5d152def7e35329bfcbe32148fe2d12633022b692f4a6e73f28","start":31}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=yuanrong-faas-invocation facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2e656b33a074c55a3cb335b0d110601d18f00dad88d165a5321f11d9e015ef1a -->
**未连接时抛 RuntimeError("client not connected")；流式 HTTP 非 2xx 转为队列 error 项**
_ensure_connected 在 self._connected 为假时抛 RuntimeError("client not connected")；_do_invoke_stream 中 200<=status<300 不成立时读取响应体、记录日志并把 ("error", 含 http_status 与 body 的 JSON) 经 call_soon_threadsafe 放入输出队列后 return——return 只结束该线程函数，不表示进程退出。

来源：[jiuwenswarm/extensions/yuanrong_frontend_client.py:L969–L971](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/yuanrong_frontend_client.py#L969-L971), [jiuwenswarm/extensions/yuanrong_frontend_client.py:L1936–L1943](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/yuanrong_frontend_client.py#L1936-L1943)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":971,"path":"jiuwenswarm/extensions/yuanrong_frontend_client.py","sha256":"7701c60c750b210ba3a5557330833fbecb43221103ff5e19843a4928d0b68b94","start":969},{"end":1943,"path":"jiuwenswarm/extensions/yuanrong_frontend_client.py","sha256":"d8bb07a5aa39b3ea0d3c3d04f5656c5e043e11adc29563f8bee08a6c382cbac3","start":1936}],"trace":[]} -->
<!-- /kb:depth -->
