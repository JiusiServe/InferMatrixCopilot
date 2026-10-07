---
title: "IM Attachment Persist Hook (E2A + HTTP Bridge)：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/channel/test_attachment_persist.py:L39-L46, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/channel/test_attachment_persist.py:L113-L122, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/channel/test_attachment_persist.py:L40-L46, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/channel/test_attachment_persist.py:L220-L234, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/channel_manager.py:L255-L262, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/channel/test_attachment_persist.py:L93-L109, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/channel/test_attachment_persist.py:L184-L199, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/channel_manager.py:L255-L264, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/channel_manager.py:L260-L262, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/channel/test_attachment_persist.py:L227-L234, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/channel_manager.py:L177-L180]
feature: "im-attachment-persist-hook-969909e1"
entry_points: ["jiuwenswarm/gateway/channel_manager/channel_manager.py"]
source_globs: ["jiuwenswarm/gateway/channel_manager/channel_manager.py"]
---

# IM Attachment Persist Hook (E2A + HTTP Bridge)：实现深读

[功能概览](feature-im-attachment-persist-hook-969909e1.md) · [owner 入口](_index.md)

<!-- kb:depth feature=im-attachment-persist-hook-969909e1 facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=af516605131887956b474cb98aab2da19ea750ac0e3ba8890245ce800b68d5ee -->
**Hook contract: async (content, category, filename) returning a dict with path/name/size/mime_type**
The wired hook is awaited as hook(b"x", "images", "a.png") and returns a dict whose keys include path, name, size, mime_type; FeishuFileService exposes set_persist_hook to install it, and the service's _persist_downloaded_file uses it.

