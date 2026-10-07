---
title: "/security-review 安全审查斜杠命令与 git 预执行：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py:L243-L255, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/gateway/test_message_handler_security_review_prompt.py:L48-L56, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/gateway/test_message_handler_security_review_prompt.py:L28-L39, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py:L14-L22, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py:L39-L45, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py:L14-L17, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py:L48-L60, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/gateway/test_message_handler_security_review_prompt.py:L136-L141, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py:L10-L11, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py:L63-L72, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py:L5-L7, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/message_handler/message_handler.py:L52-L56]
feature: "channel-security-review-slash-command"
entry_points: ["jiuwenswarm/gateway/message_handler/message_handler.py", "jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py"]
source_globs: ["jiuwenswarm/gateway/message_handler/message_handler.py", "jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py"]
---

# /security-review 安全审查斜杠命令与 git 预执行：实现深读

[功能概览](feature-channel-security-review-slash-command.md) · [owner 入口](_index.md)

<!-- kb:depth feature=channel-security-review-slash-command facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=df78e994ab230d7209ecd0915eada8eab7ea03e971574e8968be75f62752acc5 -->
**_build_inlined_intro 接收 git_outputs 字典；GitPreExecError 表示单条只读 git 命令非零退出的中止**
_build_inlined_intro(git_outputs: dict[str, str]) -> str 以标签到命令输出的映射为入参返回 intro 字符串（可见片段只展示到循环开头，未见访问 git_outputs 具体键的行）。GitPreExecError(Exception) 的 docstring 定义为“某条只读 git 命令非零退出 —— 预执行失败的中止语义”。

