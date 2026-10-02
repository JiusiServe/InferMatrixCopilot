---
title: "账号登录与凭据续期：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/auth/account_kit.py:L92-L99, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/华为账号登录.md:L15-L27", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/auth/model_catalog.py:L200-L252, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/gateway/test_web_http_auth_routes.py:L81-L124, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/gateway/test_web_http_auth_routes.py:L140-L152, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/gateway/test_web_http_auth_routes.py:L166-L184, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/auth/service.py:L342-L357, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/auth/account_kit.py:L265-L274, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/auth/account_kit.py:L291-L308, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/auth/service.py:L252-L267, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/华为账号登录.md:L191-L192"]
feature: "login"
entry_points: ["jiuwenswarm/common/auth/service.py"]
source_globs: ["jiuwenswarm/common/auth/service.py", "jiuwenswarm/common/auth/*.py"]
---

# 账号登录与凭据续期：实现深读

[功能概览](feature-login.md) · [owner 入口](_index.md)

<!-- kb:depth feature=login facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=baf31ae3ac6ef818dd200592854ad3cb5a8d11bd59242f94a88a777dd700d3a8 -->
**登录开关由远端配置决定**
login_enabled() 的唯一判据是 get_remote_config() 返回非 None 且 is_effective 为真；配置地址有默认值所以默认开启，把 JIUWENSWARM_CONFIG_URL 显式设为 off（或空串等）或拉不到配置即整体关闭（auth 路由 404）。