来源：[tests/unit_tests/channel/test_attachment_persist.py:L39–L46](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/channel/test_attachment_persist.py#L39-L46), [tests/unit_tests/channel/test_attachment_persist.py:L113–L122](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/channel/test_attachment_persist.py#L113-L122)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":46,"path":"tests/unit_tests/channel/test_attachment_persist.py","sha256":"42c1cb68edb441f8d367059c42ae62af8520717e4551c155040aae2bb624bfe8","start":39},{"end":122,"path":"tests/unit_tests/channel/test_attachment_persist.py","sha256":"52fe97bee7480d5ecf1e1f190e1be863614658dc88e1d9d69face86092720f14","start":113}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-attachment-persist-hook-969909e1 facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8def56194a57d8dfb57fe06ea116a83d79052ac4abe3b2349d0fb02d009858a1 -->
**Hook channel_id defaults to "im" when platform is falsy**
Within the shown hook body, channel_id is passed as `platform or "im"` with label "im.file_persist"; no other setting or precedence is visible in the offered lines.

来源：[jiuwenswarm/gateway/channel_manager/channel_manager.py:L255–L262](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/channel_manager.py#L255-L262)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":262,"path":"jiuwenswarm/gateway/channel_manager/channel_manager.py","sha256":"3de39998f59f8b3845ca8e870ff2f4830e348fe68655caada2d99513b4b2b35d","start":255}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-attachment-persist-hook-969909e1 facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7d4d9f4c4707884a753ff1831d987b7e71c8f95094e2a916437291dff010f92c -->
**Large attachments routed to HTTP bridge instead of base64 E2A: avoids frame limit, adds failing upload step**
设计推断（非作者历史意图）：

Inference from the tests' docstrings: attachments larger than E2A_PAYLOAD_MAX_BYTES are uploaded via the authenticated HTTP bridge rather than base64-in-E2A to stay under the internal WS ~8MB frame limit (benefit), at the cost of an extra network step whose failure raises and fails the whole message as retryable (per decision D6 docstring) rather than degrading to inline delivery.

来源：[tests/unit_tests/channel/test_attachment_persist.py:L93–L109](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/channel/test_attachment_persist.py#L93-L109), [tests/unit_tests/channel/test_attachment_persist.py:L184–L199](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/channel/test_attachment_persist.py#L184-L199)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":109,"path":"tests/unit_tests/channel/test_attachment_persist.py","sha256":"036eb6b225f93aff88a04dfcccabfc2e4c821a5113747ada5ec4753cd54a8fed","start":93},{"end":199,"path":"tests/unit_tests/channel/test_attachment_persist.py","sha256":"58d25ef52d99c221588c55a41488ed205796aafa0d94e1ffb02641e59d960dea","start":184}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-attachment-persist-hook-969909e1 facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a9d2cb556408be8db021dbfdef6d8b1d3e9ff1363776f5aaaf00687507d41c56 -->
**Runtime tests: hook failure raises AttachmentPersistError; AgentOS hook raises RuntimeError on user_id gap**
test_persist_hook_failure_raises_attachment_persist_error installs a failing hook and asserts pytest.raises(AttachmentPersistError) around _persist_downloaded_file; test_agentos_attachment_never_falls_back_to_gateway_workspace asserts channel.hook is not None and pytest.raises(RuntimeError, match="authenticated AgentOS user_id") on hook(b"x", "images", "a.png"). Not executed here.

来源：[tests/unit_tests/channel/test_attachment_persist.py:L40–L46](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/channel/test_attachment_persist.py#L40-L46), [tests/unit_tests/channel/test_attachment_persist.py:L220–L234](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/channel/test_attachment_persist.py#L220-L234)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":46,"path":"tests/unit_tests/channel/test_attachment_persist.py","sha256":"2bf5ffb9dc9c62147f0754f75cef87ed8794fb41007afc648aee5668723de416","start":40},{"end":234,"path":"tests/unit_tests/channel/test_attachment_persist.py","sha256":"ef851f945072dfe849c2f555206b549b621f271fad75a5c132ab4c79bcfdbbac","start":220}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-attachment-persist-hook-969909e1 facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0bc08656fc0fd0c8941330dda14e513867a4e9ede0e4d17e0010fdbb96ad3fc2 -->
**_persist_hook local branch: labeled call, RuntimeError on not-ok, returns payload, installed via setter**
在 _persist_hook 的可见分支中，以 session_id=None、user_id=None、channel_id=platform 或 "im"、label="im.file_persist" 发起调用；若返回 not ok 则 raise RuntimeError(error 或回退 "im.file_persist failed")，否则返回 payload，最后经 setter(_persist_hook) 安装。调用目标与赋值语句不在片段内，不作断言。

来源：[jiuwenswarm/gateway/channel_manager/channel_manager.py:L255–L264](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/channel_manager.py#L255-L264)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":264,"path":"jiuwenswarm/gateway/channel_manager/channel_manager.py","sha256":"917b1499aee67c391a4025de22cc784779d178231ffd37cd54ca0bfb3ef08972","start":255}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-attachment-persist-hook-969909e1 facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=73aaed72f7d38eca1facd809a7a6eae913e15280eb78b859653950fba4ebcb9c -->
**not-ok 分支抛 RuntimeError 且错误文案回退到 "im.file_persist failed"**
当调用返回 ok=False 时，_persist_hook 抛出 RuntimeError，消息取 payload.get("error")，取不到则回退为 "im.file_persist failed"；该分支在片段内即结束执行（局部 return 不发生）。测试侧另构造带 agent_client=object() 的 manager 并调用 _try_wire_file_persist_hook 后，断言 hook 抛出匹配 "authenticated AgentOS user_id" 的 RuntimeError；该测试的 client 判定条件未在片段内展示。

来源：[jiuwenswarm/gateway/channel_manager/channel_manager.py:L260–L262](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/channel_manager.py#L260-L262), [tests/unit_tests/channel/test_attachment_persist.py:L227–L234](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/channel/test_attachment_persist.py#L227-L234), [jiuwenswarm/gateway/channel_manager/channel_manager.py:L177–L180](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/channel_manager.py#L177-L180)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":262,"path":"jiuwenswarm/gateway/channel_manager/channel_manager.py","sha256":"ed0b7beffe21be26851488f00dabb062481057e1592bac904d0e4500e91c9613","start":260},{"end":234,"path":"tests/unit_tests/channel/test_attachment_persist.py","sha256":"fde30c3e541cdfa9a2756da7bfa98e9c05989f07c99ecfbf0a8bb4d7e9a1ec60","start":227},{"end":180,"path":"jiuwenswarm/gateway/channel_manager/channel_manager.py","sha256":"c114b01655c55b28ce5e50acd76daf24f91c702725ec665ba66da26686cb17b2","start":177}],"trace":[]} -->
<!-- /kb:depth -->
