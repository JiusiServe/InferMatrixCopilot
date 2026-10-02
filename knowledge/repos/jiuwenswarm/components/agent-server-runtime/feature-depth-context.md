---
title: "上下文压缩与卸载：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_agentserver_modes.py:L48-L138, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_agentserver_modes.py:L141-L170]
---

# 上下文压缩与卸载：实现深读

[功能概览](feature-context.md) · [owner 入口](_index.md)

<!-- kb:depth feature=context facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1d64d65d9c3af2cbbcab6127f2bb5f7e92d8550c2118337695fc40741ddb655b -->
**卸载提交与重试的单元测试**
tests/unit_tests/agentserver/test_agentserver_modes.py::test_external_memory_unload_commits_serialized_session_messages 验证卸载时先等 rail 同步任务完成再调用一次 on_session_end，消息按 dict/model_dump/to_dict 三种形态序列化提交并注销 rail；test_external_memory_finalize_retries_after_commit_failure 验证首次提交抛错后标志保持 False、第二次调用重试成功。此处仅记录测试断言的行为，不代表当前已运行通过。

来源：[tests/unit_tests/agentserver/test_agentserver_modes.py:L48–L138](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/test_agentserver_modes.py#L48-L138), [tests/unit_tests/agentserver/test_agentserver_modes.py:L141–L170](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/test_agentserver_modes.py#L141-L170)

<!-- kb:depth-proof {"evidence":[{"path":"tests/unit_tests/agentserver/test_agentserver_modes.py","start":48,"end":138,"sha256":"3dbf9ebc40f7cfda0854ed9984005f9db313454a66193203be55a03069575f92"},{"path":"tests/unit_tests/agentserver/test_agentserver_modes.py","start":141,"end":170,"sha256":"842c17cad31443f482e6d559a0a8aaff97af1de7178bee91aec973dcb726e3f3"}],"trace":[]} -->
<!-- /kb:depth -->
