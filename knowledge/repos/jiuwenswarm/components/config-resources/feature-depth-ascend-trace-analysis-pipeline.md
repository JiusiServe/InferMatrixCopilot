---
title: "ascend-moe-optimizer-trace-analyzer CLI 主流程：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/llm_analysis.py:L171-L221, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/app.py:L71-L90, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/app.py:L8-L34, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/app.py:L171-L197, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/app.py:L158-L170, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/app.py:L94-L99, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/llm_analysis.py:L188-L221, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/SKILL.md:L157-L217]
feature: "ascend-trace-analysis-pipeline"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/app.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/app.py", "jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/phase_mapper.py", "jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/diagnosis.py", "jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/llm_analysis.py", "jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/metrics.py", "jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/parser.py", "jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/plots.py", "jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/reporter.py"]
---

# ascend-moe-optimizer-trace-analyzer CLI 主流程：实现深读

[功能概览](feature-ascend-trace-analysis-pipeline.md) · [owner 入口](_index.md)

<!-- kb:depth feature=ascend-trace-analysis-pipeline facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c7b1eedf1ed7de6a65ce15d90d671c76eda5a109844d659299daa02e40fe900b -->
**main() 在校验输入后依次解析 trace 并构建 PhaseMapper**
main() 先 parse_args()，再 validate_inputs()（文件不存在时抛 FileNotFoundError），ensure_dir(args.output_dir) 后调用 parse_trace_json/events_to_dicts 解析事件，最后用 PhaseMapper(args.phase_map) 构建 phase 映射；后续摘要构建与诊断表内容不在已展示行内，不展开。

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/app.py:L158–L170](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/app.py#L158-L170), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/app.py:L94–L99](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/app.py#L94-L99)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":170,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/app.py","sha256":"f5a1caf8d20ac1e863a351e624ace80fce5eb68ad816f5bf133d9f03a1099583","start":158},{"end":99,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/app.py","sha256":"bc84661857b0b920254bf213dbf3bfdb1b7b97539453ade65047de74371f9c1d","start":94}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ascend-trace-analysis-pipeline facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6e8cbcc110794cbfe871ed0a6dc6f8b79e4b19f8d9d6ead61475d52d62f95a29 -->
**run_llm_command(prompt, command, timeout_s=120) 契约：stdin 送 prompt，返回 status/analysis/error 字典**
调用方传入 prompt 字符串与 shell 命令字符串；命令经 shlex.split 后以 subprocess.run 执行，prompt 写入 stdin，capture_output 收集输出，check=False；成功时返回 {"status":"ok","analysis":stdout.strip(),"error":""}，失败路径返回错误 status 与 error 文本。

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/llm_analysis.py:L171–L221](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/llm_analysis.py#L171-L221)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":221,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/llm_analysis.py","sha256":"ab4792545c32fce6f3b5e26b6f2141ec27bd82e1ed04f4a3f1673b6f287979f6","start":171}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ascend-trace-analysis-pipeline facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=46f3fc9eeeb4feaf28c3d106c58c3ee8c9ec50f6b372321a7dc9ee5cd53a6d5e -->
**LLM analysis is opt-in: --llm-analysis flag off by default, --llm-command default None, --llm-timeout default 120**
argparse defines --llm-analysis with action="store_true" (absent by default), --llm-command with default=None whose help says the command can alternatively come from TRACE_ANALYSIS_LLM_CMD, and --llm-timeout type=int default=120 described as the timeout in seconds for the --llm-analysis command. The shown span does not include the code that resolves --llm-command against the environment variable, so precedence is not established here.

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/app.py:L71–L90](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/app.py#L71-L90)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":90,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/app.py","sha256":"5150342f273bafd988182cbefa11e6431b7050ee5a3a1e461edec7fa01b082f0","start":71}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ascend-trace-analysis-pipeline facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9209bcdb11ca1fba7202a6f3ca09135ad0b82d504f24d731d7884728c8eee16c -->
**main() derives all summary tables from the single instances_df built by build_phase_instances**
app.py imports parser, PhaseMapper, eleven metrics builders, diagnosis and llm_analysis helpers, and reporter functions from the sibling analyzers modules; inside main(), phase/category/core-group/name/tid/overlap/bubble/overview outputs are all computed from instances_df, so a change in build_phase_instances' row shape propagates to every downstream table and to build_auto_diagnosis's inputs.

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/app.py:L8–L34](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/app.py#L8-L34), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/app.py:L171–L197](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/app.py#L171-L197)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":34,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/app.py","sha256":"cf60f185d2e8edcb014f0137e7e7b41d4d643eaa02cb79e185a7815e52f94ec0","start":8},{"end":197,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/app.py","sha256":"d4ea752bade3e8853650fbeda0a351eab611114ec413ee144d81cebedf9dc54d","start":171}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ascend-trace-analysis-pipeline facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2aef4e0ed6234727fc8eeda152cd063a2647d2bd3af5b29c9808c990ee85dc8a -->
**run_llm_command converts only shlex, empty-command, FileNotFoundError, TimeoutExpired and nonzero exit into status dicts**
shlex.split raising ValueError returns {status: "error", error: f"Invalid LLM command: {exc}"}; an empty argv returns {status: "not_configured", error: "Empty LLM command."}; subprocess.run's FileNotFoundError and TimeoutExpired (after timeout_s, default 120) return status "error"/"timeout" respectively; a nonzero returncode returns stderr or a code message. Only these branches are guarded; other exceptions from subprocess.run would propagate uncaught.

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/llm_analysis.py:L171–L221](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/llm_analysis.py#L171-L221)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":221,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/llm_analysis.py","sha256":"ab4792545c32fce6f3b5e26b6f2141ec27bd82e1ed04f4a3f1673b6f287979f6","start":171}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ascend-trace-analysis-pipeline facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3fa5dcbfc58ba0d7e1aa61fb02d163a3b6156c0d1f99866308497b86eff6c239 -->
**run_llm_command 以 check=False 加状态字典返回，非零退出不抛异常但丢弃其 stdout**
设计推断（非作者历史意图）：

run_llm_command 用 subprocess.run(check=False) 运行外部 LLM 命令：收益是非零退出不抛异常而是返回 {"status":"error", "error": stderr 或退出码信息}；代价是失败分支不返回 result.stdout，超时/找不到可执行文件分支同样 analysis 为空字符串。

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/llm_analysis.py:L188–L221](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/llm_analysis.py#L188-L221)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":221,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/analyzers/llm_analysis.py","sha256":"10789197042c4f1973f404408a95c0641b1cddf7eeb1685a47f6cf89b02a2209","start":188}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ascend-trace-analysis-pipeline facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=30068572300720272dcc112db9c50e390c037f85bfa1ac9e9eadcf3a3fc4bcde -->
**SKILL.md 记录的基础验证命令（documented_manual，未执行）**
文档中的人工验收步骤（本轮未执行）：

SKILL.md「依赖和验证」节给出基础验证步骤：cd 到 skill 根目录后运行 python3 app.py --trace <TRACE_JSON> --phase-map <PHASE_MAP> --output-dir <OUTPUT_DIR> --top-n 20，预期是完成一次分析运行。该文档还声明默认运行只用 Python 标准库。这是已记录的手工过程，本次未执行；未提供针对 app.py 的自动化测试证据。

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/SKILL.md:L157–L217](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/SKILL.md#L157-L217)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":217,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-trace-analyzer/SKILL.md","sha256":"03034456c8f2e2a91dfa29c3bd7a76a91e2d13d9c221fc1c3bed2b166e28a167","start":157}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
