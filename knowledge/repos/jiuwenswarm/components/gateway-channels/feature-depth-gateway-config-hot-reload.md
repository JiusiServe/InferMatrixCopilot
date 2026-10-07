---
title: "Gateway Config-Save Hot Reload (agent.reload_config retry, restart fallback, browser/proactive side effects)：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L3205-L3254, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L3205-L3242, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L3211-L3241, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L3211-L3242, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L3197-L3216, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/gateway/test_app_gateway_acp.py:L175-L191]
feature: "gateway-config-hot-reload"
entry_points: ["jiuwenswarm/gateway/app_gateway.py"]
source_globs: ["jiuwenswarm/gateway/app_gateway.py"]
---

# Gateway Config-Save Hot Reload (agent.reload_config retry, restart fallback, browser/proactive side effects)：实现深读

[功能概览](feature-gateway-config-hot-reload.md) · [owner 入口](_index.md)

<!-- kb:depth feature=gateway-config-hot-reload facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=de8b2cc54d89dc6dec9cc20b15512b8a6116cebae8539375fbca0efe056146ca -->
**_schedule_channel_config_retry spawns a background _retry task that reapplies a failed channel config**
调用 _schedule_channel_config_retry 后创建名为 initial-channel-retry-<channel> 的 asyncio 任务：_retry 先 sleep 2.0s，若 channel_manager.get_conf_revision 仍等于 expected_revision 就 await set_conf 重放快照；成功记日志并 return，任务完成后从 channel_retry_tasks 集合移除。

来源：[jiuwenswarm/gateway/app_gateway.py:L3205–L3254](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L3205-L3254)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":3254,"path":"jiuwenswarm/gateway/app_gateway.py","sha256":"b03284b487b823c8286ef873107c2703d09b48fa48a195f4c2602ccc59e6b109","start":3205}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=gateway-config-hot-reload facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=49c88caefe16980ea3f32de0b19c5e3f6b201308d90b202affe37746d36d3633 -->
**Retry delay starts at 2.0s and doubles per failed attempt, capped at 60.0s**
delay_seconds 初始 2.0；每次 set_conf 抛异常后 expected_revision 刷新且 delay_seconds = min(delay_seconds * 2, 60.0)，再 continue 进入下一轮。

来源：[jiuwenswarm/gateway/app_gateway.py:L3205–L3242](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L3205-L3242)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":3242,"path":"jiuwenswarm/gateway/app_gateway.py","sha256":"b093829f3e3101fabd86541060c905df6342f2aa08bdb65e4e821332e8d75f2d","start":3205}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=gateway-config-hot-reload facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=db55739d2c875a364a60227acd7a64b2188eb2eea707cae1f7fcda43ae046104 -->
**Retry correctness depends on channel_manager's conf revision counter**
_retry 通过 channel_manager.get_conf_revision(channel_name) 与 expected_revision 比较来取消，并用 channel_manager.set_conf 应用/回滚配置；注释说明 set_conf 在回调出错后会回滚可见快照，因此失败时还要 set_conf(channel_name, {}) 让变化检测器也回滚。

来源：[jiuwenswarm/gateway/app_gateway.py:L3211–L3241](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L3211-L3241)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":3241,"path":"jiuwenswarm/gateway/app_gateway.py","sha256":"138ce99362cfddb41a7273806e5b2921c92d761becad1014789b7798850f8e27","start":3211}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=gateway-config-hot-reload facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c643e6ea0a3857e436990f19f8c696e9c40595a816170c41f803f30188d3d71e -->
**Revision mismatch cancels the retry; set_conf failure logs, resets to empty conf, and backs off**
revision 不匹配时记 info 日志并 return（放弃重试）；set_conf 抛异常时记 warning，随后尝试 set_conf(channel_name, {})，若该重置也失败仅再记 warning，刷新 expected_revision 后按指数退避继续重试。

来源：[jiuwenswarm/gateway/app_gateway.py:L3211–L3242](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L3211-L3242)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":3242,"path":"jiuwenswarm/gateway/app_gateway.py","sha256":"ee943e68d0ad3607aa1d02452ff51c98ec7d480e5a729ce9d1b132b1ad0c967b","start":3211}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=gateway-config-hot-reload facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=73735987beabdf71e03b46547089d3826aa72aa206c7be46e946735f2ec7ea0b -->
**Background retry isolates optional channels but needs a revision guard against stale snapshots**
设计推断（非作者历史意图）：

推断：后台任务让失败的可选频道不阻塞启动（docstring 明示 'without delaying Web/Cron startup'），代价是必须靠 revision 比较防止用户在 Settings 改动后被旧启动快照复活配置；guard 缺失或 revision 未递增时会错误重放旧配置。

来源：[jiuwenswarm/gateway/app_gateway.py:L3197–L3216](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L3197-L3216)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":3216,"path":"jiuwenswarm/gateway/app_gateway.py","sha256":"0c6ff32de634f3bd440d8c837eb7ae7c72add7a1af8c86e883c859bd47bc8a5c","start":3197}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=gateway-config-hot-reload facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e408452cc86af6836b36a6b3114d4027bd49120dfecab03ccd351e85ee3af5c4 -->
**helper_unit test: _schedule_gateway_restart sets request event without execv**
In tests/unit_tests/gateway/test_app_gateway_acp.py, the async test test_schedule_gateway_restart_sets_event_without_execv monkeypatches os.execv to record calls, constructs a GatewayRestartRequest, calls _schedule_gateway_restart(restart_request, delay=0.0), then awaits restart_request.ready_event within 1.0s and asserts restart_request.requested is True and execv_calls == []. Coverage is limited to the restart-scheduling helper, not the agent.reload_config retry loop.

来源：[tests/unit_tests/gateway/test_app_gateway_acp.py:L175–L191](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/gateway/test_app_gateway_acp.py#L175-L191)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":191,"path":"tests/unit_tests/gateway/test_app_gateway_acp.py","sha256":"b9e8c07c15de7508d2a41d62f13b0ecce99c7f2b6f950986d3309b72f643e743","start":175}],"trace":[],"validation_kind":"helper_unit"} -->
<!-- /kb:depth -->
