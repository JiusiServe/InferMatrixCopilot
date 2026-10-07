---
title: "SOP 结构化抽取（parse_sop_raw_text / parse_sop_file）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py:L14-L15, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_chunk_merge.py:L559-L560, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/__init__.py:L3-L21, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py:L349-L363, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py:L289-L306, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py:L349-L364, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py:L371-L391]
feature: "sop-structure-extraction"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py", "jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_chunk_merge.py", "jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_fallback.py", "jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/__init__.py", "jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/models.py"]
---

# SOP 结构化抽取（parse_sop_raw_text / parse_sop_file）：实现深读

[功能概览](feature-sop-structure-extraction.md) · [owner 入口](_index.md)

<!-- kb:depth feature=sop-structure-extraction facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c56c708bf2543bd0250d526a025ddeb7a3ea0dade9abe024dca96324932d510a -->
**auto 模式按 room_single 判定分块，否则单次抽取并记录弱抽取原因**
mode 为 auto 时仅当 len(raw_text) > room_single 才走 extract_structure_chunked（run_reconcile=True），否则截断到 room_single 走单次抽取；随后计算 weak_reasons，置 sop.raw_text=raw_text 并返回 (sop, extraction_meta)。

来源：[jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py:L289–L306](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py#L289-L306), [jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py:L349–L364](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py#L349-L364), [jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py:L371–L391](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py#L371-L391)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":306,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py","sha256":"333bd213c72a0e975e4a8798e95963ddb31f089ab6dbe098c31817d5c03f2339","start":289},{"end":364,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py","sha256":"247156a0197c23d228816b6c2d8130c17dbed3a5c48967ee638d2d37dde7c9d4","start":349},{"end":391,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py","sha256":"248324eb7ee9ec32cf96d11355cb4b3859f05744def564416dde512c639ed0a3","start":371}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=sop-structure-extraction facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=414bd2f638840afad775326bfb2381bc897a7b0dc47fe58972fd885ab26bff39 -->
**sop_parser 依赖 sop_chunk_merge 与 models.SOPStructure**
sop_parser.py 导入 extract_structure_chunked/extract_structure_single_shot 与 SOPStructure，抽取结果的 dict 经 SOPStructure.from_dict 转为结构化对象；包 __init__ 对外导出 parse_sop_raw_text/parse_sop_file 及 DEFAULT_SINGLE_SHOT_BUDGET。

来源：[jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py:L14–L15](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py#L14-L15), [jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_chunk_merge.py:L559–L560](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_chunk_merge.py#L559-L560), [jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/__init__.py:L3–L21](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/__init__.py#L3-L21)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":15,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py","sha256":"cf57dfb36f83888abec656266e0913a155a206dbfacb47fdbfb25aebcb1e96b9","start":14},{"end":560,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_chunk_merge.py","sha256":"709b4122970c72ccf91c23a04207eb01a135658b915f7481778e2a30f6b7507a","start":559},{"end":21,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/__init__.py","sha256":"f7e964b087d5684db7b583c2d6ac67c11fdd2885de2d150f92c9f8fd4451c5be","start":3}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=sop-structure-extraction facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=26ed2df76b49b83fd120eabe720fa640c1dd17a36753f560aa77e4267f7426d9 -->
**超长单次输入截断换取成本可控，代价是提示不完整（推断）**
设计推断（非作者历史意图）：

非分块路径直接把 raw_text 截到 room_single 并在 merge_warnings 记 "single_shot_prompt_truncated_to_{n}_chars"，避免分块多次调用；代价是截断后文档尾部信息不进入本次抽取（推断自 shown lines 350-363）。

来源：[jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py:L349–L363](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py#L349-L363)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":363,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py","sha256":"dbd52d0c8f9e794a2360f5f2c9439b6949515073b333d571b843834b9134b968","start":349}],"trace":[]} -->
<!-- /kb:depth -->
