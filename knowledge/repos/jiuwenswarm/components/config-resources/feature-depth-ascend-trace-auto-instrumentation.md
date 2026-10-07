---
title: "TRACE_POINT 自动埋点改写（instrument_operator）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L108-L125, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L101-L105, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L111-L115, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L61-L64, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L82-L84, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L48-L58, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L74-L89, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L67-L68, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L82-L86, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L36-L45, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L71-L98, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L10-L24, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/reference.md:L469-L479]
feature: "ascend-trace-auto-instrumentation"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py"]
---

# TRACE_POINT 自动埋点改写（instrument_operator）：实现深读

[功能概览](feature-ascend-trace-auto-instrumentation.md) · [owner 入口](_index.md)

<!-- kb:depth feature=ascend-trace-auto-instrumentation facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e7403fe8b57b38455ac1cd0fbb78b823f4c666ababdac0f2612e32019d057b3c -->
**CLI: --target 必填，--root-label 默认 processing，--dry-run 仅预览**
main 通过 argparse 要求 --target（文件或目录），可选 --root-label 与 --dry-run；iter_targets 在目录模式下仅收集后缀为 .h/.hpp/.c/.cc/.cpp 的文件，apply_file 返回 (计数, 消息) 并由 logger.info 逐文件输出。

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L108–L125](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py#L108-L125), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L101–L105](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py#L101-L105)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":125,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py","sha256":"ea68c99787a97bf99c9f99b650c006619175b152a8d06b72ce70e68a4328aab3","start":108},{"end":105,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py","sha256":"86bd07be84875b222c0d711840610f2121b2515c9a9d5c163a3527f29ecdda5f","start":101}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ascend-trace-auto-instrumentation facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ab767e44ddf372f447043bf4d00a07c2266ccb283d5acc83cdd60eaad7f28a54 -->
**--root-label 默认 processing，函数名 process 例外使用根标签**
--root-label 默认值为 "processing"（argparse default）；apply_file 中仅当函数名小写等于 "process" 时使用 root_label，其他函数用 normalize_label 把驼峰/下划线转为小写连字符标签。

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L111–L115](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py#L111-L115), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L61–L64](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py#L61-L64), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L82–L84](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py#L82-L84)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":115,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py","sha256":"9a07a0fe7b1b5e9c9428e9d47e8df06dbf20d5905d401bbd6f7c35b6a8b1ea02","start":111},{"end":64,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py","sha256":"bbdc0e5514517a0a437e009259859f06204a498710f7ecb75e328eb941a7ccd2","start":61},{"end":84,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py","sha256":"53a4a0037c9ac3ec79669d712edb15fd47c67ca8f9b9966502e17b53fd5537b9","start":82}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ascend-trace-auto-instrumentation facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0f206ad3b73d5aebe13aa8cb045c9b96338f6a2661392e31c8588f565f5839ce -->
**未匹配闭括号时 find_match_brace 兜底返回 len(text)-1；无函数/已埋点时跳过**
find_match_brace 扫描到文本末尾仍未配平时返回 len(text)-1（不抛错，end 语句可能插入到文件末字符前）；apply_file 在 find_functions 为空时返回 (0, "skip ... (no function found)")，全部函数已含埋点时返回 (0, "skip ... (already instrumented)")，两种情况均不写文件。

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L48–L58](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py#L48-L58), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L74–L89](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py#L74-L89)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":58,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py","sha256":"452a5099cc2905ef5dd0edc15bfc4ace726a6994933a12b4a2cc1b01be9aa761","start":48},{"end":89,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py","sha256":"9961323d9febcce14d0b7ec115c8422ba8b880ee08163d544a4395dd76a22680","start":74}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ascend-trace-auto-instrumentation facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=26438436370ba56b92c05a66c340f577703223a86373c27241379e8aff776296 -->
**子串级幂等跳过实现零依赖，但启发式识别可能漏配或错配**
设计推断（非作者历史意图）：

收益：should_skip 用子串判断即可避免重复插入，且只改写文件、无外部依赖。代价（推断）：FUNC_RE/括号计数忽略字符串与注释内容，未匹配到闭括号时 find_match_brace 回退返回 len(text)-1，end 语句可能插在最后一个字符之前；识别为启发式，不保证覆盖所有 C++ 函数形式。

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L48–L58](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py#L48-L58), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L67–L68](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py#L67-L68), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L82–L86](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py#L82-L86)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":58,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py","sha256":"452a5099cc2905ef5dd0edc15bfc4ace726a6994933a12b4a2cc1b01be9aa761","start":48},{"end":68,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py","sha256":"63b5ad225306e07a4ef87be2941ad708b51829c239e00f023738e7123c4c73f7","start":67},{"end":86,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py","sha256":"bc6f4ae984561e57374261e19d6b860121d7a4ac8f469e2660e41c49d20d8588","start":82}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ascend-trace-auto-instrumentation facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=92cc95682b94727076a17768f23258cce0e2beea0e02b00c3004a5854fba9ac9 -->
**apply_file：FUNC_RE 定位函数后按降序插入 B/E 打点并写回**
apply_file 读入文本后由 find_functions 用 FUNC_RE.finditer 提取函数块（find_match_brace 深度配对求 close_brace）；无函数返回 0 并报 skip。每个函数体经 should_skip 检查后构造 MoeTracing(TRACE_POINT(label,"B"/"E")) 编辑，编辑按位置降序逐个插入，非 dry_run 时写回磁盘并返回 len(edits)//2。

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L36–L45](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py#L36-L45), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L71–L98](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py#L71-L98)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":45,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py","sha256":"9baf7e74c91b2390aa646be54d7948e0a9c8553c9d6789042e370e184b8f0450","start":36},{"end":98,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py","sha256":"de58b185c167c9f02b7f23fa4b4ca12d7b5c72cf83b52ec688d5b5567acf978d","start":71}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ascend-trace-auto-instrumentation facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=adf8229dc405982b985746da36d5d0aa61066376203b4051d64593165a5e10a8 -->
**仅标准库模块 + FUNC_RE 多行正则的文本级函数识别**
所引片段中脚本只 import argparse/logging/pathlib/re/dataclass/typing 标准库；函数识别完全依赖 FUNC_RE 单个多行正则（find_functions 于 L38 直接 FUNC_RE.finditer），find_match_brace 为纯字符深度计数，配对失败时回退返回 len(text)-1。

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L10–L24](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py#L10-L24), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L36–L45](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py#L36-L45), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py:L48–L58](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py#L48-L58)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":24,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py","sha256":"dda7aa2c3c246ce08488d0c71a71df4fce7d159fd624867f877704398e4e3247","start":10},{"end":45,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py","sha256":"9baf7e74c91b2390aa646be54d7948e0a9c8553c9d6789042e370e184b8f0450","start":36},{"end":58,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/instrument_operator.py","sha256":"452a5099cc2905ef5dd0edc15bfc4ace726a6994933a12b4a2cc1b01be9aa761","start":48}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ascend-trace-auto-instrumentation facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d2f7cadaf819eaead65bb0f0099db1872721bd7d70578d0f1dcb86ac9fc95ef7 -->
**文档化的可选草稿插桩命令（未执行，不能替代人工审查）**
文档中的人工验收步骤（本轮未执行）：

reference.md 记载可运行 `python <skill_root>/scripts/instrument_operator.py --target <operator_src_file_or_dir> --root-label processing` 自动写入打点代码，并将其归类为「辅助（可选）——规划/草稿插桩，不能替代人工审查」。这是文档化手动流程，本次未执行，也不证明生成的插桩语义/编译正确。

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/reference.md:L469–L479](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/reference.md#L469-L479)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":479,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/reference.md","sha256":"9ca068c4069a45f0ec9e5438995394599b53754f966821e741d05c12cfab1915","start":469}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
