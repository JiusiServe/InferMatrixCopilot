---
title: "Session Share-Image Export (Job Registry + Headless Renderer)：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/share_image_export.py:L86-L98, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/share_image_export.py:L101-L117, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/app_web.py:L1226-L1232, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/share_image_export.py:L44-L52, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/share_image_export.py:L210-L210, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/share_image_export.py:L69-L98, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/channels/web/test_share_image_export.py:L614-L625, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/channels/web/test_share_image_export.py:L525-L531, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/channels/web/test_share_image_export.py:L516-L522, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/share_image_export.py:L196-L208, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/share_image_export.py:L212-L235, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/shareImageExport.tsx:L1466-L1478]
feature: "share-image-export"
entry_points: ["jiuwenswarm/channels/web/frontend/vite.config.ts", "jiuwenswarm/channels/web/share_image_export.py"]
source_globs: ["jiuwenswarm/channels/web/frontend/vite.config.ts", "jiuwenswarm/channels/web/share_image_export.py", "jiuwenswarm/channels/web/frontend/src/features/shareImageExport.tsx", "jiuwenswarm/channels/web/frontend/src/features/shareImageArchive.ts", "jiuwenswarm/channels/web/frontend/src/features/shareImageExport.css", "jiuwenswarm/channels/web/app_web.py", "jiuwenswarm/channels/web/frontend/src/features/shareImageJob.ts", "jiuwenswarm/channels/web/frontend/src/features/shareImagePng.worker.ts", "jiuwenswarm/channels/web/frontend/src/features/shareImagePngEncoder.ts", "jiuwenswarm/channels/web/frontend/src/App.tsx", "jiuwenswarm/channels/web/frontend/src/main.tsx", "jiuwenswarm/channels/web/frontend/src/features/shareImageRaster.ts"]
---

# Session Share-Image Export (Job Registry + Headless Renderer)：实现深读

[功能概览](feature-share-image-export.md) · [owner 入口](_index.md)

<!-- kb:depth feature=share-image-export facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6af69cca82435ad50f77b69a793a350f41b5bf37bef3b21df19c8fbebc09613a -->
**render_share_image keyword-only contract with module-level timeout defaults, returns Path**
render_share_image 仅接受关键字参数：必需的 base_url、job_id、output_path（Path），可选 on_phase 回调、render_auth，以及四个超时/轮询参数（init_timeout_seconds、idle_timeout_seconds、absolute_timeout_seconds、poll_interval_seconds），默认值取模块常量 _RENDER_*；函数返回 Path。

