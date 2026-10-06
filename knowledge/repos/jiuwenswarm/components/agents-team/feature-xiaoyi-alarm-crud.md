---
title: "小艺手机工具 — 设备闹钟 CRUD（create/search/modify/delete_alarm）"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py:L320-L333, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py:L263-L288, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L58-L96, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L168-L207, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py:L596-L601, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py:L205-L221, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L87-L104, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py:L263-L278, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py:L286-L292, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L210-L228]
feature: "xiaoyi-alarm-crud"
entry_points: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py", "jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py", "jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py", "jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py"]
---

# 小艺手机工具 — 设备闹钟 CRUD（create/search/modify/delete_alarm）

<!-- kb:knowledge owner=feature-xiaoyi-alarm-crud facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**验证入口未在所示范围内出现**

所示片段不包含任何测试文件或测试引用；本任务无法基于这些证据描述该功能的测试入口与覆盖情况。

Sources / 来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py:L320–L333](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py#L320-L333)

<!-- kb:knowledge owner=feature-xiaoyi-alarm-crud facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**命令构造 + 共享通道执行**

每个工具本地校验参数并构造一个 `header: Common/Action` 命令，`executeParam` 固定指向 `bundleName: com.huawei.hmos.clock` 与对应 intentName（CreateAlarm/SearchAlarm/ModifyAlarm/DeleteAlarm），然后交给共享的 `execute_device_command`。该函数从 runtime 取 xiaoyi channel，从 config 读会话标识，注册按 `intent_name` 匹配的 data-event 处理器，`asyncio.wait_for` 默认 60 秒等待响应，并在 finally 中注销处理器。`delete_alarm` 的输入归一化委托给未在节选中展示的 `_normalize_delete_items`。

Sources / 来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py:L263–L288](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py#L263-L288), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L58–L96](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L58-L96), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L168–L207](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L168-L207), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py:L596–L601](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py#L596-L601)

<!-- kb:knowledge owner=feature-xiaoyi-alarm-crud facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**创建默认值、枚举校验与会话配置**

`create_alarm` 在参数缺省时填入默认值：标题 "闹钟"、`alarm_snooze_duration=10`、`alarm_snooze_total=0`、`alarm_ring_duration=5`、`days_of_wake_type=0`，随后对枚举型字段做成员校验（合法值集合定义于未展示的模块级常量 `_ALARM_SNOOZE_DURATION` 等，节选只显示校验逻辑与报错文案）。运行时会话身份从 config 读取：`channels.xiaoyi.last_session_id` / `last_task_id`；缺少有效 session_id 时抛 RuntimeError。命令内常量固定：`timeOut: 5`、`needUnlock: True`、`executeMode: background`。

Sources / 来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py:L205–L221](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py#L205-L221), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L87–L104](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L87-L104), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py:L263–L278](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py#L263-L278)

<!-- kb:knowledge owner=feature-xiaoyi-alarm-crud facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**所示输入中的验证入口**

所示文件节选（alarm_tools.py、utils.py 及对照的 calendar/contact tools）均为实现代码，不含测试文件或测试引用；本页无法基于这些证据描述该功能的测试入口与覆盖情况。已有的验证手段是运行时防御：参数校验抛 `ToolInputError`、设备错误经 `raise_if_device_error` 检查 `code`/`retErrCode` 后抛 RuntimeError。

Sources / 来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py:L286–L292](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py#L286-L292), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L210–L228](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L210-L228)

