---
title: "Application Plugin 与前端贡献：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/application_host.py:L96-L110, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/application_host.py:L70-L77, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/application_host.py:L15-L16, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/application_host.py:L30-L44, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/application-plugins.md:L47-L48, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/application_host.py:L88-L94, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/application_host.py:L18-L21]
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
