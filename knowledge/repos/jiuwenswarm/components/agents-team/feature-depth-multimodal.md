---
title: "多模态理解与媒体配置：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/multimodal_config.py:L233-L282, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/multimodal_config.py:L185-L230, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/image_tools.py:L89-L93, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/image_tools.py:L167-L233, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/image_tools.py:L15-L25, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/image_tools.py:L150-L161, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/image_tools.py:L210-L214, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/image_tools.py:L167-L171, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/image_tools.py:L218-L224, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/image_tools.py:L225-L231, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agents/test_visual_gen_tools.py:L330-L343, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/visual_gen_tools.py:L105-L132, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/visual_gen_tools.py:L136-L139]
feature: "multimodal"
entry_points: ["jiuwenswarm/agents/harness/common/tools/multimodal_config.py", "jiuwenswarm/agents/harness/common/tools/image_tools.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/multimodal_config.py", "jiuwenswarm/agents/harness/common/tools/image_tools.py", "jiuwenswarm/agents/harness/common/tools/*"]
---

# 多模态理解与媒体配置：实现深读

[功能概览](feature-multimodal.md) · [owner 入口](_index.md)

<!-- kb:depth feature=multimodal facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ff154ce22414cd58af99de2c4167d5eda0f90393a94fbc1d22b3b9df6d295525 -->
**strict 开关与三级回退优先级**
models.{model_type}.model_config 的 strict 默认为 False（_parse_bool(mc.get("strict"), default=False)）。非 strict 时按 embed.embed_api_key/embed_api_base、embed 模型名、环境变量 API_KEY/API_BASE/MODEL_NAME/MODEL_PROVIDER 逐项回退；strict 时跳过全部回退。视频类型额外将 strict 写为环境变量 VIDEO_UNDERSTANDING_STRICT="1"，且 config_base 非 dict 时会 pop 该变量。运行时 _get_vision_api_credentials 中 VISION_MODEL_NAME 缺省为 "gpt-4o"。

