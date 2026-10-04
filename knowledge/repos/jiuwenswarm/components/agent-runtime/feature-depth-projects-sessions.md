---
title: "项目、会话与历史管理：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/session_catalog.py:L230-L281, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/session_catalog.py:L162-L188, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/session_catalog.py:L156-L159, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/mode_matrix.py:L309-L326, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/session_catalog.py:L119-L131, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/session_catalog.py:L1-L19, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/项目与会话管理.md:L130-L149", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/system_tests/test_process_cli_session_runtime_live.py:L78-L142, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/system_tests/test_process_cli_session_runtime_live.py:L24-L31, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/session_catalog.py:L94-L98, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/session_catalog.py:L211-L227, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/session/coordinator.py:L763-L789, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/session/work_scheduler.py:L132-L152, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/service.py:L1120-L1140]
feature: "projects-sessions"
entry_points: ["jiuwenswarm/runtime/session_catalog.py", "jiuwenswarm/runtime/session_lifecycle.py"]
source_globs: ["jiuwenswarm/runtime/session_catalog.py", "jiuwenswarm/runtime/session_lifecycle.py", "jiuwenswarm/runtime/session*.py"]
---

# 项目、会话与历史管理：实现深读

[功能概览](feature-projects-sessions.md) · [owner 入口](_index.md)

<!-- kb:depth feature=projects-sessions facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3bdb5accc849d940eea6a5f1433b0102e99267b3c000008823d16fc527554e30 -->
**会话列表查询链路：list_sessions 投影过滤到模式归一**
调用方传入 SessionListInput（channel_id、limit/offset、search）。list_sessions 先校验 channel 与分页，再遍历 _collect_session_metadata 的每条 metadata：_project_session 按 channel_id 归一比较、经 _single_agent_mode 用 deprecate_mode 把旧 canonical 模式映射到新值并只保留单 Agent 模式，最后构造 SessionSummary；命中 search 词的项按 last_message_at 降序排序并切片分页，返回 SessionListResult。

调用路径：`jiuwenswarm/runtime/session_catalog.py`（`list_sessions`） → `jiuwenswarm/runtime/session_catalog.py`（`_project_session`） → `jiuwenswarm/runtime/session_catalog.py`（`_single_agent_mode`） → `jiuwenswarm/common/mode_matrix.py`（`deprecate_mode`）

