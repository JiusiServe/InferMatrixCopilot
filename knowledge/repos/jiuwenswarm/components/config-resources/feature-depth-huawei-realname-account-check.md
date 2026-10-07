---
title: "华为云账号实名认证状态检测（check_account）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py:L50-L58, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py:L110-L128, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py:L111-L126, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py:L56-L82, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py:L57-L64, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py:L97-L107, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/huawei_selectors.py:L602-L605, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/huawei_selectors.py:L561-L565, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/cdp_client.py:L195-L228, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py:L35-L47, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/SKILL.md:L193-L227]
feature: "huawei-realname-account-check"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py", "jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/huawei_selectors.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py", "jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/huawei_selectors.py"]
---

# 华为云账号实名认证状态检测（check_account）：实现深读

[功能概览](feature-huawei-realname-account-check.md) · [owner 入口](_index.md)

<!-- kb:depth feature=huawei-realname-account-check facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ab022550c3e24b2f013f23d2af1a87c18134b8216c2fc11bb99d328f254af62d -->
**check_account(cdp_url, timeout_s=15) 返回结果 dict；CLI 以退出码表达 ok**
函数签名 check_account(cdp_url: str, timeout_s: int = 15) -> dict，成功返回 make_success 附 realname_authenticated/popups_closed/realname_auth_url；main 接受 --cdp-url/--timeout/--json，cdp_url 为空时自动 resolve_cdp_url()，仍为空则输出失败 JSON 并返回 1，否则返回 0 当且仅当 result.get("ok")。

来源：[jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py:L50–L58](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py#L50-L58), [jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py:L110–L128](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py#L110-L128)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":58,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py","sha256":"0b6da5dbb383c177d66f3ae6168f0f57c63212d3652c6c34efa42d43b5e1b6b4","start":50},{"end":128,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py","sha256":"84749d5c70569b49c155b2a4ad8b379d52fdf09dc018685d8be622004ff8fc10","start":110}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=huawei-realname-account-check facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f2e2d0c5f605ec8a5279d27d66967c87ea7df04e2c42302f9a1aa91ab6977503 -->
**CLI 默认 --cdp-url 为空自动解析、--timeout 默认 15 秒**
argparse 定义 --cdp-url 默认空串（空则调 resolve_cdp_url() 自动解析）与 --timeout 默认 15；check_account 内部另将连接超时固定为 connect_page(timeout_ms=15_000)、检测超时固定为 8_000ms，不随 --timeout 改变。

来源：[jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py:L111–L126](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py#L111-L126), [jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py:L56–L82](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py#L56-L82)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":126,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py","sha256":"3b8f17827bc2590b1d34dc51a5f1ca3cc91c84f9b5ddc0ca2ace0f40ae713c06","start":111},{"end":82,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py","sha256":"30e4bb368cbd70e02617e264a08ac76e9167fa6f375334011da10a1b0b6e51df","start":56}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=huawei-realname-account-check facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ed8eb93463dc30c70397d42b8ee0e5d1db7edf06f17f057872bb0c007b1a8ec5 -->
**check_account depends on Playwright over CDP reusing the first context's existing page, with a new-page fallback; playwright must be pip-installed**
connect_page lazily imports playwright.sync_api (raising RuntimeError with an install hint if missing), connects via chromium.connect_over_cdp, raises if browser.contexts is empty, takes contexts[0] and reuses pages[0] when present else creates a page, and sets page.set_default_timeout(timeout_ms). check_account also depends on lib.huawei_selectors (dismiss_popups, detect_realname_status, HUAWEI_REALNAME_AUTH_URL) and lib.flow_state result builders.

来源：[jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/cdp_client.py:L195–L228](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/cdp_client.py#L195-L228), [jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py:L35–L47](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py#L35-L47)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":228,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/cdp_client.py","sha256":"dc9e09cd335510dd2db393adbb815d56d96531bb75ed6bbb3ba59d7bf7a8e56a","start":195},{"end":47,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py","sha256":"6f8747bdd6a2a0318cc7fdeaff67dbb501e113dccbe6be6ee0d1845ea2c1d63c","start":35}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=huawei-realname-account-check facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=67fe37a77a350efeec3f98c34c55bddd8d8ea6cdd7f6a1a7ccd90cf1a7e5bbc5 -->
**连接失败与检测异常均转为 {ok:false} 返回，不抛给上层**
connect_page 抛异常时返回 make_failure("connect_failed", ...)；检测阶段任何 Exception 返回 make_failure("exception", ...)；detect_realname_status 在 timeout_ms 内两级探测都无果时 emit 超时消息并返回 False（视为未认证兜底）；finally 中 pw.stop() 失败仅记 debug 日志。

来源：[jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py:L57–L64](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py#L57-L64), [jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py:L97–L107](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py#L97-L107), [jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/huawei_selectors.py:L602–L605](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/huawei_selectors.py#L602-L605)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":64,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py","sha256":"f555cdd09b914b348f607055af8e58ccb639bbeaa5732e8a71dc18c3a21e5381","start":57},{"end":107,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py","sha256":"0efe542572268bcda08df198c03932fee2b8b78158d7bdb87c671f1d56928f33","start":97},{"end":605,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/huawei_selectors.py","sha256":"a53662dc3933691285716e856b13ba17cd3c200a086276eae11c9a9e03136281","start":602}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=huawei-realname-account-check facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1fb794b626efdc635f0bd00282bf3ab19cc41d7fd31d10f2ee58c06a28baf228 -->
**JS 变量优先+DOM 兜底的检测换取稳定性，超时兜底偏向未认证**
设计推断（非作者历史意图）：

（推断）detect_realname_status 优先读 window.myRoleTags（不受文案/DOM 变化影响），DOM 提醒条作兜底，提高容错；代价是两级探测都未就绪时超时返回 False，即把未知状态判为未实名，可能产生误报。固定 sleep 2.0s + 弹窗关闭 sleep 也增加总时长。

来源：[jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/huawei_selectors.py:L561–L565](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/huawei_selectors.py#L561-L565), [jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/huawei_selectors.py:L602–L605](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/huawei_selectors.py#L602-L605)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":565,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/huawei_selectors.py","sha256":"56503ff21fb3e32490a53352b3bb1ce43af69ab0be23de9e4e14d4581c147fca","start":561},{"end":605,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/huawei_selectors.py","sha256":"a53662dc3933691285716e856b13ba17cd3c200a086276eae11c9a9e03136281","start":602}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=huawei-realname-account-check facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8e6312baf2136ebca14664a3c29eed7ba37ceb608d13ad81b99483fedb2e99a6 -->
**SKILL.md documents running check_account.py --json --cdp-url with expected JSON for both realname outcomes (documented procedure, NOT EXECUTED here)**
文档中的人工验收步骤（本轮未执行）：

SKILL.md step 2 gives the exact command `python <skill_dir>/scripts/check_account.py --json --cdp-url "<CDP_URL>"` and expected outputs: {"ok": true, "stage": "check_account", "realname_authenticated": true|false, "popups_closed": 1, "realname_auth_url": ...}. This is a documented manual procedure only; no automated test evidence for this feature is supplied, and nothing was executed in this batch.

来源：[jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/SKILL.md:L193–L227](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/SKILL.md#L193-L227)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":227,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/SKILL.md","sha256":"dd606b253852c40ac631d770297079f3f704564c31a0fbe2016464c571a68959","start":193}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
