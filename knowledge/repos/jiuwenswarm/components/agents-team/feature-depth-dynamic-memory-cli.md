---
title: "Dynamic Memory CLI（SQLite UT 记忆库与发布/构建流水线）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/dynamic-memory-cli/scripts/dynamic_memory_cli.py:L506-L511, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/dynamic-memory-cli/scripts/dynamic_memory_cli.py:L543-L546, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/dynamic-memory-cli/scripts/dynamic_memory_cli.py:L98-L100, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py:L70-L76, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/rails/test_eternal_conversation_rail.py:L1166-L1172, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/rails/test_eternal_conversation_rail.py:L759-L762, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py:L83-L106, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py:L126-L136, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py:L64-L80, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py:L43-L57, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py:L64-L107, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/dynamic-memory-cli/scripts/dynamic_memory_cli.py:L247-L250, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py:L115-L120]
feature: "dynamic-memory-cli"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/dynamic-memory-cli/scripts/dynamic_memory_cli.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/dynamic-memory-cli/scripts/dynamic_memory_cli.py", "jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py"]
---

# Dynamic Memory CLI（SQLite UT 记忆库与发布/构建流水线）：实现深读

[功能概览](feature-dynamic-memory-cli.md) · [owner 入口](_index.md)

<!-- kb:depth feature=dynamic-memory-cli facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0ace074bcbbed36d117255b9e75e106f65db2326ce5c67a906f3251ccb9aa9f0 -->
**call() double-checks initialization, then _invoke() spawns the CLI and returns its parsed stdout JSON**
Under the init lock, if root/memory.sqlite3 is absent the gateway runs `init --path` without --root; _initialized is set only after that succeeds, so a failed init is retried on the next call. _invoke then runs [sys.executable, script, "--root", root, *args] with cwd=root, UTF-8 env overrides, stdin from DEVNULL, parses stdout as JSON, appends a memory-cli-calls audit entry, and raises RuntimeError when returncode != 0; otherwise it returns the parsed JSON value (whatever json.loads produced, not guaranteed to be a dict).

