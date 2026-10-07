---
title: "arXiv 论文 Figure/Table 检测与高清导出（extract_arxiv_visuals）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py:L1410-L1465, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py:L200-L246, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py:L55-L56, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py:L96-L112, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py:L1370-L1370, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py:L1298-L1299, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py:L1224-L1232, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py:L1330-L1333, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py:L891-L901, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py:L1259-L1266]
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

<!-- kb:depth feature=arxiv-visual-extraction facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e9ded6399d97c3ab7322f1ffc8e71e2a9ffe0bf241938dc719842b7d7197c648 -->
**--dpi defaults to DEFAULT_DPI; pages/ rendering only runs when options.keep_pages is true**
L1370 将 --dpi 的 argparse 默认值设为 DEFAULT_DPI。L1298–L1299 显示 render_all_pages(doc, output/"pages", dpi) 仅在 options.keep_pages 为真时执行；未展示禁用时是否创建 pages/ 目录。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py:L1370–L1370](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py#L1370-L1370), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py:L1298–L1299](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py#L1298-L1299)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1370,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py","sha256":"fa2014ee57c73cc0191d354d5ee5a9bdb884070203c9c77e9292de6e330a8bdf","start":1370},{"end":1299,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py","sha256":"2eab7252380118768ad755004423b068e96d3815c179ca2c37335bd2dcb0504e","start":1298}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=arxiv-visual-extraction facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=03da57cf6e2c8d2e2c023f619a237b2bc97aa761bad0f354b7aa4cd37256ce96 -->
**Out-of-range page_index candidates are recorded as failures and skipped; failures are included in manifest**
候选的 page_index 不满足 0 <= page_index < doc.page_count 时，向 failures 追加含 asdict(candidate) 与 error "page_index out of range" 的条目并 continue；manifest 的 "failures" 字段输出这些条目。另外 load_pdffigures_json 在路径缺失时抛 FileNotFoundError，顶层格式不符时抛 ValueError。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py:L1224–L1232](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py#L1224-L1232), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py:L1330–L1333](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py#L1330-L1333), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py:L891–L901](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py#L891-L901)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1232,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py","sha256":"ad2328babd117bdb70c86e03e93f35fe0fc89b157987ae00e7f2c552305a91f8","start":1224},{"end":1333,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py","sha256":"38c3c785083b60ee03a1f0749d965e66cb0f4b57150535cb7ecc6cdd8c3c2e94","start":1330},{"end":901,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py","sha256":"78cf1683088164ddfaa26f8afe7841703a9b483f34428ad612c59de06776dedc","start":891}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=arxiv-visual-extraction facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0255169e76abdd76b0e4ce590ac4593d2cdd241cb769c9694536238ffcc061d7 -->
**Caption render fallback via copy2 may duplicate image content; copy failure is uncaught here**
设计推断（非作者历史意图）：

For each candidate the script unions region and caption bboxes and tries render_region; if that raises, or union_rect returns None, it calls shutil.copy2(image_path, caption_path). Benefit (inference): a caption file is still attempted when rendering fails; cost: when copy succeeds the caption file duplicates the plain image instead of including the caption, and copy2 itself is not wrapped in try here so its failure propagates.

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py:L1259–L1266](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py#L1259-L1266)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1266,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/extract_arxiv_visuals_v2_2.py","sha256":"bfe79d39d9a2d50d2b144dda8e11cbc905ff68e259efcba2cb91a7e5b7888c2b","start":1259}],"trace":[]} -->
<!-- /kb:depth -->
