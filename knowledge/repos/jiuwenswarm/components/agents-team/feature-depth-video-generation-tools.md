---
title: "generate_video / check_video_status Submit-then-Poll Video Generation：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L240-L264, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L285-L319, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L199-L207, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L233-L238, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L240-L245, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L256-L264, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L287-L297, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L318-L319, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L211-L222, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L199-L199, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agents/test_video_gen_tools.py:L16-L21, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agents/test_video_gen_tools.py:L339-L349, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agents/test_video_gen_tools.py:L276-L278, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L352-L359, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L285-L287, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L37-L39]
feature: "video-generation-tools"
entry_points: ["jiuwenswarm/agents/harness/common/tools/video_gen_tools.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/video_gen_tools.py", "jiuwenswarm/agents/harness/common/tools/gen_toolkits.py"]
---

# generate_video / check_video_status Submit-then-Poll Video Generation：实现深读

[功能概览](feature-video-generation-tools.md) · [owner 入口](_index.md)

<!-- kb:depth feature=video-generation-tools facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=06c66c5e47d20b571fe50930492f77d6cc2c8c7ff64585b08f841db4a00000bf -->
**generate_video 默认分支：提交 POST {api_base}/videos 后轮询，完成则下载**
先取凭证并校验 prompt（video_gen_tools.py:240-248）；detect_backend 无匹配时走默认 OpenRouter 风格分支：POST {api_base}/videos（287），非 200/201/202 即返回错误，否则取 job id 后经 _poll_job 轮询（301），completed 才调 _download_video（317），未到终态则返回含 job_id 的提示（306-310）。

