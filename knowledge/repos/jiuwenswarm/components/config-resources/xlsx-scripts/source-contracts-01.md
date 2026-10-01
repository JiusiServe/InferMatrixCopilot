---
title: "xlsx-scripts 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# xlsx-scripts 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c9e0770adbc7d7e5348d2c451f299183b2fa839065870df322b1998fcbf25326 -->
**`jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py`**

- 源码对模块职责的说明：Shared helpers for the XLSX XML-editing scripts.。
- 调用入口 `col_to_num(col)`。
- 调用入口 `num_to_col(n)`。
- 调用入口 `split_ref(ref)`。
- 调用入口 `parse(path)`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import os`；`import re`；`from lxml import etree`。
- 模块级配置或常量名称：`MAIN`, `RNS`, `XMLNS`, `M`, `R`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py#L1-L260)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1ff21f6b0dc33577a6cccf495a053e1e8b9e11915f70ad27d62f5195c298e90e -->
**`jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py`**

- 源码对模块职责的说明：doctor.py - Environment & dependency self-check for the XLSX skill.。
- 调用入口 `check_python(results)`。
- 调用入口 `check_py_deps(results)`。
- 调用入口 `check_cli(results)`。
- 调用入口 `check_cjk_font(results)`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import importlib`；`import json`；`import shutil`。
- 模块级配置或常量名称：`PY_DEPS`, `CLI_TOOLS`, `CJK_FONT_HINTS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py#L1-L134)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=034175eab788c36696fa52710eb5f821a0da76b8bebb38a3d268e7ad3503e31a -->
**`jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py`**

- 源码对模块职责的说明：formula_check.py - Static validation of a workbook's formulas & cached values.。
- 调用入口 `main()`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import json`；`import sys`。
- 模块级配置或常量名称：`ERROR_TOKENS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/formula_check.py#L1-L83)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/libreoffice_recalc.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f45d04479eeb871e47eaf092021c058979c4191857979e25f6b3d1aada1b1075 -->
**`jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/libreoffice_recalc.py`**

- 源码对模块职责的说明：libreoffice_recalc.py - Recalculate formulas and write back cached values.。
- 调用入口 `main()`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import os`；`import shutil`；`import subprocess`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/libreoffice_recalc.py#L1-L70)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1d20dbf5abe1c5c92755f93476da5964b69795dc29eb0ae23df1258ec8f8c15a -->
**`jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py`**

- 源码对模块职责的说明：xlsx_add_column.py - Add a computed column to an unpacked workbook dir.。
- 调用入口 `numfmt_of(st, sidx)`。
- 调用入口 `style_of(sd, col, rownum)`。
- 调用入口 `main()`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import sys`；`import _xlsx_common as X`；`from _xlsx_common import M`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_add_column.py#L1-L120)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=06ecc213666f28f14b0a9d41b1ba83726660241421a4746faf4da60ccbd88aef -->
**`jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py`**

- 源码对模块职责的说明：xlsx_insert_row.py - Insert a row into an unpacked workbook dir.。
- 调用入口 `parse_pairs(items)`。
- 调用入口 `style_of(sd, col, rownum)`。
- 调用入口 `main()`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import sys`；`import _xlsx_common as X`；`from _xlsx_common import M`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py#L1-L95)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e63b7734ee29be388969d1837b5a4e8d483e134c07f9f326936e0b3dc2c480cd -->
**`jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py`**

- 源码对模块职责的说明：xlsx_pack.py - Repack a directory into a valid .xlsx/.xlsm.。
- 调用入口 `main()`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import os`；`import sys`；`import zipfile`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_pack.py#L1-L58)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=aabe447c7059f9d9897856327311744d255ee5beabf078810f73096506b55251 -->
**`jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py`**

- 源码对模块职责的说明：xlsx_reader.py - Structure discovery + structural diff for the XLSX skill.。
- 调用入口 `describe(path)`。
- 调用入口 `preview(path, sheet, n)`。
- 调用入口 `diff_against(new_path, old_path)`。
- 调用入口 `main()`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import json`；`import sys`；`import zipfile`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py#L1-L200)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_render.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1f1bc167b80a2ab6b8e9ca271bd954314610019ac4b8b5c219bcd7fb28c67af9 -->
**`jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_render.py`**

- 源码对模块职责的说明：xlsx_render.py - Render a workbook to PNG/PDF for visual review, with CJK fonts.。
- 调用入口 `to_pdf(src, outdir)`。
- 调用入口 `pdf_to_pngs(pdf, outdir, prefix)`。
- 调用入口 `render(src, outdir, pdf_only)`。
- 调用入口 `render_diff_html(old_src, new_src, html_path)`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import base64`；`import glob`；`import os`。
- 模块级配置或常量名称：`CJK_FONT_CANDIDATES`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_render.py#L1-L169)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_shift_rows.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=27b6e9b8ca7748605b5d63377d431819ce5865fb6d2ca3329544b471b3c1c075 -->
**`jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_shift_rows.py`**

- 源码对模块职责的说明：xlsx_shift_rows.py - Low-level row shifter on an unpacked workbook dir.。
- 调用入口 `main()`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import sys`；`import _xlsx_common as X`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_shift_rows.py#L1-L50)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_unpack.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a770502ad38210030c53737595f8e6f272c830ab1fcdacfca8d2b7dcce3cd78c -->
**`jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_unpack.py`**

- 源码对模块职责的说明：xlsx_unpack.py - Unpack a workbook (ZIP of XML parts) into a directory.。
- 调用入口 `main()`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import os`；`import sys`；`import zipfile`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_unpack.py#L1-L42)。
<!-- /kb:file -->
