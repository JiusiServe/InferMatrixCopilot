---
title: "华为云 MaaS 委托授权自动化（auto_authorize）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py:L98-L133, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py:L135-L205, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py:L215-L234, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py:L98-L104, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/cdp_client.py:L195-L228, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py:L100-L104, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py:L68-L95, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py:L114-L124, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py:L215-L230, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py:L98-L112, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py:L135-L176, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py:L179-L212, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/flow_state.py:L9-L17, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/SKILL.md:L285-L309]
feature: "huawei-maas-cdp-authorize"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py"]
---

# 华为云 MaaS 委托授权自动化（auto_authorize）：实现深读

[功能概览](feature-huawei-maas-cdp-authorize.md) · [owner 入口](_index.md)

<!-- kb:depth feature=huawei-maas-cdp-authorize facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a01f37c2dd0ff5b030f57997b0978bde018a541f9c4f50589fc15c44967022b7 -->
**auto_authorize 连接 CDP 后按固定步骤检测并完成授权**
auto_authorize 经 connect_page 连接浏览器（timeout_ms=15_000），page.goto 导航到 MAAS_HOMEPAGE_URL（timeout=30_000），sleep 2.5s 等 SPA 渲染并 handle_disclaimer；若 _detect_auth_warning 为假则直接 make_success(auth_done=False, skipped_reason="no_warning")，否则点击"此处"链接（缺失/失败时兜底点警告元素本身），等待授权对话框与"确定"按钮，最后等待成功提示并 make_success(auth_done=True)。