来源：[jiuwenswarm/runtime/session_catalog.py:L230–L281](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_catalog.py#L230-L281), [jiuwenswarm/runtime/session_catalog.py:L162–L188](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_catalog.py#L162-L188), [jiuwenswarm/runtime/session_catalog.py:L156–L159](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_catalog.py#L156-L159), [jiuwenswarm/common/mode_matrix.py:L309–L326](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mode_matrix.py#L309-L326)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/runtime/session_catalog.py","start":230,"end":281,"sha256":"96ee70f8ffcf82fd1e7bc31daede832a1d3bbf9b1d13d28b7a74373f68b795a8"},{"path":"jiuwenswarm/runtime/session_catalog.py","start":162,"end":188,"sha256":"1279af566b829e6990bd19bee9ba1c8513c05b1ea53c5d1faae8dc46f1298b5e"},{"path":"jiuwenswarm/runtime/session_catalog.py","start":156,"end":159,"sha256":"5aeec3f3659f66b184c3f52e8f6eced51dde4e1fbb0eff6f419aa985461687e1"},{"path":"jiuwenswarm/common/mode_matrix.py","start":309,"end":326,"sha256":"bc8108e2b196f629e8c22e0f7f8fe79d4b220357a519cc5f6a9898b640ba4b38"}],"trace":[{"path":"jiuwenswarm/runtime/session_catalog.py","symbol":"list_sessions","start":230,"end":281},{"path":"jiuwenswarm/runtime/session_catalog.py","symbol":"_project_session","start":162,"end":188},{"path":"jiuwenswarm/runtime/session_catalog.py","symbol":"_single_agent_mode","start":156,"end":159},{"path":"jiuwenswarm/common/mode_matrix.py","symbol":"deprecate_mode","start":309,"end":326}]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=projects-sessions facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=eb87b4ea7c7a5244156b68b70a1a67ed392c12a38d7c63af79136085ddf7d20e -->
**list_sessions 的输入契约与分页输出**
调用方必须传入 SessionListInput 实例：channel_id 去除首尾空白并转小写后非空，否则抛 SessionCatalogError(code="BAD_REQUEST")；limit 必须是 1..200 的整数（排除 bool），offset 为非负整数；search 必须是长度 ≤200 的字符串。通过后按 last_message_at 降序、session_id 升序排序，返回 SessionListResult 页（sessions/total/limit/offset），total 是过滤后的总数而非当前页大小。

来源：[jiuwenswarm/runtime/session_catalog.py:L230–L281](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_catalog.py#L230-L281), [jiuwenswarm/runtime/session_catalog.py:L94–L98](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_catalog.py#L94-L98), [jiuwenswarm/runtime/session_catalog.py:L119–L131](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_catalog.py#L119-L131)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/runtime/session_catalog.py","start":230,"end":281,"sha256":"96ee70f8ffcf82fd1e7bc31daede832a1d3bbf9b1d13d28b7a74373f68b795a8"},{"path":"jiuwenswarm/runtime/session_catalog.py","start":94,"end":98,"sha256":"15394dd0b737b1ccd5a333557e9f3f072741e2ecb103e3249b5e9753bd306a9c"},{"path":"jiuwenswarm/runtime/session_catalog.py","start":119,"end":131,"sha256":"bce77a05f8ac9a143ebf5eb016c05ea3a8954bbc08a7ca0211e5800013d46f3d"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=projects-sessions facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=952d8b7b14d1afdf5f5ee03d9d5096245881f7978e4bd8015648fdd5ba1b511b -->
**分页默认值与上限**
模块常量 _DEFAULT_LIMIT=20、_MAX_LIMIT=200；_validate_page 强制 limit 为 1..200 的 int（bool 显式排除），offset 为非负 int，否则抛 "limit must be between 1 and 200" / "offset must be a non-negative integer"（code="BAD_REQUEST"）。文档侧 session.list 同样写明 limit 默认 20、最大 200。

来源：[jiuwenswarm/runtime/session_catalog.py:L119–L131](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_catalog.py#L119-L131), [jiuwenswarm/runtime/session_catalog.py:L1–L19](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_catalog.py#L1-L19), [docs/zh/项目与会话管理.md:L130–L149](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E9%A1%B9%E7%9B%AE%E4%B8%8E%E4%BC%9A%E8%AF%9D%E7%AE%A1%E7%90%86.md#L130-L149)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/runtime/session_catalog.py","start":119,"end":131,"sha256":"bce77a05f8ac9a143ebf5eb016c05ea3a8954bbc08a7ca0211e5800013d46f3d"},{"path":"jiuwenswarm/runtime/session_catalog.py","start":1,"end":19,"sha256":"99c4c88ef853f863dc80425364a2fb2db0d5df0a1d6df1382499dd130af16b34"},{"path":"docs/zh/项目与会话管理.md","start":130,"end":149,"sha256":"13215362c91f4794f9ee6f86c711a5a9ec579ce1810a226251579f35e450624f"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=projects-sessions facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1043e39e8f7a86d83412cd33b4c02d675c51029dafa8093dc0463e1fd4aeb7ed -->
**活体两轮恢复门测**
tests/system_tests/test_process_cli_session_runtime_live.py::test_process_cli_two_turn_session_resume_live 通过 app.run 跑两轮对话，断言第二轮返回同一 session_id、load_history_records 记录数增长，且协调器快照 state 为 CLOSED、所有 execution 终态。该测试带 system/slow 标记，仅在 RUN_LIVE_SESSION_RUNTIME_TESTS=1/true/yes 时执行（需真实模型），此处仅记录入口与断言范围，不代表当前已通过。

来源：[tests/system_tests/test_process_cli_session_runtime_live.py:L78–L142](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/system_tests/test_process_cli_session_runtime_live.py#L78-L142), [tests/system_tests/test_process_cli_session_runtime_live.py:L24–L31](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/system_tests/test_process_cli_session_runtime_live.py#L24-L31)

<!-- kb:depth-proof {"evidence":[{"path":"tests/system_tests/test_process_cli_session_runtime_live.py","start":78,"end":142,"sha256":"fe0e8c48bcae7b6fb6609ecc6bee187904b2b4b4d141a94468b80456ff39a46d"},{"path":"tests/system_tests/test_process_cli_session_runtime_live.py","start":24,"end":31,"sha256":"c4fd4976697e8bb10ee9e3f6ccde3bcc1ac799a2860a16446b606de1d6b65186"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=projects-sessions facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=234a4589188548aa8cd0d2490e112effe1324fc942775da200ddddbfe00f005f -->
**协调器超时先抛错、无超时才关调度器；Runtime cancel_all 委托 AgentManager**
协调器 close：timed_out 非空先抛 SessionCloseTimeoutError，否则才以 self._cancel_timeout 调 self._scheduler.close（默认 wait_timeout=5.0 被覆盖）；AgentRuntime.cancel_all_inflight_work 经 _closed 守卫（否则抛 RuntimeStateError）委托 _agent_manager 同名方法。

来源：[jiuwenswarm/runtime/session/coordinator.py:L763–L789](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session/coordinator.py#L763-L789), [jiuwenswarm/runtime/session/work_scheduler.py:L132–L152](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session/work_scheduler.py#L132-L152), [jiuwenswarm/runtime/service.py:L1120–L1140](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/service.py#L1120-L1140)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":789,"path":"jiuwenswarm/runtime/session/coordinator.py","sha256":"5ffbf1698153d2bde82f88dcf157fc92e69ca7fb640e4c887e5350b282da26ef","start":763},{"end":152,"path":"jiuwenswarm/runtime/session/work_scheduler.py","sha256":"08a0349dee6291a1d562631836ffdb2be951de018099e0a2122c34cbaf888c34","start":132},{"end":1140,"path":"jiuwenswarm/runtime/service.py","sha256":"225dbab5a831d41cbe073be1b6b9df90f4388efb5405f24ea8f75f067ba120c7","start":1120}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=projects-sessions facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4112a2b80176b9351cdc52fb8d92597821ce0d11f0cfd5ea8ec9b7a71ca24346 -->
**get_session：非目录异常包装为 READ_FAILED，空元数据返回 None**
在 `get_session` 中，`_read_session_metadata` 抛出的 `SessionCatalogError` 原样上抛；其余 `Exception` 被包装为 `SessionCatalogError("failed to read session", code="READ_FAILED")` 并以 `from None` 传播给调用方；若读到的 metadata 为空或非 Mapping，则返回 None 而不抛错。

来源：[jiuwenswarm/runtime/session_catalog.py:L211–L227](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_catalog.py#L211-L227)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":227,"path":"jiuwenswarm/runtime/session_catalog.py","sha256":"c86d5b5ee0dc6f9972ed8e2d64964efeeed2d4e775bcf6cfff583eef3856d5b1","start":211}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=projects-sessions facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=43134f01c72f972cf02f15975cd68c758e049e12f81bc4c6ff64cca6cfbc444a -->
**Coordinator.close 聚合各会话关闭异常但只抛 errors[0]；timed_out 非空时在调度器关闭前抛 SessionCloseTimeoutError**
设计推断（非作者历史意图）：

收益（推断）：单条 close_session 异常仅追加进 errors，循环继续关闭其余 record（772-779）；代价：无超时时只有 errors[0] 向上传播（788-789），timed_out 非空则 780-783 在 785 的 _scheduler.close 之前抛出，该分支跳过调度器关闭。

来源：[jiuwenswarm/runtime/session/coordinator.py:L763–L789](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session/coordinator.py#L763-L789)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":789,"path":"jiuwenswarm/runtime/session/coordinator.py","sha256":"5ffbf1698153d2bde82f88dcf157fc92e69ca7fb640e4c887e5350b282da26ef","start":763}],"trace":[]} -->
<!-- /kb:depth -->