来源：[jiuwenswarm/agents/harness/common/tools/multimodal_config.py:L233–L282](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/multimodal_config.py#L233-L282), [jiuwenswarm/agents/harness/common/tools/multimodal_config.py:L185–L230](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/multimodal_config.py#L185-L230), [jiuwenswarm/agents/harness/common/tools/image_tools.py:L89–L93](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/image_tools.py#L89-L93)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/tools/multimodal_config.py","start":233,"end":282,"sha256":"54c0a38caea3ae1064de8af294e4c8d1c797747bde1764564856e5be34a6083a"},{"path":"jiuwenswarm/agents/harness/common/tools/multimodal_config.py","start":185,"end":230,"sha256":"f21db03fd3855e3c233dbf890b6345b45a93efaa808a80a50b1809cfc79768fe"},{"path":"jiuwenswarm/agents/harness/common/tools/image_tools.py","start":89,"end":93,"sha256":"9217a4c8603c01bc7f13d10f26c81eff310ed020b9db9eadea5f4ddec32ac735"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=multimodal facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e369b46cfee444a92a278a75d205f14fe8b5457c7961cfee1bb78caeddd0a65a -->
**以环境变量作为配置传递介质（推断）**
设计推断（非作者历史意图）：

推断：apply_vision_model_config_from_yaml 把 YAML 配置落到 VISION_API_KEY 等进程级环境变量，视觉工具经 _get_vision_api_credentials 读取。收益是配置装配与工具运行时解耦（工具无需持有 config 字典）；代价是引入进程全局可变状态，同一进程内多个配置来源互相覆盖，且 VISION_MODEL_NAME 之类缺省值只在消费端可见。

来源：[jiuwenswarm/agents/harness/common/tools/multimodal_config.py:L185–L230](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/multimodal_config.py#L185-L230), [jiuwenswarm/agents/harness/common/tools/image_tools.py:L89–L93](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/image_tools.py#L89-L93)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/tools/multimodal_config.py","start":185,"end":230,"sha256":"f21db03fd3855e3c233dbf890b6345b45a93efaa808a80a50b1809cfc79768fe"},{"path":"jiuwenswarm/agents/harness/common/tools/image_tools.py","start":89,"end":93,"sha256":"9217a4c8603c01bc7f13d10f26c81eff310ed020b9db9eadea5f4ddec32ac735"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=multimodal facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=463d86430d7e94d51e449ffd0ea99d43b8034b368088525df6f6c2637f8e3d1f -->
**GEMINI_API_KEY 已设置时的 Gemini VQA 本地文件执行路径**
`_invoke_gemini_vision` 在 GEMINI_API_KEY 已设置时把本地文件字节读成 `types.Part`（HTTP 来源最多尝试 4 次，延时 5/15/60 秒），调用 `gemini-2.5-pro` 成功后返回 `resp.text`。

来源：[jiuwenswarm/agents/harness/common/tools/image_tools.py:L167–L233](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/image_tools.py#L167-L233)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":233,"path":"jiuwenswarm/agents/harness/common/tools/image_tools.py","sha256":"13aca13e32711fe59c16ba674f549b266aa27eff04cf5d22e117880c8f15c847","start":167}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=multimodal facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=14c5144909ba23aa12e0a81c0fdff8839622ddb41b21a0962859d8ff3357b8a6 -->
**generate_visual：async 契约，凭据缺失或空 prompt 时返回错误串而非抛异常**
async 工具 generate_visual(prompt, aspect_ratio="16:9", resolution="512", save_dir=None) -> str；凭据不全或 prompt 去空白后为空时返回 "[ERROR]" 开头的错误串而不抛异常；检测到后端时直接 return await gen_toolkits.generate_image(...)。

来源：[jiuwenswarm/agents/harness/common/tools/visual_gen_tools.py:L105–L132](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/visual_gen_tools.py#L105-L132), [jiuwenswarm/agents/harness/common/tools/visual_gen_tools.py:L136–L139](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/visual_gen_tools.py#L136-L139)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":132,"path":"jiuwenswarm/agents/harness/common/tools/visual_gen_tools.py","sha256":"3609454b99a19f861e708a22431bedf4581206b4be2c1c5ec8c84df029b3825a","start":105},{"end":139,"path":"jiuwenswarm/agents/harness/common/tools/visual_gen_tools.py","sha256":"6f414aa39325237a9c85eb2c293b0a927f8d5545b28532b8b337fc7f2543ff49","start":136}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=multimodal facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4d8c1e8f010492b2a34d9a305aa07bb86fbfdc8a06dd43c3e2893df15f4236e8 -->
**image_tools 视觉运行时耦合 openai/genai SDK 与 _RetryExecutor(max_tries=3)，配置函数导入自共享 multimodal_config**
`_call` 以 `OpenAI(api_key,base_url)` 调 `chat.completions.create`（空 content 抛异常），并经 `_RetryExecutor.with_backoff(max_tries=3)` 执行；Gemini 分支以 `genai.Client` 调 `gemini-2.5-pro`；模块并从共享 multimodal_config 导入 apply_image/apply_vision/_get_model_config。

来源：[jiuwenswarm/agents/harness/common/tools/image_tools.py:L15–L25](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/image_tools.py#L15-L25), [jiuwenswarm/agents/harness/common/tools/image_tools.py:L150–L161](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/image_tools.py#L150-L161), [jiuwenswarm/agents/harness/common/tools/image_tools.py:L210–L214](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/image_tools.py#L210-L214)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":25,"path":"jiuwenswarm/agents/harness/common/tools/image_tools.py","sha256":"86c811d54a1d84c845e3c870d703a59c942b8b28bf9f13758992ecc163439bed","start":15},{"end":161,"path":"jiuwenswarm/agents/harness/common/tools/image_tools.py","sha256":"22e61b4b87bd98690cc1bc7086cb60117387e7721346b7c50c6cc4d98ae818f6","start":150},{"end":214,"path":"jiuwenswarm/agents/harness/common/tools/image_tools.py","sha256":"580e3ee30ff4afe8c1ebe0652cf194395f0c372ea8122b602d45421f604a5006","start":210}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=multimodal facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a502790fb1506b00f611ed23c47ce466030de3ac157103e8711dc3a954d729ff -->
**GEMINI_API_KEY 为空本地返回精确错误串；503/429/500/空文本类异常重试，retries>max_r 时终止返回错误**
GEMINI_API_KEY 未设置或为空时 `_invoke_gemini_vision` 守卫直接返回 "[ERROR]: GEMINI_API_KEY is not configured for Gemini vision."；异常串含 503/429/500/"Response text is None or empty" 时重试并 sleep，retries>max_r 返回 "[ERROR]: Gemini Error after {retries} retries: {e}"。

来源：[jiuwenswarm/agents/harness/common/tools/image_tools.py:L167–L171](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/image_tools.py#L167-L171), [jiuwenswarm/agents/harness/common/tools/image_tools.py:L218–L224](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/image_tools.py#L218-L224), [jiuwenswarm/agents/harness/common/tools/image_tools.py:L225–L231](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/image_tools.py#L225-L231)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":171,"path":"jiuwenswarm/agents/harness/common/tools/image_tools.py","sha256":"3fd34f1ddc9a5673198129d30c9a9f6d3fc54f8407c7aca413d8d7f63fcd5a57","start":167},{"end":224,"path":"jiuwenswarm/agents/harness/common/tools/image_tools.py","sha256":"7feab6266709679b50ef2374b3bfa30a3c3696018a289626ac5e4836cdce9028","start":218},{"end":231,"path":"jiuwenswarm/agents/harness/common/tools/image_tools.py","sha256":"10e47803380e42025751c2be9bc2a39a4c3da421f6f318d7182f173536afed86","start":225}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=multimodal facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3da6091a0e0e319231662e8e019f1715dd9be7897a2279e7d0d9c4fe873b0020 -->
**test_generate_visual_no_images_returned_error 的运行时精确输出断言（本次未执行该测试）**
该 pytest.mark.asyncio 用例以 `_patch_async_client` 注入 200 响应（choices content="I cannot generate that image."），断言 `await generate_visual(prompt="a cat")` 精确等于 "[ERROR]: no images returned. Model response: I cannot generate that image."。

来源：[tests/unit_tests/agents/test_visual_gen_tools.py:L330–L343](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agents/test_visual_gen_tools.py#L330-L343)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":343,"path":"tests/unit_tests/agents/test_visual_gen_tools.py","sha256":"d0f7382f320cf71e7b78d06eabf8f1d994902204daf8c31bab365f85feafde94","start":330}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
