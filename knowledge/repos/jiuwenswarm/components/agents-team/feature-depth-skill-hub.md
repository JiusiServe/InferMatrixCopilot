---
title: "Skill Hub 与市场流通：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/marketplace/hub_client.py:L220-L245, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/marketplace/hub_client.py:L45-L54, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/marketplace/hub_models.py:L163-L177]
---

# Skill Hub 与市场流通：实现深读

[功能概览](feature-skill-hub.md) · [owner 入口](_index.md)

<!-- kb:depth feature=skill-hub facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5690fb62640ef30007b78c75d14371ef8f8f6c48927e0a8a04e7e2eb35353527 -->
**get_plugin 到 HubPage.from_payload 的解析链**
HubClient.get_plugin 以 asset_id 为输入：清洗参数后通过 HubTransport.get_data 请求 /api/v1/plugins，把返回 payload 交给 HubPage.from_payload 解析；解析得到的分页对象再由调用方按 asset_id 精确匹配，命中则返回 HubCatalogItem，未命中抛 HubNotFoundError。

调用路径：`jiuwenswarm/server/runtime/marketplace/hub_client.py`（`HubClient.get_plugin`） → `jiuwenswarm/server/runtime/marketplace/hub_models.py`（`HubPage.from_payload`）

来源：[jiuwenswarm/server/runtime/marketplace/hub_client.py:L220–L245](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/marketplace/hub_client.py#L220-L245), [jiuwenswarm/server/runtime/marketplace/hub_models.py:L163–L177](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/marketplace/hub_models.py#L163-L177)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/server/runtime/marketplace/hub_client.py","start":220,"end":245,"sha256":"666cc4280235e2fb610db80a0032cfe3fd90b9ba428487d3ea89f1d7ee93e2ed"},{"path":"jiuwenswarm/server/runtime/marketplace/hub_models.py","start":163,"end":177,"sha256":"330b9fbc6744d52d34aea19855d0f493df4435ca9758ae655ef93bd7b3188517"}],"trace":[{"path":"jiuwenswarm/server/runtime/marketplace/hub_client.py","symbol":"HubClient.get_plugin","start":220,"end":245},{"path":"jiuwenswarm/server/runtime/marketplace/hub_models.py","symbol":"HubPage.from_payload","start":163,"end":177}]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skill-hub facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=71fcb2eecf96293bd1c99dd3eef8f1a90ac84b0821692686aaee2b3201f4397b -->
**HubClient.get_plugin 的精确查询契约**
调用方必须传入非空 asset_id（空白即抛 ValueError("asset_id is required")）。方法按 asset_id（可选 plugin_type）过滤首页结果并返回 asset_id 完全相等的 HubCatalogItem；页面中没有匹配项时抛 HubNotFoundError，payload 非法时抛 HubProtocolError。

来源：[jiuwenswarm/server/runtime/marketplace/hub_client.py:L220–L245](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/marketplace/hub_client.py#L220-L245)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/server/runtime/marketplace/hub_client.py","start":220,"end":245,"sha256":"666cc4280235e2fb610db80a0032cfe3fd90b9ba428487d3ea89f1d7ee93e2ed"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skill-hub facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=837dee9dee6344a956bd35783e549b35241e762d96562dcd197ab321beb52e77 -->
**Hub 默认地址与不安全 HTTP 开关**
默认 Hub 地址为 DEFAULT_HUB_BASE_URL = "https://swarmskills.openjiuwen.com"，默认超时 60.0 秒。环境变量 TEAM_SKILLS_HUB_ALLOW_INSECURE_HTTP 默认关闭，仅当值（去空白并小写后）属于 {"1","true","yes","on","enabled"} 时 _allow_insecure_http 才返回真。

来源：[jiuwenswarm/server/runtime/marketplace/hub_client.py:L45–L54](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/marketplace/hub_client.py#L45-L54)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/server/runtime/marketplace/hub_client.py","start":45,"end":54,"sha256":"b5712e504fdf8ddacaffdbb6fe95c4d6d750505b8f8ed71208ab1515259d923a"}],"trace":[]} -->
<!-- /kb:depth -->
