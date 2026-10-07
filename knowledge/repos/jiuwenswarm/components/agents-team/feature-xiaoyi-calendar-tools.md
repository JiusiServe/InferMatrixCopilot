---
title: "Xiaoyi 设备日历日程工具（create/search_calendar_event）"
created: 2026-10-06
updated: 2026-10-07
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L131-L171, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L237-L281, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L106-L110, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L276-L287, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L137-L161, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L244-L261, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L120-L135, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L222-L235, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L264-L274, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L87-L89, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L193-L195, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L120-L129, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L222-L229, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L91-L95, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L113-L118, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L198-L202, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L283-L287]
feature: "xiaoyi-calendar-tools"
entry_points: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py"]
---

# Xiaoyi 设备日历日程工具（create/search_calendar_event）

<!-- kb:knowledge owner=feature-xiaoyi-calendar-tools facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**职责与数据流**

每个工具是薄适配层：校验输入、把时间字符串转为毫秒时间戳，组装 HarmonyOS 意图命令（header namespace `Common`，create 用 `ActionAndResult`、search 用 `Action`），交给共享的 `execute_device_command` 下发到设备日历（bundle `com.huawei.hmos.calendardata`），再对结果做错误检查与格式化。search 额外从 `result.items` 取日程并用 `_convert_event_timestamps` 把时间戳转成可读格式。命令细节（如 `intentParam` 字段 `dtStart/dtEnd` vs `timeInterval`）在此层静态构造。

Sources / 来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L131–L171](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L131-L171), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L237–L281](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L237-L281)

<!-- kb:knowledge owner=feature-xiaoyi-calendar-tools facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**验证情况**

Inference / 设计推断（非作者历史意图）：

所示片段仅含实现代码，未见针对这两个工具的测试或断言；代码内仅有运行时日志（`[CALENDAR_TOOL]`/`[SEARCH_CALENDAR_TOOL]`）和异常路径作为可观测性手段。依据部分输入无法确认测试是否存在。

Sources / 来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L106–L110](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L106-L110), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L276–L287](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L276-L287)

<!-- kb:knowledge owner=feature-xiaoyi-calendar-tools facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**命令参数为静态构造**

两个工具的设备命令参数在代码中硬编码：目标 bundle 均为 `com.huawei.hmos.calendardata`，`executeMode: "background"`、`needUnlock: True`、`achieveType: "INTENT"`，payload 中均含 `timeOut: 5`（单位在所示片段中未标注）。差异在于：search 的 `executeParam` 额外含 `appType: "OHOS_APP"` 和 `permissionId: []`，而 create 的注释明确其 executeParam 不含这两项（L137、L251、L254）。所示片段中未出现从环境或配置文件读取的设置项。

Sources / 来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L137–L161](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L137-L161), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L244–L261](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L244-L261)

<!-- kb:knowledge owner=feature-xiaoyi-calendar-tools facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**支持的行为与依赖**

create 将 `yyyy-mm-dd hh:mm:ss` 字符串经 `datetime.strptime` 转为毫秒时间戳，以 `intentParam` 的 `dtStart/dtEnd` 下发 `CreateCalendarEvent` 意图（L122–L135、L147）。search 用模块内辅助 `_parse_time_string_ymd_hhmmss` 解析 `YYYYMMDD hhmmss`，以 `timeInterval` [起, 止] 毫秒区间下发 `SearchCalendarEvent`，可选 `title` 过滤；结果从 `result.items` 取出并经 `_convert_event_timestamps` 转为可读时间（L222–L235、L270–L274）。两者均依赖共享的 `execute_device_command` 下发命令（L164、L265）。

Sources / 来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L120–L135](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L120-L135), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L222–L235](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L222-L235), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L264–L274](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L264-L274)

<!-- kb:knowledge owner=feature-xiaoyi-calendar-tools facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**时间格式不统一与提示层超时约束**

Inference / 设计推断（非作者历史意图）：

推断（无作者意图的文档证据）：两个工具采用不同的时间输入格式——create 用 `yyyy-mm-dd hh:mm:ss`（datetime.strptime 校验），search 用 `YYYYMMDD hhmmss`（_parse_time_string_ymd_hhmmss 校验）——各自匹配工具描述，但调用方需按工具区分格式。另外，工具描述声称执行最长可达 60 秒并要求“勿重复调用、最多重试一次、先获取当前真实时间”，这是提示层约束；所示代码中唯一的数值超时是设备命令里的 timeOut: 5，未见代码层强制 60 秒上限或重试限制。

Sources / 来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L87–L89](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L87-L89), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L193–L195](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L193-L195), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L120–L129](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L120-L129), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L222–L229](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L222-L229)

<!-- kb:knowledge owner=feature-xiaoyi-calendar-tools facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**工具入口与错误契约**

两个公开入口均为用 `@tool` 装饰的异步可调用工具：`create_calendar_event(title, dt_start, dt_end)` 和 `search_calendar_event(start_time, end_time, title=None)`，返回 `Dict[str, Any]`。当传入空字符串（如 `title`/`dt_start`/`dt_end` 或 `start_time`/`end_time` 为空、时间格式非法）时，函数体内抛出 `ToolInputError` 且不被兜底 except 转换；其余异常被包装为 `RuntimeError`（中文消息「创建日程失败/搜索日程失败」）重新抛出。成功时通过 `format_success_response` 返回包含结果或日程列表的字典。

Sources / 来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L91–L95](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L91-L95), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L113–L118](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L113-L118), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L198–L202](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L198-L202), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L283–L287](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L283-L287)

