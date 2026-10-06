---
title: "XLSX Row Insert with Range Extension（jiuwenswarm skills/xlsx 脚本）"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L57-L77, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L66-L89, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L3-L7, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L52-L60, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L96-L113, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L5-L20, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_shift_rows.py:L9-L12, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L66-L85, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L154-L169, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L14-L20, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L179-L196, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L142-L157, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L5-L7]
feature: "xlsx-insert-row"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py", "jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_shift_rows.py", "jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py"]
---

# XLSX Row Insert with Range Extension（jiuwenswarm skills/xlsx 脚本）

<!-- kb:knowledge owner=feature-xlsx-insert-row facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**架构：分层与数据流**

三层结构：xlsx_insert_row.py 是面向用户的编排层，xlsx_shift_rows.py 是薄 CLI 包装，共享逻辑集中在 _xlsx_common.py。数据流为：workbook.xml 按表名查 r:id，再到 workbook.xml.rels 解析出 worksheet XML 路径（支持绝对/相对 Target）；随后依次 shift_rows → extend_ranges → get_or_make_row → 写入新单元格 → sort_sheetdata → update_dimension → 原位写回。所有编辑直接作用于解包目录里的 XML，宣称对未触碰单元格零格式损失。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L57–L77](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py#L57-L77), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L66–L89](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py#L66-L89), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L3–L7](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py#L3-L7)

<!-- kb:knowledge owner=feature-xlsx-insert-row facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**配置：参数与默认值**

本组件无配置文件，行为完全由 CLI 参数决定。--at 为必需整数；--sheet 缺省时取 workbook.xml 中第一个 sheet（first_sheet_name，找不到表时 SystemExit）；--text/--values/--formula 缺省为空列表；--copy-style-from 缺省为 None（不加样式属性 s）。文本单元格写成 inlineStr 并保留空白，数值写 <v>，公式的等号前缀被去掉后写入 <f>。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L52–L60](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py#L52-L60), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L96–L113](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py#L96-L113)

<!-- kb:knowledge owner=feature-xlsx-insert-row facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**验证：文档要求的外部校验**

所示片段中没有这些脚本的自动化测试入口；验证方式是流程性的：xlsx_insert_row.py 的文档要求编辑后用 xlsx_pack.py 重新打包并校验，且因单单元格引用不被范围扩展覆盖、xlsx_shift_rows.py 不改写公式文本，两个脚本都明确提示“总是事后验证（Always validate afterwards）”。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L5–L20](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py#L5-L20), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_shift_rows.py:L9–L12](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_shift_rows.py#L9-L12)

<!-- kb:knowledge owner=feature-xlsx-insert-row facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**功能：插行、条件性样式复制与尽力而为的范围扩展**

插入流程在写新单元格前先 shift_rows 腾位并调用 extend_ranges。范围扩展是尽力而为：只对公式文本中 A1:B9 形态的范围端点按行号 >= at 加 delta，单单元格引用不动，文档要求事后核对合计值。样式复制仅在显式传入 --copy-style-from 时发生（按同列读取源行单元格的 s 属性）；未提供时新单元格不带 s 属性。写回前会重排行列并调用 update_dimension，而它只在 dimension 元素已存在且 maxr>0 时更新 @ref。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L66–L85](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py#L66-L85), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L154–L169](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py#L154-L169), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L14–L20](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py#L14-L20), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L179–L196](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py#L179-L196)

<!-- kb:knowledge owner=feature-xlsx-insert-row facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**取舍：直接编辑 XML 的得失**

Inference / 设计推断（非作者历史意图）：

脚本选择直接用 lxml 原位编辑解包目录中的 worksheet XML，模块文档声称对未触碰的单元格零格式损失；代价是公式改写只覆盖范围形态（_RANGE 正则），shift_rows 只改 row@r/cell@r 而不重写公式文本，因此两个脚本的文档都要求编辑后校验。这些是所示源码呈现的边界；将其解读为有意保守的设计选择属于推断，所示证据未包含设计历史。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L3–L7](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py#L3-L7), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py:L142–L157](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/_xlsx_common.py#L142-L157), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_shift_rows.py:L9–L12](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_shift_rows.py#L9-L12), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py:L5–L7](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_insert_row.py#L5-L7)

