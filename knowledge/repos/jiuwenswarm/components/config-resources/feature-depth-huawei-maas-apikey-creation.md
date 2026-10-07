---
title: "华为云 MaaS API Key 自动创建与捕获（auto_create_apikey）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py:L380-L406, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py:L380-L397, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py:L234-L260, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py:L371-L377, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py:L353-L370, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/huawei_selectors.py:L459-L467, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py:L363-L370]
feature: "huawei-maas-apikey-creation"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py", "jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/huawei_selectors.py"]
---

# 华为云 MaaS API Key 自动创建与捕获（auto_create_apikey）：实现深读

[功能概览](feature-huawei-maas-apikey-creation.md) · [owner 入口](_index.md)

<!-- kb:depth feature=huawei-maas-apikey-creation facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d6879f6b1a2235de4e2b107752773e2c45371129c3fd3eba898a0291deb9a7ab -->
**main 解析参数后连接 CDP 浏览器并逐步创建、捕获 Key**
main 解析 --cdp-url/--tag/--description/--timeout/--json；cdp_url 为空时回退 resolve_cdp_url()，仍为空则输出失败 JSON 并 return 1。否则调用 auto_create_apikey 并 output_json(result)，按 result.get("ok") 返回 0 或 1（main 的返回值，非本片段可证的进程退出码）。

来源：[jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py:L380–L406](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py#L380-L406)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":406,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py","sha256":"32f29e233dbc4936daf5e0384ff313f0b7e55d59556cb0ac2d36a71f27f74722","start":380}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=huawei-maas-apikey-creation facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ccfdfea12140fd39adb7d24add7798ac8561aea4ae3590bf76653b1e65feadde -->
**main 的 CLI 契约：--tag 默认 jiuwenswarm、--cdp-url 空时回退 resolve_cdp_url()，按 ok 返回 0/1**
main 接受 --cdp-url（默认空）、--tag（默认 "jiuwenswarm"）、--description（默认 "jiuwenswarm-config"）、--timeout（默认 30 秒）与 --json 标志；cdp_url 为空时调用 resolve_cdp_url() 解析，仍无则输出 make_failure("init", "未找到 CDP URL") 并 return 1。成功路径 auto_create_apikey 返回 make_success("apikey", ..., api_key, tag, description, dialog_closed)，main 输出 JSON 并 return 0 if result.get("ok") else 1。

来源：[jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py:L380–L406](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py#L380-L406), [jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py:L363–L370](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py#L363-L370)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":406,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py","sha256":"32f29e233dbc4936daf5e0384ff313f0b7e55d59556cb0ac2d36a71f27f74722","start":380},{"end":370,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py","sha256":"d4379aa74ed40e9bbc752df0c3b09d22838bb305405b2e4bd8c70d64ab06a672","start":363}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=huawei-maas-apikey-creation facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d2e0b00912cce32860bce43738ac5baab4e145cc5d309b63f1426b3530ae5774 -->
**CLI 默认值：tag=jiuwenswarm、description=jiuwenswarm-config、timeout=30 秒**
argparse 定义 --cdp-url 默认空串（空时回退 resolve_cdp_url()）、--tag 默认 "jiuwenswarm"、--description 默认 "jiuwenswarm-config"、--timeout 默认 30（单步超时秒数）、--json 布尔开关。这些是本函数内的参数默认值，未在片段中显示更外层配置优先级。

来源：[jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py:L380–L397](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py#L380-L397)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":397,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py","sha256":"bf0b5eb59b745dc048734397e93f38dbbbf588db32d5153f04690feee7345f09","start":380}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=huawei-maas-apikey-creation facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=26d4dff10c1bac02d6e6c42468a52b4188aea8e469c33cc87bf824c152968250 -->
**连接/导航/按钮缺失各自短路为结构化失败，异常统一兜底**
connect_page 抛异常时 return make_failure("connect_failed", …)；goto 失败 return make_failure("navigate_failed", …)；创建按钮 15s 内未找到则带 page_url 与 page_text_preview 返回 make_failure("create_btn_not_found", …)；步骤中任意未预期异常被外层 except 捕获返回 make_failure("exception", …)，finally 中 best-effort pw.stop()。

来源：[jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py:L234–L260](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py#L234-L260), [jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py:L371–L377](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py#L371-L377)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":260,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py","sha256":"4e07bb70236198409252c5553e13bd305d33b78698a167625752f3877d5080a4","start":234},{"end":377,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py","sha256":"176b2933cc2ea9f4ef1cb818243dec4e354cef73a61f9a3cded3eba9aa2d35b8","start":371}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=huawei-maas-apikey-creation facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=58d7d30ea6afa7331c0df1033a7c53d030b93f44fbad0b5d618cf160602d1b31 -->
**复制按钮 best-effort：不阻塞成功路径，但复制可能静默失败**
设计推断（非作者历史意图）：

成功捕获 Key 后 click_copy_key_button(page) 在 huawei_selectors 中 try 内 3s 等待可见并点击，任何异常返回 False；主流程仅 emit 记录，仍继续返回 make_success（dialog_closed 单独记录）。推断：收益是复制失败不影响 Key 捕获结果，代价是用户剪贴板可能没有该 Key 而流程不报错。

来源：[jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py:L353–L370](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py#L353-L370), [jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/huawei_selectors.py:L459–L467](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/huawei_selectors.py#L459-L467)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":370,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py","sha256":"ca7c7e5e635fa691bc0b0703095c27893a7fa7a3b36082d33e607be7cad34595","start":353},{"end":467,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/huawei_selectors.py","sha256":"cedc9766a29e8e4be7172a722bc36955647aff3aba4c38875f53ee3b7c94021c","start":459}],"trace":[]} -->
<!-- /kb:depth -->
