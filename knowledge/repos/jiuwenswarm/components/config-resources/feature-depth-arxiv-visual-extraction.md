---
title: "arXiv 论文 Figure/Table 检测与高清导出（extract_arxiv_visuals）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py:L1410-L1465, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py:L200-L246, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py:L55-L56, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py:L96-L112]
feature: "arxiv-visual-extraction"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py"]
---

# arXiv 论文 Figure/Table 检测与高清导出（extract_arxiv_visuals）：实现深读

[功能概览](feature-arxiv-visual-extraction.md) · [owner 入口](_index.md)

<!-- kb:depth feature=arxiv-visual-extraction facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c8c32d4f54fb849c6b233f23c36e5b8677b21fb7c1d59ec9928758e37f8f4ec4 -->
**main()：解析参数→解析输入→获取 PDF→签名校验→extract_visuals→输出摘要并返回 0**
main() 先校验参数，resolve_input 解析输入，本地 PDF 走 copy_local_pdf，否则 download_pdf；再读前 5 字节校验 %PDF- 后调用 extract_visuals，emit 结果计数与 manifest 路径，本地返回 0。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py:L1410–L1465](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py#L1410-L1465)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1465,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py","sha256":"c1afa3e699ad797f229c72d80fd7beabe21b6b066e67393c476d7da2cedde4c3","start":1410}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=arxiv-visual-extraction facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1ac6c7a21e37a7410a31b4858e7e1d85b7663661c0f806fc37ef396a34a478d1 -->
**resolve_input：接受 arXiv ID/链接、HTTP(S) PDF 链接或本地 PDF 路径，否则 ValueError**
调用方传入原始字符串：本地文件后缀非 .pdf 抛 ValueError「本地文件不是 PDF」；命中 arXiv ID/URL 正则得到 pdf_url=https://arxiv.org/pdf/{id}；其它 http(s) 链接按文件名生成 paper_id；都不匹配抛 ValueError 列出四种合法输入。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py:L200–L246](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py#L200-L246)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":246,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py","sha256":"b4a8f783a258bb3ea81263fd1e0608b9db1b9107140954ee46956a9af589ff47","start":200}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=arxiv-visual-extraction facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=30eed90eeb8f2377e5893f82d07ad5b8343574d2d71f6087483cc150c3fd8752 -->
**ensure_dependencies：import 探测 DEPENDENCIES，缺失且禁用自动安装时抛 RuntimeError**
对 DEPENDENCIES 表逐个 importlib.import_module，ImportError 记入 missing；auto_install=False 时拼出 pip install 命令并以 RuntimeError 抛出（含 sys.executable），由调用方决定安装。PIL 固定规格为 Pillow>=10,<13。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py:L55–L56](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py#L55-L56), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py:L96–L112](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py#L96-L112)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":56,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py","sha256":"a8f21b52eff2dc2499d03ff15b3f5288297f1e4963f2d5522f46f303213f95a3","start":55},{"end":112,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py","sha256":"8484412988b7675a1bd208b5c9844d1f2ac945dd40cbe1737be8dbd361d07080","start":96}],"trace":[]} -->
<!-- /kb:depth -->
