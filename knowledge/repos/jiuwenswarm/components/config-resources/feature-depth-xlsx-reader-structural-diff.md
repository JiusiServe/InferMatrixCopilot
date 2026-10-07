---
title: "XLSX Read-Only Structure Reader and Edit-Damage Differ：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L25-L29, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L32-L44, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L165-L178, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L199-L200, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L126-L141, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L67-L71, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L81-L101, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L126-L130, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L156-L196]
feature: "xlsx-reader-structural-diff"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py"]
---

# XLSX Read-Only Structure Reader and Edit-Damage Differ：实现深读

[功能概览](feature-xlsx-reader-structural-diff.md) · [owner 入口](_index.md)

<!-- kb:depth feature=xlsx-reader-structural-diff facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5cedb8b06510330b9f671d630b2cd923a11f39ac195bbf5b39b98b33786f639b -->
**main() dispatches --diff-against to diff_against() and returns 0 only when report['ok']**
When --diff-against OLD is given, main() calls diff_against(args.file, OLD), prints JSON or a text report (issues prefixed '!', notes '.', up to 20 '~' changed-cell lines), and returns 0 if rep['ok'] else 1; main()'s return value is passed to sys.exit at module run.

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L165–L178](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py#L165-L178), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L199–L200](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py#L199-L200)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":178,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py","sha256":"4394110275cd0c95d74c2e13592fd476627df88af87066279e8211399f02c143","start":165},{"end":200,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py","sha256":"c86a687dc0735836998a4f2d1ad0536d34c088d503731b70989149cd3c97105a","start":199}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-reader-structural-diff facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=796e59d96111fd35abedee5526d1c32020b134dd0245ec0f246cb0a1cc22335d -->
**main() CLI: FILE plus --diff-against OLD.xlsx dispatch, returning 0/1 from the diff branch**
main() 接受位置参数 file、--sheet、--preview（默认 0）、--diff-against、--json。当 --diff-against 为真时调用 diff_against(args.file, args.diff_against)，--json 打印缩进 JSON，否则打印 RESULT 与 issues/notes/前 20 条 changed_cells_sample，并在该分支内 return 0 if rep["ok"] else 1；仅当 --preview 和 --sheet 同时为真才调用 preview()。入口处 sys.exit(main())。

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L156–L196](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py#L156-L196), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L199–L200](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py#L199-L200)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":196,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py","sha256":"f81444e9dc165ffcc55eb670c3414da5fc1c0c86df49cac86b4740130edf009f","start":156},{"end":200,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py","sha256":"c86a687dc0735836998a4f2d1ad0536d34c088d503731b70989149cd3c97105a","start":199}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-reader-structural-diff facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0ecacc038a7af5ba738dbd787b6981d15a4ca85350d88189e5932c646652901f -->
**采样默认值：_sheet_sample 默认 max_sheets=50、max_cells=200，且限制的是保留的非空单元格数**
diff_against 调用 _sheet_sample 时不传参，使用默认 50/200；循环遍历所有行与列并跳过 None 值，仅在保留的非空单元格计数达到 max_cells 时提前 break，因此该默认不限制被扫描的单元格总数。

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L81–L101](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py#L81-L101), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L126–L130](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py#L126-L130)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":101,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py","sha256":"1647fc42f41a182034e87aa4320a621f85f33497d06c01016ef545523562de27","start":81},{"end":130,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py","sha256":"64587135716b2341ba93e6290b473f41846a318976ddea674eba9adbae210d4d","start":126}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-reader-structural-diff facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=afd5070e0a965aa9765825a5682700d485870dc7c544bf734ad39f3ab82a4cad -->
**Depends on openpyxl (hard) and stdlib zipfile for feature detection**
If `from openpyxl import load_workbook` fails, the script prints 'openpyxl is required: ...' to stderr and exits 2. _zip_features instead reads the package with stdlib zipfile to detect vbaProject.bin, pivotTable/pivotCache names, xl/charts/ parts without openpyxl parsing.

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L25–L29](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py#L25-L29), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L32–L44](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py#L32-L44)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":29,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py","sha256":"ba0685ce2f10d5994634654eb5bb973254b7f9f6f616f7f1c37dc32daf0d04c7","start":25},{"end":44,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py","sha256":"c27a0219fee68ba4bc2613f3a312853650d1a4fc5234646f1b106d5c2cb02a24","start":32}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-reader-structural-diff facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=06d248f3c637e21ac904d2debb81ffe973de47eb9692c364c4c9f5f8593611b4 -->
**In diff mode, cell-sample exceptions become notes without clearing ok; preview() raises SystemExit on missing sheet**
diff_against wraps _sheet_sample calls in try/except: on exception it appends 'cell sample diff skipped: {e}' to report['notes'] and leaves report['ok'] unchanged. Separately, preview() raises SystemExit('sheet not found: ...; available: ...') when the requested sheet is absent — a preview-mode failure, not part of the diff branch.

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L126–L141](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py#L126-L141), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L67–L71](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py#L67-L71)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":141,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py","sha256":"83919907c9ac2329871c0d798b0419d6b343994c1635620cb5a965753a8807ba","start":126},{"end":71,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py","sha256":"026d64ed9d4c59840e87f9ea0f738042c80d4b8f641bf473f1ec0af73b41628f","start":67}],"trace":[]} -->
<!-- /kb:depth -->
