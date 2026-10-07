---
title: "mcp_exec_command 跨平台命令执行工具：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/command_tools.py:L1099-L1139, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/command_execution_context.py:L10-L42, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/command_execution_context.py:L57-L60, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/command_tools.py:L878-L884, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/command_runtime.py:L35-L60, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/command_tools.py:L1124-L1127, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agents/test_command_tools_sandbox.py:L156-L168, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agents/test_command_tools_sandbox.py:L56-L57, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agents/test_command_tools_sandbox.py:L66-L104, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/command_tools.py:L20-L36]
feature: "command-execution-tool"
entry_points: ["jiuwenswarm/agents/harness/common/tools/command_tools.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/command_tools.py", "jiuwenswarm/agents/harness/common/tools/command_execution_context.py", "jiuwenswarm/agents/harness/common/tools/command_runtime.py"]
---

# mcp_exec_command 跨平台命令执行工具：实现深读

[功能概览](feature-command-execution-tool.md) · [owner 入口](_index.md)

<!-- kb:depth feature=command-execution-tool facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=21863a86f3c4f617f745bcba7ee50c765de617eb88081dc07a9c25bdfd05480f -->
**mcp_exec_command 入口：空命令/安全检查/限流后解析 workdir 并钳制超时**
命令先 strip，为空返回 "[ERROR]: command cannot be empty."；随后 _check_command_safety 拒绝、按会话执行 TUI spawn 限流；_resolve_command_workdir 抛异常时返回 "[ERROR]: workdir is outside project workspace."；timeout_seconds 与环境变量上限（默认 600）取 min 后至少为 1。

