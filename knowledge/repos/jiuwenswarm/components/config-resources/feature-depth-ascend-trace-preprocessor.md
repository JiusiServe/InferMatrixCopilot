---
title: "TRACE_POINT 预处理器与 point_map 映射导出：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py:L32-L43, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py:L77-L85, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py:L95-L106, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py:L115-L135, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py:L28-L28, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py:L87-L93, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py:L121-L135, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/patch_build_pipeline.py:L54-L59, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/apply_trace_scaffold.sh:L20-L26, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py:L32-L35, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/reference.md:L337-L348]
feature: "ascend-trace-preprocessor"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py", "jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/apply_trace_scaffold.sh", "jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/patch_build_pipeline.py"]
---

# TRACE_POINT 预处理器与 point_map 映射导出：实现深读

[功能概览](feature-ascend-trace-preprocessor.md) · [owner 入口](_index.md)

<!-- kb:depth feature=ascend-trace-preprocessor facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8be10186c2b39497e3612c3a73eb3374e287497540bb5f2ec67f60493c86d29f -->
**process_file 在 modify 模式下用 point_id 原地替换 TRACE_POINT 调用**
`process_file` 以正则匹配每个 `TRACE_POINT("标签", "类型")`,按行号排序后分配递增 point_id;当 `modify=True` 且有匹配点时,按 start 位置倒序把每处调用文本替换为数字 point_id 并回写源文件(UTF-8),随后 `save_mappings` 把 `point_map` 以 `output_dir` 相对路径写入 `point_map.json`。

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py:L32–L43](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py#L32-L43), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py:L77–L85](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py#L77-L85), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py:L95–L106](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py#L95-L106)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":43,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py","sha256":"148f70a7aac8e85e0a16e19729f02a013659b42b47d524dc7b1f45cac29587ce","start":32},{"end":85,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py","sha256":"ba6939fb4255abfdf7945a695a1882f6a71a14d447d89a357c66385f02863a35","start":77},{"end":106,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py","sha256":"185754682e31b83bc81dd82650cb99fe5f287ae5bf7685571b9c6fbcaf984620","start":95}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ascend-trace-preprocessor facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7e601c6206b5286a899823e443a8b0390f7fd89ab307f383423f95a0f638abb8 -->
**main 接受 src、output 位置参数与可选 --modify,有匹配点时才导出映射**
CLI 契约:`src`(文件或目录)、`output`(point_map.json 输出目录)、`--modify`(store_true,替换源文件中的 TRACE_POINT)。src 为文件走 `process_file`,为目录走 `process_directory`;仅当返回的匹配点列表非空时调用 `save_mappings`,因此无 TRACE_POINT 时不会生成映射文件。

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py:L115–L135](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py#L115-L135)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":135,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py","sha256":"634d5e29ea52fac6bf58a2c69cef4f480089fc8d2fc2dd03afecbe0b627f84d5","start":115}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ascend-trace-preprocessor facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3e69ba906afade0da7c2f1444a46d6cc8367154ca93eed477077af12dc4e5fe4 -->
**modify 默认关闭，--modify 开启源码改写；仅当发现点时导出映射**
process_file/process_directory 的 modify 默认 False（只扫描不改写）；CLI 用 --modify（store_true）开启替换。main 仅在返回的点列表非空时调用 save_mappings。

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py:L28–L28](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py#L28-L28), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py:L87–L93](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py#L87-L93), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py:L121–L135](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py#L121-L135)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":28,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py","sha256":"82c76076b76753e77d0f02963544976f728583ca2d9b7049326079c0cd1286d9","start":28},{"end":93,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py","sha256":"20cce02f98f8284f248a544f6f885d26b6c9fea4ae7e9d67429d61e8a4753be1","start":87},{"end":135,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py","sha256":"cad49830320fd653779eddf4f8a6f7c3041a4c60759ea0b54dcb6fac86b793fc","start":121}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ascend-trace-preprocessor facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=177086d9ac2a489d4b95ff8bf2b728646941f05395588dc398af5aa74c4ded63 -->
**apply_trace_scaffold.sh 调用 patch_build_pipeline 注入 trace_preprocessor 命令**
patch_build_pipeline.inject_hook 把 --preprocessor-cmd 文本插入编译脚本（用 START/END 标记包裹）；apply_trace_scaffold.sh 以占位的 trace_preprocessor.py ... --modify 命令调用它，并注明该命令需按仓库实际变量名修改。

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/patch_build_pipeline.py:L54–L59](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/patch_build_pipeline.py#L54-L59), [jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/apply_trace_scaffold.sh:L20–L26](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/apply_trace_scaffold.sh#L20-L26)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":59,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/patch_build_pipeline.py","sha256":"85d4740f6aff3d1ccad694aa57d5b175d6e2a6e10b202f1f54184acffd12d244","start":54},{"end":26,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/apply_trace_scaffold.sh","sha256":"d1530ef44dac472dd0c65bc879c5ef8c8c4957ef79972551b9291e35f5e67dbb","start":20}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ascend-trace-preprocessor facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f11c624f7eb682d86b1990228e6aea3806a89463cbf3a214f9266deb97afc474 -->
**纯正则文本匹配：无需语法解析，但只识别两个双引号参数的特定文本形式且无匹配时静默跳过**
设计推断（非作者历史意图）：

L32 的正则仅按文本形式匹配 TRACE_POINT 后两个由双引号括起的非引号字符序列；无匹配时 L34-35 直接返回 [] 且不告警。推断：收益是无需 C/C++ 语法解析即可替换打点，代价是宏生成或其它书写形式的打点会被静默漏检。

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py:L32–L35](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py#L32-L35)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":35,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/scripts/trace_preprocessor.py","sha256":"7e07b884fec771febb48e907c02d5bf9034b6a8d6369da1d01e7d96c4aac580a","start":32}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ascend-trace-preprocessor facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e9a4d322c1e3148bbd91fda5a525c49a18b1d7dcf939d08ee338ecb17e633acb -->
**文档化手工流程：以 --modify 运行 trace_preprocessor.py 生成含 label/event_type/file/line/event_id 的 point_map.json（未执行）**
文档中的人工验收步骤（本轮未执行）：

reference.md 记录的手工步骤：python <skill_root>/scripts/trace_preprocessor.py <operator_src_dir> <output_dir> --modify，预期输出 point_map.json，其 points 以 point_id 为键，每项含 label、event_type、file、line、event_id。此为已记录的手工流程，本次 NOT EXECUTED，未声称任何运行时或自动化测试覆盖。

来源：[jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/reference.md:L337–L348](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/reference.md#L337-L348)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":348,"path":"jiuwenswarm/resources/agent/workspace/skills/ascend-moe-optimizer-auto-trace/reference.md","sha256":"7cd8efd95048705d91618e807c6b062ad30a30ac37d39f50cab9e438f29bdadf","start":337}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
