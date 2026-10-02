---
title: "Agent Loop 与 Rail 装配：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L4363-L4374, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L4756-L4777, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L9561-L9568, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_agentserver_modes.py:L141-L170, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/test_app_agentserver.py:L57-L104]
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
