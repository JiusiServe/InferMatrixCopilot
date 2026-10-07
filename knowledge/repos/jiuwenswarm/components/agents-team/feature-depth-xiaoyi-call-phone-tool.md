---
title: "小艺拨打电话工具 (call_phone)：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py:L45-L107, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py:L24-L44, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py:L98-L107, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py:L46-L61, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py:L70-L82, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py:L14-L21, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py:L91-L96, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L171-L207, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py:L109-L113, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py:L53-L61, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py:L91-L98, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L46-L55]
feature: "xiaoyi-call-phone-tool"
entry_points: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py"]
---

# 小艺拨打电话工具 (call_phone)：实现深读

[功能概览](feature-xiaoyi-call-phone-tool.md) · [owner 入口](_index.md)

<!-- kb:depth feature=xiaoyi-call-phone-tool facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=885cfe9f5d2571cd0cacd2907c7f52dce44e5e05c994976d9dfb2ddaf39b8580 -->
**call_phone 校验入参后构造 StartCall 命令并等待设备响应**
slot_id 为 None 时置 0；phone_number 非空字符串且 strip 后非空、slot_id 属于 (0, 1)，否则抛 ToolInputError。随后构造 Common/Action、intentName=StartCall 的命令，交给 execute_device_command("StartCall", command)，dict 化后经 raise_if_device_error 检查，成功返回 content 内嵌 outputs JSON 的响应。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py:L45–L107](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py#L45-L107)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":107,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py","sha256":"d4c5294fc0bcd496a102bfd17eb25c6918cda0d96c98c9d2c1df5f8ff28b3080","start":45}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-call-phone-tool facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1cfd0a42f38e675ef0bab5b493d923a7f088fcf80bb14deb220b59301c4ed37c -->
**async call_phone(phone_number: str, slot_id: Optional[int] = None) -> Dict[str, Any]**
用 @tool(name="call_phone") 注册；docstring 声明返回 success、code、phoneNumber、slotId、message（与设备成功回调字段一致），实际返回 {"content":[{"type":"text","text":<设备 outputs 的 JSON>}]}. 调用方须传有效 phone_number。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py:L24–L44](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py#L24-L44), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py:L98–L107](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py#L98-L107)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":44,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py","sha256":"e64b3f8580346c7838d9c30e855f8a0b1827cefee8ad10be392f71ef4fc2ef7d","start":24},{"end":107,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py","sha256":"797159d7f64093934f862a56c7b79e709d2216c8f9a6bc959b8aaa361cb365a9","start":98}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-call-phone-tool facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fc0a2c393ad29732c56b4fe751a0c51a528f7274a73edefd8367e5f7d570af62 -->
**slot_id 未传时按 0（主卡），仅接受 0 或 1**
slot_id 默认 None，函数内 if slot_id is None: slot_id = 0；随后 slot_id not in (0, 1) 时抛 ToolInputError("slot_id 必须是 0（主卡）或 1（副卡）")。命令中另固定 timeOut: 5、executeMode: "background" 等字段，非可配置参数。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py:L46–L61](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py#L46-L61), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py:L70–L82](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py#L70-L82)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":61,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py","sha256":"47a62e9c490334b68f910d8c81643d5d2113ab5d68a938b6ffc8342ccacfd145","start":46},{"end":82,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py","sha256":"4e2b3b46a6e40a291322f3620d606f99ce3d04b85abdd98ee3011acf135954f5","start":70}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-call-phone-tool facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9f915c440475510f22176ae491e0f6e1d2bb8b02d0d0b338bbcbc62184263efb -->
**依赖 execute_device_command 与 raise_if_device_error，经频道 WebSocket 与设备通信**
call_phone 从 .utils 导入 execute_device_command、raise_if_device_error、ToolInputError，并经 openjiuwen 的 @tool 注册。execute_device_command 通过 channel.send_xiaoyi_phone_tools_command 发送并在 asyncio.wait_for(result_event.wait(), timeout=timeout) 内等响应；发送失败（sent 为假）抛 RuntimeError("发送指令失败，WebSocket 未连接")，finally 注销事件处理器。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py:L14–L21](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py#L14-L21), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py:L91–L96](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py#L91-L96), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L171–L207](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L171-L207)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":21,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py","sha256":"b4519f69d241d7eb4599fd93d742fb63bba9c5740d8e687c53ed81951aa230af","start":14},{"end":96,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py","sha256":"6ce67d6b3941ca5e85dbb856eb0a7d3c5439b18a7d38b2cfebc49c3b38a10680","start":91},{"end":207,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py","sha256":"91f54f6dbfef2166a8495a6ea9f17f4fad23ef17519709612d3cfbe2a09c3c7a","start":171}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-call-phone-tool facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d2a0aa7da9fe96e4760012970b623e669aefd9e70368c4685a3dbd28a5e8efc3 -->
**统一包装为 RuntimeError 简化了非输入错误的对外类型，但调用方需经 __cause__ 区分原始异常**
设计推断（非作者历史意图）：

收益：非输入失败统一为 RuntimeError 并带中文上下文「拨打电话失败: …」；成本：调用方若需原始异常类型必须检查 __cause__（`from e` 已保留），不能仅凭被抛类型区分超时、设备错误等不同来源。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py:L109–L113](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py#L109-L113)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":113,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py","sha256":"caec5624c98839fcea98818b06a3cf2a037a492ba013b3c7e0baab8d4914ec8a","start":109}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-call-phone-tool facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f908541d51e7a426fb21d0bb811296771756fd291fd9eb65870be6635f0b3723 -->
**输入校验抛 ToolInputError；其他异常被包装为 RuntimeError 且 ToolInputError 原样重抛**
phone_number 为空/非字符串、strip 后为空或 slot_id 不在 (0,1) 时抛 ToolInputError（其 status 属性为 400；docstring 称框架会返回 HTTP 400，但框架处理代码未在所示片段中）；except 分支中 ToolInputError 原样 raise，其余 Exception 记录 error 日志并以 RuntimeError("拨打电话失败: ...") from e 重抛。execute_device_command 的非 dict 输出先兜底为 {} 再经 raise_if_device_error 检查。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py:L53–L61](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py#L53-L61), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py:L91–L98](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py#L91-L98), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py:L109–L113](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py#L109-L113), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L46–L55](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L46-L55)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":61,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py","sha256":"43e9e8768f84af607c784bd52e5b949d01d96e8c35a88ce4592e415a62e198f9","start":53},{"end":98,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py","sha256":"524d4aa79e3a23b74372582a3eea6bc56c24be394dc55e09610aa9ea6b2f32ab","start":91},{"end":113,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/phone_tools.py","sha256":"caec5624c98839fcea98818b06a3cf2a037a492ba013b3c7e0baab8d4914ec8a","start":109},{"end":55,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py","sha256":"555d9215f54e93cceb4fadc7ed194b9f16c86b8d2077cb67843064dc5094d417","start":46}],"trace":[]} -->
<!-- /kb:depth -->
