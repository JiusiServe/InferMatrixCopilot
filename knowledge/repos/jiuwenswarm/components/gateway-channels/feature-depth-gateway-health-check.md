---
title: "Gateway HealthCheck 周期探活服务：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/health_check/health_check.py:L128-L134, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/health_check/health_check.py:L332-L351, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/health_check/health_check.py:L166-L175, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/health_check/health_check.py:L336-L340, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/gateway/test_heartbeat_contracts.py:L45-L64, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/health_check/health_check.py:L142-L150, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/health_check/health_check.py:L177-L216, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/health_check/health_check.py:L76-L92, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/health_check/health_check.py:L9-L18, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/health_check/health_check.py:L200-L207, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/health_check/health_check.py:L177-L207, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/health_check/__init__.py:L10-L28]
feature: "gateway-health-check"
entry_points: ["jiuwenswarm/gateway/health_check/__init__.py", "jiuwenswarm/gateway/health_check/health_check.py"]
source_globs: ["jiuwenswarm/gateway/health_check/__init__.py", "jiuwenswarm/gateway/health_check/health_check.py", "jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py"]
---

# Gateway HealthCheck 周期探活服务：实现深读

[功能概览](feature-gateway-health-check.md) · [owner 入口](_index.md)

<!-- kb:depth feature=gateway-health-check facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4ebd2cf0768faf65bb5bd89532c7cabb42a56b98a275d426dde428032a9ddbc3 -->
**start 防重入后启动循环；_tick 在活跃时段构造 E2A 探活并标记成功状态**
start 在 self._running 已为真时直接返回，否则置真并用 asyncio.create_task 启动 _run_loop 并打 INFO 日志（含 interval_seconds）。每次 _tick 先经 _is_active_now() 守卫，不活跃则打 debug 日志并返回；随后用毫秒时间戳加 secrets.token_hex(3) 生成 request_id 与 session_id，经 e2a_from_agent_fields 构造以 config.channel_id 为通道的探活信封（params 含 HEALTH_CHECK_PROMPT）。若 timeout_seconds 非 None 且 > 0 则用 asyncio.wait_for 包裹 agent_client.send_request，否则直接 await；成功后置 _last_tick_at 与 _last_tick_ok = True。

