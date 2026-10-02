---
title: "Agent Loop 与 Rail 装配：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L4363-L4374, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L4756-L4777, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L9561-L9568, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_agentserver_modes.py:L141-L170, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/test_app_agentserver.py:L57-L104, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/auto_harness/service.py:L1683-L1722, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/permissions/permissions_layers.py:L216-L227, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/stream_event_rail.py:L983-L998, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/stream_event_rail.py:L589-L611, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/Harness.md:L73-L84, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/stream_event_rail.py:L589-L622, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/stream_event_rail.py:L983-L994, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/stream_event_rail.py:L598-L622, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/stream_event_rail.py:L983-L985]
feature: "harness"
entry_points: ["jiuwenswarm/server/runtime/agent_adapter/interface_deep.py"]
source_globs: ["jiuwenswarm/server/runtime/agent_adapter/interface_deep.py", "jiuwenswarm/agents/harness/common/rails/*"]
---

# Agent Loop 与 Rail 装配：实现深读

[功能概览](feature-harness.md) · [owner 入口](_index.md)

<!-- kb:depth feature=harness facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f7ad9245dc714bbd6679c10f8bb772f683bfbdb8a223c90ddc9db69168b99366 -->
**浏览器运行时开关与 BROWSER_DRIVER 默认值**
_browser_runtime_enabled 依次读取环境变量 PLAYWRIGHT_RUNTIME_MCP_ENABLED、BROWSER_RUNTIME_MCP_ENABLED（先者优先），去空白并小写后属于 {"1","true","yes","on"} 才启用；浏览器子代理启用而 BROWSER_DRIVER 为空时，_build_configured_subagents 会写入默认值 "managed"。另有 _resolve_enable_subagent_runtime：_subagent_runtime_supported 缺省为 True，最终由 is_subagent_runtime_enabled(config_base 或 get_config()) 决定。

来源：[jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L4363–L4374](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L4363-L4374), [jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L4756–L4777](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L4756-L4777), [jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L9561–L9568](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L9561-L9568)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/server/runtime/agent_adapter/interface_deep.py","start":4363,"end":4374,"sha256":"16e3366b984c72a6bed8b57e79bf0f225f4e06b082176e89d25c715ac054e435"},{"path":"jiuwenswarm/server/runtime/agent_adapter/interface_deep.py","start":4756,"end":4777,"sha256":"03717cd3da00942464200858edd87462d6ec478f6ad54baa64987194277ce7d9"},{"path":"jiuwenswarm/server/runtime/agent_adapter/interface_deep.py","start":9561,"end":9568,"sha256":"abaa95e35dd022dfae21aea099882270b9cdaefded803e0e80c00e5339fb31a2"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=harness facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f0af6abc7a054783cb40deb9529151e85ec114cba873b1362715e668e1769b91 -->
**相关单测入口**
tests/unit_tests/agentserver/test_agentserver_modes.py 中 test_external_memory_finalize_retries_after_commit_failure 用 object.__new__(JiuWenSwarmDeepAdapter) 直接驱动 _finalize_external_memory_session，断言 provider 首次抛错后可重试、成功后才置 _external_memory_session_finalized=True；test_app_agentserver.py 的 test_run_does_not_delete_agent_teams_directory 断言 app_agentserver._run 的启动顺序且不删除目录。所提供切片中没有直接覆盖 rail 装配链的测试。