来源：[jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py:L10–L11](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py#L10-L11), [jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py:L63–L72](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py#L63-L72)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":11,"path":"jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py","sha256":"32b8fa7274133a34d0cf211e3f4f41c391d350bdf3401c1bd79af7e0a2c8e237","start":10},{"end":72,"path":"jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py","sha256":"89c4e54e3afe32cf1a4c8a18ef083a6e9fe27772ae1ff4f38444d7408ab6bd7a","start":63}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=channel-security-review-slash-command facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=30afaa9cefa1830e06f96beb0ea9e9b53245f315b149c9a8043ca518b1a6a44d -->
**输出语言由 config 的 preferred_language 决定；cwd 缺省 None 回退指令式 prompt**
输出语言读取 get_config() 的 `preferred_language`（如 "en"→`Respond in English.`，"zh"→`Respond in Chinese (simplified).`）；cwd 参数缺省 None，此时退回旧的“指令式” prompt（让 LLM 自己跑 git），行为不变。

来源：[jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py:L243–L255](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py#L243-L255), [tests/unit_tests/gateway/test_message_handler_security_review_prompt.py:L48–L56](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/gateway/test_message_handler_security_review_prompt.py#L48-L56), [tests/unit_tests/gateway/test_message_handler_security_review_prompt.py:L28–L39](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/gateway/test_message_handler_security_review_prompt.py#L28-L39)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":255,"path":"jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py","sha256":"aeb0ea3b5d756a646144715977f2b9302dcbd6c30bf9e632cb49f309dff62c7f","start":243},{"end":56,"path":"tests/unit_tests/gateway/test_message_handler_security_review_prompt.py","sha256":"8cb98daca384a1c4ca3e57f85dbdd9c4f7f199e451c216017f9ffded248fe9e0","start":48},{"end":39,"path":"tests/unit_tests/gateway/test_message_handler_security_review_prompt.py","sha256":"3512cb0651e362574bf998c6e360fd0a5c462cf2138a996b9350a111b40046b2","start":28}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=channel-security-review-slash-command facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=387d0928e20a81206c896c53bf0f1fe3d1f8d2e4e7bef51b1beea759160a38e0 -->
**security_review_prompt.py 依赖 subprocess 与 response_language_line；MessageHandler 导入其 GitPreExecError 与 build_security_review_prompt**
模块 import subprocess（预执行 git 的进程机制）并从 jiuwenswarm.gateway.message_handler.prompts 引入 response_language_line；message_handler.py L53–L56 显式导入 GitPreExecError 与 build_security_review_prompt，把预执行失败异常类型与 prompt 构建函数耦合进 MessageHandler。调 subprocess 实际运行 git 的调用点不在已展示行内。

来源：[jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py:L5–L7](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py#L5-L7), [jiuwenswarm/gateway/message_handler/message_handler.py:L52–L56](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/message_handler.py#L52-L56)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":7,"path":"jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py","sha256":"c20bf144eed732ffc53ddbc6d9332430c2ba14d0878c35c8fed8103a29e53034","start":5},{"end":56,"path":"jiuwenswarm/gateway/message_handler/message_handler.py","sha256":"988371f7e1cf44ba54cbcad58c704b6854f13696fec35df66e08edb9be47012a","start":52}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=channel-security-review-slash-command facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6bab2558220ede28a67e96c396fa71b643defbbe1cc82955824c948c8c738fe0 -->
**git 非零退出触发受保护分支：抛 GitPreExecError 携带命令、退出码与 stderr**
subprocess.run 返回后先检查 result.returncode != 0，命中即 raise GitPreExecError(f"git {args} failed (exit {code}): {stderr.strip()}")，该条及后续命令输出不再写入 outputs；异常向上传播，本片段内无捕获。注释注明仅 origin/HEAD 未设置、无共同历史等真失败才非零。

来源：[jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py:L14–L22](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py#L14-L22), [jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py:L39–L45](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py#L39-L45)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":22,"path":"jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py","sha256":"2b1cafd0be34229913bf911cc0e1864ca6f32af17f49241c604ae8097d965522","start":14},{"end":45,"path":"jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py","sha256":"0236a0d255d885bb1e8596d6e0579f78921104476180af8d778ad89408b1220e","start":39}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=channel-security-review-slash-command facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=683071f286fb6d104d23f91ceb2e8921f0a6d4cc6959b4a9570fe8ca041ef4fd -->
**取舍：预执行内联真实 git 输出，但分支无仓库上下文时退回让 LLM 自己跑 git 的指令式提示**
设计推断（非作者历史意图）：

收益（推理）：有 cwd 时把四段真实仓库状态内联进提示词，模型无需自行执行命令、结果确定。成本（推理）：无仓库上下文（cwd=None，如单测）时使用 _SECURITY_REVIEW_INTRO_FALLBACK 的旧指令式措辞，把执行 git 的负担和不确定性交回 LLM。此取舍由源码注释直接陈述。

来源：[jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py:L14–L17](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py#L14-L17), [jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py:L48–L60](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py#L48-L60)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":17,"path":"jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py","sha256":"e6adbc93588c99129cb453a6c7aa4578db18ff39833172ecdfd3cebc606b1f7f","start":14},{"end":60,"path":"jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py","sha256":"4782220b3d9dd62dfc5a77143cca71441e154bc1c1faa0e3829c199b89b96e7e","start":48}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=channel-security-review-slash-command facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0d0c35acc9f5e749fb4810ad20579555d72120b8462e2aa61d4786be696aadbd -->
**单测运行时断言 prompt 文本、语言切换与 git 失败中止**
tests/unit_tests/gateway/test_message_handler_security_review_prompt.py 实际调用 build_security_review_prompt 并断言：cwd=None 时含 `` `git status` `` 等指令且无 `Additional instructions:`（28-39 行）；zh 配置输出 `Respond in Chinese (simplified).`（48-56 行）；无 origin/HEAD 的仓库抛 GitPreExecError（136-141 行）。这些断言覆盖 prompt 构建函数本身，未覆盖斜杠命令的完整频道链路。

来源：[tests/unit_tests/gateway/test_message_handler_security_review_prompt.py:L28–L39](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/gateway/test_message_handler_security_review_prompt.py#L28-L39), [tests/unit_tests/gateway/test_message_handler_security_review_prompt.py:L48–L56](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/gateway/test_message_handler_security_review_prompt.py#L48-L56), [tests/unit_tests/gateway/test_message_handler_security_review_prompt.py:L136–L141](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/gateway/test_message_handler_security_review_prompt.py#L136-L141)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":39,"path":"tests/unit_tests/gateway/test_message_handler_security_review_prompt.py","sha256":"3512cb0651e362574bf998c6e360fd0a5c462cf2138a996b9350a111b40046b2","start":28},{"end":56,"path":"tests/unit_tests/gateway/test_message_handler_security_review_prompt.py","sha256":"8cb98daca384a1c4ca3e57f85dbdd9c4f7f199e451c216017f9ffded248fe9e0","start":48},{"end":141,"path":"tests/unit_tests/gateway/test_message_handler_security_review_prompt.py","sha256":"4fa5d5509a2610a5da1c4bdfcba54fdefda0fa428d9153b729c4c677d722bcef","start":136}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