来源：[jiuwenswarm/gateway/health_check/health_check.py:L142–L150](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/health_check/health_check.py#L142-L150), [jiuwenswarm/gateway/health_check/health_check.py:L177–L216](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/health_check/health_check.py#L177-L216)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":150,"path":"jiuwenswarm/gateway/health_check/health_check.py","sha256":"0b57f5d18c18b642276417ec8de77fdff6dfe439f8aecae8584408080ec8ce41","start":142},{"end":216,"path":"jiuwenswarm/gateway/health_check/health_check.py","sha256":"b6a0e10d268b9e9aaf780854ce8eafc9a457e9031254beb2063fa6446d05726b","start":177}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=gateway-health-check facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bac9d11e400a711ddc683c806fc679a5786f3e05c8034cfe83db1bca2a5b3410 -->
**构造注入 agent_client/config/可选 message_handler；update_conf 校验 every 并按参数就地更新**
__init__ 接受 agent_client、HealthCheckConfig 与可选 message_handler；update_conf 中 every 非 None 时要求 >0 否则抛 ValueError("health_check 'every' must be > 0")，target/active_hours 非 None 时写入 _config；三者全为 None 则直接返回不改状态。

来源：[jiuwenswarm/gateway/health_check/health_check.py:L128–L134](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/health_check/health_check.py#L128-L134), [jiuwenswarm/gateway/health_check/health_check.py:L332–L351](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/health_check/health_check.py#L332-L351)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":134,"path":"jiuwenswarm/gateway/health_check/health_check.py","sha256":"71e6f87a0e11530e23b6f6d04fa1625f92e5322e24efd67b6015203f74053908","start":128},{"end":351,"path":"jiuwenswarm/gateway/health_check/health_check.py","sha256":"c691eee9fd0c90c1c5d8895b5d89188b352c10ddebf4d02b9de45e7e88bbf6b8","start":332}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=gateway-health-check facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=26bdf1adde879e1be1c30fd19856f3ecd2e0e195cccb60d50252c934da3dd768 -->
**HealthCheckConfig 默认值：timeout_seconds/relay_channel_id/active_hours 默认 None，channel_id 默认 HEALTH_CHECK_CHANNEL_ID**
interval_seconds 为必填 float；timeout_seconds 默认 None（文档注明可选、提供则 MUST > 0，_tick 仅在非 None 且 > 0 时套 asyncio.wait_for）；channel_id 默认常量 HEALTH_CHECK_CHANNEL_ID（文档注明默认 __health_check__）；relay_channel_id 默认 None，文档说明从 .env 的 HEARTBEAT_RELAY_CHANNEL_ID 读取且为 None 则不回传；active_hours 默认 None 表示始终生效。模块文档说明配置已从 config.yaml 的 heartbeat 段迁移到 health_check 段，环境变量保留 HEARTBEAT_RELAY_CHANNEL_ID 等旧名。

来源：[jiuwenswarm/gateway/health_check/health_check.py:L76–L92](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/health_check/health_check.py#L76-L92), [jiuwenswarm/gateway/health_check/health_check.py:L9–L18](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/health_check/health_check.py#L9-L18), [jiuwenswarm/gateway/health_check/health_check.py:L200–L207](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/health_check/health_check.py#L200-L207)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":92,"path":"jiuwenswarm/gateway/health_check/health_check.py","sha256":"e935be7f2599531fcd5d5790fbdd657d91ffbd5ff9850629312f177a798a5559","start":76},{"end":18,"path":"jiuwenswarm/gateway/health_check/health_check.py","sha256":"b12ae8fc92179b6f7c0ee6e64a27f620af439288e06ee90b325e4c48601af5d5","start":9},{"end":207,"path":"jiuwenswarm/gateway/health_check/health_check.py","sha256":"62110a4c7535dfd744c55d3e036e9566576ac7618fa13a23551727e9d48aac8f","start":200}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=gateway-health-check facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cd13652718ad066ec9d15af5b53fb6ee9cc5066c260f850a5cc9aa1d2f6d9b33 -->
**循环吞掉普通异常继续运行，CancelledError 退出；update_conf 对 every<=0 抛 ValueError**
_run_loop 捕获 asyncio.CancelledError 后 break 结束循环；其他 Exception 仅 logger.exception("Gateway health check loop error") 后继续下一轮。update_conf 在 every<=0 时抛 ValueError，由调用方处理。

来源：[jiuwenswarm/gateway/health_check/health_check.py:L166–L175](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/health_check/health_check.py#L166-L175), [jiuwenswarm/gateway/health_check/health_check.py:L336–L340](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/health_check/health_check.py#L336-L340)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":175,"path":"jiuwenswarm/gateway/health_check/health_check.py","sha256":"8b4f2adfedd9b30d1e2d692153573257afb37bf39fd8e38d781b91fbb34b4cac","start":166},{"end":340,"path":"jiuwenswarm/gateway/health_check/health_check.py","sha256":"9aca04a24db5f0b45f6abd61c82392e38f99d5f00461e2ef3ac89116cf251018","start":336}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=gateway-health-check facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e945dea5196976e6bd3ecec3464ff4dcdbeda4306b9beb2b8eefcc5d8a4c435c -->
**宽捕获换取循环存活，代价是单次探活失败仅以日志呈现（推断）**
设计推断（非作者历史意图）：

收益：_run_loop 对普通异常宽捕获使周期探活不会因一次 _tick 错误退出；成本：此类失败只通过 logger.exception 呈现，循环本身不重试加速也不上报（依据 shown 实现，属推断）。

来源：[jiuwenswarm/gateway/health_check/health_check.py:L166–L175](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/health_check/health_check.py#L166-L175)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":175,"path":"jiuwenswarm/gateway/health_check/health_check.py","sha256":"8b4f2adfedd9b30d1e2d692153573257afb37bf39fd8e38d781b91fbb34b4cac","start":166}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=gateway-health-check facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a928077757c7e7829f673b281792d461d0c55033a7f7f2f6d4e7798847470eed -->
**运行时测试断言旧 heartbeat.relay 在入口归一化为 HEALTH_CHECK_RELAY 并保留别名**
test_legacy_health_check_relay_normalizes_at_gateway_ingress 实际调用 MessageHandler._response_to_message 并断言 message.event_type is EventType.HEALTH_CHECK_RELAY 且 payload 同时含 health_check.relay 与 heartbeat/health_check 双键（未在本会话执行）。

来源：[tests/unit_tests/gateway/test_heartbeat_contracts.py:L45–L64](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/gateway/test_heartbeat_contracts.py#L45-L64)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":64,"path":"tests/unit_tests/gateway/test_heartbeat_contracts.py","sha256":"362f95e11e991f8ef10f1a73187a0f8466c2d3693319402fa0272eb01ee0b178","start":45}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->

<!-- kb:depth feature=gateway-health-check facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8c41aba01080a4a438796d392c783f291a2d960525256e1c5ee29972159b1c89 -->
**构造注入 AgentServerClient，_tick 内延迟导入 e2a_from_agent_fields 构造信封**
GatewayHealthCheckService 通过构造函数注入 agent_client: "AgentServerClient" 与 config；_tick 局部导入 jiuwenswarm.common.e2a.gateway_normalize.e2a_from_agent_fields 构造 E2A 信封后经 self._agent_client.send_request 发送。包 __init__ 从 health_check 模块再导出 HEALTH_CHECK_CHANNEL_ID、HEALTH_CHECK_OK、HEALTH_CHECK_PROMPT、GatewayHealthCheckService、HealthCheckConfig、IHealthCheck、normalize_active_hours。

来源：[jiuwenswarm/gateway/health_check/health_check.py:L128–L134](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/health_check/health_check.py#L128-L134), [jiuwenswarm/gateway/health_check/health_check.py:L177–L207](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/health_check/health_check.py#L177-L207), [jiuwenswarm/gateway/health_check/__init__.py:L10–L28](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/health_check/__init__.py#L10-L28)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":134,"path":"jiuwenswarm/gateway/health_check/health_check.py","sha256":"71e6f87a0e11530e23b6f6d04fa1625f92e5322e24efd67b6015203f74053908","start":128},{"end":207,"path":"jiuwenswarm/gateway/health_check/health_check.py","sha256":"ccb82a3467fc0390502c2024941ab3927045b26a724be0930881724c84bf375a","start":177},{"end":28,"path":"jiuwenswarm/gateway/health_check/__init__.py","sha256":"7b22c540bd8e5766dfde408bc8b6307072b746c9bb3bd04638e610f140d9c721","start":10}],"trace":[]} -->
<!-- /kb:depth -->
