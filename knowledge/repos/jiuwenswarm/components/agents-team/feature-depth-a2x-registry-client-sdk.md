---
title: "A2X Registry Client SDK — mirrored sync/async service registry client：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/a2x/client/client.py:L515-L530, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/a2x/client/client.py:L99-L107, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/a2x/client/async_client.py:L256-L281, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/a2x/client/async_client.py:L58-L60, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/a2x/client/client.py:L365-L388, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_a2x_client_init.py:L272-L308]
feature: "a2x-registry-client-sdk"
entry_points: ["jiuwenswarm/agents/harness/team/a2x/client/__init__.py", "jiuwenswarm/agents/harness/team/a2x/client/async_client.py", "jiuwenswarm/agents/harness/team/a2x/client/client.py"]
source_globs: ["jiuwenswarm/agents/harness/team/a2x/client/__init__.py", "jiuwenswarm/agents/harness/team/a2x/client/async_client.py", "jiuwenswarm/agents/harness/team/a2x/client/client.py", "jiuwenswarm/agents/harness/team/a2x/client/_internal.py", "jiuwenswarm/agents/harness/team/a2x/client/errors.py", "jiuwenswarm/agents/harness/team/a2x/client/models.py", "jiuwenswarm/agents/harness/team/a2x/client/transport.py", "jiuwenswarm/agents/harness/team/a2x/client/ownership.py"]
---

# A2X Registry Client SDK — mirrored sync/async service registry client：实现深读

[功能概览](feature-a2x-registry-client-sdk.md) · [owner 入口](_index.md)

<!-- kb:depth feature=a2x-registry-client-sdk facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a9c664f661da5cc0c1e2670e8fd4327008503dc38afe9cbc468021e33a7e8e48 -->
**Sync restore_to_blank for an owned agent: resolve endpoint, build blank card, replace card**
After the _assert_owned guard passes, _resolve_endpoint supplies the endpoint, build_blank_agent_card builds the card, and replace_agent_card overwrites the service; the docstring notes L3 raises ValueError when neither the L1 cache nor the current card yields an endpoint.

来源：[jiuwenswarm/agents/harness/team/a2x/client/client.py:L365–L388](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/a2x/client/client.py#L365-L388)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":388,"path":"jiuwenswarm/agents/harness/team/a2x/client/client.py","sha256":"ef94c706bded1ba198460558221e9f06aaebc6cc69573513133237dec3d28824","start":365}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=a2x-registry-client-sdk facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d075fbd3ecf87972dd3be1c704c24a7bf7d6c8ecbe9cbb74cf4697f73b2e2577 -->
**release_my_lease：本地 _assert_owned 授权后 DELETE 租约路径，幂等返回 bool**
同步 A2XRegistryClient.release_my_lease(dataset, service_id) 先 _assert_owned（只能释放自己注册的 sid），随后 DELETE _i.service_lease_path(dataset, service_id)，按响应 JSON 的 "released" 返回 bool；无租约时返回 False 而不报错。

来源：[jiuwenswarm/agents/harness/team/a2x/client/client.py:L515–L530](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/a2x/client/client.py#L515-L530)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":530,"path":"jiuwenswarm/agents/harness/team/a2x/client/client.py","sha256":"8d1c592568b4634adccf30b99e4a26f6a7b8a76f639ff6b53f5503ba9e79712d","start":515}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=a2x-registry-client-sdk facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=228294a69951e4128fb2b4028b2acbb9403251020199867d46ece709fd3eb68a -->
**create_dataset 的 embedding_model 默认取 _i.DEFAULT_EMBEDDING_MODEL**
A2XRegistryClient.create_dataset 的 embedding_model 参数默认值为 _internal.DEFAULT_EMBEDDING_MODEL，formats 默认 _i.UNSET；调用方未传时 body 由 _i.build_create_dataset_body 用这些默认值构造，POST 到 _i.DATASETS_ROOT。

来源：[jiuwenswarm/agents/harness/team/a2x/client/client.py:L99–L107](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/a2x/client/client.py#L99-L107)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":107,"path":"jiuwenswarm/agents/harness/team/a2x/client/client.py","sha256":"f36b02434955856fcb970abd5bd67445cc179af16985cd6d0a41cd9bda576798","start":99}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=a2x-registry-client-sdk facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=322793360a88a804dadcefcbc9d632cff751f9081a22f5e900d9f264d3a03578 -->
**replace_agent_card 遇 NotFoundError：清本地 owned/blank_endpoints 后原样上抛**
异步 replace_agent_card 在 POST a2a_register_path 抛 NotFoundError 时，await to_thread 移除 owned 条目并 pop _blank_endpoints 缓存，然后 re-raise；而 release_lease=True 时 release_my_lease 抛 A2XConnectionError/ServerError/NotFoundError 只 warnings.warn（租约靠 TTL 过期），注册结果仍正常返回。

来源：[jiuwenswarm/agents/harness/team/a2x/client/async_client.py:L256–L281](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/a2x/client/async_client.py#L256-L281)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":281,"path":"jiuwenswarm/agents/harness/team/a2x/client/async_client.py","sha256":"b753825418675949e72c40afa8460e238648606479f9d706e9c724701c125578","start":256}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=a2x-registry-client-sdk facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=02f4012ae89bb32430b7d2af97b2231bd374a2fb272cfef77cab794cb10a89d8 -->
**Async client keeps _blank_endpoints cache lock-free, relying on event-loop serialization**
设计推断（非作者历史意图）：

Benefit (inference): the pure in-memory dict avoids per-access locking overhead. Cost: correctness depends on the event loop serializing access, per the code comment — the stated rationale is local to this implementation.

来源：[jiuwenswarm/agents/harness/team/a2x/client/async_client.py:L58–L60](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/a2x/client/async_client.py#L58-L60)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":60,"path":"jiuwenswarm/agents/harness/team/a2x/client/async_client.py","sha256":"f417f4059490123c392d7a06271ac9f1eef2d2266625140984760bf7b412fe5e","start":58}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=a2x-registry-client-sdk facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4834c7f1dff71022dbfb234a67c32eebd79505f2d1f208217b157acc54fe0713 -->
**Runtime helper test asserts blank-card replacement via a faked SDK client, not the real client**
test_teammate_destroy_restore_replaces_agent_card monkeypatches sys.modules so AsyncA2XRegistryClient is _FakeAsyncA2XRegistryClient, then asserts restore_teammate_blank_agent_on_destroy returns True, one client instance exists, closed is True, and card_replacements records dataset "team_pool", service_id "blank-service-id", a blank card with description "__BLANK__" and release_lease True. This validates the runtime helper against a mock; the real SDK's replace path is not exercised. NOT EXECUTED here.

来源：[tests/unit_tests/agentserver/test_a2x_client_init.py:L272–L308](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/test_a2x_client_init.py#L272-L308)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":308,"path":"tests/unit_tests/agentserver/test_a2x_client_init.py","sha256":"9d7dfd3717eaecaf2f57bd9b04de4c9845cacc739c30da26d2487ffb3c23e9a0","start":272}],"trace":[],"validation_kind":"helper_unit"} -->
<!-- /kb:depth -->