来源：[jiuwenswarm/channels/web/share_image_export.py:L196–L208](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/share_image_export.py#L196-L208)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":208,"path":"jiuwenswarm/channels/web/share_image_export.py","sha256":"9b77f7cec2597ad5557ff6cbea536e6fbadab56411ec6756679c9cbcf00f947f","start":196}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=share-image-export facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4d813925e00ffc803d2d170bc27009f54c1f344ccf6b1154a80edbf5fa22fd65 -->
**Browser config: browser_type defaults to "auto" mapping to chrome channel; missing executable path errors**
_configured_browser resolves the first non-blank configured path key, raises RuntimeError configured_share_export_browser_not_found if that path is not a file, and browser_type (default "auto", lowercased) maps to channel "msedge" only for {msedge, edge, microsoft-edge, microsoft_edge}, otherwise "chrome"; executable_path defaults to None when unset.

来源：[jiuwenswarm/channels/web/share_image_export.py:L86–L98](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/share_image_export.py#L86-L98)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":98,"path":"jiuwenswarm/channels/web/share_image_export.py","sha256":"13f32906e9d017c4b77dfd5e6876d7fbe1f13538c4f65ade9d90ca4956052ee1","start":86}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=share-image-export facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=53bfc359f6342dcaec99b0f9dcb3e61900930ed1f1c540ad62ff32de3eda377e -->
**render_share_image lazily imports playwright.sync_api and couples browser launch to config-resolved chrome_path/browser_type**
playwright.sync_api is imported inside render_share_image's body, so the function depends on Playwright only when invoked. _configured_browser reads resolve_env_vars(get_config())['browser'], maps a dict chrome_path by platform key (else 'default'), raises RuntimeError "configured_share_export_browser_not_found" when a resolved path is not an existing file, and derives channel "msedge" only for edge-like browser_type values, otherwise "chrome"; a missing/empty path returns (None, channel), so no executable is mandatory here.

来源：[jiuwenswarm/channels/web/share_image_export.py:L210–L210](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/share_image_export.py#L210-L210), [jiuwenswarm/channels/web/share_image_export.py:L69–L98](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/share_image_export.py#L69-L98)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":210,"path":"jiuwenswarm/channels/web/share_image_export.py","sha256":"9250d0b9d61a8647f5d5d511381e1621f75dd4349e503377abd79baa13612bf8","start":210},{"end":98,"path":"jiuwenswarm/channels/web/share_image_export.py","sha256":"4a299eb05fbc05075f426e832d99814aa524f202702305c133a20182fc9f7ad6","start":69}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=share-image-export facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2976a1e51b6129d42d10d583f37b179b78644e8aa0ce96794c7ef170503928b3 -->
**_validate_png_stream fails fast on truncated or malformed PNG chunks**
A stream smaller than signature+IEND, a mismatched signature, a short chunk header, or a chunk length exceeding the remaining bytes raises RuntimeError share_export_png_incomplete or share_export_png_invalid_signature; at the API layer, FileNotFoundError from snapshot building becomes 404 history_not_found and ValueError becomes 400 with the error string.

来源：[jiuwenswarm/channels/web/share_image_export.py:L101–L117](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/share_image_export.py#L101-L117), [jiuwenswarm/channels/web/app_web.py:L1226–L1232](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/app_web.py#L1226-L1232)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":117,"path":"jiuwenswarm/channels/web/share_image_export.py","sha256":"60ac10fd0c1ac8275f9f4bf5ef360ca40e94ea2d9ecb7bf7bdc98bf8979dc2cb","start":101},{"end":1232,"path":"jiuwenswarm/channels/web/app_web.py","sha256":"a1f5d4dc487538ce0937a4ea7ecf6a6dd33776c20714daa3cd575364383fbe77","start":1226}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=share-image-export facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=043c647cf90bb79cb3ff3a15a59f74378ec3fc5492b1523c6703e4a672a721fd -->
**ShareImageRenderAuth suppresses cookie_value from repr, hiding the desktop token at the cost of debuggability**
设计推断（非作者历史意图）：

cookie_value is declared field(repr=False) so the desktop access token never appears in the dataclass repr; the cost is that the token value cannot be inspected via repr when diagnosing auth issues (inference from the shown field declaration).

来源：[jiuwenswarm/channels/web/share_image_export.py:L44–L52](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/share_image_export.py#L44-L52)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":52,"path":"jiuwenswarm/channels/web/share_image_export.py","sha256":"42f63ff1e95b1a3ff7de2aa38f64e2590322566bcf6d61ad5e573b928b4f72f9","start":44}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=share-image-export facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=38fb91012f26ce40d066c8ce6f0a83bbc73bb1e0cbd8945dc1ce01d2382a92fe -->
**Automated runtime test asserts init-timeout failure path, secret non-disclosure and context closure in render_share_image**
test_render_runner_not_initialized_fails_within_init_timeout drives the real share_image_export.render_share_image via _call_render with a faked playwright module and _configured_browser monkeypatched to (None, "chrome"), and asserts pytest.raises(RuntimeError, match="share_export_runner_not_initialized"), elapsed < 5 seconds, "desktop-secret" absent from the exception text, and harness.context.closed.

来源：[tests/unit_tests/channels/web/test_share_image_export.py:L614–L625](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/channels/web/test_share_image_export.py#L614-L625), [tests/unit_tests/channels/web/test_share_image_export.py:L525–L531](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/channels/web/test_share_image_export.py#L525-L531), [tests/unit_tests/channels/web/test_share_image_export.py:L516–L522](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/channels/web/test_share_image_export.py#L516-L522)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":625,"path":"tests/unit_tests/channels/web/test_share_image_export.py","sha256":"d40b5abc4248dc6a257e323ee4271f93208580b6d774bcc829629bf32e83349d","start":614},{"end":531,"path":"tests/unit_tests/channels/web/test_share_image_export.py","sha256":"9827468e7f214a82cb71ef64ef2146389c0c3f649287c1f57fac9ee7249ce21d","start":525},{"end":522,"path":"tests/unit_tests/channels/web/test_share_image_export.py","sha256":"b54cff8e3ef992545ed4d4ab2e2884d42026e75455e73e1bb6b1556ef7b67fc7","start":516}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->

<!-- kb:depth feature=share-image-export facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2a8b0ada8aa734cc2b2134ddb9aaa5d6f579385daefca736e2c0a69ec477c044 -->
**render_share_image resolves browser config, then reports launching and starts headless Chromium with a 900×900 context**
在 render_share_image 内，先调用 _configured_browser()（L220），再根据 executable_path 是否为真组装 launch_options（设 executable_path，否则设 channel，且 headless: True，L221–L225），此后才执行 report("launching")（L229）——因此配置解析/失败可发生在 launching 回调之前。随后 sync_playwright 里 chromium.launch(**launch_options) 启动浏览器并 new_context(viewport 900×900, accept_downloads=True)。report 是条件回调：仅当 on_phase 非 None 时转发 phase。前端侧 ShareImageExportRunner 的 useEffect 回调先把 window.__SHARE_IMAGE_EXPORT_STATE 置为 { status: 'loading_snapshot' }，再 fetch /share-api/jobs/<jobId>/snapshot（cache: 'no-store'）。

来源：[jiuwenswarm/channels/web/share_image_export.py:L212–L235](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/share_image_export.py#L212-L235), [jiuwenswarm/channels/web/frontend/src/features/shareImageExport.tsx:L1466–L1478](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/shareImageExport.tsx#L1466-L1478)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":235,"path":"jiuwenswarm/channels/web/share_image_export.py","sha256":"555eb8491a05368951ba3ee1bdf271b3aebbf685e53465b604804c9b2bfbdd66","start":212},{"end":1478,"path":"jiuwenswarm/channels/web/frontend/src/features/shareImageExport.tsx","sha256":"c79b67941a448b2841b07c66aa960d13f5f86751d9ef727f731a8343cc24bc41","start":1466}],"trace":[]} -->
<!-- /kb:depth -->