来源：[jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py:L43–L57](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py#L43-L57), [jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py:L64–L107](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py#L64-L107)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":57,"path":"jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py","sha256":"7eeefb08a5c153c188b1b7f5e9411c13eb35fed856aacf3d79587764f6230f10","start":43},{"end":107,"path":"jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py","sha256":"6c90fd50b98a6e9ef11b015fd74167c89b2350dfca2cc648d49df57bb271ad63","start":64}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=dynamic-memory-cli facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=52d721ab03c733f30e35e5178e5598d58ef4fa614a3d2a28ba620edf24350876 -->
**CLI search() returns the single group for one query, {"queries": groups} otherwise; gateway search short-circuits blank queries**
CLI-side search(root, queries) computes one search_one group per query and returns groups[0] when len==1, else {"queries": groups}. Gateway-side search(query) strips the query and returns {"query": "", "matches": []} locally when empty; otherwise it dispatches `search <query>` through call(), a path a gateway comment says merges published Pending and Built UTs.

来源：[jiuwenswarm/resources/agent/workspace/skills/dynamic-memory-cli/scripts/dynamic_memory_cli.py:L247–L250](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/dynamic-memory-cli/scripts/dynamic_memory_cli.py#L247-L250), [jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py:L115–L120](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py#L115-L120)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":250,"path":"jiuwenswarm/resources/agent/workspace/skills/dynamic-memory-cli/scripts/dynamic_memory_cli.py","sha256":"c2445629001aae9b1444ea7696bfbad78cd9b8db6a7de10a2e8cecb1d61c94ff","start":247},{"end":120,"path":"jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py","sha256":"7a083fd677854b37be9277ba7e965ded086a927d7bd3ccc54e5b92102f64e48b","start":115}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=dynamic-memory-cli facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=17f329e999aa844792bdeecaa7ba432df293f621fea6789155c6e39e868556fa -->
**Root resolution and auto-init default; UTF-8 subprocess env**
--root is the global project option (init instead takes --path); commands other than init call require_project and raise ValueError("dynamic memory project not found at {root}") if the DB file is missing. The gateway forces PYTHONUTF8=1 and PYTHONIOENCODING=utf-8 on every CLI subprocess.

来源：[jiuwenswarm/resources/agent/workspace/skills/dynamic-memory-cli/scripts/dynamic_memory_cli.py:L506–L511](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/dynamic-memory-cli/scripts/dynamic_memory_cli.py#L506-L511), [jiuwenswarm/resources/agent/workspace/skills/dynamic-memory-cli/scripts/dynamic_memory_cli.py:L543–L546](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/dynamic-memory-cli/scripts/dynamic_memory_cli.py#L543-L546), [jiuwenswarm/resources/agent/workspace/skills/dynamic-memory-cli/scripts/dynamic_memory_cli.py:L98–L100](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/dynamic-memory-cli/scripts/dynamic_memory_cli.py#L98-L100), [jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py:L70–L76](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py#L70-L76)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":511,"path":"jiuwenswarm/resources/agent/workspace/skills/dynamic-memory-cli/scripts/dynamic_memory_cli.py","sha256":"ad095b28b76d1e29490e523c9c5b2861436810844b8a57563d0a1afb19c2a8d0","start":506},{"end":546,"path":"jiuwenswarm/resources/agent/workspace/skills/dynamic-memory-cli/scripts/dynamic_memory_cli.py","sha256":"df443ae129c378220081b1bc03c7d3ef470e89ba3badee0689193e07c61805d0","start":543},{"end":100,"path":"jiuwenswarm/resources/agent/workspace/skills/dynamic-memory-cli/scripts/dynamic_memory_cli.py","sha256":"a772c5bf969783a0a5ed59da8e1b9411df0c9ffac1cb38f873edd551f339f15b","start":98},{"end":76,"path":"jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py","sha256":"4047a2afdccaf8379700e0984c7352dc61c34b84769c2ee113f687aedf94f419","start":70}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=dynamic-memory-cli facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5e19dfd03dbfa3748638b0e968b6b540da39a4e7ee08b66b072307a95e8cff26 -->
**无效 JSON 与非零 returncode 在审计后抛 RuntimeError；取消时杀掉子进程再重抛**
_invoke 中 json.loads 失败时构造 {"error":"invalid_json",...} 结果、先 append_audit 再抛 RuntimeError；returncode != 0 时在审计后抛 "dynamic-memory-cli failed"。communicate() 期间收到 CancelledError 则 _stop_process 杀进程并重抛（returncode 已设置时直接返回）。

来源：[jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py:L83–L106](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py#L83-L106), [jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py:L126–L136](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py#L126-L136)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":106,"path":"jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py","sha256":"10c44aaee57d77312ad520c80e9722d5ac15d7fd37fc6e4bf031fa1cb323b48a","start":83},{"end":136,"path":"jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py","sha256":"14aed5b0db7aa680398d6d781a930bf7afb527994e99ceb574f9507117eabe1c","start":126}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=dynamic-memory-cli facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d44242243a0afd049aa9b199a2d1bfee32e2037e5ed16177de003f3732fd4637 -->
**每次 call 起新子进程：换来进程隔离与 UTF-8 固定环境，代价是每命令的启动开销**
设计推断（非作者历史意图）：

（推断）每次 _invoke 都 create_subprocess_exec 一个新的 Python 解释器并强制 PYTHONUTF8=1、PYTHONIOENCODING=utf-8，受益是与 CLI 的编码和运行时隔离；代价是每条命令都付出解释器启动成本。这是对显示实现的推断，非文档记载的历史意图。

来源：[jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py:L64–L80](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py#L64-L80)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":80,"path":"jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py","sha256":"917344e9c87f9b42eb31af7f8ccbf1cafff14f96dc0b926804d56ad92359ffde","start":64}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=dynamic-memory-cli facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=930c5bfb8c31bf84c55a10a57b26a994d6aed83047110a9ffddbd9a5290dda80 -->
**Runtime test: gateway search returns built UT after coordinator restart**
test (starting at line 1104 area, shown span 1166-1172) restarts SessionCoordinator on the same tmp_path, resumes background work, and asserts restarted.memory.search("NimbusGate")["matches"][0]["build_state"] == "built" — an actual runtime assertion through the gateway search path. NOT EXECUTED now; cited as existing test evidence.

来源：[tests/unit_tests/agentserver/rails/test_eternal_conversation_rail.py:L1166–L1172](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/rails/test_eternal_conversation_rail.py#L1166-L1172), [tests/unit_tests/agentserver/rails/test_eternal_conversation_rail.py:L759–L762](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/rails/test_eternal_conversation_rail.py#L759-L762)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1172,"path":"tests/unit_tests/agentserver/rails/test_eternal_conversation_rail.py","sha256":"c35cce6c927a38124aec78f4273f5e34ddfcba641e5a266c93057cc7156d238e","start":1166},{"end":762,"path":"tests/unit_tests/agentserver/rails/test_eternal_conversation_rail.py","sha256":"7304ec4f538a5da5e04f1be07569e0585659d7223ef4183e896c7e71e693b811","start":759}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
