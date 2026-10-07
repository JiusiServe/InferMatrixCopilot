---
title: "设备日历日程工具（create/search_calendar_event）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L113-L129, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L137-L164, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L166-L173, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L137-L160, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L244-L256, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L219-L229, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L265-L267, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L198-L207, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L210-L228, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L121-L125, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L72-L79, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L19-L24, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L163-L167, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L264-L267, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/agents/swarm/test_swarm_assembly.py:L1872-L1880, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/tools.py:L121-L150, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/tools.py:L461-L469]
feature: "xiaoyi-calendar-tools"
entry_points: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py"]
---

# 设备日历日程工具（create/search_calendar_event）：实现深读

[功能概览](feature-xiaoyi-calendar-tools.md) · [owner 入口](_index.md)

<!-- kb:depth feature=xiaoyi-calendar-tools facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ae20634ebed2441d906ebcbd43786b9b8e9c046de76c5c0259088c31b0abd2d5 -->
**create_calendar_event：校验后构造命令并经 execute_device_command 下发**
校验 title/dt_start/dt_end 非空，strptime 按 %Y-%m-%d %H:%M:%S 转毫秒时间戳，构造 executeParam 后 await execute_device_command("CreateCalendarEvent", command)；若 result 为 dict 才调用 raise_if_device_error，最后返回 format_success_response。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L113–L129](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L113-L129), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L137–L164](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L137-L164), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L166–L173](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L166-L173)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":129,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py","sha256":"d8f9ddb09452cae0bb3a582db1fc579a4967aca75bd37436851406af3d48b365","start":113},{"end":164,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py","sha256":"2c7b201cba3b138121480561fe01fd7efe09e1c8f133d178c213d0a857358ebc","start":137},{"end":173,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py","sha256":"f705847914b8993b10841fa241f37a126199dbd93d8aa029916917f037f00867","start":166}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-calendar-tools facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=472920258adec57f946d5d476d7c01abec4c730ae0b257cb11e609c8095f44a0 -->
**命令字面量硬编码：timeOut 5、bundleName com.huawei.hmos.calendardata**
两处命令构造均硬编码 executeMode="background"、timeOut 5、bundleName "com.huawei.hmos.calendardata"；create 的 executeParam 不含 appType/permissionId，search 则含 appType="OHOS_APP" 与 permissionId=[]。所示片段内无外部配置读取。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L137–L160](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L137-L160), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L244–L256](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L244-L256)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":160,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py","sha256":"93f7a10912fc4a6997a40fbe356dffef60fd274e68b47e9584defa7d2e7b7478","start":137},{"end":256,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py","sha256":"121af4bef125859d049d264c487bcb4016f64998f5519cb03088e687f5b3e222","start":244}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-calendar-tools facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f3b749558e27485e59b093ec80d2cf11e672ee00a205b474bb5a23dfbd1d7ac1 -->
**输入错误抛 ToolInputError；设备错误码与超时分别转 RuntimeError 传播**
search 中 start_time/end_time 缺失或 _parse_time_string_ymd_hhmmss 抛 ValueError 时转为 ToolInputError 并原样重抛；设备 outputs 的 code 失败或 retErrCode 非 "0" 时 raise_if_device_error 抛 RuntimeError；execute_device_command 超时抛 asyncio.TimeoutError 转为 RuntimeError，finally 中注销事件处理器。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L219–L229](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L219-L229), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L265–L267](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L265-L267), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L198–L207](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L198-L207), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L210–L228](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L210-L228)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":229,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py","sha256":"8289e32065ee30ae459d5477ae07f53884e8bcb1274157665c3d5c31f5c11886","start":219},{"end":267,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py","sha256":"2189769086d9c4e29b3db12505c1d09ea158db0e7f129f30d18b42b13f695203","start":265},{"end":207,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py","sha256":"14978fe0cb6f23d3b789c8877bf3809be5867f4e150aaa8c06653dfc3887d465","start":198},{"end":228,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py","sha256":"a169af0afefd26625f182cf29b8ee64ff9143b48e91f859ae040a396304da003","start":210}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-calendar-tools facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=994f6d8301e21578712b9ae43976899846775b15557059c803ea58d00736dde9 -->
**朴素 datetime 解析实现简单，但结果依赖主机本地时区**
设计推断（非作者历史意图）：

（推断）create 用 strptime+timestamp()、解析器用 datetime(...).timestamp()*1000，均按本地时区换算毫秒，实现简洁；代价是同一输入字符串在不同时区主机上产生不同的毫秒时间戳。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L121–L125](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L121-L125), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L72–L79](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L72-L79)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":125,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py","sha256":"9416a343568485f1869f6935951119d1e3f23aea9d58efed9e4b275d8a6591f4","start":121},{"end":79,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py","sha256":"73438926b086b59dd4fabddf8775ee0efebb8478c520b0bfee5b1dc987395d16","start":72}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-calendar-tools facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fd6f61e0716e10a973c57ff99680e2fc81dc8e51538be5bbcbbc1d3d4735ea33 -->
**依赖同包 .utils 辅助函数与共享 execute_device_command 下发命令**
模块从 .utils 导入 execute_device_command、format_success_response、raise_if_device_error、ToolInputError（L19–L24）。create 将命令委托给 await execute_device_command("CreateCalendarEvent", ...)，仅当 result 为 dict 时调用 raise_if_device_error（L163–L167）；search 委托 execute_device_command("SearchCalendarEvent", ...) 后无条件调用 raise_if_device_error（L264–L267）。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L19–L24](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L19-L24), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L163–L167](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L163-L167), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py:L264–L267](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py#L264-L267)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":24,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py","sha256":"7b3b9835146d384b2986af92efb6a62df16fbf47e6e1695841c6e3b61e0d9b63","start":19},{"end":167,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py","sha256":"c5b52c5ab0e2f96352e99d8af3884c9b7d8451e746797d395ea6618ea69b0d21","start":163},{"end":267,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py","sha256":"a09ea5d8b03edbad314dac31afdd2d15399f0492097e09cead8fa7ae04cd6748","start":264}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-calendar-tools facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3f375857f839aa1d74a695b1d712db55eb7ead8141508cc57805b0d5d722a96d -->
**既有装配测试仅覆盖配置开关门控（helper 级，未执行）**
tests/agents/swarm/test_swarm_assembly.py 的 test_xiaoyi_phone_tools_gated_by_config 实际调用 _build_xiaoyi_phone_tools：config 含 channels.xiaoyi.phone_tools_enabled=True 时断言返回 27 个工具，config 为空时断言返回 []。生产元组 _XIAOYI_PHONE_TOOLS 明确包含 create_calendar_event 与 search_calendar_event，故两工具的注册随该开关被此测试间接覆盖；但断言只检查聚合计数与空列表，不校验单工具身份、意图构造或设备执行结果。validation_kind 为 helper_unit：断言只覆盖构建 helper 本身。标注：本条为对既有测试的静态审读，测试未在本次执行。

来源：[tests/agents/swarm/test_swarm_assembly.py:L1872–L1880](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/agents/swarm/test_swarm_assembly.py#L1872-L1880), [jiuwenswarm/agents/swarm/providers/tools.py:L121–L150](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/tools.py#L121-L150), [jiuwenswarm/agents/swarm/providers/tools.py:L461–L469](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/tools.py#L461-L469)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1880,"path":"tests/agents/swarm/test_swarm_assembly.py","sha256":"937552f24d47dad020214418cf9aa430b1b2216fcf692530e3cf03099a34a880","start":1872},{"end":150,"path":"jiuwenswarm/agents/swarm/providers/tools.py","sha256":"3676650a09a0441ad25e82a12fd8ebbe503b9960efb9475671b40b741fd2a722","start":121},{"end":469,"path":"jiuwenswarm/agents/swarm/providers/tools.py","sha256":"9b10b462d3ed8ef84ff21833831933c9f431f48a177788b8e433376d3794e913","start":461}],"trace":[],"validation_kind":"helper_unit"} -->
<!-- /kb:depth -->
