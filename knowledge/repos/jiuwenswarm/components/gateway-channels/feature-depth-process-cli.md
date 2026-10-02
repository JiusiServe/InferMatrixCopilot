---
title: "机器执行与本地 CLI：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/process_cli/app.py:L732-L921, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/process_cli/app.py:L80-L116, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/process_cli/display_context.py:L228-L252, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/schema/agent.py:L68-L94, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/process_cli/client.py:L73-L252, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/process_cli/test_control_commands.py:L1-L180]
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
