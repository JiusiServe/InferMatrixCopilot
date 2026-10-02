---
title: "上下文压缩与卸载：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_agentserver_modes.py:L48-L138, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_agentserver_modes.py:L141-L170, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py:L108-L123, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py:L132-L153, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L18326-L18329, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L18358-L18360, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py:L2-L22, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py:L32-L58, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L8898-L8930, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L3095-L3115]
feature: "context"
entry_points: ["jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py", "jiuwenswarm/server/runtime/agent_adapter/interface_deep.py"]
source_globs: ["jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py", "jiuwenswarm/server/runtime/agent_adapter/interface_deep.py", "jiuwenswarm/agents/harness/common/*"]
---

# 上下文压缩与卸载：实现深读

[功能概览](feature-context.md) · [owner 入口](_index.md)

<!-- kb:depth feature=context facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1d64d65d9c3af2cbbcab6127f2bb5f7e92d8550c2118337695fc40741ddb655b -->
**卸载提交与重试的单元测试**
tests/unit_tests/agentserver/test_agentserver_modes.py::test_external_memory_unload_commits_serialized_session_messages 验证卸载时先等 rail 同步任务完成再调用一次 on_session_end，消息按 dict/model_dump/to_dict 三种形态序列化提交并注销 rail；test_external_memory_finalize_retries_after_commit_failure 验证首次提交抛错后标志保持 False、第二次调用重试成功。此处仅记录测试断言的行为，不代表当前已运行通过。

来源：[tests/unit_tests/agentserver/test_agentserver_modes.py:L48–L138](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/test_agentserver_modes.py#L48-L138), [tests/unit_tests/agentserver/test_agentserver_modes.py:L141–L170](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/test_agentserver_modes.py#L141-L170)

<!-- kb:depth-proof {"evidence":[{"path":"tests/unit_tests/agentserver/test_agentserver_modes.py","start":48,"end":138,"sha256":"3dbf9ebc40f7cfda0854ed9984005f9db313454a66193203be55a03069575f92"},{"path":"tests/unit_tests/agentserver/test_agentserver_modes.py","start":141,"end":170,"sha256":"842c17cad31443f482e6d559a0a8aaff97af1de7178bee91aec973dcb726e3f3"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=context facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dbd81150d75f6a556e7c388bd5dee341d90d624a6cab29f6e0e71e3a68892b6d -->
**'up_to' 部分压缩：模型仅见 pivot 前缀，摘要在保留近期消息之前**
'up_to' 分支用 PARTIAL_COMPACT_UP_TO_PROMPT：模型只看到 pivot 之前的消息（新消息 "you do not see them here"），产出的摘要将置于保留的近期消息之前，并须按模板 1-9 节结构组织。

来源：[jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py:L108–L123](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py#L108-L123), [jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py:L132–L153](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py#L132-L153)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":123,"path":"jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py","sha256":"a731ef45362647608f5845aa5879a0b2e88f04f0844b0a6f3c778e827ec52d3a","start":108},{"end":153,"path":"jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py","sha256":"598cb325c42c7bdbf5ee40cfaa928f5c46c38ea33e2701a24247da5899dc3432","start":132}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=context facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5e6dad4fab562dcb250e2c7696071f3847ae7a9b7e7165d52319e0d9abe87f01 -->
**compact_partial_prompts 常量契约：纯文本、先 <analysis> 后 <summary>、禁工具**
模块为 /rewind summarize 提供 NO_TOOLS_PREAMBLE 与 PARTIAL_COMPACT_PROMPT 常量；模板要求模型不得调用任何工具、工具调用会被拒绝，须以纯文本先输出 <analysis> 块再输出 <summary> 块，摘要含 9 个规定小节（Primary Request and Intent 到 Optional Next Step）。

来源：[jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py:L2–L22](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py#L2-L22), [jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py:L32–L58](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py#L32-L58)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":22,"path":"jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py","sha256":"12c9baaf66ce25755bbe065678110899195460d0e47fafbfc8e6d387cc7b8555","start":2},{"end":58,"path":"jiuwenswarm/server/runtime/agent_adapter/compact_partial_prompts.py","sha256":"38b520fb1b352ee2060dd0842f15dfea4305e21b5935d6da62f70fa1503abd46","start":32}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=context facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1c93fb814eb2bbc2a88e9a9188daeeb674a43ec9ab61e68e25f9dd925622de8c -->
**execution_guard.model_anomaly_detection_rail 默认关闭；tool_loop_compact 缺省 None**
config_base 缺省时用 get_config()，读取 execution_guard.model_anomaly_detection_rail；enabled 非 True（默认 False）即返回 None 并记 info 日志；开启后 max_retries 默认 2、repeat_window_chars 默认 1024、tool_loop_compact 未配置为 None。

来源：[jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L8898–L8930](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L8898-L8930)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":8930,"path":"jiuwenswarm/server/runtime/agent_adapter/interface_deep.py","sha256":"ab76cd9453bb062d5e1d5f1f408995667f57de86964dba58c6e1c87610ae36e7","start":8898}],"trace":[]} -->
<!-- /kb:depth -->
