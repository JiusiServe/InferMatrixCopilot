---
title: "小艺保存到手机工具 (save_media_to_gallery / save_file_to_file_manager)：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L29-L40, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py:L36-L92, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L43-L54, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py:L39-L43, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py:L60-L89, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L35-L40, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py:L60-L92, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L273-L277, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L187-L225, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L29-L54, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L249-L277, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L187-L208, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L264-L277, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L46-L55]
feature: "xiaoyi-save-to-phone-tools"
entry_points: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py", "jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py"]
---

# 小艺保存到手机工具 (save_media_to_gallery / save_file_to_file_manager)：实现深读

[功能概览](feature-xiaoyi-save-to-phone-tools.md) · [owner 入口](_index.md)

<!-- kb:depth feature=xiaoyi-save-to-phone-tools facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2d2e3d326db0dadfbad56dc2e363f205886b45642bf373f27e89587328bd4038 -->
**_get_obs_config 读取 channels.xiaoyi 的 file_upload_url/api_key/uid，但 uid 经 str() 转换削弱了缺失检查**
从 get_config() 取 cfg["channels"]["xiaoyi"]，读取 file_upload_url、api_key、uid；三者传入非空检查，缺失时抛 ToolInputError("缺少 channels.xiaoyi 的 file_upload_url / api_key / uid 配置...")。但 uid 先执行 str(xc.get("uid")) 再判空：uid 为 None 时变成非空字符串 "None"、为 0 时变成 "0"，因此该检查实际只可靠拦截 file_upload_url 与 api_key 的缺失。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L43–L54](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py#L43-L54)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":54,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py","sha256":"5c10cc275cadd89b96b482b9af1fc84f468bd44d4c313d467f8c495998136e7c","start":43}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-save-to-phone-tools facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=63a5e9b3f95b25940f62d2e36a0ef9dee10dda67770e7d889ed77cf41b1fbd23 -->
**Local paths depend on three-step OBS upload via shared aiohttp session**
_ensure_public_url 对非 http(s) 路径调用 upload_local_file_public_url：POST prepare（sha256/size 元数据）→ 按 uploadInfos[0] 的 method/url 直传文件 → POST completeAndQuery 取 fileDetailInfo.url；上传与设备命令均经由调用方创建的 aiohttp.ClientSession 或 execute_device_command 通道完成。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L29–L40](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py#L29-L40), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py:L36–L92](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py#L36-L92)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":40,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py","sha256":"32dfa32121a2036cb32c38fa2061849211c23e347730afbf0e5ddb32d9170813","start":29},{"end":92,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py","sha256":"fd7609457dd5a151908251049a7b3b67b9f12555a470e3de5ab39d06e0fda0b7","start":36}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-save-to-phone-tools facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d968d0b1e29dcb148de3e896274d74af41447f363dc7ff8a5e695a2bbd00aa31 -->
**非 ToolInputError 异常在工具层被包装为 RuntimeError 后抛出**
上传 helper 中显式分支失败（prepare/upload/completeAndQuery HTTP 非 ok、code!="0"、无 uploadInfos、fileDetailInfo.url 为空）各自 raise RuntimeError（file_upload_helpers.py L60–92）；工具函数里除 ToolInputError 原样上抛外，其余 Exception 记录日志并以 raise RuntimeError(...) from e 重新抛出（save_tools.py L273–277）。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py:L60–L92](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py#L60-L92), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L273–L277](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py#L273-L277)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":92,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py","sha256":"01a8ad6dc5a055a83ef5d355327df78b4649cca14c3dc3da93f37f650b04689b","start":60},{"end":277,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py","sha256":"3260fa94ad2ed97a58fb5ef91c3eea73db39cf5b7cffbe5c6910c6e8edf481b1","start":273}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-save-to-phone-tools facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4b31d49dc60bb2d62911fe1cee484b3b7bec166b3684eb785abcbf9946e1edfa -->
**本地文件全量读入内存并经三次串行请求换公网 URL：实现简单但内存与延迟成本随文件增大**
设计推断（非作者历史意图）：

（推断）收益：一次性 f.read() 使 sha256、fileSize 与上传体来自同一份内存内容，逻辑简单、无需流式分块。成本：整个文件驻留内存，且本地输入需顺序完成 prepare、文件传输、completeAndQuery 三次网络请求才拿到 URL，大文件时内存峰值与总延迟同时升高；http(s) 输入则完全跳过该路径。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py:L39–L43](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py#L39-L43), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py:L60–L89](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py#L60-L89), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L35–L40](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py#L35-L40)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":43,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py","sha256":"d3d4e803ca1f95efd39a2300d1f6d7508e33f471dd572daee6bfc93efa665289","start":39},{"end":89,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py","sha256":"1dc6d0174ed54775e2860b2c48007e0e7b70fd3d84ad69cfc440f9ed62516ea0","start":60},{"end":40,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py","sha256":"6c15658515431494f38c94776f0b503b8fffae5724dff01dcbe6aea6e6b9e42f","start":35}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-save-to-phone-tools facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=eff0a549fffb6f078a7bb74073718d20f4126c0c7f9b0b8f0e8a8154ad834995 -->
**save_file_to_file_manager：校验入参后经 _ensure_public_url 换公网 URL 并下发 SaveFileToFileManager 命令**
在 save_file_to_file_manager 内，url/file_name/suffix 任一为空或非字符串时先抛 ToolInputError；随后 _get_obs_config 取配置，_ensure_public_url 对已是 http(s):// 的 url 原样返回，否则经 upload_local_file_public_url 上传，返回空则抛 RuntimeError。命令交给 execute_device_command("SaveFileToFileManager", command)，输出非 dict 时包成 {"outputs": outputs}，再经 raise_if_device_error 检查，成功后以 content[0].text 返回 json.dumps 的 outputs。注意 L51–L52 中 uid 经 str(xc.get("uid")) 转换，缺失时成为 "None" 字符串并通过非空检查，不触发 ToolInputError。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L187–L225](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py#L187-L225), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L29–L54](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py#L29-L54), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L249–L277](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py#L249-L277)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":225,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py","sha256":"28076ec46b93336474fb1596b4ae5a52c98ddb5935928b27e24f255d9854c5b5","start":187},{"end":54,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py","sha256":"d6d34b311bdaf50bd563785317711612371bc5a31e672ef3cc19fd72334b30e6","start":29},{"end":277,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py","sha256":"a3f65f89b25970affd63e2b4a5566ddb9a7c85e39d465248922d791b190b623b","start":249}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-save-to-phone-tools facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9eb469511c02489a0f841595c18bf9b73f5a8b3e55e8d9c77a23801d485b04c7 -->
**save_file_to_file_manager 契约：三个字符串必填参数，ToolInputError(status=400) 原样上抛，成功返回 content[0].text 为 JSON 字符串**
调用方须传非空字符串 url、file_name、suffix，任一不满足抛 ToolInputError（L203–L208）；该异常在兜底 except 中被原样 re-raise 不包装（L273–L274），其余异常记日志后包装为 RuntimeError 并链上原异常（L275–L277）。ToolInputError 的 __init__ 设 self.status = 400；其 docstring 说明抛出后框架返回 HTTP 400 而非 500，属文档陈述。成功返回 {"content": [{"type": "text", "text": json.dumps(outputs, ensure_ascii=False)}]}。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L187–L208](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py#L187-L208), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L264–L277](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py#L264-L277), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L46–L55](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L46-L55)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":208,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py","sha256":"c954a49f59b40d560f2cdcbb9cbcd8018144d75a58d07c8685b20fb701c12bd9","start":187},{"end":277,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py","sha256":"6f986496b63d8274a366fe47f9dc980002a29a621c4396620307f9e270109f02","start":264},{"end":55,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py","sha256":"555d9215f54e93cceb4fadc7ed194b9f16c86b8d2077cb67843064dc5094d417","start":46}],"trace":[]} -->
<!-- /kb:depth -->
