---
title: "小艺图库搜索与照片上传工具 (search_photo_gallery / upload_photo)：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py:L133-L151, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py:L192-L195, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py:L62-L130, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py:L88-L109, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py:L208-L229, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L58-L68, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L79-L97, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py:L111-L116, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py:L173-L229, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py:L234-L275, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py:L154-L156]
feature: "xiaoyi-photo-gallery-tools"
entry_points: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py"]
---

# 小艺图库搜索与照片上传工具 (search_photo_gallery / upload_photo)：实现深读

[功能概览](feature-xiaoyi-photo-gallery-tools.md) · [owner 入口](_index.md)

<!-- kb:depth feature=xiaoyi-photo-gallery-tools facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cf5e07b214c8fa55144a359b090e4ef0930ec21b265e84cddaa07ae27ddeaecc -->
**upload_photo 规范化入参后下发 ImageUploadForClaw 意令并返回解码后的公网 URL 列表**
upload_photo 先调用 _normalize_media_uris 将 media_uris 规范为列表；非空、≤5 条且每项为非空字符串时，构造 intentName 为 ImageUploadForClaw 的命令并 await execute_device_command。返回的 result.imageUrls 中的非字符串项被跳过，字符串 URL 经 _decode_image_url_escapes 替换 \u003d/\u0026 后，以 {imageUrls, count, message} 的 JSON 文本 content 返回。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py:L173–L229](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py#L173-L229), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py:L234–L275](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py#L234-L275), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py:L154–L156](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py#L154-L156)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":229,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py","sha256":"a1e64f3b56d50dd61676e9b7fb61da42cf02a072a8ed70987149e8ac732896ae","start":173},{"end":275,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py","sha256":"27f40b7f0d5579fbbef5d2776557108217a0ddd0f60138157ba1303242150320","start":234},{"end":156,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py","sha256":"54709ac0792c1da4335918bed43acd58ffabc67382028c635d5d877c6d57c0dd","start":154}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-photo-gallery-tools facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a73cda42d67983ff700626f1973d705b9109788a97703ab605d060f6b8446ec7 -->
**search_photo_gallery(query: str) 校验非空字符串并包装设备 outputs 返回**
search_photo_gallery 接收单个 query 字符串，非字符串/为空/strip 后为空均抛 ToolInputError；设备 outputs 若非 dict 则包成 {"outputs": ...}，经 raise_if_device_error 检查后按 result.items 数量以 format_success_response 返回完整 outputs。调用方需传入有效会话下可用的描述语料。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py:L62–L130](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py#L62-L130)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":130,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py","sha256":"2bd3b6dba0c53f877dc483e0b84f3d1af21c29c5493a13174493b515c5c236b6","start":62}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-photo-gallery-tools facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6a399c0e979a1b6a7471c0d36fccd1e21b499cea46dc0e2c4e1c617eb4e3a205 -->
**两工具命令硬编码 executeMode/timeOut，等待超时用 execute_device_command 默认 60 秒**
两个工具的 command 中 executeMode="background"、needUnlock=True、timeOut=5 均为硬编码；调用 execute_device_command 时未传 timeout，因此使用其签名默认 timeout=60.0 秒（文档注释称其为超时秒数）。所示片段不含覆盖该默认的配置项。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py:L88–L109](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py#L88-L109), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py:L208–L229](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py#L208-L229), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L58–L68](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L58-L68)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":109,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py","sha256":"b088834b520550541c9380fbe56dbcdb9150f5b10c3e7dc81a7cdafbd44810c9","start":88},{"end":229,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py","sha256":"b1d1619d0a513eb5ff4210d618fb0d0204d9fb938ee886968aa4a730eda8f36d","start":208},{"end":68,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py","sha256":"bb6887f6c639bab3d1fa19beb21109fd450075aafaf75c7c1b58096796730957","start":58}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-photo-gallery-tools facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cc58a6a4876cc3e19051b3abf15a08f9a2b7d49b8d4e9de86a58166d869854ae -->
**依赖运行时 XiaoyiChannel 与 config 的 xiaoyi 会话标识**
两个工具都通过 execute_device_command 执行；该函数从 get_runtime_xiaoyi_channel() 取通道，若为 None 抛 RuntimeError（提示仅能在活跃会话中使用），否则从 config 的 channels.xiaoyi 读取 last_session_id/last_task_id（默认空字符串）。所示片段未展示这些标识后续如何使用。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L79–L97](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L79-L97), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py:L111–L116](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py#L111-L116)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":97,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py","sha256":"4fb43e00faf00ff71cb6b2165ee7fe917c2b73321a0dfdfd697db80863136157","start":79},{"end":116,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py","sha256":"484640213825f41e002da2e2af1aa493bd184f04662f3527f876f03fd22b122a","start":111}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-photo-gallery-tools facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6c84e1f7da6a754f6d4de055471b641113515572af91dc315f675c53e13a5655 -->
**media_uris 兼容数组与 JSON 字符串带来灵活性，解析失败需调用方处理**
设计推断（非作者历史意图）：

（推断）_normalize_media_uris 同时接受 list 与 JSON 数组字符串，方便不同调用形态；代价是字符串解析失败抛 ToolInputError 且超 5 条需分批，把重试/分批负担转移给调用方。5 条上限本身是文档与代码一致的事实，代价部分为推断。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py:L133–L151](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py#L133-L151), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py:L192–L195](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py#L192-L195)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":151,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py","sha256":"f0c111c426f8ece410dbd2a756244a8aeccd256e0c07ee9df75c0bb1b4b88acd","start":133},{"end":195,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/photo_tools.py","sha256":"b64820d498405278e6e27fff9f2b8d8dd05c06aa74db35343e80002929053a4e","start":192}],"trace":[]} -->
<!-- /kb:depth -->
