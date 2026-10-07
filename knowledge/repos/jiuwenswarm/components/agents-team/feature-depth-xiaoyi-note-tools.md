---
title: "小艺备忘录工具 (create_note / search_notes / modify_note)：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py:L107-L173, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py:L176-L204, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py:L35-L51, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py:L53-L80, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py:L211-L233, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py:L93-L97, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L210-L228, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L46-L55, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py:L15-L23, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py:L82-L87, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L80-L104, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L184-L196]
feature: "xiaoyi-note-tools"
entry_points: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py"]
---

# 小艺备忘录工具 (create_note / search_notes / modify_note)：实现深读

[功能概览](feature-xiaoyi-note-tools.md) · [owner 入口](_index.md)

<!-- kb:depth feature=xiaoyi-note-tools facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f97d40f9e767f7ba2de9791e66503ec9d37eb97cb8c082355689c37e6c889464 -->
**search_notes 的完整执行路径：参数校验、构造 intent 命令、等待设备响应并包装返回**
search_notes(query) 先检查 query 为非空字符串并 strip 后非空，否则抛 ToolInputError；随后构造 namespace=Common/name=Action、intentName=SearchNote、bundleName=com.huawei.hmos.notepad 的命令，await execute_device_command("SearchNote", command) 取 outputs；非 dict 时包为 {"outputs": outputs}，经 raise_if_device_error 检查后从 result.items 统计条数 n，返回 format_success_response(dict(outputs), f"搜索到 {n} 条备忘录")。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py:L107–L173](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py#L107-L173)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":173,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py","sha256":"72974996b693e17a037e6b499fe36bd640e84fba819d17817946bf00fde9021e","start":107}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-note-tools facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b0f2c435ae514b913d410151fba218385b6e7f8104df607ff81e55bac93d52b4 -->
**三个异步工具的契约：字符串入参、非空 guard、Dict 返回，modify_note 需先经 search_notes 取 entityId**
create_note(title, content)、search_notes(query)、modify_note(entity_id, text) 均为 async 函数返回 Dict[str, Any]；每个参数都要求非空字符串（仅 search_notes 额外 strip，空白串抛 ToolInputError("query 不能为空")）。modify_note 的描述声明 entityId 必须先从 search_notes 获取，且设备侧字段名为 entityId。成功时返回经 format_success_response 包装的完整 outputs。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py:L176–L204](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py#L176-L204), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py:L35–L51](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py#L35-L51)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":204,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py","sha256":"a3608afd9cc8d12ddd22730e32ba8fdbcb88802272ec3be4967feaf74214fae2","start":176},{"end":51,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py","sha256":"fe998dca6858b9c84c468e12cab78fc850ce8be93b0d2f66e0fb6c57bc45f6fb","start":35}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-note-tools facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9c43e0d1ac2998ea3656b973e83ef58d776005bc2a3a05ecef36e9c6dfc7c06d -->
**命令 payload 的固定字面量：executeMode=background、achieveType=INTENT、executeParam 内 timeOut=5**
三个工具的命令均为硬编码：executeParam 含 executeMode="background"、achieveType="INTENT"、needUnlock=True、actionResponse=True、timeOut=5，bundleName="com.huawei.hmos.notepad"；payload 层（非 executeParam）固定 needUploadResult=True、noHalfPage=False、pageControlRelated=False。create/search 的 executeParam 不含 appType、permissionId，modify_note 则含 appType="OHOS_APP" 和 permissionId=[]。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py:L53–L80](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py#L53-L80), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py:L211–L233](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py#L211-L233)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":80,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py","sha256":"8871ecf16764f49fd1f390ffc2a064b3da4d63b7af1b5ce2a35d0fdc11025777","start":53},{"end":233,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py","sha256":"e4c4fc47421a63c2cd6060e98aaeeb2ad0fd1adb82d98bf3c1d3decee1a24943","start":211}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-note-tools facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4bfb14c061f6f3b3c898198ec852c37b2844820375694a1cbbc146e7ef9e4fd5 -->
**输入错误原样抛出 ToolInputError，其余异常包装为 RuntimeError，设备错误码触发 RuntimeError**
三个工具中 except ToolInputError: raise 保持输入错误不变（其 status=400，文档称框架会返回 HTTP 400）；其他任何 Exception 被记录日志并 raise RuntimeError（如 f"创建备忘录失败: {str(e)}"）from e。raise_if_device_error 在 outputs 为 dict 且 code 检查不过或 retErrCode 非 "0" 时抛 RuntimeError(f"{what_failed}: {err_msg} …")。注意 create/modify 的非空 guard 接受纯空白字符串（仅 search_notes strip）。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py:L93–L97](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py#L93-L97), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L210–L228](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L210-L228), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L46–L55](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L46-L55)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":97,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py","sha256":"db7dedae6fbd6df4938eef848c1ffdccc28f089cc27c42934ba166325c86c65d","start":93},{"end":228,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py","sha256":"a169af0afefd26625f182cf29b8ee64ff9143b48e91f859ae040a396304da003","start":210},{"end":55,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py","sha256":"555d9215f54e93cceb4fadc7ed194b9f16c86b8d2077cb67843064dc5094d417","start":46}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-note-tools facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=81bf123344dd60e2df6c1aafc0a97314d40f8351fd8ab8777b23b8d678fe6192 -->
**create_note 委托 execute_device_command，后者在无 channel 或 last_session_id 为空时抛 RuntimeError**
create_note 通过共享的 execute_device_command("CreateNote", command) 下发命令（note_tools.py:18–23 导入该助手）；该助手在 get_runtime_xiaoyi_channel() 返回 None，或 config 中 channels.xiaoyi.last_session_id 为空（含取配置异常后的空串）时抛出 RuntimeError，提示只能在活跃会话中使用。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py:L15–L23](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py#L15-L23), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py:L82–L87](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py#L82-L87), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L80–L104](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L80-L104)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":23,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py","sha256":"7ec39ff1784e0a2702450a9a866d7ba4d7b24e1fa0df885dba91f96954ddcbd2","start":15},{"end":87,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py","sha256":"7266fb8e77143d7b9b4dce12aff55fcbb94608614b19018c4dc1f9348baf0345","start":82},{"end":104,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py","sha256":"c91a4bbf6ab378befd151b0531c45606e364519be05b93dac6c9a953d517e7ca","start":80}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-note-tools facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b03c8d4d21848fbebd7b4e8a78cb552de429bf1312318ed407354b6aab313322 -->
**共享执行管线用显式 None 检查代替 or 短路：成功空 outputs 保留为 {}，但 None 与 {} 返回值相同**
设计推断（非作者历史意图）：

execute_device_command 在 error_result 非空时先抛出，随后用 `{} if result_data is None else result_data` 返回，注释说明空 dict 为假、勿用 or 短路。收益（推断）：设备成功但 outputs 为空 dict 时不会被误替换；代价（推断）：此处返回的 {} 既可能是真实空结果也可能是 result_data 为 None，调用方无法区分。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L184–L196](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L184-L196), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py:L82–L87](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py#L82-L87)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":196,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py","sha256":"d907867785bbe40fdd49ae08e849c626e057e9eef9c8d027059d7350dc3d8e70","start":184},{"end":87,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/note_tools.py","sha256":"7266fb8e77143d7b9b4dce12aff55fcbb94608614b19018c4dc1f9348baf0345","start":82}],"trace":[]} -->
<!-- /kb:depth -->
