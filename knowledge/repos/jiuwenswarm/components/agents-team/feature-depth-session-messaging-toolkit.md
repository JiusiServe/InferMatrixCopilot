---
title: "跨会话消息 Agent 工具集（SessionMessagingToolkit 六工具）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L325-L342, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L287-L302, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_session_messaging.py:L866-L882, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L358-L378, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L43-L67, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L330-L433, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L435-L445, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L594-L600, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L344-L356, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L358-L385, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L404-L418, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L330-L342, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L43-L54, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L350-L356]
feature: "session-messaging-toolkit"
entry_points: ["jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py"]
---

# 跨会话消息 Agent 工具集（SessionMessagingToolkit 六工具）：实现深读

[功能概览](feature-session-messaging-toolkit.md) · [owner 入口](_index.md)

<!-- kb:depth feature=session-messaging-toolkit facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=160ef687d8768c427d34b42ea8eb45ea2928bc7f15224574ae7bc09cd4956150 -->
**before_tool_call 回调按守卫绑定路由后再由 send_message 构造来源并调用服务**
before_tool_call 仅当工具名属于 _SESSION_MESSAGING_TOOL_NAMES 且路由含 session_id 与 request_id 时，把路由和 tool_call_id 写入上下文变量；send_message 随后用该 tool_call_id 调 source_for_call 并调用 service.send_message。

