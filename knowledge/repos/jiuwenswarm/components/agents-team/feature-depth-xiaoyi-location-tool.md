---
title: "设备定位工具（get_user_location）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py:L33-L86, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py:L34-L68, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L168-L207, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py:L16-L16, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py:L19-L31, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py:L68-L86, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py:L68-L73, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L215-L228, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/agents/swarm/test_swarm_assembly.py:L1872-L1880, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/tools.py:L461-L469, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/tools.py:L121-L150]
feature: "xiaoyi-location-tool"
entry_points: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py"]
---

# 设备定位工具（get_user_location）：实现深读

[功能概览](feature-xiaoyi-location-tool.md) · [owner 入口](_index.md)

<!-- kb:depth feature=xiaoyi-location-tool facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2c7312d6299c3f160889180c27c5e20ac08eeae418b9b41dd4e9e8d52d90aadb -->
**构建 GetCurrentLocation 指令并经设备通道等待响应**
无参协程先构造 namespace=Common/name=Action、intentName=GetCurrentLocation（isNeedGeoAddress=True、timeOut=5、executeMode=background）的命令 dict，调用 execute_device_command 等待 outputs；非 dict 则包成 {"value": outputs}，经 raise_if_device_error 校验后以 content[0].text 返回 outputs 的 JSON 字符串（ensure_ascii=False）。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py:L33–L86](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py#L33-L86)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":86,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py","sha256":"81af2c402a26c8b19da1d6a194534488074011b7510435cd35603b8012e4b66f","start":33}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-location-tool facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=de7c01cbf68ad0d16329939c653577e78bda99250e54c1e0f8e3cb36c15c0a31 -->
**无参异步工具，返回设备 outputs 的 JSON 文本**
get_user_location 以 @tool(name="get_user_location") 注册，async 无参；成功时返回 {"content":[{"type":"text","text": json.dumps(outputs)}]}，outputs 为 WebSocket 指令 GetCurrentLocation 的设备响应（非 dict 时包装为 {"value": outputs}）。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py:L19–L31](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py#L19-L31), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py:L68–L86](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py#L68-L86)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":31,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py","sha256":"ae33caf4baa23403d956460267bb836744e663a51571242d3345ad1b8cde3260","start":19},{"end":86,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py","sha256":"ba4e47988176391d2fffc439182a58ff4dc1db1b39ec79e8450126ea52531b11","start":68}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-location-tool facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a1b8fe890702f0bd5a5e823fef84a6b890cdf764550aef7ab8fcd35fae229b03 -->
**指令参数在函数体内硬编码，无外部配置入口**
executeParam 各项（achieveType="INTENT"、bundleName="com.huawei.hmos.aidispatchservice"、intentName、timeOut=5、needUnlock=True 等）均为字面量硬编码；get_user_location 本身不接收也不读取任何配置。execute_device_command 的 timeout 由其自身默认/调用方决定，此处未传入。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py:L34–L68](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py#L34-L68)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":68,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py","sha256":"b9c854095176ea8ee15d9b595521e80ff548218b7a062bf8b8bcaed233adf393","start":34}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-location-tool facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1d0814d532c1daf431002f09512d0c89d4d5fce46e4941fa20f2178543b1d088 -->
**依赖 execute_device_command 的 WebSocket 通道与事件处理**
工具将发送与等待全部委托给 execute_device_command：后者注册 intent_name 数据事件处理器，经 channel.send_xiaoyi_phone_tools_command 发送；sent 为假抛 RuntimeError("发送指令失败，WebSocket 未连接")，成功路径返回 result_data（None 时返回 {}，注释明确勿用 or 短路），finally 中注销处理器。工具对通道协议的耦合即此两函数调用。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L168–L207](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L168-L207), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py:L16–L16](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py#L16-L16)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":207,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py","sha256":"42ee64fede81ebd6d8ebf5db7e0874626dce86c7c65a473fb2cf5ef571271283","start":168},{"end":16,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py","sha256":"024034d70ea51ce5958a49adec2c6fa3cdb2cc9968c897449714b282cb30c29a","start":16}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-location-tool facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b36d1c2f6467d66af9bb23b0bbcb05c952373111374ee6d6dcb9b6f9cdd1a176 -->
**非 dict outputs 先包装；code/retErrCode 校验失败抛 RuntimeError**
L70–L73 将非 dict 的 outputs 包成 {"value": outputs} 后调用 raise_if_device_error。utils.py L215–L228：非 dict 直接 return；顶层 code 未通过 _outputs_top_level_code_ok 时抛 RuntimeError，消息含 errorMsg/errMsg（默认"未知错误"）与错误码；retErrCode 仅在非 None 且 str(ret) != "0" 时抛 RuntimeError（空字符串也触发），消息含 retErrCode 值。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py:L68–L73](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py#L68-L73), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L215–L228](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L215-L228)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":73,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py","sha256":"0e7eaf746271b9cee16596f0f565eb04aae06b366dd696c4757de571d7b00429","start":68},{"end":228,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py","sha256":"9725759159d197d90a589b891e69482480884cf5bbb28b30840d31332670951b","start":215}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-location-tool facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=311076e440a69641490d805506f7e68a81e9ca400aa4d6ba275891498f6ed2b8 -->
**装配测试断言 27 个工具与空列表，get_user_location 位于生产元组**
test_swarm_assembly.py:1872 的测试实际调用 _build_xiaoyi_phone_tools，断言 channels.xiaoyi.phone_tools_enabled 为 True 时返回 27 个工具、配置为空时返回 []。生产元组 _XIAOYI_PHONE_TOOLS 显式包含 get_user_location。该断言仅覆盖配置门控辅助函数与聚合数量，不涉及 get_user_location 的运行时行为；本条为已有测试证据，本次未执行。

来源：[tests/agents/swarm/test_swarm_assembly.py:L1872–L1880](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/agents/swarm/test_swarm_assembly.py#L1872-L1880), [jiuwenswarm/agents/swarm/providers/tools.py:L461–L469](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/tools.py#L461-L469), [jiuwenswarm/agents/swarm/providers/tools.py:L121–L150](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/tools.py#L121-L150)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1880,"path":"tests/agents/swarm/test_swarm_assembly.py","sha256":"937552f24d47dad020214418cf9aa430b1b2216fcf692530e3cf03099a34a880","start":1872},{"end":469,"path":"jiuwenswarm/agents/swarm/providers/tools.py","sha256":"9b10b462d3ed8ef84ff21833831933c9f431f48a177788b8e433376d3794e913","start":461},{"end":150,"path":"jiuwenswarm/agents/swarm/providers/tools.py","sha256":"3676650a09a0441ad25e82a12fd8ebbe503b9960efb9475671b40b741fd2a722","start":121}],"trace":[],"validation_kind":"helper_unit"} -->
<!-- /kb:depth -->
