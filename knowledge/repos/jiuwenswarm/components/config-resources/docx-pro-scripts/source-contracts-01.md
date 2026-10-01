---
title: "docx-pro-scripts 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# docx-pro-scripts 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=07b1bbd594eeab85daf2a4b7e37548cd183f0ada9af5c6f11bdcf992dbe6648b -->
**`jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py`**

- 源码对模块职责的说明：docx_pro.py - 专业 Word 文档操作命令行工具（docx-pro 技能主入口）。
- 调用入口 `cmd_create(args)`。
- 调用入口 `cmd_from_md(args)`。
- 调用入口 `cmd_to_md(args)`。
- 调用入口 `cmd_replace(args)`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import io`；`import json`；`import logging`；`import os`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py#L1-L425)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_replace.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=63400e5c5b32e1033d704aff25563ff05476a701afb98155e617fe859999a3d4 -->
**`jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_replace.py`**

- 源码对模块职责的说明：docx_replace.py - Word (.docx) 保真文本替换引擎（docx-pro 技能）。
- 调用入口 `replace_in_xml(xml_text, old, new, case_sensitive, count_only)`。
- 调用入口 `replace_in_docx(src, dst, pairs, **options)`。
- 调用入口 `count_in_docx(path, old, scope, case_sensitive)`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import bisect`；`import json`；`import re`；`import zipfile`。
- 模块级配置或常量名称：`SENTINEL`, `WT_RE`, `BREAK_PAT`, `REPLACE_ALL_PARTS`, `REPLACE_ALL_PREFIXES`, `REPLACE_BODY_PARTS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_replace.py#L1-L348)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/md_export.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ad2e34a6a4e91fb6fd354a1a1c596b310b970d276ee98771b7c5a5e301c8db4d -->
**`jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/md_export.py`**

- 源码对模块职责的说明：docx -&gt; Markdown 导出器。。
- 调用入口 `docx_to_markdown(path, images_dir)`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import logging`；`import os`；`import re`；`from docx import Document`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/md_export.py#L1-L229)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/md_parser.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a997b43d6dd6bd25a5733c8a4198c49451b3a5e8b09d17dec01970faa0de12bb -->
**`jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/md_parser.py`**

- 源码对模块职责的说明：Markdown -&gt; docx-pro 大纲 解析器。。
- 调用入口 `parse_markdown(md_text, base_dir)`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import os`；`import re`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/md_parser.py#L1-L225)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/renderer.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c1ec348ba25b443917eccb7181b102e98c46f2b995c9845f0978d23d7e611bdc -->
**`jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/renderer.py`**

- 源码对模块职责的说明：docx-pro 渲染引擎：主题系统 + 文档块渲染器。。
- 调用入口 `get_theme(name)`。
- 调用入口 `parse_inline(text)`。
- 调用入口 `add_runs(p, spec, theme, **options)`。
- 调用入口 `add_hyperlink(p, url, text, theme, size)`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import os`；`import re`；`from xml.sax.saxutils import escape`；`from docx import Document`。
- 模块级配置或常量名称：`THEMES`, `DEFAULT_THEME`, `INLINE_TOKEN_RE`, `BLOCK_RENDERERS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/renderer.py#L1-L714)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/setup_check.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9c48978b9a09211cf9de085006d3ddab61b1ace52a543b277ae3b0d3618a7226 -->
**`jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/setup_check.py`**

- 源码对模块职责的说明：docx-pro 依赖自检：确认 python-docx 可用。。
- 调用入口 `check()`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import logging`；`import sys`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/setup_check.py#L1-L30)。
<!-- /kb:file -->
