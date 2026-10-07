---
title: "XLSX Skill Format-Preserving Unpack/Repack：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_unpack.py:L16-L38, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py:L30-L54, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py:L22-L27, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py:L47-L52, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_unpack.py:L3-L13, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py:L3-L19, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_unpack.py:L17-L23, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py:L31-L47, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py:L48-L52, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py:L8-L15, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/SKILL.md:L100-L105]
feature: "xlsx-workbook-unpack-repack"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py", "jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_unpack.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py", "jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_unpack.py"]
---

# XLSX Skill Format-Preserving Unpack/Repack：实现深读

[功能概览](feature-xlsx-workbook-unpack-repack.md) · [owner 入口](_index.md)

<!-- kb:depth feature=xlsx-workbook-unpack-repack facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7eac0c326a836e407eeb63a5387fd26a695524253e80abe9d6a913e40280bf16 -->
**Unpack extracts workbook ZIP parts, then pack walks the dir and rewrites a sorted ZIP**
xlsx_unpack.py main() 校验 argv 长度与 zipfile.is_zipfile 后 extractall 到 outdir 并打印 part 数及 VBA/pivot/chart 提示；xlsx_pack.py main() 用 os.walk 收集文件为 arc 名，按 _order_key 排序（[Content_Types].xml 首位、_rels/ 次之），逐个写入输出 ZIP，vbaProject.bin 用 ZIP_STORED 其余 ZIP_DEFLATED，最后打印 packed N parts 并 return 0。

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_unpack.py:L16–L38](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_unpack.py#L16-L38), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py:L30–L54](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py#L30-L54)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":38,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_unpack.py","sha256":"3a03858563ae432c30f78c9484080274eaa6a42259d82bd3b5df02b9371ba115","start":16},{"end":54,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py","sha256":"51ee28f957a2f89c463ce3b0e4295216e8a751f1f7431fff10200898f861e720","start":30}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-workbook-unpack-repack facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=149b4a45af0349a67f7c14bdc4c42937b4b648c4e0c82f2c0a275156ede46ee1 -->
**Both scripts take exactly two positional argv paths; wrong argc returns 2, ZIP/dir checks return 1**
`xlsx_unpack.py INPUT.xlsx OUTDIR/` 先用 `zipfile.is_zipfile` 校验输入，再 `extractall` 到（必要时创建的）目录，并打印解包的部件数；仅当存在 `xl/vbaProject.bin`、pivotTable 或 `xl/charts/` 部件时额外打印 NOTE。`xlsx_pack.py SRCDIR/ OUTPUT.xlsx` 要求 SRCDIR 是目录，遍历后按 `_order_key` 排序写入输出 ZIP 并打印 `packed N parts`，随后 `return 0`（main 内返回，非进程退出码断言）。

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_unpack.py:L16–L38](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_unpack.py#L16-L38), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py:L30–L54](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py#L30-L54)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":38,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_unpack.py","sha256":"3a03858563ae432c30f78c9484080274eaa6a42259d82bd3b5df02b9371ba115","start":16},{"end":54,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py","sha256":"51ee28f957a2f89c463ce3b0e4295216e8a751f1f7431fff10200898f861e720","start":30}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-workbook-unpack-repack facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=10ff66371d6debe76cfef91ebf973847ef83931075e3f2ef2ec2b24f402569bb -->
**No configurable settings; entry ordering and compression are hardcoded**
两个脚本均无配置项或环境变量：入口顺序由 _order_key 硬编码（[Content_Types].xml → (0,arc)、_rels/ → (1,arc)、其余 (2,arc)），压缩方式仅由文件名后缀 vbaProject.bin 决定 ZIP_STORED，否则 ZIP_DEFLATED。

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py:L22–L27](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py#L22-L27), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py:L47–L52](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py#L47-L52)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":27,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py","sha256":"f3a3177520eda3f031ad4f0e434bb05980530ca99cb9b1a7f977b9cc2518fe3c","start":22},{"end":52,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py","sha256":"e72e4b6213e6d22e60f474db086b07581c62d4d2e1521df90146bc92c92fdd2a","start":47}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-workbook-unpack-repack facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1ef24791078b3a85c2e96f8313fc70a8cfb2e832925461e398ab112887dad577 -->
**Depends only on Python stdlib (os, sys, zipfile), avoiding openpyxl round-trips**
两个脚本仅 import os/sys/zipfile，把 .xlsx 当 ZIP of XML parts 处理；模块 docstring 说明这是 openpyxl 往返的 format-preserving 替代方案，vbaProject.bin 以未压缩存储保持宏有效。

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_unpack.py:L3–L13](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_unpack.py#L3-L13), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py:L3–L19](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py#L3-L19)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":13,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_unpack.py","sha256":"7adcdd35dfd894fc5916fc54f784216e9cbd343ef350930177be7ada72050c59","start":3},{"end":19,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py","sha256":"9a6c6e3ee46762ed02f9d1b80a575a533f0e2bb82580ac9379a49a27b396b68c","start":3}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-workbook-unpack-repack facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a9871608c01ea767f1729e6116c2eb412b32893a8aa1a498a90c7a72ff4921ab -->
**Usage error returns 2; non-zip input or missing srcdir returns 1 with stderr message**
unpack: `len(sys.argv)!=3` → stderr usage、return 2；`not zipfile.is_zipfile(src)` → stderr "not a valid xlsx/zip: src"、return 1。pack: 目录不存在 → stderr "not a directory: srcdir"、return 1；若收集的 arcs 缺 [Content_Types].xml 仅打印 WARNING 到 stderr 仍继续打包（return 0）。

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_unpack.py:L17–L23](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_unpack.py#L17-L23), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py:L31–L47](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py#L31-L47)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":23,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_unpack.py","sha256":"db4a466f69300ef19fabc528d07c43e9d40a29b0086e8dd897fe7298c4e33409","start":17},{"end":47,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py","sha256":"f87c082925b69afa093adcfcd3cb6b2a3a48bd4785b00fcd360096b94c9baf68","start":31}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-workbook-unpack-repack facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e31db51eb70eaca1a54b37a683a783ddbdae9b088af3ebcacdb15c5788bd7d97 -->
**Pack keeps vbaProject.bin stored uncompressed but shifts sharedStrings/calcChain repair to the caller**
Benefit (documented intent): xlsx_pack.py writes parts ending in vbaProject.bin with ZIP_STORED and all others deflated so macros stay valid. Cost (documented): pack does NOT recompute sharedStrings counts or rebuild calcChain — the caller must edit those in the unpacked dir or run libreoffice_recalc.py for formula cells without a cached <v>. Inference: storing the macro blob uncompressed can enlarge the output file relative to deflating it.

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py:L48–L52](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py#L48-L52), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py:L8–L15](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py#L8-L15)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":52,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py","sha256":"db6639b97d23d4374a189f203d068b3e06c210b7356d5e13c4ad065c123b7b46","start":48},{"end":15,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py","sha256":"27bec7bb29a34f16a78a6c7b9ff29d5129f341a3f8939887ab03c8f04c9cc4c0","start":8}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-workbook-unpack-repack facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=116c4c708b292022e9652d5b2a3deb64f7ad792606af9dbb797bab9841825269 -->
**Documented manual EDIT verification: xlsx_reader.py --diff-against the input (NOT EXECUTED here)**
文档中的人工验收步骤（本轮未执行）：

SKILL.md EDIT rule 5 directs running xlsx_reader.py output.xlsx --diff-against input.xlsx after packing and confirming original sheet names, named ranges, pivots/macros, and a sample of original data before delivery; a failed check must be fixed before delivering. This is a documented procedure only — it was not executed and no automated runtime or source-text test for this feature is shown.

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/SKILL.md:L100–L105](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/SKILL.md#L100-L105)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":105,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/SKILL.md","sha256":"42b94fde0cdc45e934046266d14c89b712addd9f295bf119d9f69e641399669f","start":100}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
