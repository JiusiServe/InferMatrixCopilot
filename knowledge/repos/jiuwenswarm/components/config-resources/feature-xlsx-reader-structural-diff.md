---
title: "XLSX 只读结构读取器与编辑损伤差分（xlsx_reader.py）"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L32-L50, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L104-L141, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L156-L163, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L81-L99, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L109-L124, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L67-L78, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L136-L139, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L176-L177, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L165-L178, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L32-L44, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L116-L119, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L138-L139]
feature: "xlsx-reader-structural-diff"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py"]
---

# XLSX 只读结构读取器与编辑损伤差分（xlsx_reader.py）

<!-- kb:knowledge owner=feature-xlsx-reader-structural-diff facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**只读双通道：原始 zip 探测 + openpyxl 解析**

数据流分两条通道：`_zip_features` 直接读 zip 包文件名来判定宏、透视表/缓存、图表、sharedStrings、calcChain 等部件是否存在（不解析 XML，作者注释称 robust）；`describe` 再用 `load_workbook(read_only=True)` 补充表名、行列数、sheet 状态与命名区域。差分模式 `diff_against` 对新旧文件各跑一次 `describe` 做结构对比，再调用 `_sheet_sample` 做单元格采样对比，全程不写任何文件。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L32–L50](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py#L32-L50), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L104–L141](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py#L104-L141)

<!-- kb:knowledge owner=feature-xlsx-reader-structural-diff facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**CLI 选项与采样上限**

配置全部来自命令行：`--preview` 默认 0（关闭预览），`--json` 切换 JSON 输出，`--diff-against` 指定旧文件（L156–L163）。`_sheet_sample` 的采样上限硬编码为默认参数 `max_sheets=50`、`max_cells=200`（每个工作表最多收集 200 个非空单元格，且只遍历前 50 张表）（L81–L99）。diff 的判定范围由代码固定：工作表名称及顺序变化、三个特征位（宏、透视表、图表）丢失、命名范围被删除，以及尽力而为的单元格样本比较（L109–L139）。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L156–L163](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py#L156-L163), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L81–L99](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py#L81-L99), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L109–L124](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py#L109-L124)

<!-- kb:knowledge owner=feature-xlsx-reader-structural-diff facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**只读结构发现与损伤差分**

两条只读通道：`_zip_features` 直接读 zip 文件名判定宏、透视表/缓存、图表、sharedStrings、calcChain 等部件存在性（L32–L44）；`describe`/`preview` 用 openpyxl `read_only=True` 补充表名、行列数、sheet 状态、命名区域与预览（L47–L78），全程不写文件。`--diff-against` 比较新旧文件的结构与单元格样本：预览用 `data_only=True` 读取的是文件中已缓存的公式结果值而非重新计算（L68）；样本变更列表在 JSON 报告中截断为 100 条（L136），纯文本输出下最多展示 20 条（L176–L177）。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L32–L50](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py#L32-L50), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L67–L78](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py#L67-L78), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L136–L139](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py#L136-L139), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L176–L177](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py#L176-L177)

<!-- kb:knowledge owner=feature-xlsx-reader-structural-diff facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**验证方式：退出码与输出形态**

diff 模式的验证信号是退出码：`ok` 为真返回 0，否则返回 1（L178）。文本输出分支会打印 `RESULT: OK.../PROBLEMS FOUND` 以及 issues、notes 和最多 20 条样本变更（L170–L177）；但 `--json` 分支只输出 JSON 报告，不打印 RESULT 文本（L167–L168）。因此自动化校验应依赖退出码或 JSON 的 `ok` 字段，而非 RESULT 文本。所提供的材料中未包含该脚本的测试文件。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L165–L178](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py#L165-L178)

<!-- kb:knowledge owner=feature-xlsx-reader-structural-diff facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**zip 探测的取舍与有限的特征丢失检查**

结构探测用 `_zip_features` 直接读 zip 文件名而非解析 XML，作者注释称 robust（无解析开销/风险），代价是只能判断部件存在性（L32–L44）。差分只对三个特征位——宏、透视表、图表——检查"旧有新无"并计入 issues；其余已探测部件（透视缓存、sharedStrings、calcChain 等）丢失不会触发问题报告（L116–L119）。单元格对比是尽力而为的采样：默认每表最多 200 个非空单元格、前 50 张表（L81–L99），且异常时降级为 notes 而非失败（L138–L139），因此大表超出采样范围的损伤可能漏检。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L32–L44](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py#L32-L44), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L116–L119](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py#L116-L119), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L81–L99](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py#L81-L99), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py:L138–L139](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/xlsx_reader.py#L138-L139)

