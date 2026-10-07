---
title: "3rdagent.list / 3rdagent.switch 第三方智能体切换：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/extensions/test_agentos_router.py:L839-L857, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/extensions/test_agentos_router.py:L1065-L1083, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/client/third_agent.py:L14-L49, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/agentos/agentos_router/router_client.py:L1572-L1582, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/routing/third_agent.py:L1-L17, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/extensions/test_agentos_router.py:L1407-L1420, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/client/third_agent.py:L55-L82, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/client/third_agent.py:L52-L89, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/routing/third_agent.py:L11-L17, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/client/third_agent.py:L17-L22, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/client/third_agent.py:L24-L37, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/client/third_agent.py:L39-L49]
feature: "thirdagent-list-switch"
entry_points: ["jiuwenswarm/extensions/agentos/agentos_router/router_client.py"]
source_globs: ["jiuwenswarm/extensions/agentos/agentos_router/router_client.py", "jiuwenswarm/common/client/third_agent.py", "jiuwenswarm/gateway/routing/third_agent.py"]
---

# 3rdagent.list / 3rdagent.switch 第三方智能体切换：实现深读

[功能概览](feature-thirdagent-list-switch.md) · [owner 入口](_index.md)

<!-- kb:depth feature=thirdagent-list-switch facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cd9879bac6fd485903f531e785c96720376b426a14672d5d3c12e3f4a2c859bf -->
**thirdagent_switch on a registry agent creates one sandbox; on builtin jiuwenswarm it creates none**
In the router-client test path, thirdagent_switch(user_id="u1", agent_type="opencode", session_id="sess-1") returns ok with payload.agent_type="opencode" and payload.sandbox_id="sbx-1" after exactly one yuanrong.create; switching to agent_type="jiuwenswarm" returns ok with sandbox_id="" and zero creates.

