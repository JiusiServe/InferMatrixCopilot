---
title: "小艺收藏/个人知识库工具 (query/add/delete_collection)：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L293-L373, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L377-L384, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L165-L231, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L126-L146, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L217-L237, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L293-L303, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L386-L390, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L215-L231, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L310-L330, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L19-L24, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L215-L220, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L313-L330, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/agents/swarm/test_swarm_assembly.py:L1872-L1880, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/tools.py:L141-L143, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/tools.py:L461-L469]
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

<!-- kb:depth feature=xiaoyi-collection-tools facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f5f5ec81258fcef767c9aa61dd49d7b3daa2e839261b30c33a82c9904ae2cc60 -->
**本地路径上传分支内读取 channels.xiaoyi 三项配置（uri 非空且无远程前缀）**
在 add_collection 中，仅当 uri 为真值且不以 http://、https://、file:// 开头时，才惰性调用 get_config() 读取 channels.xiaoyi 下的 file_upload_url、api_key、uid。缺失 file_upload_url 或 api_key 时抛出 RuntimeError；uid 先经 str() 转换，缺失时变为字符串 "None" 仍为真值，不触发该报错。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L310–L330](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py#L310-L330)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":330,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py","sha256":"450ab2039f69c87f34ca8584f2b3fa9701f109964fd1cf05b4c095a0a6f4aceb","start":310}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-collection-tools facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2fe11c2abddd2e9d01ff640ce06cb8d47472155c576fa16b94e057fb968a905e -->
**共享 .utils 与模块级导入的 file_upload_helpers、分支内导入的 aiohttp/get_config**
模块顶层从 .utils 导入 execute_device_command、raise_if_device_error、ToolInputError，并从 .file_upload_helpers 导入 XiaoyiObsUploadConfig 和 upload_local_file_public_url（L19–L24）；delete_collection 通过 execute_device_command("DeleteCollection", ...) 执行并用 raise_if_device_error 检查（L215–L220）。仅 aiohttp 与 get_config 在本地文件分支内延迟导入（L314–L315），随后用 aiohttp.ClientSession 调用上传助手，返回为空则抛 RuntimeError（L325–L330）。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L19–L24](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py#L19-L24), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L215–L220](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py#L215-L220), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py:L313–L330](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py#L313-L330)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":24,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py","sha256":"74a8ffb222955f314089e9ff454ff90db1acf3e97dd06a7ec0c773ad50b1c310","start":19},{"end":220,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py","sha256":"0372542569e42aa693223a8e68fa3b8b29cc92d75422047b25e5d617bf06b196","start":215},{"end":330,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py","sha256":"6dd0b9e5f61d74fb77a1ef05d9dbae34fd34355bd9f835a5a7f2e1f5ff279800","start":313}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-collection-tools facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=37e4a8a38bc8bdeb1a74321aad8ba05d88d88bee02b3f98de534b4b2e5bae627 -->
**既有 swarm 装配测试覆盖配置门控下的构建数量，未覆盖工具行为**
既有测试 test_xiaoyi_phone_tools_gated_by_config 执行实际的 _build_xiaoyi_phone_tools：channels.xiaoyi.phone_tools_enabled 为 True 时断言返回 27 个工具，config 为空（默认 False）时断言返回空列表。生产元组 _XIAOYI_PHONE_TOOLS 显式包含 query_collection、add_collection、delete_collection。该断言只验证聚合数量与门控默认值，不校验单个工具身份、intent 组装或设备结果；属配置门控辅助函数级别的 helper 单元验证。本次 NOT EXECUTED，未运行该测试。

来源：[tests/agents/swarm/test_swarm_assembly.py:L1872–L1880](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/agents/swarm/test_swarm_assembly.py#L1872-L1880), [jiuwenswarm/agents/swarm/providers/tools.py:L141–L143](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/tools.py#L141-L143), [jiuwenswarm/agents/swarm/providers/tools.py:L461–L469](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/tools.py#L461-L469)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1880,"path":"tests/agents/swarm/test_swarm_assembly.py","sha256":"937552f24d47dad020214418cf9aa430b1b2216fcf692530e3cf03099a34a880","start":1872},{"end":143,"path":"jiuwenswarm/agents/swarm/providers/tools.py","sha256":"e3dcffc8979908ac542e704ebbec7079e56c6fb19f8d942ba5e0da2f6dc5099d","start":141},{"end":469,"path":"jiuwenswarm/agents/swarm/providers/tools.py","sha256":"9b10b462d3ed8ef84ff21833831933c9f431f48a177788b8e433376d3794e913","start":461}],"trace":[],"validation_kind":"helper_unit"} -->
<!-- /kb:depth -->
