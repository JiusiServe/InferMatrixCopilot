---
title: "小艺收藏/个人知识库工具 (query/add/delete_collection)：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L293-L373, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L377-L384, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L165-L231, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L126-L146, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L217-L237, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L293-L303, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L386-L390, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L215-L231]
feature: "xiaoyi-collection-tools"
entry_points: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py"]
---

# 小艺收藏/个人知识库工具 (query/add/delete_collection)：实现深读

[功能概览](feature-xiaoyi-collection-tools.md) · [owner 入口](_index.md)

<!-- kb:depth feature=xiaoyi-collection-tools facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=92d99cf9be45c431d83fea6d848636093d07a50e45f23031e9d09badebab0049 -->
**add_collection 校验入参后可先上传本地文件再下发 AddCollection 指令**
add_collection 先校验 dataType ∈ {HYPER_LINK,TEXT,IMAGE,FILE} 及对应必填字段；若 uri 不以 http://、https://、file:// 开头，则读取 channels.xiaoyi 配置上传换公网 URL，随后组装 executeMode=background、intentName=AddCollection 的 command，经 execute_device_command 执行，输出 dict 包成 content[0].text 的 JSON 字符串返回。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L293–L373](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py#L293-L373), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L377–L384](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py#L377-L384)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":373,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py","sha256":"de9b4e8f763515868b4646b151c0e9b9ffa0b022ea3265b1631333f33a97560a","start":293},{"end":384,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py","sha256":"9ed3622a55c6c4402a387d651c38f22f62a365692684d607dfe6260d2053177c","start":377}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-collection-tools facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=72e7e96469f970a8b46731236758b847a05424ea3ce37f0f64aaefc1049f079b -->
**delete_collection 接受数组或 JSON 数组字符串的 item_ids，返回 content[0].text JSON**
delete_collection(item_ids: Union[str, List[str]]) 经 _normalize_item_ids 归一（None/非数组 JSON/其他类型抛 ToolInputError，空数组也抛 ToolInputError），成功时返回 {"content":[{"type":"text","text": json.dumps(outputs)}]；调用方需提供非空 itemId 合集。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L165–L231](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py#L165-L231), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L126–L146](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py#L126-L146)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":231,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py","sha256":"9f0693f7cc03a7a78c26585f8566c99de35dc210c6bfd1fa34b29f11ffd4d031","start":165},{"end":146,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py","sha256":"befe96d5e6651de038667fa929d3b2ee00c86469cae40030d63d94d42baec934","start":126}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-collection-tools facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=05ded2a444d87bdf000fc76a6d5270e0061ed726e5f2f54eb1732815442655d6 -->
**输入错误抛 ToolInputError 原样上抛，其余异常统一包成 RuntimeError**
delete_collection/add_collection 中 ToolInputError 被原样 re-raise（如 itemIds 为空、dataType 非法或对应字段缺失）；任何其他 Exception 记录 error 日志后抛 RuntimeError("删除/添加小艺收藏失败: …") from e；设备返回的错误由 raise_if_device_error 以同样中文消息检查。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L217–L237](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py#L217-L237), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L293–L303](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py#L293-L303), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L386–L390](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py#L386-L390)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":237,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py","sha256":"ca6376cb0c27ae94689dc69db9bc2877a808331e42f22e9e85bcd387bb2474c6","start":217},{"end":303,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py","sha256":"231d34202726ee5202e60b6a0e8daf8db7f847e480ff402f6a1076fbe707d0dd","start":293},{"end":390,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py","sha256":"f1e31f24fa8a5a8bd4c576a7ed7fc07a385e6a6293532f4253e4c39fcca96ede","start":386}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-collection-tools facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8861c715756a47a465618b619f73a249beceb1aa3c180073cc4cef3b15a1fa9f -->
**非 dict 输出兜底包一层 outputs，换取统一返回形状**
设计推断（非作者历史意图）：

收益：execute_device_command 返回非 dict 时包成 {"outputs": …}，使后续 raise_if_device_error 与 JSON 序列化总有统一形状（推断：调用方解析逻辑因此更简单）。代价：原始标量输出被多包一层嵌套，调用方需知晓这一隐式包装约定（推断自 217-218、370-371 行的兜底分支）。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L215–L231](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py#L215-L231)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":231,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py","sha256":"19e6b50bb3c115904cba575737e8fa44b663287f64741d354a370452ee270165","start":215}],"trace":[]} -->
<!-- /kb:depth -->
