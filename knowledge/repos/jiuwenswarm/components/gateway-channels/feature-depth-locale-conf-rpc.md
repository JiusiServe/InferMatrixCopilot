---
title: "界面语言配置 RPC（preferred_language）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py:L3824-L3836, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py:L3803-L3807, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py:L3795-L3807, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py:L3832-L3836, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py:L3818-L3822, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py:L3851-L3865]
feature: "locale-conf-rpc"
entry_points: ["jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py"]
source_globs: ["jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py"]
---

# 界面语言配置 RPC（preferred_language）：实现深读

[功能概览](feature-locale-conf-rpc.md) · [owner 入口](_index.md)

<!-- kb:depth feature=locale-conf-rpc facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b8708ab1982bb466314be5255208433e8995772f2440fee5d2335e844ca5b919 -->
**locale.set_conf 在无 agent 客户端或旧版共享目录客户端时的本地写回分支**
在 locale.set_conf 处理回调内，若 _resolve(agent_client) 返回 None 或是旧版共享目录客户端，则调用 update_preferred_language_in_config(lang) 写回配置，成功时以 ok=True、payload={"preferred_language": lang} 响应；若写回抛异常，记录 warning 并以 ok=False、error=str(e)、code="INTERNAL_ERROR" 响应。两条路径均随后 return，不进入代理分支；仅在非本地分支才以 params={"preferred_language": lang}、req_method=ReqMethod.LOCALE_SET_CONF 调用 proxy_unary_request 转发。

来源：[jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py:L3851–L3865](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py#L3851-L3865)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":3865,"path":"jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py","sha256":"81426fdfbb6cce64840ecd6071d47ef151246e02027a6387a76cdd3fd683a2e9","start":3851}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=locale-conf-rpc facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=042682f6c4c75fab1ece0038eb149c7c3fc678b78b95344392c1989d4b0f6b39 -->
**locale.set_conf requires a dict params object with a string preferred_language; non-dict gets BAD_REQUEST**
_locale_set_conf rejects params that are not a dict with channel.send_response(ok=False, error="params must be object", code="BAD_REQUEST") and returns; it then reads params.get("preferred_language") and guards that it is a str. _locale_get_conf/set_conf share the web-handler callback signature (ws, req_id, params, session_id, user_id=None).

来源：[jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py:L3824–L3836](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py#L3824-L3836)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":3836,"path":"jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py","sha256":"07dcae7a50a7f9da034146b4a41ab1332338dc6963910a97dfb23b379801c2e3","start":3824}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=locale-conf-rpc facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=11845ed6135e37fdf9b593c1e847f60577493acaa2f1b8b7e1ff23533a7f575d -->
**Local-branch language default is "zh" via cfg.get("preferred_language") or "zh", lowercased and stripped**
In the local/legacy branch of _locale_get_conf, a missing or falsy preferred_language in get_config() yields "zh" after strip().lower() normalization; this default applies only to that branch, not the proxied AgentServer path.

来源：[jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py:L3803–L3807](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py#L3803-L3807)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":3807,"path":"jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py","sha256":"878af6a3895a4e58179b792046a7323a7acea9729b1842f515a10aa38b2d8c58","start":3803}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=locale-conf-rpc facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ab04003c88905cac2862f672c0275fbd52e7ddd8aa13edbf682a405aff7c64f8 -->
**Handlers couple to e2a_proxy (proxy_unary_request, is_legacy_shared_directory_client) and ReqMethod.LOCALE_GET_CONF**
Both locale handlers import proxy_unary_request from jiuwenswarm.gateway.routing.e2a_proxy inside the callback; get_conf also imports is_legacy_shared_directory_client to route legacy shared-directory clients to the local config read instead of the AgentServer proxy.

来源：[jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py:L3795–L3807](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py#L3795-L3807), [jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py:L3824–L3836](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py#L3824-L3836)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":3807,"path":"jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py","sha256":"b3698023a1fae737d60ef79f660e5d9dbdf4afa521b5f85e67e825431e9dc38e","start":3795},{"end":3836,"path":"jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py","sha256":"07dcae7a50a7f9da034146b4a41ab1332338dc6963910a97dfb23b379801c2e3","start":3824}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=locale-conf-rpc facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8d7a17bd10ffbed3150f98ca2994ddd199622e76a56431e3b81b1cfeb319f7f5 -->
**Non-dict params to locale.set_conf return ok=False with error "params must be object" and code BAD_REQUEST**
The guard `if not isinstance(params, dict)` sends the error response and returns from the handler; no downstream proxy call or config write occurs on that branch. The shown lines do not cover the non-string preferred_language branch's response.

来源：[jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py:L3832–L3836](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py#L3832-L3836)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":3836,"path":"jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py","sha256":"1b0965091c2570f88f656590417ae33742be481599d9d24b596ba72b900e46e0","start":3832}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=locale-conf-rpc facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a6a82c5dc6eb17f5f637be92f8316c9eda4a172f8a34429e5b4814eeb8f4212a -->
**get_conf dual paths: local fallback defaults to "zh", proxy path forwards to AgentServer (inferred pros and cons)**
设计推断（非作者历史意图）：

When resolved_client is None or a legacy client, _locale_get_conf reads preferred_language from local get_config() and normalizes it with `or "zh"` then strip().lower() as a fallback; on the non-local path, it is forwarded as an empty params via ReqMethod.LOCALE_GET_CONF. Inferred benefit: legacy/single-machine deployments can still obtain a language configuration with a default value; cost: the same RPC has two language value sources (local config.yaml vs AgentServer), and maintenance needs to be synchronized.

来源：[jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py:L3795–L3807](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py#L3795-L3807), [jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py:L3818–L3822](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py#L3818-L3822)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":3807,"path":"jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py","sha256":"b3698023a1fae737d60ef79f660e5d9dbdf4afa521b5f85e67e825431e9dc38e","start":3795},{"end":3822,"path":"jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py","sha256":"a1d256c85bfe861958821c424274ea3189def2293eac3b2761147272577dd67d","start":3818}],"trace":[]} -->
<!-- /kb:depth -->
