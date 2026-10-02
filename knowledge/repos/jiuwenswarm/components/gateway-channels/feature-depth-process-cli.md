---
title: "机器执行与本地 CLI：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/process_cli/app.py:L732-L921, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/process_cli/app.py:L80-L116, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/process_cli/display_context.py:L228-L252, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/schema/agent.py:L68-L94, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/process_cli/client.py:L73-L252, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/process_cli/test_control_commands.py:L1-L180, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/process_cli/app.py:L855-L860, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/命令行指令.md:L241-L242", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/process_cli/control_commands.py:L22-L28, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/process_cli/control_commands.py:L53-L57, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/process_cli/app.py:L867-L888, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/process_cli/app.py:L924-L929, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/process_cli/protocol/model.py:L669-L682, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/process_cli/machine_result.py:L90-L96]
feature: "process-cli"
entry_points: ["jiuwenswarm/channels/process_cli/app.py"]
source_globs: ["jiuwenswarm/channels/process_cli/app.py", "jiuwenswarm/channels/process_cli/*.py"]
---

# 机器执行与本地 CLI：实现深读

[功能概览](feature-process-cli.md) · [owner 入口](_index.md)

<!-- kb:depth feature=process-cli facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3b6343ed64cf88b7a4a76598ae3095e55dc83b0eb837a69ca1222f158cce208e -->
**Chat request construction chain: run.execute → _build_request → resolve_cli_work_mode**
In the chat operation, run.execute first calls create_or_resume_session to obtain a session ID, then passes it into _build_request. _build_request calls resolve_cli_work_mode with args.mode and args.work_mode to determine the work mode (a mode with a two-segment profile like agent.code uses the embedded profile and takes precedence), and finally assembles an AgentRequest with channel_id="process_cli" and is_stream=True for streaming submission.

调用路径：`jiuwenswarm/channels/process_cli/app.py`（`run.execute`） → `jiuwenswarm/channels/process_cli/app.py`（`_build_request`） → `jiuwenswarm/channels/process_cli/display_context.py`（`resolve_cli_work_mode`）