来源：[jiuwenswarm/agents/harness/common/tools/command_tools.py:L1099–L1139](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/command_tools.py#L1099-L1139)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1139,"path":"jiuwenswarm/agents/harness/common/tools/command_tools.py","sha256":"42e4edcde8f665ad47bbfc001194a547d112e6a51a92be08df8da48b45ece9bd","start":1099}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=command-execution-tool facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1f57eebd4275ecd499d671013086678c66a510bf4a9b81032487b66f0e861d14 -->
**bind_command_execution(sys_operation, *, sandboxed) 返回 Token 并要求非空对象**
bind_command_execution 把 sys_operation 与布尔 sandboxed 存入冻结 dataclass 并经 ContextVar.set 返回 Token；sys_operation 为 None 抛 ValueError，sandboxed 非 bool 抛 TypeError。调用方须以 reset_command_execution(token) 还原。

来源：[jiuwenswarm/agents/harness/common/tools/command_execution_context.py:L10–L42](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/command_execution_context.py#L10-L42), [jiuwenswarm/agents/harness/common/tools/command_execution_context.py:L57–L60](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/command_execution_context.py#L57-L60)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":42,"path":"jiuwenswarm/agents/harness/common/tools/command_execution_context.py","sha256":"3f0606654c0beed2e9d6962101bb611f7ed4da042dca4fdb151a009c8651f3ce","start":10},{"end":60,"path":"jiuwenswarm/agents/harness/common/tools/command_execution_context.py","sha256":"efd91e9198d7a2d39504a8d5f6ec39e854f7a26c1359c46dbf96ba2418a0c60c","start":57}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=command-execution-tool facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=92268cf237352767ba12c7699876f7ddb817f4db3e21fa605589bdee2c43a9c4 -->
**JW_START_NEW_SESSION 默认启用子进程新会话（非 Windows）**
在 _run_command_sync 中，当 os.name != "nt" 时读取环境变量 JW_START_NEW_SESSION，默认 "true"；仅当取值属于 ("0","false","no","off") 才不设置 popen_kw["start_new_session"]=True。

来源：[jiuwenswarm/agents/harness/common/tools/command_tools.py:L878–L884](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/command_tools.py#L878-L884)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":884,"path":"jiuwenswarm/agents/harness/common/tools/command_tools.py","sha256":"3e512380a23711b740a09d01118ae459dc971b521554f34f2692394bffc8d62f","start":878}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=command-execution-tool facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=61e7d36bdf6c852e5658c3b6032859266ba84091784d693846f981cf37269982 -->
**mcp_exec_command 依赖 openjiuwen 进程注册表与 command_runtime 的路径契约**
command_tools.py 顶部从 openjiuwen shell_process_registry 导入注册/终止/取消消费函数，并复用 command_runtime.resolve_command_workdir：候选目录必须位于 project_root、workspace_root 或 agent_workspace_root 之内，否则抛出 ValueError("workdir is outside project workspace")。

来源：[jiuwenswarm/agents/harness/common/tools/command_tools.py:L20–L36](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/command_tools.py#L20-L36), [jiuwenswarm/agents/harness/common/tools/command_runtime.py:L35–L60](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/command_runtime.py#L35-L60)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":36,"path":"jiuwenswarm/agents/harness/common/tools/command_tools.py","sha256":"b5558fd17291bca705b114eebdaef1bfa684b1fc80938fe42d37b200630a9596","start":20},{"end":60,"path":"jiuwenswarm/agents/harness/common/tools/command_runtime.py","sha256":"b0d9887d5334ea78ec9040fa6536368f977f1e2cd1cebe00c6f718fcbe94b8c8","start":35}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=command-execution-tool facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e4ac22277ae378330501740621df36099a03b228083baa87bf141d8b2a3876d5 -->
**workdir 越界抛 ValueError("workdir is outside project workspace")**
resolve_command_workdir 将候选路径 resolve 后须落在 project_root、可选 workspace_root 或 agent_workspace_root 之一内，否则抛 ValueError；工具层捕获后返回错误字符串且不调用 shell（测试断言 calls == []）。

来源：[jiuwenswarm/agents/harness/common/tools/command_runtime.py:L35–L60](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/command_runtime.py#L35-L60), [jiuwenswarm/agents/harness/common/tools/command_tools.py:L1124–L1127](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/command_tools.py#L1124-L1127), [tests/unit_tests/agents/test_command_tools_sandbox.py:L156–L168](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agents/test_command_tools_sandbox.py#L156-L168)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":60,"path":"jiuwenswarm/agents/harness/common/tools/command_runtime.py","sha256":"b0d9887d5334ea78ec9040fa6536368f977f1e2cd1cebe00c6f718fcbe94b8c8","start":35},{"end":1127,"path":"jiuwenswarm/agents/harness/common/tools/command_tools.py","sha256":"0a5038bfd0e0b4ae4de616ab2da79f281bd7d060481380b69a9ba467f2d9ac88","start":1124},{"end":168,"path":"tests/unit_tests/agents/test_command_tools_sandbox.py","sha256":"aaae35739eadc5f6b29cf3022a5f3de39f24ad0ca5433ef9355fe6149a10aac4","start":156}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=command-execution-tool facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a7ffa85c86d27f9fcb19889d3adf91c72f0df2c819aa3a8b6c13e173d583ecc4 -->
**沙箱绑定运行时测试：前台路径经 execute_cmd 且复位后绑定清除**
test_bound_sandbox_foreground_never_uses_host_subprocess 通过 mcp_exec_command._func 调用，断言 stdout 为 "A-stdout"、shell.calls 记录 ("printf ok", {cwd, timeout:17, shell_type:"bash"})，monkeypatch 使 _run_command_sync 触发 pytest.fail，且 reset 后 current_command_execution() 为 None。

来源：[tests/unit_tests/agents/test_command_tools_sandbox.py:L56–L57](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agents/test_command_tools_sandbox.py#L56-L57), [tests/unit_tests/agents/test_command_tools_sandbox.py:L66–L104](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agents/test_command_tools_sandbox.py#L66-L104)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":57,"path":"tests/unit_tests/agents/test_command_tools_sandbox.py","sha256":"766c39f5c0c90a2172e3af482493ddfbca84f822e4a9bb9949739e15939c133a","start":56},{"end":104,"path":"tests/unit_tests/agents/test_command_tools_sandbox.py","sha256":"115a1cc9e2e02797adb1c4a0ad14a48983bf0a07d8121ade780b0ae72c9186e7","start":66}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
