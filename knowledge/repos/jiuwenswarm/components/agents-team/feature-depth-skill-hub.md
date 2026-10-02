---
title: "Skill Hub 与市场流通：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/marketplace/hub_client.py:L220-L245, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/marketplace/hub_client.py:L45-L54, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/marketplace/hub_models.py:L163-L177, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/test_hub_catalog_cache.py:L76-L84, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/test_hub_catalog_cache.py:L275-L281, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/server/marketplace/test_hub_publish_client.py:L366-L375, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/marketplace/hub_client.py:L176-L184, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/marketplace/hub_publish_client.py:L26-L27, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/marketplace/hub_client.py:L108-L147]
feature: "skill-hub"
entry_points: ["jiuwenswarm/server/runtime/marketplace/hub_client.py"]
source_globs: ["jiuwenswarm/server/runtime/marketplace/hub_client.py", "jiuwenswarm/server/runtime/marketplace/*"]
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

<!-- kb:depth feature=skill-hub facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6df7528a41910e2325738b424e4cfc662fceceb2220c7106a749570649ee9086 -->
**读路径不阻塞换来的代价是冷启动与分页期间数据不完整**
设计推断（非作者历史意图）：

选择：读取不等刷新完成，loader 在后台任务中分页拉取，read 立即返回旧快照或 miss。收益：测试中上游 post 被 gate 阻塞时，handle_skills_swarm_skills_hub_recommend 仍在 asyncio.wait_for 的 0.05 秒内返回 state='miss'，调用方不被慢 Hub 请求卡住。代价：冷启动首个请求拿到空列表（not items 且 state['refreshing']），分页全部完成前只能看到部分条目（len(items)==2 且 has_more 为真）。该取舍为基于所引测试行为的推断，非文档记载的历史意图。

来源：[tests/test_hub_catalog_cache.py:L76–L84](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/test_hub_catalog_cache.py#L76-L84), [tests/test_hub_catalog_cache.py:L275–L281](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/test_hub_catalog_cache.py#L275-L281)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":84,"path":"tests/test_hub_catalog_cache.py","sha256":"027d479aa81734177c337287f6aa3cea8df78176411848cfb812eb54b687124a","start":76},{"end":281,"path":"tests/test_hub_catalog_cache.py","sha256":"6cd988e274dcaeedeab3d333d20f401b80016c9351754e6eb8e9114e097046a6","start":275}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skill-hub facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2f207c464c8bf559ef13d447ecd701a7e04c03097df1b01857a6ba5f645c06e5 -->
**hub_publish_client 模块级导入 hub_client 与 hub_publish_port；hub_client 仅在 publish() 的 _publisher 为空分支内按需导入 HubPublishClient**
hub_publish_client.py 在模块级从 hub_client 导入 HttpHubTransport、从 hub_publish_port 导入 parse_publish_result（L26–L27）。HubClient.publish 仅在 self._publisher is None 分支内才在函数体导入 HubPublishClient 并以 base_url=self.base_url 构造（L178–L183），之后复用该实例（L184），把这次耦合推迟到首次 publish。

来源：[jiuwenswarm/server/runtime/marketplace/hub_client.py:L176–L184](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/marketplace/hub_client.py#L176-L184), [jiuwenswarm/server/runtime/marketplace/hub_publish_client.py:L26–L27](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/marketplace/hub_publish_client.py#L26-L27)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":184,"path":"jiuwenswarm/server/runtime/marketplace/hub_client.py","sha256":"be48dd5141d4682bb3f13093d0e8a81d62b22cb0209c761980b175f9154fc3f4","start":176},{"end":27,"path":"jiuwenswarm/server/runtime/marketplace/hub_publish_client.py","sha256":"7cba6f2a0b38e9ee7247c188c8c7c053eca5acee9ee510ed8862f9adc0f1771b","start":26}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skill-hub facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=91c216f53d1a82f019291fffa036c4b09981a3f3293e34347a27c6064b899c50 -->
**HttpHubTransport.get_data：404 抛 HubNotFoundError，其余非成功状态抛携带 status_code/retry_after 的 HubProtocolError**
get_data（L108–L147，函数完整可见）在请求未抛异常后检查状态：response.status_code == 404 时抛 HubNotFoundError("SkillHub 资源不存在")（L125–L126）；not response.is_success 时抛 HubProtocolError 并设置 error.status_code 与取自 Retry-After 响应头的 error.retry_after（L127–L131）。异常直接上抛，函数内无重试。

来源：[jiuwenswarm/server/runtime/marketplace/hub_client.py:L108–L147](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/marketplace/hub_client.py#L108-L147)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":147,"path":"jiuwenswarm/server/runtime/marketplace/hub_client.py","sha256":"5f73c0d723ac3878c967525e3673f3d5168ad17d06c8d24957a332f21f20ead6","start":108}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skill-hub facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5bf3c3a8c0bc8386fa75113ded947887fa09fe0282ece4983f33c6f3909c177e -->
**发布超时 outcome_unknown 的 MockTransport 运行时测试**
test_http_request_timeout_is_uncertain 用 httpx.MockTransport 处理器返回 408，断言 HubPublishClient(...).publish(draft, auth=PublishAuth("secret")) 抛 PublishUploadError 且 exc.value.outcome_unknown 为真。

来源：[tests/unit_tests/server/marketplace/test_hub_publish_client.py:L366–L375](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/server/marketplace/test_hub_publish_client.py#L366-L375)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":375,"path":"tests/unit_tests/server/marketplace/test_hub_publish_client.py","sha256":"7efb2ca8f71a383074b263bc7a221855658a804e86c8895b26bc12b0907f93d0","start":366}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