来源：[jiuwenswarm/channels/process_cli/app.py:L732–L921](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/process_cli/app.py#L732-L921), [jiuwenswarm/channels/process_cli/app.py:L80–L116](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/process_cli/app.py#L80-L116), [jiuwenswarm/channels/process_cli/display_context.py:L228–L252](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/process_cli/display_context.py#L228-L252), [jiuwenswarm/common/schema/agent.py:L68–L94](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/schema/agent.py#L68-L94)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/process_cli/app.py","start":732,"end":921,"sha256":"63ee0b3bfe0bbb027c6fbace0e78eb8cd518a77a52e3813696520024595c98f6"},{"path":"jiuwenswarm/channels/process_cli/app.py","start":80,"end":116,"sha256":"5d972f0161f1ce9d5931b037a14a8cba17d3b24fd7787bb01b0db5f69ae17777"},{"path":"jiuwenswarm/channels/process_cli/display_context.py","start":228,"end":252,"sha256":"db7dbedb6947e84e7aecbd86b0f5b12b900dbd645409679058a95c576853bf38"},{"path":"jiuwenswarm/common/schema/agent.py","start":68,"end":94,"sha256":"114d1e8a37aed90b06d608423f9b153d46018439c9d0606e460377b8b3227662"}],"trace":[{"path":"jiuwenswarm/channels/process_cli/app.py","symbol":"run.execute","start":754,"end":853},{"path":"jiuwenswarm/channels/process_cli/app.py","symbol":"_build_request","start":80,"end":116},{"path":"jiuwenswarm/channels/process_cli/display_context.py","symbol":"resolve_cli_work_mode","start":228,"end":252}]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=process-cli facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=59385e4a819d9eee7f562e3def2df35718cd6a9c0d7904dc6f38b695ef318f78 -->
**In-process coupling with AgentRuntime**
InProcessRuntimeClient directly holds an AgentRuntime instance in __init__ (or injects one), with start/stream/invocation/session methods forwarding directly to it, without any socket or line protocol. This determines that the process CLI process itself is responsible for starting and cleaning up the Runtime (client.close in run's finally block).

来源：[jiuwenswarm/channels/process_cli/client.py:L73–L252](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/process_cli/client.py#L73-L252), [jiuwenswarm/channels/process_cli/app.py:L732–L921](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/process_cli/app.py#L732-L921)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/process_cli/client.py","start":73,"end":252,"sha256":"c764dbb52863db86c68c7a947b8ec1b62529f0947a92ec8a9d957245307135c6"},{"path":"jiuwenswarm/channels/process_cli/app.py","start":732,"end":921,"sha256":"63ee0b3bfe0bbb027c6fbace0e78eb8cd518a77a52e3813696520024595c98f6"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=process-cli facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9c23c96d1f9598edf4726bb003f68b77062e415784ae8564342bf79ab175b015 -->
**Unit test entry points for interactive control commands**
tests/unit_tests/process_cli/test_control_commands.py::test_sessions_status_and_permissions_query_current_runtime_state replaces query_runtime and asserts that /sessions, /status, /permissions trigger session.list, session.get, permission.get in order with correct parameters, and that the output contains the current session marker and model line. Another test test_sessions_search_and_selection_restore_owned_session exercises search pagination parameter iteration and the session_id update after selection.

来源：[tests/unit_tests/process_cli/test_control_commands.py:L1–L180](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/process_cli/test_control_commands.py#L1-L180)

<!-- kb:depth-proof {"evidence":[{"path":"tests/unit_tests/process_cli/test_control_commands.py","start":1,"end":180,"sha256":"0bcc4bac69eb3519ab2885f392557adefb313f3465ce9bc7129b353bfaecd3fb"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=process-cli facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6989f700edb1c0735b5e92ede60e7b4249a1997e01b8f20407a2f5be93856490 -->
**OneShotRunResult 构造期校验 error 类型与 status/exit_code 组合**
构造时若 error 非空且不是 RuntimeErrorInfo，抛 TypeError("error must be RuntimeErrorInfo")；status 等于 RunStatus.COMPLETED.value 时要求 session_id 存在、exit_code 为 0 且 error 为 None，任一违反抛 ValueError。

来源：[jiuwenswarm/channels/process_cli/protocol/model.py:L669–L682](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/process_cli/protocol/model.py#L669-L682)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":682,"path":"jiuwenswarm/channels/process_cli/protocol/model.py","sha256":"01fe1fc3eafc7b0ef596c480e01d23d445511b30964a233776f3a9fca58d0a12","start":669}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=process-cli facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=213577aee6b915c2478dc3fce0648a64f94f2fcff893e38e25ce0a4f61745667 -->
**--timeout 缺省时不包装 execute()；query_runtime 的 timeout 默认 30.0**
app.py 仅在 `args.timeout is not None` 时用 asyncio.timeout(args.timeout) 包住 execute()（文档选项表 `--timeout <seconds>` 默认为 —，未设置即无此截止包装）；query_runtime 的 timeout 形参默认 30.0，作为请求中的 timeout_seconds 发送，外层 wait_for 另用 timeout + 5 兜底。

来源：[jiuwenswarm/channels/process_cli/app.py:L855–L860](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/process_cli/app.py#L855-L860), [docs/zh/命令行指令.md:L241–L242](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%91%BD%E4%BB%A4%E8%A1%8C%E6%8C%87%E4%BB%A4.md#L241-L242), [jiuwenswarm/channels/process_cli/control_commands.py:L22–L28](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/process_cli/control_commands.py#L22-L28), [jiuwenswarm/channels/process_cli/control_commands.py:L53–L57](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/process_cli/control_commands.py#L53-L57)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":860,"path":"jiuwenswarm/channels/process_cli/app.py","sha256":"f1e8aa19a2dfaff0cc90e53a9eb89b9c05902c65b2c5ae6ba3cc565846482dd6","start":855},{"end":242,"path":"docs/zh/命令行指令.md","sha256":"283e9e70addbb7b7893a094799cb98b8b65d7eae49cc820d0ce100d6dae9002b","start":241},{"end":28,"path":"jiuwenswarm/channels/process_cli/control_commands.py","sha256":"32cbb35990bb30db47620b057ea8c232a35fd45464387eff908a1b5a617ba637","start":22},{"end":57,"path":"jiuwenswarm/channels/process_cli/control_commands.py","sha256":"d9e62eae4d1246f805a0450130885b599c3aff9d851ce79510f9c233a65f685f","start":53}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=process-cli facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1e9e8a1869b88c8ca5054d8ac214baf9c8192d7ba6f24204398027807b5d898a -->
**run.execute 超时返回 124、CancelledError 重抛；仅 CHAT 且 request 非空时执行有界 cancel**
TimeoutError 分支在 request 不为 None 且 operation == CHAT_OPERATION 时 `await _bounded_cleanup(client.cancel(_cancel_request(request)))`——wait_for 限时 SHUTDOWN_STEP_TIMEOUT_SECONDS 并吞掉 Exception——然后渲染 TimeoutError 错误事件并 return 124；CancelledError 分支同样有界取消、renderer.interrupted() 后 raise。

来源：[jiuwenswarm/channels/process_cli/app.py:L867–L888](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/process_cli/app.py#L867-L888), [jiuwenswarm/channels/process_cli/app.py:L924–L929](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/process_cli/app.py#L924-L929)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":888,"path":"jiuwenswarm/channels/process_cli/app.py","sha256":"6e90b5a4fab5bb59317255db831c1b957c9fac2fb20889dcc81aac3eaff84d07","start":867},{"end":929,"path":"jiuwenswarm/channels/process_cli/app.py","sha256":"3cbe3d94cb75fa2c59b0b30fef84d5965526cbb23f36daec9ba3d059095c88d0","start":924}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=process-cli facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d505df172224b085c7f4b5abde036f712e2ab6e03678d6a9a16f30ce007a8a87 -->
**details 构造失败时丢弃诊断以保留原始失败（TypeError/ValueError 分支）**
设计推断（非作者历史意图）：

当构造 details 引发 TypeError/ValueError 时，该分支改返回不含 details 的 RuntimeErrorInfo：收益（代码注释：可选诊断不得掩盖执行失败、不得序列化任意 Runtime 对象），代价是这些诊断信息被静默丢弃。

来源：[jiuwenswarm/channels/process_cli/machine_result.py:L90–L96](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/process_cli/machine_result.py#L90-L96)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":96,"path":"jiuwenswarm/channels/process_cli/machine_result.py","sha256":"f05640a0009ba63dc5d46f57b955c034610831b051a47836af6e48b9e9a6e39d","start":90}],"trace":[]} -->
<!-- /kb:depth -->