来源：[jiuwenswarm/common/auth/account_kit.py:L92–L99](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/auth/account_kit.py#L92-L99), [docs/zh/华为账号登录.md:L15–L27](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%8D%8E%E4%B8%BA%E8%B4%A6%E5%8F%B7%E7%99%BB%E5%BD%95.md#L15-L27)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/common/auth/account_kit.py","start":92,"end":99,"sha256":"2edda21cdf757b022d7e96dac26658571143bd52b1089eb052065942f7c3cafb"},{"path":"docs/zh/华为账号登录.md","start":15,"end":27,"sha256":"c181611912d83f895ad333e358f18c935445f8270348d8529c1a9d3c00f5cfe2"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=login facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=33e5ec46532bcfdfbc462751c5275b81fb612083a18004c41951c44f8d5c3f1b -->
**resolve_id_token 默认 allow_refresh=True；未登录或续期失败抛 ModelAuthRequired，非阻塞调用方须传 False**
resolve_id_token(session_id, allow_refresh=True) 返回调 APIG 用的 credential.id_token（Authorization: Bearer）；会话解析不到抛 ModelAuthRequired(not_logged_in)，ensure_fresh 返回 None 抛(session_expired)；不能阻塞的调用方须传 allow_refresh=False，续期改后台做。

来源：[jiuwenswarm/common/auth/service.py:L342–L357](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/auth/service.py#L342-L357)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":357,"path":"jiuwenswarm/common/auth/service.py","sha256":"f9aaaa8b424107847203b72b8c3e56a2c179dbc312a1d176baa9adaf6eff1588","start":342}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=login facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8b714d3e226306ce5cc3d6b7ec81b781805d69ca99f4efc78aee741046b972d7 -->
**get_models 受 get_remote_config 的 is_effective 门控；memo 新鲜度同时看 TTL 与缓存文件 mtime**
get_models 先读 get_remote_config(allow_refresh)，config 为 None 或 is_effective=false 时直接返回 []，docstring 言明 models.list、模型缓存与请求级凭据透传等下游同受此门控；进程内 memo 命中还需缓存文件 mtime 未变，否则经 _read_cache 重读磁盘（注释：Gateway 写缓存、AgentServer 另一进程要读到）。

来源：[jiuwenswarm/common/auth/model_catalog.py:L200–L252](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/auth/model_catalog.py#L200-L252)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":252,"path":"jiuwenswarm/common/auth/model_catalog.py","sha256":"9cb2f384ccedd8d50f963c04addeced9fcba321d841ce697f9e01de273b1aa19","start":200}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=login facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0f698159fd1210bfdb3af9e53ef4f93e6692a2a49ad78cd6e44c0a9bdeedf4c6 -->
**begin_callback：记录仍在且 callback_seen=True 抛 oauth_callback_replayed（不删记录）；无记录（含被 claim 弹出或过期清理）抛 oauth_state_invalid**
锁内查 _items：state 无记录（含 claim 成功后弹出、_prune 过期清理）抛 OAuthError(oauth_state_invalid)；记录存在且 callback_seen=True 抛 OAuthError(oauth_callback_replayed)，此分支不弹出记录，异常直接传给调用方。

来源：[jiuwenswarm/common/auth/account_kit.py:L265–L274](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/auth/account_kit.py#L265-L274), [jiuwenswarm/common/auth/account_kit.py:L291–L308](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/auth/account_kit.py#L291-L308)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":274,"path":"jiuwenswarm/common/auth/account_kit.py","sha256":"2243bd68d4e6b2d5781c98ca27bf587dfaaa2905490aa53dc593236ccb18fe5e","start":265},{"end":308,"path":"jiuwenswarm/common/auth/account_kit.py","sha256":"781e69537a65aa6b398e9354dce81fdb34718cf805104538e9f27aabb8af7dad","start":291}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=login facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=21290e06e5225bf9f4741458e5b3166311ee0dbb442f3c7618ba176c1bbb8c63 -->
**按 user_id 进程内锁合并同账号并发续期：省重复刷新但同账号需排队（推断）**
设计推断（非作者历史意图）：

try_refresh 按 user_id 取进程内 threading.Lock，同账号并发续期合并成一次；推断收益：省重复刷新请求，且华为不轮换 refresh_token、并发刷新不互废；推断代价：同账号调用排队等一次同步续期，合并仅限本进程，跨进程靠持锁后重读会话（按 mtime）发现。

来源：[jiuwenswarm/common/auth/service.py:L252–L267](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/auth/service.py#L252-L267), [docs/zh/华为账号登录.md:L191–L192](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%8D%8E%E4%B8%BA%E8%B4%A6%E5%8F%B7%E7%99%BB%E5%BD%95.md#L191-L192)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":267,"path":"jiuwenswarm/common/auth/service.py","sha256":"b3adec69ba7c4e36df9df6cbe405e122b6872b2f456b4ae077f175dd3ffa22b0","start":252},{"end":192,"path":"docs/zh/华为账号登录.md","sha256":"6295d842574b1c70f13d41048a1f261b24152d7b85aa53b52810ae707b2737ea","start":191}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=login facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8a523e02f34be5e5633ccfeb4ec523e3874597127a85f95be98e7a5a6b82adbc -->
**TestClient 上的 authorize→callback→claim 全链路测试，逐条断言三态与落地页安全头**
client fixture 对注册了 auth 路由的 FastAPI 实例构造 TestClient（默认带 X-Jiuwen-Auth 头）；test_full_login_flow 依次断言回调前 claim 为 202、落地页 200 且 Set-Cookie 含 jiuwenswarm_auth、cache-control 为 no-store、认领 200 并以 X-Auth-Session 返回会话 id、再次 claim 为 400。此处描述测试代码及其断言本身。

来源：[tests/unit_tests/gateway/test_web_http_auth_routes.py:L81–L124](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/gateway/test_web_http_auth_routes.py#L81-L124), [tests/unit_tests/gateway/test_web_http_auth_routes.py:L140–L152](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/gateway/test_web_http_auth_routes.py#L140-L152), [tests/unit_tests/gateway/test_web_http_auth_routes.py:L166–L184](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/gateway/test_web_http_auth_routes.py#L166-L184)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":124,"path":"tests/unit_tests/gateway/test_web_http_auth_routes.py","sha256":"4b4d4eb1bbf86fa88d53b7987cd2e174f0dab9501d6af67b73e966653009be3d","start":81},{"end":152,"path":"tests/unit_tests/gateway/test_web_http_auth_routes.py","sha256":"1f9ad4b68272e58a6c7d78ee9b5c8d1d002e4101dbcdd56154c309ef4e5fe8c5","start":140},{"end":184,"path":"tests/unit_tests/gateway/test_web_http_auth_routes.py","sha256":"23d869d885962c7b6a9bd70f5fce0f8072394e3983425d91dfc4bd1e1ca1ab57","start":166}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
