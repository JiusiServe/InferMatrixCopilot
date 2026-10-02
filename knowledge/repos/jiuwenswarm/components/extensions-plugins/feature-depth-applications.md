---
title: "Application Plugin 与前端贡献：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/application_host.py:L96-L110, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/application_host.py:L70-L77, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/application_host.py:L15-L16, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/application_host.py:L30-L44, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/application-plugins.md:L47-L48, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/application_host.py:L88-L94, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/application_host.py:L18-L21, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/test_application_plugins.py:L168-L178, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/test_application_plugins.py:L193-L207, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/test_application_plugins.py:L77-L83, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/test_application_plugins.py:L140-L153, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/sdk/application_plugin.py:L107-L112, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/sdk/application_plugin.py:L128-L131]
feature: "applications"
entry_points: ["jiuwenswarm/extensions/application_host.py"]
source_globs: ["jiuwenswarm/extensions/application_host.py"]
---

# Application Plugin 与前端贡献：实现深读

[功能概览](feature-applications.md) · [owner 入口](_index.md)

<!-- kb:depth feature=applications facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4719025e1d85b63427193257166a3bc19188ec5e5f7c778ce2d4923a436d2876 -->
**资产路由契约**
GET /api/application-plugins/{plugin_id}/assets/{asset_path:path} 要求 registry 中存在该插件（_plugin_or_404，否则 HTTP 404 "application plugin not found"），且 plugin.frontend_asset_root() 非 None；命中时返回 FileResponse(target) 并带 Cache-Control: no-cache 头。调用方只需给出插件 id 与相对资产路径，宿主负责把路径限制在 resolve 后的 asset root 内。

