---
title: "Session Input Lane (steer/follow_up) and Execution Binding：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/session_input.py:L58-L73, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/service.py:L2159-L2176, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/session_input.py:L65-L73, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/runtime/test_session_input.py:L257-L274, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/service.py:L1319-L1325, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/service.py:L1747-L1769, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/session_input.py:L33-L55, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/service.py:L1748-L1761]
feature: "session-input-steering"
entry_points: ["jiuwenswarm/runtime/service.py"]
source_globs: ["jiuwenswarm/runtime/service.py", "jiuwenswarm/runtime/session_input.py"]
---

# Session Input Lane (steer/follow_up) and Execution Binding：实现深读

[功能概览](feature-session-input-steering.md) · [owner 入口](_index.md)

<!-- kb:depth feature=session-input-steering facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=30cc3d8cc24451e5238a77e87b15bdb98599a5e2f7ea948f464d5e6c806b1dd6 -->
**AgentRuntime.invoke delegates session-input requests to stream, which validates then routes CONTROL_INPUT to _deliver_control**
In invoke, when _is_session_input_request(request) is true the branch consumes self.stream(...) and returns only events whose payload is not None. In stream, after validate_session_input, a foreground-only guard, cross-session admission and session snapshot/state checks, session_work_kind returning CONTROL_INPUT routes the request to _deliver_control with the caller's on_control_event.

来源：[jiuwenswarm/runtime/service.py:L1319–L1325](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/service.py#L1319-L1325), [jiuwenswarm/runtime/service.py:L1747–L1769](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/service.py#L1747-L1769)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1325,"path":"jiuwenswarm/runtime/service.py","sha256":"97581795a6d7f2e25c14d3dab9695f6d6987430c5900d1fc29c45dd396ccec11","start":1319},{"end":1769,"path":"jiuwenswarm/runtime/service.py","sha256":"5499a159b6219fd18b6e93dd1b785e2e787f39a740120af1b2d4353922bb0d33","start":1747}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=session-input-steering facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=39c1d0213962de1c57caacd8c97b91aa06812eeabfc37314ab685154b22dcf22 -->
**validate_session_input caller obligations: non-empty query, steer-only binding, text-only steer**
validate_session_input(params) raises ValueError unless params['query'] is non-blank text; if 'expected_execution_id' is present it must be a non-empty string and resolve_session_input_mode(params) must be STEER; in STEER mode any non-empty images/image_files/files/attachments/audio_files/video_files raise ValueError("steering supports text only; send attachments as a queued task").

来源：[jiuwenswarm/runtime/session_input.py:L58–L73](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_input.py#L58-L73)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":73,"path":"jiuwenswarm/runtime/session_input.py","sha256":"58e417b8c5af98b9bb74d34381c73ba86868601177686cf0b6bed7b4313de972","start":58}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=session-input-steering facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f0603fc9fc675291ba944fc8f1af42f1dce2aa1ab5c162e998a3f589eba1670d -->
**input_mode wins over the runtime_mode alias; both truthy and differing raises; unknown values fall back to None**
resolve_session_input_mode reads params['input_mode'] (primary) and params['runtime_mode'] (alias); if both are truthy and their normalized forms differ it raises ValueError('input_mode and runtime_mode must agree'), otherwise the primary (or alias when primary is falsy) is normalized and mapped to SessionInputMode, with unknown values returning None. The docstring notes interaction answers are classified separately before this intent.

来源：[jiuwenswarm/runtime/session_input.py:L33–L55](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_input.py#L33-L55)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":55,"path":"jiuwenswarm/runtime/session_input.py","sha256":"6885d1477a31ef0889eebb6d21a43e01ef5cea794c72780a4c70122691ead43d","start":33}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=session-input-steering facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5e8d497b4a8bcd5f7f9976f6a4a0e857e1b140bff507d5d3eb2b576026c1179a -->
**Supplement delivery requires an active agent exposing deliver_session_input**
Input delivery looks up the agent via agent_manager.get_agent_for_session_nowait(owner_channel, session_id); if no agent is found it raises SessionInputRejectedError("session has no active agent: ..."), and if the agent lacks a callable deliver_session_input it raises SessionInputRejectedError("active agent does not support supplemental input") before streaming.

来源：[jiuwenswarm/runtime/service.py:L2159–L2176](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/service.py#L2159-L2176)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":2176,"path":"jiuwenswarm/runtime/service.py","sha256":"d03a29adf86ba68ad626d15cd1b542c59ac9da20bba3114f7eb69134a07073b1","start":2159}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=session-input-steering facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=609b7bf134d7b4f49fd2cec3fd9c53dccd62ab878690de932ec98c7238eb90af -->
**validate_session_input raises ValueError for blank query, non-steer expected_execution_id, and steer attachments**
If params contains expected_execution_id it must be a non-empty string and the resolved mode must be STEER, else ValueError; a query that is not a non-empty-trimmed string raises 'session input requires non-empty text'; in STEER mode any truthy value among images/image_files/files/attachments/audio_files/video_files raises 'steering supports text only; send attachments as a queued task'. Separately, stream raises ValueError for background session input and RuntimeStateError when the session snapshot is missing or in CLOSED/QUIESCING.

来源：[jiuwenswarm/runtime/session_input.py:L58–L73](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_input.py#L58-L73), [jiuwenswarm/runtime/service.py:L1748–L1761](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/service.py#L1748-L1761)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":73,"path":"jiuwenswarm/runtime/session_input.py","sha256":"58e417b8c5af98b9bb74d34381c73ba86868601177686cf0b6bed7b4313de972","start":58},{"end":1761,"path":"jiuwenswarm/runtime/service.py","sha256":"fb6d7b0f0f8a301da7f1aea37e633e9d3032d3777de2bf5190bff721fffe5b40","start":1748}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=session-input-steering facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fe2e58dbdee4d9da2e51931c4345a889b675743d8d8ddd0aa6a1bfad9049f3b4 -->
**Steering accepts text only: avoids silent attachment loss at the cost of a separate queued task**
设计推断（非作者历史意图）：

The comment at session_input.py:68-73 states the SDK's active steering queue carries text only, so non-empty attachment keys are rejected rather than acknowledged-and-dropped; the cost (design inference) is that callers with attachments must send them as an ordinary queued task instead of a steer.

来源：[jiuwenswarm/runtime/session_input.py:L65–L73](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_input.py#L65-L73)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":73,"path":"jiuwenswarm/runtime/session_input.py","sha256":"115547298cfe2717edc2cb807397538f47f4735b6709f53ef3d43a9b59387a34","start":65}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=session-input-steering facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=79e799de328e92905d7bc7db3e4d666de7c9c84285fbd101bb830c046bf04f56 -->
**Automated runtime test asserts bound input keeps the original execution and returns its id**
test_bound_input_keeps_original_execution_and_returns_its_id (parametrized unary/stream) starts an original stream, snapshots the coordinator to get target execution_id, sends request(expected_execution_id=target), asserts events == [runtime.accepted] with payload['execution_id'] == target, exactly one CHAT_STREAM execution remains, original is not done and agent not cancelled, and the original's final event carries the same execution_id.

来源：[tests/unit_tests/runtime/test_session_input.py:L257–L274](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/runtime/test_session_input.py#L257-L274)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":274,"path":"tests/unit_tests/runtime/test_session_input.py","sha256":"700f91b991597c254451baf3d2678261d7339d27ea6deb1f86d61642d685b170","start":257}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
