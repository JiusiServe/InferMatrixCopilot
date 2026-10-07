---
title: "XLSX Computed Column Adder：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py:L67-L115, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py:L57-L78, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L50-L77, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py:L28-L38, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py:L105-L109, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py:L21-L25, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py:L67-L78, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py:L51-L65, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py:L111-L116, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py:L104-L109, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L242-L257, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/SKILL.md:L97-L108, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/SKILL.md:L118-L127]
feature: "xlsx-add-computed-column"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py"]
---

# XLSX Computed Column Adder：实现深读

[功能概览](feature-xlsx-add-computed-column.md) · [owner 入口](_index.md)

<!-- kb:depth feature=xlsx-add-computed-column facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f0e45819dc1540ec9518784826c6f72010fd284a0c404358e798d9a17a75ccda -->
**main(): resolve sheet, patch styles, write header/formula/total cells, then repack-ready save**
main() splits the target column ref, resolves the worksheet (defaulting to the first sheet name from workbook.xml), builds Styles, adds numfmt/border entries, writes optional header, formula cells for --formula-rows via {row} substitution, optional total cell, optional row-wide top border, then sorts sheetData, updates dimension, saves styles and writes the worksheet XML, printing "added column <col> on '<sheet>'".

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py:L67–L115](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py#L67-L115)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":115,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py","sha256":"efb4a566996572252fc4a2653e4b1e789ed329fe1c5e484d03bbed990cf3aa68","start":67}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-add-computed-column facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b1713f72e81c817cda6da0efa8f4f9bb0f321daac62e42a7e3b6d0e65947002e -->
**main()：位置参数 workdir 加 --col（必填）等选项，成功后打印并局部 return 0**
命令行契约：位置参数 workdir，--col 必填；--header-row 默认 1，--border-style 默认 "medium"，--sheet/--header/--formula/--formula-rows/--total-row/--total-formula/--numfmt/--border-row 可选。成功路径先排序、更新 dimension、保存 styles 与 worksheet XML，打印 "added column …" 后局部 return 0（不构成进程退出码证明）。

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py:L51–L65](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py#L51-L65), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py:L111–L116](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py#L111-L116)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":65,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py","sha256":"25e1cb9e5506f9c5582202b3fcbfb307e559f827ec76b51e345da63582475389","start":51},{"end":116,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py","sha256":"30ee48cc8b7573de410b1608b8d8bf2d2b58b01224465d84529cf53776f6c059","start":111}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-add-computed-column facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6f3517f8b8c7ec03d90a07c4295c12b3a70687f3cd06d27f6e30d6b5609486dd -->
**Defaults within main(): header-row 1, border-style "medium", sheet falls back to first sheet**
When --sheet is omitted, sheet = X.first_sheet_name(args.workdir), i.e. the first <sheet> in xl/workbook.xml. --header-row defaults to 1 and --border-style defaults to "medium"; style wiring is conditional: data_xf is created only if a --numfmt was given, and total_xf/border styles only if --border-row is set.

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py:L57–L78](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py#L57-L78)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":78,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py","sha256":"5650a398e46d657350d4a0438e37c4a02e316880c6b758dd8970d230645fbfb0","start":57}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-add-computed-column facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=257e4d9a26a3d9e85404901fb840e60104e8ebd89854f5564f4b22e36c185d55 -->
**Imports _xlsx_common and resolves the target sheet through workbook.xml and its .rels**
xlsx_add_column.py imports _xlsx_common as X and uses its first_sheet_name/resolve_worksheet/Styles helpers; resolve_worksheet maps the sheet display name to an r:id in xl/workbook.xml and then to a Target in xl/_rels/workbook.xml.rels, raising SystemExit("sheet not found: …") or "relationship not found…" when either lookup fails.

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py:L21–L25](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py#L21-L25), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py:L67–L78](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py#L67-L78), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L50–L77](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py#L50-L77)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":25,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py","sha256":"2074a174a399e5bdc1697eb544c973334f983c716b6b3663ddc4022fad18a914","start":21},{"end":78,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py","sha256":"7505d5ae1d3f200cfb3a930669b7aa690b85861be14a2ccd232f844da198a269","start":67},{"end":77,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py","sha256":"689b0d54c7e9d3a355f2aa5a27fca05ad4998f4a85c8dff936a4147de7488352","start":50}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-add-computed-column facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=afebf2ef7856148a633f699b28ecca056ee93fcbe08f9f3354abf39c073805b7 -->
**Sheet resolution failures raise SystemExit with message; border pass preserves each cell's numFmtId**
resolve_worksheet raises SystemExit("sheet not found: <name>") when the display name is absent from workbook.xml and SystemExit("relationship not found for sheet: ...") when the r:id has no matching relationship entry; first_sheet_name raises SystemExit("no sheets found in workbook.xml") if workbook.xml has no sheet. In the border pass, numfmt_of returns numFmtId 0 when the cell's style index or cellXfs is missing, so add_xf is still applied.

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L50–L77](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py#L50-L77), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py:L28–L38](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py#L28-L38), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py:L105–L109](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py#L105-L109)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":77,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py","sha256":"689b0d54c7e9d3a355f2aa5a27fca05ad4998f4a85c8dff936a4147de7488352","start":50},{"end":38,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py","sha256":"efb2d6c75547ab6f0a1ce0024fd7cd9b28a04b43dc48dc9373c58937e59550f4","start":28},{"end":109,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py","sha256":"05a0a6a33de6d3ba2f812948cb0593690b09100c22e9a9f8116c4bf9dfae2657","start":105}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-add-computed-column facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ba117b1769f89ce6ecb789caf137dbcde3ee36c955f03675ab2409051c4edf54 -->
**--border-row 保留各单元格 numFmtId，但新 xf 将 fontId/fillId 固定为 0 且逐格追加 xf**
设计推断（非作者历史意图）：

推断：行级加顶边框时用 numfmt_of 读取原样式的 numFmtId 并写入新 xf，避免破坏数字格式；代价是每个单元格的字体/填充被重置为 fontId="0"、fillId="0"，且 add_xf 为每个单元格追加新 cellXfs 条目而非复用。

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py:L104–L109](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py#L104-L109), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py:L28–L38](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py#L28-L38), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L242–L257](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py#L242-L257)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":109,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py","sha256":"62069084db9df821be8f1fe008038475211304e64d73c96ce94f49c1e7e5f3f8","start":104},{"end":38,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py","sha256":"efb2d6c75547ab6f0a1ce0024fd7cd9b28a04b43dc48dc9373c58937e59550f4","start":28},{"end":257,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py","sha256":"26bde344bcf90076fe03eaa4bd7de111f2d4e9759d38a0968c9e1bd4395ae798","start":242}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-add-computed-column facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0436ce50503164a6ef1c2eb05c26e849efb442d1dfeafde7288619d05cf32576 -->
**Documented manual edit-and-verify procedure for the add-column flow (NOT EXECUTED)**
文档中的人工验收步骤（本轮未执行）：

SKILL.md documents a manual procedure: unpack input.xlsx with xlsx_unpack.py, run xlsx_add_column.py (e.g. --col G with --formula '=F{row}/$F$10' --formula-rows 2:9 --total-row 10 --total-formula '=SUM(G2:G9)' --numfmt '0.0%' --border-row 10 --border-style medium), repack with xlsx_pack.py into output.xlsx, then verify with `xlsx_reader.py --diff-against input.xlsx` and confirm original sheet names, named ranges, pivots/macros, and a sample of original data are present; if verification fails, fix before delivering. These steps are documented only and were NOT EXECUTED here.

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/SKILL.md:L97–L108](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/SKILL.md#L97-L108), [jiuwenswarm/resources/agent/workspace/skills/xlsx/SKILL.md:L118–L127](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/SKILL.md#L118-L127)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":108,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/SKILL.md","sha256":"03c9dd4d5a1c999be293bdf50e99a79d65f84479c033b655e5748a8e39bdcf08","start":97},{"end":127,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/SKILL.md","sha256":"debfbf11add6d21aa3aec206eb5a079e419cd3460e199a7de1c5cb4ff125efd7","start":118}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