来源：[jiuwenswarm/extensions/application_host.py:L96–L110](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/application_host.py#L96-L110), [jiuwenswarm/extensions/application_host.py:L70–L77](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/application_host.py#L70-L77)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/extensions/application_host.py","start":96,"end":110,"sha256":"f9718d0555173fe1a6617f9ca6c926b0a2906e5d75b535903e51698756843851"},{"path":"jiuwenswarm/extensions/application_host.py","start":70,"end":77,"sha256":"f50b2bbc0d8f83caf19397ce56bff1e0b5f65ec6ccecd72ecc9b4a97047f9617"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=applications facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9b24181e4ad256429dc28cefd83fa348ba6c01f5f98f03df825f518eeccbf09a -->
**API 前缀与贡献默认值**
HTTP 前缀由常量 APPLICATION_PLUGIN_API_PREFIX = "/api/application-plugins" 固定，两条路由（清单与资产）都基于它拼接。无前端贡献的插件在清单中合成 id 为 "{plugin_id}:management" 的条目，render_mode="none"、position=1000；文档声明 nav_key/render_mode/entrypoint/position 缺省分别为 app:{plugin_id}、iframe、index.html、100。

来源：[jiuwenswarm/extensions/application_host.py:L15–L16](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/application_host.py#L15-L16), [jiuwenswarm/extensions/application_host.py:L30–L44](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/application_host.py#L30-L44), [docs/zh/application-plugins.md:L47–L48](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/application-plugins.md#L47-L48)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/extensions/application_host.py","start":15,"end":16,"sha256":"e8ed030d195b55e257bfc30fd26e43e3817135544ef51627192210cc1740095a"},{"path":"jiuwenswarm/extensions/application_host.py","start":30,"end":44,"sha256":"27329838e0abdf4494ae516bc082070adf739e4a0f9923804848ec719a5debd5"},{"path":"docs/zh/application-plugins.md","start":47,"end":48,"sha256":"1642b5b1fb0485a41293824323566020e47a30411fdccb5b13cf45282be8b37f"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=applications facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fe1181d3cf5f3149e6ae085264cdea7c4910d88d965c7d4e7e5dfc2549a0b33a -->
**对 FastAPI 与 ExtensionRegistry 的耦合**
mount_application_plugin_http_routes 直接接收 FastAPI 实例并通过 @app.get 注册路由，说明应用插件的 HTTP 面完全寄生在宿主 Web 框架上；插件列表本身来自 ExtensionRegistry.get_application_plugins()，registry 为 None 时 _plugins 返回空元组，清单退化为 {"api_version": 1, "plugins": []} 而不是报错。

来源：[jiuwenswarm/extensions/application_host.py:L88–L94](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/application_host.py#L88-L94), [jiuwenswarm/extensions/application_host.py:L18–L21](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/application_host.py#L18-L21)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/extensions/application_host.py","start":88,"end":94,"sha256":"5b60cad833dadfd0b9e4cbcc43bf8fdec4fdbdfcdaa46f225d9ac3bb6c7b7ed1"},{"path":"jiuwenswarm/extensions/application_host.py","start":18,"end":21,"sha256":"460494a8416a7d656ce4c3bfc5736cf9ca6693ebad8a2f236d546f1d9cd71654"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=applications facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=84c0d1ae2a7efc4b232df74ad8dae67f37b23f74b6cc1ce7be5f34af3ebe3d46 -->
**测试内 manifest-only 插件经 ExtensionLoader 注册后由资产路由返回 index.html**
测试在 tmp_path 写入 extension.yaml 与 frontend/dist/index.html 后，await ExtensionLoader(registry).load_extension(root) 为真且 registry.get_application_plugin("hello-plugin") 非空；manifest 首条 entry_url 以 /hello-plugin/assets/index.html 结尾，TestClient GET 该 URL 返回 200 与文件原文。

来源：[tests/unit_tests/test_application_plugins.py:L168–L178](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/test_application_plugins.py#L168-L178), [tests/unit_tests/test_application_plugins.py:L193–L207](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/test_application_plugins.py#L193-L207), [jiuwenswarm/extensions/application_host.py:L96–L110](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/application_host.py#L96-L110)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":178,"path":"tests/unit_tests/test_application_plugins.py","sha256":"35106dad3fa85f6b268fdab927eebd765244154f43351d4a90e097c92f80af86","start":168},{"end":207,"path":"tests/unit_tests/test_application_plugins.py","sha256":"5d370e20f91e99f33d9d6689d82580c98ea978b603b8b3b686ad2ddd69fcf209","start":193},{"end":110,"path":"jiuwenswarm/extensions/application_host.py","sha256":"f9718d0555173fe1a6617f9ca6c926b0a2906e5d75b535903e51698756843851","start":96}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=applications facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=77d19ba77c5773594e170848b9cdd45e89f7f4ff6c451f0aa474a2ce8cdae001 -->
**禁用插件的方法按注册时 available_when_disabled 区分错误码与放行**
enabled=False 的 _TestPlugin 经 registry.bind_application_plugins(channel) 绑定后，调用绑定产物 example.ping 返回 code="APPLICATION_PLUGIN_DISABLED"；注册时带 available_when_disabled=True 的 example.settings 仍返回 payload={"settings": true}。两个方法均以 local_only=True 注册。

来源：[tests/unit_tests/test_application_plugins.py:L77–L83](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/test_application_plugins.py#L77-L83), [tests/unit_tests/test_application_plugins.py:L140–L153](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/test_application_plugins.py#L140-L153)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":83,"path":"tests/unit_tests/test_application_plugins.py","sha256":"dc8fc03086c5d6db3dfd58e29dbd624b5eda95ee6536f2b3376bbf945ea51e63","start":77},{"end":153,"path":"tests/unit_tests/test_application_plugins.py","sha256":"df9335037ecfba58f0d164710ac49e442b5cd40d0ef75a04c37f9b0b4b086148","start":140}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=applications facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f3010d37be5b04d14664c64caa44411d2582adb87b4e080090f7d109a13736f0 -->
**Manifest-only 插件以仅限 iframe 换取无需 Python 后端**
设计推断（非作者历史意图）：

设计推断：收益是 ManifestApplicationPlugin 面向无需 Python 后端的预构建 iframe 应用、由 loader 自动创建注册（类 docstring 自述）；代价是其 frontend render_mode 非 iframe 即 raise ValueError("manifest-only application plugins support iframe frontends only")。

来源：[jiuwenswarm/extensions/sdk/application_plugin.py:L107–L112](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/sdk/application_plugin.py#L107-L112), [jiuwenswarm/extensions/sdk/application_plugin.py:L128–L131](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/sdk/application_plugin.py#L128-L131)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":112,"path":"jiuwenswarm/extensions/sdk/application_plugin.py","sha256":"88b6eea934068709f3c49825a6efe0d459ed6546ae336e390d47b2a101c1f1c9","start":107},{"end":131,"path":"jiuwenswarm/extensions/sdk/application_plugin.py","sha256":"8e7bb16d5328efadb1ff1aaa6ae996fb6ecf16f7c61c9387f0ff278f2481854b","start":128}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=applications facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dcee578de72fddae66f64793d54bed6de6ab33264a08d93e1e8ad868c89e7a50 -->
**自动化运行时测试断言禁用门禁与 available_when_disabled 放行**
test_registry_binds_local_methods_and_blocks_disabled_plugins 用真实 ExtensionRegistry 注册并绑定 enabled=False 插件，断言 channel.local_only == {"example.ping", "example.settings"}、responses[0]["code"] == "APPLICATION_PLUGIN_DISABLED" 且 responses[1]["payload"] == {"settings": true}。

来源：[tests/unit_tests/test_application_plugins.py:L77–L83](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/test_application_plugins.py#L77-L83), [tests/unit_tests/test_application_plugins.py:L140–L153](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/test_application_plugins.py#L140-L153)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":83,"path":"tests/unit_tests/test_application_plugins.py","sha256":"dc8fc03086c5d6db3dfd58e29dbd624b5eda95ee6536f2b3376bbf945ea51e63","start":77},{"end":153,"path":"tests/unit_tests/test_application_plugins.py","sha256":"df9335037ecfba58f0d164710ac49e442b5cd40d0ef75a04c37f9b0b4b086148","start":140}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
