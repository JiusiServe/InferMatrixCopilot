---
title: "Web Page Scraping to Unified Stage01 Blocks：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py:L820-L880, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py:L820-L876, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py:L885-L895, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py:L825-L835, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py:L718-L757, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py:L977-L986, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py:L969-L987, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py:L753-L757, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/SKILL.md:L89-L113]
feature: "skill-page-scrape-blocks"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py", "jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/print_blocks.py", "jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/common.py", "jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/download_images.py", "jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/environment_gate.py"]
---

# Web Page Scraping to Unified Stage01 Blocks：实现深读

[功能概览](feature-skill-page-scrape-blocks.md) · [owner 入口](_index.md)

<!-- kb:depth feature=skill-page-scrape-blocks facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2ca28231f6b3d7cdca92c341aca8516d5107ccac2d15f763af27ccd48cc53920 -->
**scrape_page_playwright: headless Chromium fetch of the exact URL, parse, dedupe, conditional platform-URL prepend**
scrape_page_playwright launches headless Chromium, scrapes one page, and parses html into blocks only when html is non-empty; image blocks are deduplicated by URL keeping first occurrence, video_urls deduplicated, and page_url inserted at index 0 only if is_platform_url(page_url) and it is not already in video_urls. Returns (deduped, video_urls, page_title).

来源：[jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py:L820–L876](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py#L820-L876)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":876,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py","sha256":"6503979778a587be2eb38ad35044fc8c997d7b901022ceef9afc4e8176a41319","start":820}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skill-page-scrape-blocks facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2bd2dd6ee32575822bfa61e7eb6f068a4c18bd79645d98ec71df7a74af9aa8d2 -->
**scrape_page wraps the async Playwright path synchronously**
scrape_page(url: str) -> tuple[list[dict], list[str], str] returns asyncio.run(scrape_page_playwright(url)); the async function imports playwright.async_api locally and its docstring states it scrapes only the exact URL supplied, never following page links. Callers get unified blocks, video URLs, and the page title.

来源：[jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py:L820–L880](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py#L820-L880)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":880,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py","sha256":"d7c983fbda05d21bf29431f2ba4e845f5eba6e884cc5cd3ff78558a2e58336ee","start":820}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skill-page-scrape-blocks facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a367416739504f854f4c3d5a1512f4e5555ad403b0ea9f2c8c7cb53505cca2e4 -->
**main() argparse defaults: optional url/slug, --out default None, --check-deps flag**
main() declares url with nargs="?" (optional), slug nargs="?" default None, --out default None, and boolean --check-deps described as running the shared environment gate with auto-repair then exiting; the shown slice ends at parse_args() so downstream handling of these values is not visible here.

来源：[jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py:L885–L895](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py#L885-L895)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":895,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py","sha256":"cd6a91b62a68f32ff233ea1cfa6c4884b7ae23f087dc2d2ac0ea5a3244b7263f","start":885}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skill-page-scrape-blocks facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0cc7d35db2a2bb45bf0dcdf622bf7587b5972c38fc3034351131f49c16aeaa24 -->
**scrape_one_page requires a caller-supplied Playwright page and common module constants**
scrape_one_page(page, page_url, dismiss_cookie=False) 接收外部传入的 Playwright page：先 add_init_script 注入 canvas 文本补丁，再用 page.goto(page_url, wait_until="commit", timeout=common.PAGE_LOAD_TIMEOUT_SECONDS * 1000) 导航，超时常量来自共享 common 模块。主流程随后依赖 build_bounded_stage01_payload 与 common.write_json 落盘 stage01。

来源：[jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py:L718–L757](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py#L718-L757), [jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py:L977–L986](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py#L977-L986)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":757,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py","sha256":"25c2cd648157311fa492019390a9bebddf958c6576174ea11f80d06c62b1c1e9","start":718},{"end":986,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py","sha256":"895e785fcd1451615e3aec42631fa2d46c449585f69e23ab2a46f16f0473ead3","start":977}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skill-page-scrape-blocks facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1d86e93ed344bf9facc96dfc5496dd26c5a96324aff5cf4d1ed0288ce1fe4b25 -->
**Empty or marker-blocked blocks only log a warning and still write a bounded stage01 payload**
在主流程中，当 blocks 为空或（无图片块且正文命中 _blocked_markers）时，仅输出两条 logger.warning（含用 web_fetch_webpage 兜底的提示），不抛错；随后仍构造 build_bounded_stage01_payload 并 common.write_json 写出 stage01，limits 来自 payload["content_limits"]。另外 scrape_one_page 内 resp.status >= 400 有显式判断分支入口（其后续语句未在展示范围内）。

来源：[jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py:L969–L987](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py#L969-L987), [jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py:L753–L757](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py#L753-L757)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":987,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py","sha256":"a4e53baf7ae4b52dc944d46b72cbdae90693eda33c2457275e45f8c69b7c761f","start":969},{"end":757,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py","sha256":"b89d9f480550f0d01b67bbc7b462414b87ff98a900792cd3fb64e21b88d3296f","start":753}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skill-page-scrape-blocks facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=36006a1ce776045012c2e311270340418049822a05ef7c99551cfb8b16629d13 -->
**Chromium launch flags trade HTTP/2 for fingerprint compatibility (inference from in-code comment)**
设计推断（非作者历史意图）：

The browser is launched with --disable-http2 alongside --no-sandbox and related flags; the code comment states some sites reject Playwright's H2 fingerprint with ERR_HTTP2_PROTOCOL_ERROR. Inference: forcing HTTP/1.1 trades multiplexing performance for compatibility with such sites — the benefit/cost is my reading of the comment, not a measured outcome.

来源：[jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py:L825–L835](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py#L825-L835)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":835,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py","sha256":"740b9b988e9757f8f90ca2364df343206a0440270be2e8f2cf7e40d6de19ca33","start":825}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skill-page-scrape-blocks facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=97ef61a583486e7a427d05b0a15f3bb2aeb52168a921142f49c79585ab61df47 -->
**Documented manual procedure for scrape_page.py to stage01.json (not executed)**
文档中的人工验收步骤（本轮未执行）：

SKILL.md documents a manual invocation `{python} scripts/scrape_page.py <URL> <slug>` with expected result `work/<slug>/stage01.json` containing url, slug, title, blocks (heading/text/image with source field) and video_urls, and that video-platform URLs (Bilibili/YouTube/Vimeo/Xiaohongshu) yield blocks=[] plus video_urls=[url]. This is a documented procedure only — NOT EXECUTED here, and it asserts no automated test coverage over block extraction.

来源：[jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/SKILL.md:L89–L113](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/SKILL.md#L89-L113)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":113,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/SKILL.md","sha256":"8d277fa0061004d40a80d449c4356e885acc8455b55d3ec578468991fab6a895","start":89}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