来源：[tests/unit_tests/extensions/test_agentos_router.py:L839–L857](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/extensions/test_agentos_router.py#L839-L857), [tests/unit_tests/extensions/test_agentos_router.py:L1065–L1083](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/extensions/test_agentos_router.py#L1065-L1083)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":857,"path":"tests/unit_tests/extensions/test_agentos_router.py","sha256":"e8960d3fbc9a2c18664f06c46740e5e34f109429f1156bf83edd0ce874522c4d","start":839},{"end":1083,"path":"tests/unit_tests/extensions/test_agentos_router.py","sha256":"e169a601636ad750dae06b1d8fe941616e4ea34f7412c18350e8c87aa4b88067","start":1065}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=thirdagent-list-switch facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b77b40e4d0ea0c372c56e9c17c859c24771ebd0cbfaefde99a47c7c1a9bd9c97 -->
**ThirdAgent abstract contract: thirdagent_list and thirdagent_switch keyword-only methods returning dicts**
ThirdAgent (ABC) declares abstract async thirdagent_list(*, user_id, current_agent_type="", access_mode="") and thirdagent_switch(*, user_id, agent_type, session_id="", params=None), both returning dict[str, Any]; access_mode selects which registry access_mode[].cmd is returned. normalize_agent_type maps empty or case-insensitive "jiuwenswarm" to "jiuwenswarm", otherwise preserves the raw string's case.

来源：[jiuwenswarm/common/client/third_agent.py:L14–L49](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/client/third_agent.py#L14-L49)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":49,"path":"jiuwenswarm/common/client/third_agent.py","sha256":"495c480935bea1e53d1dae492b39d41c994b9fe0b891cb7aab955e38a7ae288e","start":14}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=thirdagent-list-switch facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e0dd2113f12145a0efb550cc1dad3e3972fae62f8332e681b1c2e98d6693b843 -->
**normalize_agent_type default: empty or falsey input becomes "jiuwenswarm"; other stripped names keep case**
In ThirdAgent.normalize_agent_type, agent_type = str(raw or "").strip(), so raw that is None, empty, or any falsey value (e.g. 0, False, "") substitutes "" and yields builtin "jiuwenswarm"; only inputs whose str().strip().lower() equals "jiuwenswarm" are lowercased to the builtin, all other stripped names are returned with original case. The abstract thirdagent_list/thirdagent_switch declare keyword-only defaults current_agent_type="", access_mode="" and session_id="", params=None; access_mode selects which registry access_mode[].cmd is returned (TUI passes "tui").

来源：[jiuwenswarm/common/client/third_agent.py:L17–L22](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/client/third_agent.py#L17-L22), [jiuwenswarm/common/client/third_agent.py:L24–L37](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/client/third_agent.py#L24-L37), [jiuwenswarm/common/client/third_agent.py:L39–L49](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/client/third_agent.py#L39-L49)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":22,"path":"jiuwenswarm/common/client/third_agent.py","sha256":"343bc1126903d03bc8a240cbcd1be842892c1b079d7a80cbf247f7b3cf13f6ac","start":17},{"end":37,"path":"jiuwenswarm/common/client/third_agent.py","sha256":"ffe47bedc717aec03a22a61521482490d7b084e2bd03a135c03b83e48fa51128","start":24},{"end":49,"path":"jiuwenswarm/common/client/third_agent.py","sha256":"0d8c6a400da6de0d78a6313f71d4ee8b4ebb2c3979a3616667052256cef6442c","start":39}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=thirdagent-list-switch facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dfb0633791c4e127914f9261ca85f6c213e984ee0ec83ad34895f1540264cd72 -->
**3rdagent calls bypass E2A send_request; contract lives in common.client.third_agent re-exported by gateway**
AgentOSRouterClient.send_request states 3rdagent.list/switch are handled by the Gateway ThirdAgent (TUI local_handler), not via E2A send_request; the jiuwenswarm.gateway.routing.third_agent module only re-exports ThirdAgent, UnsupportedThirdAgent and get_unsupported_third_agent from jiuwenswarm.common.client.third_agent to keep the old import path working.

来源：[jiuwenswarm/extensions/agentos/agentos_router/router_client.py:L1572–L1582](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/agentos/agentos_router/router_client.py#L1572-L1582), [jiuwenswarm/gateway/routing/third_agent.py:L1–L17](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/routing/third_agent.py#L1-L17)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1582,"path":"jiuwenswarm/extensions/agentos/agentos_router/router_client.py","sha256":"d0db4c676c4b0c97c3b56160a9269aed44393fe776abdd4dc24143cc007b6124","start":1572},{"end":17,"path":"jiuwenswarm/gateway/routing/third_agent.py","sha256":"194e52cbb8899e1df04713bfccaf423e62e1041ec3308983bc0f6af3e8f64c81","start":1}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=thirdagent-list-switch facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=570813559a75cc133ec091729d00273c70c0cea04739d70340cf7daf7e9727ba -->
**未注册扩展时 UnsupportedThirdAgent 各自返回 ok=False、code="UNSUPPORTED"，不抛异常**
thirdagent_list 丢弃 user_id/current_agent_type/access_mode，返回 {"ok": False, "error": "3rdagent.list requires an AgentOS Router extension", "code": "UNSUPPORTED"}；thirdagent_switch 丢弃 user_id/agent_type/session_id/params，返回 error 为 "3rdagent.switch requires an AgentOS Router extension"、同样的 code。两个分支在本地返回，不 raise。

来源：[jiuwenswarm/common/client/third_agent.py:L55–L82](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/client/third_agent.py#L55-L82)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":82,"path":"jiuwenswarm/common/client/third_agent.py","sha256":"ee904ea9d58faba7e359757f20b4f63c8d35dd80b5426b6cf25969839d824501","start":55}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=thirdagent-list-switch facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=53f5c09d4ce1ffa1cf6a9ce40780c6b107ba13298a1caa0a6be6a7dd433f2710 -->
**模块级单例默认实现换来确定性的 UNSUPPORTED 拒绝，代价是空输入下不提供任何降级列表**
设计推断（非作者历史意图）：

get_unsupported_third_agent 返回模块级 _UNSUPPORTED_THIRD_AGENT 单例；对本仓内通过 jiuwenswarm.gateway.routing.third_agent re-export 导入的调用方，无扩展时可得到确定性的 ok=False 响应（推断为收益）；代价是即使 list 请求也一律失败、不返回部分目录（推断）。仅限所示实现，不跨仓保证。

来源：[jiuwenswarm/common/client/third_agent.py:L52–L89](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/client/third_agent.py#L52-L89), [jiuwenswarm/gateway/routing/third_agent.py:L11–L17](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/routing/third_agent.py#L11-L17)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":89,"path":"jiuwenswarm/common/client/third_agent.py","sha256":"fc658d6d0e7cbde84aa44fffddc74ffe146ec655d986d95d80e4ba0000185dbc","start":52},{"end":17,"path":"jiuwenswarm/gateway/routing/third_agent.py","sha256":"365e10109905e2d598bee40e6316baea223aea2e1f94d89950ab10d999f365ab","start":11}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=thirdagent-list-switch facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d1f4cbcce75dc65258744a6bc16465ae5fa2986cdd2df2dec9d591a2d6187569 -->
**test_unsupported_third_agent_returns_unsupported awaits both stub methods and asserts the UNSUPPORTED dicts**
The pytest asyncio test imports get_unsupported_third_agent via jiuwenswarm.gateway.routing.third_agent, calls thirdagent_list(user_id="u1", current_agent_type="jiuwenswarm") and thirdagent_switch(user_id="u1", agent_type="opencode", session_id="s1"), asserting listed["ok"] is False, code "UNSUPPORTED", and the same for switched. Evidence of assertions in the test source; not executed here.

来源：[tests/unit_tests/extensions/test_agentos_router.py:L1407–L1420](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/extensions/test_agentos_router.py#L1407-L1420)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1420,"path":"tests/unit_tests/extensions/test_agentos_router.py","sha256":"94e100b57c512d0b79310aa9066c44c2291d3fd2e4e12aea945190c816ba4809","start":1407}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
