---
title: "XLSX Row Insert with Range Extension：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L60-L91, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L3-L20, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L50-L58, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L29-L36, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L53-L60, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L71-L78, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L96-L100, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L50-L54, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L50-L66, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L94-L95, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L154-L169, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L14-L20, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/SKILL.md:L97-L108, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/SKILL.md:L128-L144]
feature: "xlsx-insert-row"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py", "jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_shift_rows.py", "jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py"]
---

# XLSX Row Insert with Range Extension：实现深读

[功能概览](feature-xlsx-insert-row.md) · [owner 入口](_index.md)

<!-- kb:depth feature=xlsx-insert-row facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=33919c4336e721ec686fb42efe4ca27776f92a7f3eeae5f806d705988fac8514 -->
**main()：解析工作表，移位行，扩展范围，写入单元格，排序/更新维度/写入并打印**
main() 解析参数，解析工作表 XML（使用 --sheet 或第一个工作表），调用 X.shift_rows(sd, args.at, 1) 然后调用 X.extend_ranges(sd, args.at, 1)，通过 get_or_make_row 在 --at 位置构建行，写入来自 --text/--values/--formula 的单元格（其中 {row} 被替换为 --at），然后 sort_sheetdata、update_dimension、write，并打印 "inserted row at N on 'S'"；该函数局部返回 0。

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L60–L91](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py#L60-L91)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":91,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py","sha256":"f9f38f3bcee7b2e97a4dcf35edbd72e5a252ff989badfeba3b28cdfc4a8f973b","start":60}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-insert-row facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d22b0607097fc5752b737cd0b068dd5173f6e14bba163820bf173082563e44cd -->
**CLI：位置参数 workdir，必填整数 --at，可选 --sheet/--text/--values/--formula/--copy-style-from**
接收一个解包后的工作簿目录（workdir）作为位置参数，--at 为必填整数；--text/--values/--formula 为 COL=VALUE 对（缺失 '=' 则通过 SystemExit 终止），公式中的 {row} 会被替换为 --at；输出直接写入工作表 XML，文档字符串指出需使用 xlsx_pack.py 重新打包，并在之后进行验证。

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L3–L20](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py#L3-L20), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L50–L58](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py#L50-L58), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L29–L36](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py#L29-L36)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":20,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py","sha256":"c41d7ec134caf92def30a138a646944721846607c2c28256dbd74a8dc18f50f7","start":3},{"end":58,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py","sha256":"cb24dfca52eab88a0b5eccf6569504feaca8fcb9495dd28e6bca0410077c9df4","start":50},{"end":36,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py","sha256":"23ff7477de46dbaabc758dd1b38455334158d320904ab652dc97e130a5b0d1bb","start":29}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-insert-row facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5d5a610292408ce434d27969e2e5063d40d4f5f2dce84dd549fb23a920ceba7b -->
**默认值：工作表回退至 first_sheet_name，pair 列表默认为 []，样式仅在 truthy --copy-style-from 时生效**
当省略 --sheet 时，工作表为 X.first_sheet_name(args.workdir)（workbook.xml 中的第一个 <sheet>）；--text/--values/--formula 默认为空列表；st_for(col) 返回 style_of(...) 仅当 args.copy_style_from 为 truthy 时，否则为 None，且 make_cell 仅在 style 不为 None 时设置 's' 属性。

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L53–L60](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py#L53-L60), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L71–L78](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py#L71-L78), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L96–L100](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py#L96-L100), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L50–L54](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py#L50-L54)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":60,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py","sha256":"9daee6b7626099e949140dba04d74925934fa66b569c9f8a2e98693c7f285f4a","start":53},{"end":78,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py","sha256":"a23046b132aa9f6d3644c72e4b5ece0dd5b0bd8ec1609a204fbbd06221f11b0f","start":71},{"end":100,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py","sha256":"364776dbe6af58fb6febe0eb56fc82cce04a2a1a30814adcdff2935fef1f8c1e","start":96},{"end":54,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py","sha256":"1d64ccb2e9c6493a82dca604b427228705ea998aa3b610564d154cdb6fa86591","start":50}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-insert-row facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4aabaf93e3dc2717ad649c25c7239ea51c9a9b18751f1f75f6bffdf593ca8275 -->
**通过 SystemExit 停止：格式错误的 COL=VALUE 对、没有工作表，以及未找到工作表**
parse_pairs 在任何没有 '=' 的项上引发 SystemExit("expected COL=VALUE, got: …")；first_sheet_name 在 workbook.xml 没有工作表时引发 SystemExit("no sheets found in workbook.xml")；resolve_worksheet 在名称不匹配任何工作表时引发 SystemExit("sheet not found: …")。这些错误通过 sys.exit(main()) 从正在运行的脚本中传播出来。

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L29–L36](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py#L29-L36), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L50–L66](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py#L50-L66), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L94–L95](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py#L94-L95)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":36,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py","sha256":"23ff7477de46dbaabc758dd1b38455334158d320904ab652dc97e130a5b0d1bb","start":29},{"end":66,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py","sha256":"ac5cb0865b30c0ffe6137fc1b80bee324f1184fc40b2959a3bcc5a5679a1cadc","start":50},{"end":95,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py","sha256":"c86a687dc0735836998a4f2d1ad0536d34c088d503731b70989149cd3c97105a","start":94}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-insert-row facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=22cb3ccb5d93b6ea4397bfc43fa10cd1cc504f50a425eff5fd6508e73ba08dae -->
**extend_ranges is best-effort: A1:B9-style totals ranges are bumped, single-cell refs are not**
设计推断（非作者历史意图）：

Benefit: the regex repl in extend_ranges bumps each range endpoint with row >= at by delta, so a totals-below SUM range keeps including the inserted row. Cost: it only rewrites two-cell ranges matching _RANGE — single-cell references are left untouched and the docstring says to validate totals afterwards. [inference: the benefit/cost framing within this implementation is my reading of the repl guard and module docstring.]

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L154–L169](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py#L154-L169), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L14–L20](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py#L14-L20)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":169,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py","sha256":"7ee3efee71df69ad7fa176fac88e73d99a2acc91237ae8f29ac35b4e772a1ce2","start":154},{"end":20,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py","sha256":"40b0df732715a598cea62b1f34f7ec6bd9502eda3cca2aaa28590c84596d00ca","start":14}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-insert-row facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b57d6291ebc38cbb719c03a943fa1686b2402b2ab01d83fd6e9ece508e62d153 -->
**Documented manual procedure for insert-row with post-save diff verification (NOT EXECUTED)**
文档中的人工验收步骤（本轮未执行）：

SKILL.md documents unpacking, running xlsx_insert_row.py with --at/--text/--values/--formula/--copy-style-from, then repacking with xlsx_pack.py; the EDIT rules require verifying the saved output with `xlsx_reader.py --diff-against input.xlsx` (confirming sheets, named ranges, pivots/macros, and sample data) before delivering. This is a documented procedure only; no automated test covering xlsx_insert_row.py appears in the offered evidence.

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/SKILL.md:L97–L108](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/SKILL.md#L97-L108), [jiuwenswarm/resources/agent/workspace/skills/xlsx/SKILL.md:L128–L144](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/SKILL.md#L128-L144)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":108,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/SKILL.md","sha256":"03c9dd4d5a1c999be293bdf50e99a79d65f84479c033b655e5748a8e39bdcf08","start":97},{"end":144,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/SKILL.md","sha256":"b5f626731547b6f22e65aec059c649c8125275116012d124e204d4e9f81d02f0","start":128}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