来源：[jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L287–L302](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py#L287-L302), [jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L358–L378](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py#L358-L378), [jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L43–L67](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py#L43-L67)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":302,"path":"jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py","sha256":"cc5d73344698f6731fa384cbd4c943473ff56e111fb82358c4322f720a4869a9","start":287},{"end":378,"path":"jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py","sha256":"cc94807828a33bb09bfe47f484156da38ac880a1ce68935d9e41c4ba521bc9b9","start":358},{"end":67,"path":"jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py","sha256":"9931a7b3dcd71aeafc48b3a2eb37c50fe9d44dcbc4e463a26b6ee820dffa276f","start":43}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=session-messaging-toolkit facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=96b70a9efc862f0091d95c8aaf1049bc8aed20ff2abc2e98e9ad971deaf23462 -->
**六个工具方法签名各异，均要求服务与就绪路由，SessionMessagingError 转为结构化字典返回**
list_sessions/list_messages/continue_queued/read_session/resolve_message/send_message 均先经 _service_and_route，成功时透传 service 的 dict；send_message 额外要求上下文中已有 tool_call_id，失败时返回 {"accepted": False, "code": ..., "error": ...}。get_tools 首次构建后缓存并返回列表副本。

来源：[jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L330–L433](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py#L330-L433), [jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L435–L445](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py#L435-L445), [jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L594–L600](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py#L594-L600)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":433,"path":"jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py","sha256":"34318d8e1c401c6e0bb61448b263fac7b4039e64aa7963ea3d001e4042beca11","start":330},{"end":445,"path":"jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py","sha256":"bb23c9c4f4af191891d7d22aa6a80e440c57f8e37ec5103a1f233bd98a9cf7eb","start":435},{"end":600,"path":"jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py","sha256":"397d0307535d2d0c7a4ad79534d381deda3d2ca4ffb2dff2febeacabf8cc0585","start":594}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=session-messaging-toolkit facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e5adab654351caa624b914da25a7f9ec01522d8b8e59cb4072cd1b175dd27e1a -->
**工具入参默认值仅为本地签名默认：input_mode="steer"、limit 20/50、offset 0、cursor None、max_output_chars 4000**
send_message 的 input_mode 默认 "steer"；list_sessions 默认 query=""、limit=20、offset=0；list_messages 默认 limit=50；read_session 默认 cursor=None、limit=20、max_output_chars=4000。这些是调用方未传参时的本地默认，非硬性上限。

来源：[jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L344–L356](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py#L344-L356), [jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L358–L385](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py#L358-L385), [jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L404–L418](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py#L404-L418)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":356,"path":"jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py","sha256":"c2c6e2129d71bb42dc6904e92c86a5c5fbe9e7dc56044d28c79d64434d99bce0","start":344},{"end":385,"path":"jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py","sha256":"d13b73e96997cc0e68ebc17fedd428dbe8c128d59292293c79adeb26e0f862a1","start":358},{"end":418,"path":"jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py","sha256":"17c269be96d9595cc370258a8acd5a9b88db7287c27fee0152522bcbaefa571f","start":404}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=session-messaging-toolkit facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7a7d05b084a3a167135212c5ab98b11bda95ec0cfad5318069b656582dae6495 -->
**工具依赖运行时上下文中的 session_message_service 与路由上下文变量**
_service_and_route 优先用 set_service 注入的服务，否则从 get_current_runtime() 的 session_message_service 属性取；路由来自 _SESSION_MESSAGING_ROUTE 上下文变量（由 before_tool_call 在工具名匹配 _SESSION_MESSAGING_TOOL_NAMES 且路由含 session_id/request_id 时设置）。缺任一则抛 HOST_CAPABILITY_UNAVAILABLE。

来源：[jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L325–L342](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py#L325-L342), [jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L287–L302](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py#L287-L302)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":342,"path":"jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py","sha256":"4006106ccab149157883bfae9631ce8bb439170b04268d0a28dcd11a4ed910f4","start":325},{"end":302,"path":"jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py","sha256":"cc5d73344698f6731fa384cbd4c943473ff56e111fb82358c4322f720a4869a9","start":287}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=session-messaging-toolkit facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=186ef55434b3aa64ac0ff0a03dd96e4d5b2a58ef08c30533ccccecdae6724a69 -->
**服务缺失或路由不完整触发 HOST_CAPABILITY_UNAVAILABLE，空 tool_call_id 触发 MISSING_TOOL_CALL_ID**
_service_and_route 在 service 为 None 或路由缺 session_id/request_id 时抛 code 为 HOST_CAPABILITY_UNAVAILABLE 的 SessionMessagingError；source_for_call 在 tool_call_id 为空串时抛 MISSING_TOOL_CALL_ID。所示方法内这些异常被捕获并转为 accepted=False 的字典返回。

来源：[jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L330–L342](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py#L330-L342), [jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L43–L54](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py#L43-L54), [jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L350–L356](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py#L350-L356)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":342,"path":"jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py","sha256":"741f1b99eef2c5d639c0a936a575bee92e5bd0dd6ec0b38e52ec2b67598d927c","start":330},{"end":54,"path":"jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py","sha256":"b91bff50c64c23b0f74cc3a100152045dd238a95247ed0785c60f8e2a4be8551","start":43},{"end":356,"path":"jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py","sha256":"9b3e95c7259b2433122fa6def93962d2b95f892aa20341a1f41bdd4f31170877","start":350}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=session-messaging-toolkit facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7edaa05fdaf543b904ba1fff403a9639e12b77a67cf06ece3d46ff89150e2470 -->
**每工具局部捕获 SessionMessagingError 换取 Agent 可读的错误码，代价是该异常不再向上传播**
设计推断（非作者历史意图）：

benefit：Agent 调用方直接拿到含 code 的结构化结果而非异常；cost：该异常在每个工具方法内被就地吞掉，且 except 仅覆盖 SessionMessagingError，其他异常类型不在该局部兜底内。此为基于所示实现的推断。

来源：[jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L350–L356](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py#L350-L356), [jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py:L358–L378](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py#L358-L378)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":356,"path":"jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py","sha256":"9b3e95c7259b2433122fa6def93962d2b95f892aa20341a1f41bdd4f31170877","start":350},{"end":378,"path":"jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py","sha256":"cc94807828a33bb09bfe47f484156da38ac880a1ce68935d9e41c4ba521bc9b9","start":358}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=session-messaging-toolkit facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ec610651764435f8e1f657700e20d1040b17e18595f7b0010eddc9a5a411edf7 -->
**单元测试断言 read_session 分页、截断且不触发执行**
test（866-882 行）用临时 sqlite store 调 service.read_session(limit=2, max_output_chars=8)，断言 newest_first 的 id 顺序 ["4","3"]、内容截断为 8 字符且无 private_metadata、游标翻页到 ["2","1"]、跨会话游标抛 SessionMessagingError、service._execute 未被 await。这是已存在的自动化运行时测试，本文未执行它。

来源：[tests/unit_tests/agentserver/test_session_messaging.py:L866–L882](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/test_session_messaging.py#L866-L882)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":882,"path":"tests/unit_tests/agentserver/test_session_messaging.py","sha256":"b1a7fc97e9d293b644a5916a12b12669fca376b38a14256a69ca07cf06361aec","start":866}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
