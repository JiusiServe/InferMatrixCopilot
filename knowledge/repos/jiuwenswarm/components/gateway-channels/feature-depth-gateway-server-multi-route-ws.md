---
title: "GatewayServer 多路由 WebSocket 宿主与会话/请求路由表：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L943-L977, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/gateway/test_app_gateway_acp.py:L656-L668, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L644-L663, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L785-L806, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/app_gateway.py:L900-L925]
feature: "gateway-server-multi-route-ws"
entry_points: ["jiuwenswarm/gateway/app_gateway.py"]
source_globs: ["jiuwenswarm/gateway/app_gateway.py", "jiuwenswarm/gateway/channel_manager/channel_manager.py", "jiuwenswarm/gateway/routing/route_binding.py", "jiuwenswarm/gateway/channel_manager/base.py", "jiuwenswarm/gateway/routing/keys.py"]
---

# GatewayServer 多路由 WebSocket 宿主与会话/请求路由表：实现深读

[功能概览](feature-gateway-server-multi-route-ws.md) · [owner 入口](_index.md)

<!-- kb:depth feature=gateway-server-multi-route-ws facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dfd7b129a7188887501614b3b46025bc36b032f1b96672ef4d9cd182f0ea517e -->
**_send_frame_to_ws 在发送前检查 ws 开合，序列化 frame 为 JSON 后经 ws.send 发送**
对带 channel_id/request_id/session_id 的 frame：_ws_is_open 要求 ws 非 None 且 closed 属性为假，否则直接返回 False；通过则 await ws.send(json.dumps(frame, ensure_ascii=False)) 并在本地返回 True。

来源：[jiuwenswarm/gateway/app_gateway.py:L900–L925](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L900-L925)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":925,"path":"jiuwenswarm/gateway/app_gateway.py","sha256":"8b38f0559b2e7c0d354041b2317d83e6ac399c35a64ac422e2f2691075024044","start":900}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=gateway-server-multi-route-ws facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=006a6061c3bc1ab2320b31cd0e8038a9fc22b37c87cf6f70c75af8b78635b930 -->
**_bind_route_session_client 返回 bool；session_bind_handler 可为同步或协程**
入参 (route: RouteConfig, session_id, ws)。session 键为 None、或存在其它未关闭 ws 时返回 False；成功写入映射返回 True。绑定成功且 existing_ws is not ws 且 route.session_bind_handler 非 None 时调用 handler(route.channel_id, session_id)，若结果是协程则 await；异常被捕获并记 warning，仍返回 True。

来源：[jiuwenswarm/gateway/app_gateway.py:L943–L977](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L943-L977)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":977,"path":"jiuwenswarm/gateway/app_gateway.py","sha256":"b9c24a40c022ff7df8d4709a97912f15248f55561bd9db622bdf88468b163e30","start":943}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=gateway-server-multi-route-ws facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a98f16d30f7bafbd9c3d14680460699cac1923f1d4c54d115d34c3117def05c5 -->
**RouteConfig 默认值：空 frozenset、空 local_handlers、ws_channel=None 不委托**
每条路由（如 /acp、/cli）的 RouteConfig 中 forward_methods 与 forward_no_local_handler_methods 默认 frozenset()，local_handlers 默认空 dict，各 handler/interceptor 与 ws_channel 默认 None；ws_channel=None 表示该路由无需把 ws 委托注册进外部 Channel。

来源：[jiuwenswarm/gateway/app_gateway.py:L644–L663](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L644-L663)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":663,"path":"jiuwenswarm/gateway/app_gateway.py","sha256":"80ffdf853251d600ab787b3a95dbde978471a8f474c38e3dab4edaf3d104de45","start":644}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=gateway-server-multi-route-ws facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2844fbac5b3864234bfde843ce4d164c344f9c1f47995486a1ecf2e9b05684a8 -->
**二元组兼容旧路径 vs 可选 agent_ref 第三维**
设计推断（非作者历史意图）：

（推断）_client_route_key 保持不传 agent_ref 时返回二元组以兼容旧索引路径，收益是旧调用无需改动；代价是同一 session 下二元组键无法区分多个 agent_ref，需调用方显式传入第三维才能共存，规范化失败（ar_str 为空）时静默退回二元组。

来源：[jiuwenswarm/gateway/app_gateway.py:L785–L806](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/app_gateway.py#L785-L806)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":806,"path":"jiuwenswarm/gateway/app_gateway.py","sha256":"17b899dc4957da2943eaf5839defbab93717da755ae246dc096cacba90624269","start":785}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=gateway-server-multi-route-ws facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7b8dd9076e84c7674d35cf10fa54282c0a86b05a700ff0f4d4c5e2819010ef59 -->
**运行时单测覆盖：绑定返回 False、断连后提升并回调 handler**
test_gateway_server_promotes_pending_session_client_after_stale_owner_cleanup 断言 _bind_route_session_client 返回 False，await _connection_handler(old_ws, "/tui") 后 disconnected == [([("tui","sess-race")], [])]、rebound == [("tui","sess-race")]、_session_to_client[("tui","sess-race")] is new_ws。未执行，仅引用现有断言。

来源：[tests/unit_tests/gateway/test_app_gateway_acp.py:L656–L668](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/gateway/test_app_gateway_acp.py#L656-L668)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":668,"path":"tests/unit_tests/gateway/test_app_gateway_acp.py","sha256":"6fa4a84776b10b11a7ba5f3dc19acad1db9b30f3ff59191d82b3877a2e679d8a","start":656}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