来源：[jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L240–L264](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/video_gen_tools.py#L240-L264), [jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L285–L319](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/video_gen_tools.py#L285-L319)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":264,"path":"jiuwenswarm/agents/harness/common/tools/video_gen_tools.py","sha256":"1328f88c69727608d47773f858cd0f1e9d29849bea715cfd961d6042d3de6532","start":240},{"end":319,"path":"jiuwenswarm/agents/harness/common/tools/video_gen_tools.py","sha256":"5696a7a7b189fc2bb778b507b3eecb6776abd08cdeaa22554f80532fe94088eb","start":285}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=video-generation-tools facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=35a086cf7e83da82193520358d86018c331c247232504663cf0a3efed11dac08 -->
**generate_video 工具签名：扁平参数，默认 16:9 / 480p / 15 秒，返回 str**
签名为 prompt（必填 str）、aspect_ratio="16:9"、resolution="480p"、duration_seconds=15、first_frame_path=None、generate_audio=False、save_dir=None；返回文件路径字符串，或轮询窗口结束后仍运行时返回 job_id + 状态消息（docstring 236-238）。

来源：[jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L199–L207](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/video_gen_tools.py#L199-L207), [jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L233–L238](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/video_gen_tools.py#L233-L238)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":207,"path":"jiuwenswarm/agents/harness/common/tools/video_gen_tools.py","sha256":"0a4b011699805180b358db7b3de382dd3ed637a5f0bbe1a878a5e2c5d5bbf489","start":199},{"end":238,"path":"jiuwenswarm/agents/harness/common/tools/video_gen_tools.py","sha256":"71a6263814d81ae57444e3182e69973d69bd2f3514beaa188d3ebb3ab9e794cd","start":233}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=video-generation-tools facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=925c06a29c980640273e2f52cfcb2e3fcc0c3fac688b4ef5e9e36331a99ca3cd -->
**凭证缺失时直接报错；后端由 VIDEO_GEN_PROTOCOL + api_base 探测分流**
凭证来自 _get_video_gen_api_credentials()，api_key/api_base/model 任一缺失即返回 "[ERROR]: video generation is not configured - set the Video processing API key, API URL, and model name..."（240-245）；随后 detect_backend("VIDEO_GEN_PROTOCOL", api_base) 命中时把请求转给 gen_toolkits.submit_video（258-264），否则走内置 /videos 协议。

来源：[jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L240–L245](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/video_gen_tools.py#L240-L245), [jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L256–L264](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/video_gen_tools.py#L256-L264)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":245,"path":"jiuwenswarm/agents/harness/common/tools/video_gen_tools.py","sha256":"27f002ccd88869178bcbe78cc472a7140615ecc5617a90b8fa003464f60f161f","start":240},{"end":264,"path":"jiuwenswarm/agents/harness/common/tools/video_gen_tools.py","sha256":"48dce185d4509f953574487bdda2d50f2b57ab3f561fe0a775f95f75dffa1fb5","start":256}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=video-generation-tools facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=61056aefbe104720a31d907c8ea8e15202806d24a8897daa9d7e3af9a4fd9622 -->
**check_video_status backend branch delegates to gen_toolkits.check_video before its default httpx client**
When `backend` is truthy, check_video_status builds a gen_toolkits.GenerationTarget and returns `await gen_toolkits.check_video(target, job_id, save_dir)` at video_gen_tools.py:352-354, so that branch never reaches the module's own httpx client. The non-backend poll path instead constructs httpx.AsyncClient(timeout=30, verify=get_requests_verify()) (356-359), coupling its TLS verification to ssl_config.get_requests_verify; generate_video's submit uses the same verify helper with timeout=60 (285-287).

来源：[jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L352–L359](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/video_gen_tools.py#L352-L359), [jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L285–L287](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/video_gen_tools.py#L285-L287), [jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L37–L39](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/video_gen_tools.py#L37-L39)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":359,"path":"jiuwenswarm/agents/harness/common/tools/video_gen_tools.py","sha256":"fc54a7463c7d6dbea19d398f432c02591079645c1c4356217e9cfce0fbe86f5e","start":352},{"end":287,"path":"jiuwenswarm/agents/harness/common/tools/video_gen_tools.py","sha256":"8d9334872bbe01774bbe35a7ff0de0cd8faa735ed539d9372516f9af25c3e061","start":285},{"end":39,"path":"jiuwenswarm/agents/harness/common/tools/video_gen_tools.py","sha256":"ed40dec8e2a8ca5c3982efdc6241032949dffefdccbadadcd00447ad1d49bdd4","start":37}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=video-generation-tools facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=03067eb4af84dc2d80341fbb459aa1acb3ae8691508d7d4c323b1c1bf60a7863 -->
**提交阶段四类失败均以 [ERROR] 字符串返回，不抛出**
非 200/201/202 → "[ERROR]: video generation submit failed: {status} {text}"（288-289）；JSON 解析失败 → "...invalid JSON: {exc!r}"（290-293）；缺 job id → "...returned no job id"（294-296）；httpx.HTTPError 被 except 捕获 → "[ERROR]: video generation request failed: {exc!r}"（318-319）。

来源：[jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L287–L297](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/video_gen_tools.py#L287-L297), [jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L318–L319](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/video_gen_tools.py#L318-L319)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":297,"path":"jiuwenswarm/agents/harness/common/tools/video_gen_tools.py","sha256":"784783d6c5920862df5690adddc303767ce4f24bc3e85d80b25a22ec625fe354","start":287},{"end":319,"path":"jiuwenswarm/agents/harness/common/tools/video_gen_tools.py","sha256":"ff16857152a63c5ceda28a7bc01a20e37b6ef1c33520db9e50a0444a76dc1f2f","start":318}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=video-generation-tools facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=578f26448fa7e0c10b6a68b32db5513e833aa1bf4e87cd5120a0fd4b1f84f3e2 -->
**刻意保留扁平参数而非 BaseModel，换取 LLM 可见的工具 schema**
设计推断（非作者历史意图）：

docstring 自述：CallableSchemaExtractor 对 dataclass 只生成无属性的 {"type":"object"}，BaseModel 虽可展开但会把顶层扁平参数改成嵌套对象、是对已验证工具的行为变更，故扁平签名是有意保留（211-222）。收益是模型能看到全部字段；成本是参数数量触发 pylint huawei-too-many-arguments 豁免（199）。此为基于 docstring 的推断。

来源：[jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L211–L222](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/video_gen_tools.py#L211-L222), [jiuwenswarm/agents/harness/common/tools/video_gen_tools.py:L199–L199](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/video_gen_tools.py#L199-L199)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":222,"path":"jiuwenswarm/agents/harness/common/tools/video_gen_tools.py","sha256":"98554fd96b51d34aef6c2d218a114ee704541e2feadda53124d91e3004d56e96","start":211},{"end":199,"path":"jiuwenswarm/agents/harness/common/tools/video_gen_tools.py","sha256":"c935f6b682c456c5020bed0cf9b775a93f9669c03a91b2ba84e69df4f0b63c1a","start":199}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=video-generation-tools facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1d333668a3c4afac7d882aad3427ec02050c5e7276f31b4c0403199834bf4bab -->
**单测直接调用 vg.generate_video._func，经 mock httpx 传输断言错误字符串**
测试取 @tool 包装内的原始异步函数（test 文件 16-21），如 test_generate_video_http_error_during_submit_is_caught 断言 ConnectError 时返回以 "[ERROR]: video generation request failed:" 开头的字符串（339-349），400 提交断言完整错误串（276-278）。

来源：[tests/unit_tests/agents/test_video_gen_tools.py:L16–L21](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agents/test_video_gen_tools.py#L16-L21), [tests/unit_tests/agents/test_video_gen_tools.py:L339–L349](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agents/test_video_gen_tools.py#L339-L349), [tests/unit_tests/agents/test_video_gen_tools.py:L276–L278](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agents/test_video_gen_tools.py#L276-L278)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":21,"path":"tests/unit_tests/agents/test_video_gen_tools.py","sha256":"2510d6956f2e306677db396b4a4346e8db6e6effb8aa1fb81d023c944dd92024","start":16},{"end":349,"path":"tests/unit_tests/agents/test_video_gen_tools.py","sha256":"41919db192dce366975313b74d79eddd9c140dee54f3f25e2eefd5d2d9484219","start":339},{"end":278,"path":"tests/unit_tests/agents/test_video_gen_tools.py","sha256":"edf124db47b4c3c2f1a4da767173dcfd80486dca148607ff890b7a44cdc8470e","start":276}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