来源：[tests/unit_tests/agentserver/test_agentserver_modes.py:L141–L170](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/test_agentserver_modes.py#L141-L170), [tests/unit_tests/test_app_agentserver.py:L57–L104](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/test_app_agentserver.py#L57-L104)

<!-- kb:depth-proof {"evidence":[{"path":"tests/unit_tests/agentserver/test_agentserver_modes.py","start":141,"end":170,"sha256":"842c17cad31443f482e6d559a0a8aaff97af1de7178bee91aec973dcb726e3f3"},{"path":"tests/unit_tests/test_app_agentserver.py","start":57,"end":104,"sha256":"a101f94d75eccf694bdcb8e412812314ae404e8c09d6f5ae9a400f655a3962d5"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=harness facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=35e9cacc96abc465247f1b55f94293d3e21f0885e170d3f9e9c890ac3d6eb0df -->
**before_model_call 钩子：恢复门与 abort 检查后注入/清洗模型上下文**
before_model_call 属内层 ReAct 模型级钩子（文档）；回调解析 sid 后在该检查点等恢复闩锁（事件创建即置位，未暂停立即返回），_abort_requested.get(sid) 为真则抛 asyncio.CancelledError("Agent abort requested")，否则注入 call_goal ToolInfo schema；ctx.context 非 None 时若 _read_image_multimodal_enabled() 为假则剥离图片内容并修复不完整工具上下文。

来源：[jiuwenswarm/agents/harness/common/rails/stream_event_rail.py:L983–L998](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/stream_event_rail.py#L983-L998), [jiuwenswarm/agents/harness/common/rails/stream_event_rail.py:L589–L611](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/stream_event_rail.py#L589-L611), [docs/zh/Harness.md:L73–L84](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Harness.md#L73-L84)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":998,"path":"jiuwenswarm/agents/harness/common/rails/stream_event_rail.py","sha256":"c062812d36367c1f1dcacccbe9ec5716f115a5db6d5ce6864d59604a4c790da6","start":983},{"end":611,"path":"jiuwenswarm/agents/harness/common/rails/stream_event_rail.py","sha256":"3b8e1496835cf65a3be84d7c1ca0a3e8ef2fa5cd5e30d516964b778d0ec8777b","start":589},{"end":84,"path":"docs/zh/Harness.md","sha256":"08acc5cdd1c9783e61fa9f98bc5a2926bb16fc914a1616fc2ffa812aa2f9b964","start":73}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=harness facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4736533563315e699a3714bf5063b3158739a81af8c2a7bb3199b8a073556047 -->
**AutoHarnessService.run：query/model/auto_accept 仅关键字可选，活动 run 冲突时产出 is_complete=False 的 chat.error chunk**
async 生成器 run(request, session_id, request_id, *, query="", model=None, auto_accept=False) 返回 AsyncIterator[AgentResponseChunk]，docstring 声明 chunk 由 orchestrator 输出映射；当 session_id 已在 _active_runs 时产出 event_type="chat.error"、is_complete=False 的错误 chunk。

来源：[jiuwenswarm/agents/harness/common/auto_harness/service.py:L1683–L1722](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/service.py#L1683-L1722)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1722,"path":"jiuwenswarm/agents/harness/common/auto_harness/service.py","sha256":"cb761ae0c1bf92963b5ed0acc3599070cf5744c612ea0d05650e48b5e6f340e9","start":1683}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=harness facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fc8051ac66eb2214c194fcf3bb0486fac9e350562058c8f84f90f1f505fcb096 -->
**capture_permission_layers：permission_storage_lock 内读三层，经 compose_host_effective_permissions 合成 effective**
函数内导入 permission_compose.compose_host_effective_permissions，在 permission_storage_lock(session_id) 内经 read_permission_layers_locked 一次读取 Global/User/Session 后现场合成；结果是调用方一次拿到同锁一致的 (global, user, session, effective) 四元组。

来源：[jiuwenswarm/agents/harness/common/rails/permissions/permissions_layers.py:L216–L227](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/permissions_layers.py#L216-L227)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":227,"path":"jiuwenswarm/agents/harness/common/rails/permissions/permissions_layers.py","sha256":"c613c1c3da352c3967d45569b8a400d7cf6fc00801603935f7ab396d7f5e7378","start":216}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=harness facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f48bf03ef43eb260ba9c76b3002097241e1d4a9551b07d1d66e1285d8571412a -->
**before_model_call 局部行为：闩锁等待仅捕获 TimeoutError 后 fail-open；abort 置位时抛 CancelledError**
before_model_call 先 await _wait_for_resume(sid, "before_model_call")；若 self._abort_requested.get(sid, False) 则抛 asyncio.CancelledError("Agent abort requested")。_wait_for_resume 仅捕获 asyncio.TimeoutError，超时记 error 日志后 event.set() 放行，其余异常不在此转换。

来源：[jiuwenswarm/agents/harness/common/rails/stream_event_rail.py:L589–L622](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/stream_event_rail.py#L589-L622), [jiuwenswarm/agents/harness/common/rails/stream_event_rail.py:L983–L994](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/stream_event_rail.py#L983-L994)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":622,"path":"jiuwenswarm/agents/harness/common/rails/stream_event_rail.py","sha256":"122747229e7adfdd0f634a283a272e576e4652eb20d1c4b0b7a18d62ce7d3125","start":589},{"end":994,"path":"jiuwenswarm/agents/harness/common/rails/stream_event_rail.py","sha256":"2606491c041797a0807519ba638640b06b0ecb834a5b152438b6a65a0ff5c712","start":983}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=harness facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b5df10b0afb0788023858f2da92940cbf61900b4ee9b80eb8bafd3b3484b2925 -->
**暂停闩锁超时自愈换继续执行：后续检查点免重复等待（若闩锁未被再次清除），代价是未经 resume 也放行**
设计推断（非作者历史意图）：

before_model_call 调用 _wait_for_resume：闩锁已 set 时立即返回，否则以 self._PAUSE_WAIT_TIMEOUT_SECONDS 走 asyncio.wait_for，TimeoutError 分支自行 event.set()。推断：收益是超时后该 sid 的后续检查点可立即返回，前提是同一事件仍映射该 sid 且未被 pause() 再次清除；代价是超时后没有显式 resume() 也继续执行（fail-open）。

来源：[jiuwenswarm/agents/harness/common/rails/stream_event_rail.py:L598–L622](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/stream_event_rail.py#L598-L622), [jiuwenswarm/agents/harness/common/rails/stream_event_rail.py:L983–L985](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/stream_event_rail.py#L983-L985)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":622,"path":"jiuwenswarm/agents/harness/common/rails/stream_event_rail.py","sha256":"090213c583440f5b24bfaaa10ffa65ff72a5534039a974be94492b63773b5eb3","start":598},{"end":985,"path":"jiuwenswarm/agents/harness/common/rails/stream_event_rail.py","sha256":"8113575470b8cf67a04dd7371d68e028ab32bd68ffe5cc51684ac45d0f3ba840","start":983}],"trace":[]} -->
<!-- /kb:depth -->
