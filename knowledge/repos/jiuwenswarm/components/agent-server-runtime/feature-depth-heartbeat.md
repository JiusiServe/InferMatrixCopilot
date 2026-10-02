---
title: "绑定会话的心跳续跑任务：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/heartbeat/proxy.py:L25-L66, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py:L71-L80, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py:L278-L380]
---

# 绑定会话的心跳续跑任务：实现深读

[功能概览](feature-heartbeat.md) · [owner 入口](_index.md)

<!-- kb:depth feature=heartbeat facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a4641059119698ec9d3d034a6f74d83580e9668a6d82411010a6a406c92a21ff -->
**网关代理的错误码到异常映射**
HeartbeatControllerProxy._request 把操作包装为 ReqMethod.HEARTBEAT_JOB 的 Message 经 agent_client 发送；响应失败时按 payload.code 映射异常：BAD_REQUEST→ValueError、FORBIDDEN→PermissionError、NOT_FOUND→KeyError、CONFLICT→RuntimeError、SERVICE_UNAVAILABLE→HeartbeatServiceUnavailableError。调用方需按这些异常类型处理失败。

来源：[jiuwenswarm/gateway/heartbeat/proxy.py:L25–L66](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/heartbeat/proxy.py#L25-L66)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/gateway/heartbeat/proxy.py","start":25,"end":66,"sha256":"3072ba086e6f9885e1798b209c991345dc4846bc70468183a31c26261e4f5b4b"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=heartbeat facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5f3e2b1aa893b23b1087f727ccea7e659acfadffb845b77fcbbb6e3e75ca3584 -->
**资源限制默认值与 config 覆盖**
controller 的 _DEFAULT_LIMITS 给出 max_active_jobs_per_session=5、max_active_jobs_global=100、min_interval_seconds=MIN_INTERVAL_SECONDS 等默认值，注释声明可被 config 覆盖；create_job 中 max_runs 缺省取 default_max_runs，source 缺省取 SOURCE_WEB_RPC（"web_rpc"）。

来源：[jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py:L71–L80](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py#L71-L80), [jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py:L278–L380](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py#L278-L380)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py","start":71,"end":80,"sha256":"d5ba92e0a7676926074cbe1efdbfc1d28f43836fef9d3466b90213f03d6a1a3e"},{"path":"jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py","start":278,"end":380,"sha256":"6bc2cf744cd9b34aadb82e20bb430ebfd5e4a88c017e6f4bf898e2a412fd8c16"}],"trace":[]} -->
<!-- /kb:depth -->
