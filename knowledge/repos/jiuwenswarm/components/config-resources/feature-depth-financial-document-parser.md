---
title: "财务文档解析 Skill（发票/收据/对账单解析与报告生成）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py:L82-L103, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py:L507-L554, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py:L521-L525, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py:L421-L425, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py:L17-L29, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py:L105-L108, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py:L135-L158, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py:L135-L153, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py:L532-L554, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py:L135-L148, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/SKILL.md:L24-L46]
feature: "financial-document-parser"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py"]
---

# 财务文档解析 Skill（发票/收据/对账单解析与报告生成）：实现深读

[功能概览](feature-financial-document-parser.md) · [owner 入口](_index.md)

<!-- kb:depth feature=financial-document-parser facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=554e8e37f247fd643f91f062b9666e0fd5b23c2a453a4c3f5be81fc20ad8b7df -->
**FinancialParser.parse: dispatch by file suffix, then post-process and return self.doc**
parse() 先检查文件存在,再按后缀分发:.pdf→_parse_pdf,.png/.jpg/.jpeg→_parse_image,.csv→_parse_csv,其余抛 ValueError;之后依次执行 _detect_doc_type/_categorize_items/_generate_insights 并返回 self.doc。

来源：[jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py:L82–L103](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py#L82-L103)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":103,"path":"jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py","sha256":"46910b6c12ac86565993505bd43e730744b875b8e5a3a0914b921d2b31cd5856","start":82}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=financial-document-parser facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=73f90fa672e0a133e6d7c1d40fc910bdeb69c01ec99a945580fdbedcb7a22207 -->
**main 的 CLI 契约：--format 默认 markdown，csv 导出提示受 --quiet 守卫，异常打印 stderr 并 sys.exit(1)**
main 接受位置参数 file 与 --format（choices markdown/json/csv/all，默认 markdown）。json/all 分支向 stdout 打印结果；csv 分支调用 to_csv(args.output)，仅当未传 --quiet 时才向 stderr 打印「已导出到」路径。try 块（532–550）内的任何 Exception 被捕获，打印「错误: {e}」到 stderr 后 sys.exit(1)；argparse 解析（527）不在此守卫内。

来源：[jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py:L507–L554](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py#L507-L554)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":554,"path":"jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py","sha256":"66a9cd3443fdeb99ebd68ec19f8ca1973f012f7b9c432ea86b7af22c21df881d","start":507}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=financial-document-parser facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5449379e3c6e0321f24fc4e1adf8ded220d3a53a079fdea18ac645a779fc5c1e -->
**--format 默认 markdown;to_csv 无 output 时回退为输入文件同目录 .csv 后缀**
--format/-f 的 choices 为 markdown/json/csv/all,默认 'markdown';--output 仅用于 csv。to_csv(output_path=None) 时 final_path 取 self.file_path.with_suffix('.csv')。

来源：[jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py:L521–L525](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py#L521-L525), [jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py:L421–L425](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py#L421-L425)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":525,"path":"jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py","sha256":"7b17e6676a2d21dfb1211cc5e1e160e3c1ee6d1fe4f33202aa481b8f1546f125","start":521},{"end":425,"path":"jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py","sha256":"d7d743fc9599c56125666361435757e01b48820652f24c946da5aaf0ee06532b","start":421}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=financial-document-parser facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5a4332f87b292f750935c5d1cac9167ff5467f3b30967f44b8540c75696cfe43 -->
**pdfplumber 与 pdf2image/pytesseract 为 try/except ImportError 探测的可选依赖，缺失时 PDF 抛错、图片抛错、_ocr_pdf 静默返回**
模块导入处用 try/except ImportError 设置 HAS_PDFPLUMBER/HAS_OCR 标志。_parse_pdf 在无 pdfplumber 时抛 ImportError（提示 pip install pdfplumber）；_parse_image 在无 OCR 依赖时抛 ImportError；_ocr_pdf 在无 OCR 依赖时直接 return，不写 raw_text。OCR 语言固定为 chi_sim+eng（140–144 行的 PDF 路径与 157 行的图片路径均可见）。

来源：[jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py:L17–L29](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py#L17-L29), [jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py:L105–L108](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py#L105-L108), [jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py:L135–L158](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py#L135-L158)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":29,"path":"jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py","sha256":"488595b67cacc92aa57f41241b977ef2917748eb504aa80daa32d488355aedaa","start":17},{"end":108,"path":"jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py","sha256":"303d401186d937a6fef985d68bf56029344aca626e90de6bad75e7628d71f835","start":105},{"end":158,"path":"jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py","sha256":"59efd7f11dbe53aa4a9bc1fe7dfb87ee0fe1494d08d6c7d7346543258671f72d","start":135}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=financial-document-parser facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=850abac897a2c708d22013f4bfd4fcbb54bb9ea62f3a03998bcd6dfd6e25b6b9 -->
**缺 OCR 依赖时 _parse_image 抛 ImportError,而 _ocr_pdf 静默返回**
_parse_image 在 HAS_OCR 为 False 时抛 ImportError('需要安装 OCR 依赖: pip install pdf2image pytesseract');_ocr_pdf 在同一守卫下直接 return,不报错也不填充 raw_text。main 捕获异常后以退出码 1 终止进程。

来源：[jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py:L135–L153](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py#L135-L153), [jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py:L532–L554](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py#L532-L554)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":153,"path":"jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py","sha256":"5c08b209b363f1fb164b5c359bc47a96f6302b273903ede8a8c6a3d6e05a240f","start":135},{"end":554,"path":"jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py","sha256":"ae76230826ed15d8224dec1c365092a0a7d48e9536b6a48c13528d75bb517dd7","start":532}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=financial-document-parser facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cf7e6287a018eaa91a9e2398c93be41e20c25e335739ab0c73d1d5fb9446c617 -->
**_ocr_pdf 在 HAS_OCR 为假时静默返回：本函数不崩溃，但也跳过 OCR 文本提取**
设计推断（非作者历史意图）：

在 _ocr_pdf 内部，HAS_OCR 为假时函数直接 return，不执行 convert_from_path、raw_text 赋值或 _extract_fields_from_text；好处是缺少 OCR 依赖时本函数不抛异常，代价是本函数内对扫描内容的文本提取被静默跳过（调用方后果未在所示行中体现）。

来源：[jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py:L135–L148](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py#L135-L148)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":148,"path":"jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/financial_parser.py","sha256":"0301bcc13a9723ac83a228f3783423fe92e6e3ef75797097ea918c780af4ad6d","start":135}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=financial-document-parser facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ff9da7e34a0f2f832491f459ecad60263d21754580c31c0323b1e5c71e81afd4 -->
**SKILL.md 记录的 CLI 命令用法（文档化手工流程，未执行）**
文档中的人工验收步骤（本轮未执行）：

SKILL.md 的命令行用法小节给出可直接运行的验证操作：`python financial_parser.py invoice.pdf` 输出 Markdown 报告，`--format json` 输出 JSON，`--format csv` 导出 CSV，`--format all` 输出 Markdown+JSON；并给出 receipt.jpg 图片收据与 statement.csv 银行对账单示例。上述为文档记载的操作与预期输出，本次未执行（NOT EXECUTED）。

来源：[jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/SKILL.md:L24–L46](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/SKILL.md#L24-L46)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":46,"path":"jiuwenswarm/resources/agent/workspace/skills/financial-document-parser/SKILL.md","sha256":"19a851ce6af5a82a10ab45955e638baf23851621085578eabb54140e6505a126","start":24}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