来源：[jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py:L98–L133](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py#L98-L133), [jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py:L135–L205](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py#L135-L205)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":133,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py","sha256":"8aebf1cbf872e0d27c9d870413788bc5e01c44e7ae96d042ee52bca31ff3a078","start":98},{"end":205,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py","sha256":"0b71b07579b22c182d5089857fc5351afa175c266960f3d057ea682f991abfad","start":135}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=huawei-maas-cdp-authorize facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d2d0b42a00039bbdf4b44f253ed5627991e9712208b9b8620569cf1d76e2ab94 -->
**main(argv) CLI 契约：--cdp-url/--timeout/--json，返回 0/1**
main 解析 --cdp-url（默认空）、--timeout（默认 45）、--json；cdp_url 为空时回退 resolve_cdp_url()，仍为空则 output_json(make_failure("init", "未找到 CDP URL")) 并返回 1；否则 auto_authorize 后 output_json(result)，按 result.get("ok") 返回 0 或 1（函数返回值，非进程退出码的直接证明）。auto_authorize(cdp_url, timeout_s=45) 对调用者返回结果 dict。

来源：[jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py:L215–L234](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py#L215-L234), [jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py:L98–L104](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py#L98-L104)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":234,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py","sha256":"2050ac050a26e4e3bf1b683df5a8b6084d605a7336f6d1cd304c920a93bed59e","start":215},{"end":104,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py","sha256":"2515714cadc33216130f43887625c888d16b79681917a596101945da9247ed48","start":98}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=huawei-maas-cdp-authorize facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bffff70280a5e468d4176267017a6d2c8dbce42c1d7bba5a41c6923f7558a76b -->
**main 的 --cdp-url 默认为空并回退 resolve_cdp_url，--timeout 默认 45 作为 auto_authorize 的 timeout_s**
--cdp-url 缺省为空字符串，strip 后为空则调用 resolve_cdp_url() 解析；仍为空时输出 make_failure("init") 且 main 局部返回 1。--timeout 缺省 45，以 timeout_s 传入 auto_authorize；连接超时为固定 15_000ms，页内各等待用的是固定毫秒值。

来源：[jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py:L215–L230](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py#L215-L230), [jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py:L98–L104](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py#L98-L104)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":230,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py","sha256":"994df1dbef23e61d40375ae5d3ea903b08d23739fce6d68b7975833e3a1621d8","start":215},{"end":104,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py","sha256":"2515714cadc33216130f43887625c888d16b79681917a596101945da9247ed48","start":98}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=huawei-maas-cdp-authorize facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=71658f355f59ce5c061abdeb8bd90703177b60f1a8978b92af0ec96357c04c56 -->
**惰性导入 playwright 并经 connect_over_cdp 复用首个 context 的已有 page**
import_playwright 惰性导入 playwright.sync_api，ImportError 时抛 RuntimeError 附安装指引（不需 playwright install）。connect_page 用 chromium.connect_over_cdp 连接，无 context 时抛 RuntimeError；默认 new_page=False 复用 context.pages[0]，无 page 才新建，并 set_default_timeout(timeout_ms)。auto_authorize 以默认 new_page=False 调用，故操作复用浏览器默认 context 的现有 page。

来源：[jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/cdp_client.py:L195–L228](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/cdp_client.py#L195-L228), [jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py:L100–L104](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py#L100-L104)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":228,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/cdp_client.py","sha256":"dc9e09cd335510dd2db393adbb815d56d96531bb75ed6bbb3ba59d7bf7a8e56a","start":195},{"end":104,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py","sha256":"c81d3caa64d36d5df4179cbebfe913fcf8d26a1c2131b57f4300c6cf5acfa89b","start":100}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=huawei-maas-cdp-authorize facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a4dce2abc9fee953433574aff222e8ecc79634e7c455c9d7b985ddc2461aa7e2 -->
**auto_authorize 各失败分支返回 make_failure 载荷而非抛出，finally 中 pw.stop 异常被吞掉**
在 auto_authorize 局部分支中，连接失败返回 stage="connect_failed"、导航失败 "navigate_failed"、对话框 10s 未现为 "dialog_timeout"、确定按钮未点为 "confirm_not_found"、成功提示 15s 未现为 "success_timeout"、其余异常为 "exception"；均经 make_failure 构造 dict 返回。finally 里 pw.stop() 失败仅 debug 日志。注意：'此处'点击失败且兜底 warning 为 None 时不返回，继续等待对话框。

来源：[jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py:L98–L112](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py#L98-L112), [jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py:L135–L176](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py#L135-L176), [jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py:L179–L212](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py#L179-L212), [jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/flow_state.py:L9–L17](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/flow_state.py#L9-L17)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":112,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py","sha256":"a155e8866e374028355f68ef77f6672eb59b8a06a226f081188a233e785fa66e","start":98},{"end":176,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py","sha256":"b915a2ecb2f8adaece4220339d814ec76cf581b56b8d28e8f2b7d4607eee021f","start":135},{"end":212,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py","sha256":"db426fa6ff0c95366a6d05c5f40ca9be0df6af471ffe74dc6d98e649283be422","start":179},{"end":17,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/flow_state.py","sha256":"05311fcb94baefb213deae5de4cf0446fddbd90d66d2c21d6ece0b016cd93c8f","start":9}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=huawei-maas-cdp-authorize facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c146b010b466c71df3582a1953088e828995dd991a23245ccc0997b12f90a706 -->
**两级检测 + 固定 sleep 换取稳态判定**
设计推断（非作者历史意图）：

（推断）_detect_auth_warning 先查 #authGlobalMessage 容器、容器缺失/不可见时退化为警告选择器快照并按关键词匹配，容错 DOM 变化但可能误判（如 inner_text 异常时直接返回 True，85-92 行）；授权流程多处固定 time.sleep(2.5/1.5/1.0) 等 SPA 渲染与动画，稳定性换来了最坏情况下不必要的等待时长。

来源：[jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py:L68–L95](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py#L68-L95), [jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py:L114–L124](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py#L114-L124)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":95,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py","sha256":"57a1f94f1c9ebf43a83fc616f0aace7f8bb0ce8dbdb95aac7a247815c8472403","start":68},{"end":124,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py","sha256":"9e007f11bac211e5edec88169b8643c6ba2e5844cc058e767c2b628bb8d0acd2","start":114}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=huawei-maas-cdp-authorize facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e5e752a208091cc89221f3e5b8fdfa0370f7ad85cf23f718aa5501365d3aa5ff -->
**SKILL.md 记录的手动验证流程（未执行）**
文档中的人工验收步骤（本轮未执行）：

文档化手动流程，未执行：依次运行 navigate.py 与 auto_authorize.py --json --cdp-url <CDP_URL>，期望输出形如 {"ok": true, "stage": "authorize", "auth_done": false, "skipped_reason": "no_warning", ...} 或 auth_done=true 且 disclaimer_handled=true；失败降级为提示用户手动完成委托授权后重试。此处仅为文档示例，非已运行断言。

来源：[jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/SKILL.md:L285–L309](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/SKILL.md#L285-L309)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":309,"path":"jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/SKILL.md","sha256":"8d9a112da4bee4753cc3bddc300431eaaf94de21d0cd98fb8127a0556b693483","start":285}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
