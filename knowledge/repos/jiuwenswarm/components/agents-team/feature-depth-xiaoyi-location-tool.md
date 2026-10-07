---
title: "设备定位工具（get_user_location）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py:L33-L86, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py:L34-L68, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L168-L207, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py:L16-L16, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py:L19-L31, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/location_tool.py:L68-L86]
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
