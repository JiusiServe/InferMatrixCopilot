---
title: "RSI 数据集任务文件夹完整性预检：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py:L1-L9, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py:L67-L73, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py:L67-L83, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py:L210-L218, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py:L99-L127, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py:L59-L64, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py:L72-L85, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py:L210-L214, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py:L195-L208, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/SKILL.md:L265-L290, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py:L161-L178]
feature: "rsi-dataset-folder-check"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py"]
---

# RSI 数据集任务文件夹完整性预检：实现深读

[功能概览](feature-rsi-dataset-folder-check.md) · [owner 入口](_index.md)

<!-- kb:depth feature=rsi-dataset-folder-check facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f7fa02e4d54731cd9e1c250d1d92731c4948923e2ce615216b6976a0ba4e8c64 -->
**main()：校验参数后读取 run/scorecard.json，收集 problems 并以 0/1 返回**
argv 不是恰好 2 个时记录 __doc__ 并返回 1；否则读取 root/run/scorecard.json，逐项把问题追加到 problems 列表，最后拼成一条消息用 logger.info 输出（无问题时为 "ok: …"），并返回 1 if problems else 0。该返回值经 L217-218 的 sys.exit(main()) 变为进程退出码。

来源：[jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py:L67–L83](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py#L67-L83), [jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py:L210–L218](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py#L210-L218)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":83,"path":"jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py","sha256":"2593964a6243a8cd35744447dd82599aa9c75e14b9dc6313d9ec03be6fd7e052","start":67},{"end":218,"path":"jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py","sha256":"b849051a820093d8a7262d6ade343d3cac66d4f6edefa64dc97b801004d613dd","start":210}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=rsi-dataset-folder-check facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e5a2d676eddfcc618292364e374fc9dc6b583e2460bb4c3fc5c7ae08fc335252 -->
**CLI contract: exactly one argument (task folder); wrong arity logs __doc__ and returns 1**
Callers invoke `python scripts/check_folder.py <task-folder>`; if len(sys.argv) != 2 the script logs its docstring and returns 1. It never imports the seed or runs the evaluator — it only checks shape, key sets, and numeric floors.

来源：[jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py:L1–L9](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py#L1-L9), [jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py:L67–L73](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py#L67-L73)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":9,"path":"jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py","sha256":"b6163d687f7342db684a7a2f9ad1b532aa797b334633c296f3f9734ebabfe387","start":1},{"end":73,"path":"jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py","sha256":"e145086e8dafe5415b152667d9e44edbeb885c5998bbb47d0cbb7abd2803a82a","start":67}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=rsi-dataset-folder-check facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=59c780b833698be21a99e6b5e856982e515a8c08b5f1a101fa7fdc2bedc07318 -->
**检查结果依赖 task.json 的 files_in_seed/artifact_path 与 seed/ 目录遍历一致**
脚本用 rglob("*") 遍历 seed/，跳过目录、.pyc 与含 __pycache__/、.git/、node_modules/、.venv/ 的相对路径，排序后要求 task.json 的 files_in_seed 与该清单相等，artifact_path 须等于按文件数推导的 expected，否则追加 problem——即清单或路径不同步会让文件夹被判不完整。

来源：[jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py:L99–L127](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py#L99-L127), [jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py:L59–L64](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py#L59-L64)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":127,"path":"jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py","sha256":"ee111953dc506c064303b8ae8d97cc11beab5bd2cd3f091a50a7fc29b70d9f41","start":99},{"end":64,"path":"jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py","sha256":"2fbdfc68dc0c815fd7dd499e0a57a22e6631a015a29b1cdd1556b1761b689456","start":59}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=rsi-dataset-folder-check facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a62279b1af66d6a221fd66e57109a7585e83690a7775d8800f68bbe8e16cc320 -->
**缺失文件走 problems 分支返回 1；scorecard.json 的读取与 JSON 解析无守卫，异常直接抛出**
seed/ 不是目录、task.json 不是文件时分别追加 "no seed/ directory"、"no task.json" 并最终返回 1；但 L73 对 run/scorecard.json 的 read_text/json.loads 没有 try 分支，文件缺失或非法 JSON 会以未捕获异常终止，而不是进入 problems 汇总路径。

来源：[jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py:L72–L85](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py#L72-L85), [jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py:L210–L214](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py#L210-L214)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":85,"path":"jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py","sha256":"df78dd8960492577dfeafbb2d34fb6a9007cac82725f4ee2bd0cd84ee81d9568","start":72},{"end":214,"path":"jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py","sha256":"d006b13a180843f8d1daaf00f646d73add3c6a68159ce0c132ec99347e855ec0","start":210}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=rsi-dataset-folder-check facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8f1b34590b133ea4b78b515add5642c78d5d590dc2c31786f88c833ee445b0de -->
**traceback 嗅探只进 warnings 不进 problems：不改变退出码，代价是只能提示无法证明**
设计推断（非作者历史意图）：

当 evaluator_file 以 .py 结尾且 script 含 "except" 却不含 "traceback" 时，只 logger.warning 提示（PROBE_REFUSED 风险），return 仍由 problems 单独决定——好处是不因文本启发式误判文件夹不完整，成本是注释自述这只是“smell”，无法测试运行时行为。（推断：益处为本实现的直接后果）

来源：[jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py:L195–L208](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py#L195-L208), [jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py:L210–L214](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py#L210-L214)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":208,"path":"jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py","sha256":"a1e4a1d4bb40aad6e48cf30c9417970e7f739b464ae36952b87198a3e5ff2a7b","start":195},{"end":214,"path":"jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py","sha256":"d006b13a180843f8d1daaf00f646d73add3c6a68159ce0c132ec99347e855ec0","start":210}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=rsi-dataset-folder-check facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5775b0db3231855c80ac7f6345dd8746f43f8ba1ce7abcec8db210c1fd314e69 -->
**文档化的手工程序：运行 check_folder.py 并确认输出 ok（未执行）**
文档中的人工验收步骤（本轮未执行）：

SKILL.md 记载交付前运行 `python scripts/check_folder.py <task-folder>`，并要求第 2 项检查“上述检查打印 ok”；同时说明它只查形状/键集/数值下限，不导入 seed、不运行 evaluator。此为已记载的手工步骤，本轮未执行，不能据此声称测试已通过。validation_kind: documented_manual。

来源：[jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/SKILL.md:L265–L290](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/SKILL.md#L265-L290)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":290,"path":"jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/SKILL.md","sha256":"c0123b391adc25c6fce6d28eb89ae6fbdd988c3db3875f99bb70e7de1ca6f6d7","start":265}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->

<!-- kb:depth feature=rsi-dataset-folder-check facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c5757a7720d903fde83c7530ddb2dfe18e4bd7a8a93ee5a43fffcfc8e751fe21 -->
**scorecard 数值与 options.mode 的校验规则（workers/iterations/max_tokens_per_call）**
从 card 读取 workers、iterations（缺省回退 0）：iterations < 4*workers 记 problem；options.mode 在 workers>1 时不得为 serial，workers==1 时必须为 serial；max_tokens_per_call（缺省回退 0）低于 32000 记 problem。

来源：[jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py:L161–L178](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py#L161-L178)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":178,"path":"jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py","sha256":"ba13cea2a6306e912d46333dc4403ae748bb5bc3f67a9cddb3968f57896674f1","start":161}],"trace":[]} -->
<!-- /kb:depth -->
