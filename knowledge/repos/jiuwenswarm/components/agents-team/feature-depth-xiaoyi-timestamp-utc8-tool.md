---
title: "时间戳转北京时间工具 (convert_timestamp_to_utc8_time)：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py:L49-L69, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py:L77-L84, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py:L19-L38, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py:L49-L60, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py:L13-L16, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py:L69-L75, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py:L39-L47, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py:L64-L67, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L46-L55, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py:L50-L69]
feature: "xiaoyi-timestamp-utc8-tool"
entry_points: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py"]
---

# 时间戳转北京时间工具 (convert_timestamp_to_utc8_time)：实现深读

[功能概览](feature-xiaoyi-timestamp-utc8-tool.md) · [owner 入口](_index.md)

<!-- kb:depth feature=xiaoyi-timestamp-utc8-tool facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=95d895e680fe5ff00906335cef1f9fde3dfd43367179e4fc95eb162a55f5f8b7 -->
**秒/毫秒时间戳经位宽启发式归一后转为北京时间字符串**
输入 timestamp 先经位宽判断（int 后字符串长 13 位视为毫秒、10 位视为秒，否则按 ts_abs>1000000000000 分流），乘 1000 归一为毫秒，再用固定 UTC+8 时区 datetime.fromtimestamp 转换并 strftime 为 "%Y%m%d %H%M%S"，返回 content 列表字典。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py:L49–L69](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py#L49-L69), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py:L77–L84](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py#L77-L84)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":69,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py","sha256":"1de9ffa8eda5cf3ffe800d60d24b93f8186b2930b7a8bde4b4fdf89b9e68952f","start":49},{"end":84,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py","sha256":"0e08448a7cc84c6f80cac04c8b34d77c8dad310813a6ad4878d97c4650b4d156","start":77}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-timestamp-utc8-tool facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e6212f3e70317ef6fed05dbe40852c9b2c0fa1a7e44846ec6a183c1d6c12f19f -->
**@tool 注册、单一 timestamp: float 入参、返回 text content 字典**
函数经 openjiuwen @tool 装饰注册为名为 convert_timestamp_to_utc8_time 的工具，签名仅接受 timestamp: float；返回 {"content":[{"type":"text","text":格式化时间}]}，文档字符串声明输出格式 YYYYMMDD hhmmss 并建议先转换再回答。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py:L19–L38](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py#L19-L38), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py:L77–L84](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py#L77-L84)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":38,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py","sha256":"577aa2a9dc3ed2464e82c16f163b5f41f99b1488a34144fd766dcd2ba8441ec0","start":19},{"end":84,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py","sha256":"0e08448a7cc84c6f80cac04c8b34d77c8dad310813a6ad4878d97c4650b4d156","start":77}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-timestamp-utc8-tool facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=eeaa36427c902e2a6dac5dd299daf215e684a7258c3166e4f674f9b68b6fc170 -->
**固定 UTC+8 与位数判定规则，无外部配置项**
时区固定为 timezone(timedelta(hours=8))（L63），输出格式固定为 "%Y%m%d %H%M%S"（L69）。秒/毫秒判定基于绝对值整数的字符串位数：13 位按毫秒，10 位按秒并乘 1000，超过 1000000000000 按毫秒，其余按秒乘 1000（L50–L60）。所示分支内未读取任何配置项，且输入为 None/非数字/NaN/Inf 时直接抛 ToolInputError，不会到达转换逻辑（L39–L47）。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py:L50–L69](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py#L50-L69), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py:L39–L47](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py#L39-L47)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":69,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py","sha256":"1a1912aa2a2458d6dcb482318915a2b6d6afa97c0ea296b70e7154bda6e92247","start":50},{"end":47,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py","sha256":"3398c659a0312fe69a0b96aabb8128a2d288fb6ca06dcf31ce1780cde7774494","start":39}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-timestamp-utc8-tool facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=47f02311f63dd8e40309efd9c2da1bc470b6c7a0ff3dc4ab3599e948383569b0 -->
**导入 openjiuwen @tool、logger 与本包 ToolInputError；仅成功格式化后记录 INFO 日志**
L13–L16 显示三个直接依赖：tool 装饰器注册、logger、ToolInputError。日志（L71–L75）只在通过全部守卫且 fromtimestamp 成功后才执行；前置守卫抛错或 L65–L67 转换失败时不产生该 INFO 日志。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py:L13–L16](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py#L13-L16), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py:L69–L75](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py#L69-L75)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":16,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py","sha256":"438fba86f5f5e9d7ddbcc6b25a31ad552b047c764d618b43d505d5cfcdddbda1","start":13},{"end":75,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py","sha256":"c8f4bab13b8d0837990c619d001091e2696955c8daed8a9273905045e3e881f3","start":69}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-timestamp-utc8-tool facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=28c4e6bc7796e50c29bd9aaeacaf6a354ec22fd4b7bbb2a0a40f7651ab5dc146 -->
**None、非数字、NaN/Inf 守卫与 fromtimestamp 的 OSError/OverflowError/ValueError 均抛 ToolInputError**
L39–L47 三条守卫各自抛 ToolInputError；L64–L67 的 try 仅包住 L65 的 fromtimestamp，捕获 OSError、OverflowError、ValueError 并包装为 ToolInputError 传播（携带 status=400，见 utils.py L53–L55）。不排除守卫之前其他未列异常。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py:L39–L47](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py#L39-L47), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py:L64–L67](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py#L64-L67), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L46–L55](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L46-L55)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":47,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py","sha256":"3398c659a0312fe69a0b96aabb8128a2d288fb6ca06dcf31ce1780cde7774494","start":39},{"end":67,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py","sha256":"c81cc56edbe276e3a442b2749ce3765e7938b2b1a7ad8f53168ec34bbd85ed42","start":64},{"end":55,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py","sha256":"555d9215f54e93cceb4fadc7ed194b9f16c86b8d2077cb67843064dc5094d417","start":46}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-timestamp-utc8-tool facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b2c8a4fd49bc030317338b9c20eac4adb2c501cb66d3b633216276deebe8252b -->
**位宽启发式同时接受秒/毫秒，但 11-12 位输入落入乘 1000 兜底**
设计推断（非作者历史意图）：

用 int 后十进制位宽（13/10）区分毫秒/秒并配数值兜底，收益是无需额外参数即可兼容两种位宽；代价是 11 或 12 位的时间戳既不匹配 13 也不匹配 10，落入 ts_abs>1000000000000 else 分支被强制视为秒乘 1000，可能产出错误时间（推断）。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py:L49–L60](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py#L49-L60)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":60,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/timestamp_tool.py","sha256":"d2c25211f8bfddaac763613bd1df18d34c3f7314453732f225383a37622ab108","start":49}],"trace":[]} -->
<!-- /kb:depth -->
