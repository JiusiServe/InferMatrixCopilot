---
title: "local-doc-ocr：本地离线 OCR 管线（RapidOCR：PDF/图片 → Markdown）"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py:L129-L158, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/write_ocr_md.py:L4-L17, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/setup.py:L41-L55, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py:L112-L123, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py:L175-L189, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py:L231-L234, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/pdf_to_images.py:L100-L108, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/write_ocr_md.py:L46-L47, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py:L93-L109, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py:L169-L189, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py:L22-L32]
feature: "local-doc-ocr-offline"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py", "jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/write_ocr_md.py", "jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/preprocess_img.py", "jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/pdf_to_images.py", "jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/setup.py"]
---

# local-doc-ocr：本地离线 OCR 管线（RapidOCR：PDF/图片 → Markdown）

<!-- kb:knowledge owner=feature-local-doc-ocr-offline facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**脚本入口与输入输出契约**

`ocr_offline.py` 是主 CLI：`python ocr_offline.py <PDF|图片|图片目录>`，输出 `<同名>_OCR.md`，可选 `--boxes-json` 导出 `_OCR_boxes.json`。辅助入口为 `pdf_to_images.py`（PDF→PNG，支持 `-b` 批量与 `--tiles` 分块）、`preprocess_img.py`（单图预处理）、`write_ocr_md.py`（把 `{source, engine, pages:[{label,text}]}` JSON 汇总为 md，支持 stdin `-`）。ocr_offline.py 通过 `from preprocess_img import preprocess` 复用预处理模块（ocr_offline.py:L32、pdf_to_images.py:L28）；PDF 渲染逻辑在 ocr_offline.py 内部用 fitz 实现（L93–L109），而非调用 pdf_to_images.py。"全本地" 以依赖已装齐为前提：首次运行若缺依赖会联网自动安装（仅白名单），装好后不再联网。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py:L129–L158](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py#L129-L158), [jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/write_ocr_md.py:L4–L17](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/write_ocr_md.py#L4-L17), [jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/setup.py:L41–L55](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/setup.py#L41-L55)

<!-- kb:knowledge owner=feature-local-doc-ocr-offline facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**支持的行为与边界**

支持 PDF（按页渲染为 PNG）、单张图片及图片目录（按扩展名 png/jpg/jpeg/bmp/tif/tiff/webp 过滤，目录内按名排序）。输出 Markdown 按页/图分节：PDF 分支标题用「第 N 页」（ocr_offline.py:L180），图片分支用去扩展名的文件名（L185–L189）；结尾 stdout 会列出各页的原始 src 路径，供多模态 Agent 对 PDF 中间 PNG 做手写/表格增强（L231–L234）。识别为空的页写入排查建议而非空白（L206–L213）。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py:L112–L123](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py#L112-L123), [jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py:L175–L189](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py#L175-L189), [jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py:L231–L234](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py#L231-L234)

<!-- kb:knowledge owner=feature-local-doc-ocr-offline facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**验证途径**

所示五个脚本均无自动化测试入口；体现的验证手段是运行时自检与防御性输出：`setup.py` 的 `ensure_deps` 用 `importlib.util.find_spec` 逐项检测缺失依赖并打印安装结果（可独立运行，退出码 0/1）；`ocr_offline.py` 对不支持的输入类型、空输入目录以 `sys.exit(1)` 报错退出，`pdf_to_images.py` 对 `-b` 非目录、目录无 PDF、文件不存在同样退出；每页识别为空时在 Markdown 里写入排查建议（提高 DPI、关预处理、走多模态复核等），两个落盘脚本都在输出尾部强制写入人工核对警告。所述脚本之外的测试情况无法从本次提供的证据判断。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/setup.py:L41–L55](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/setup.py#L41-L55), [jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py:L112–L123](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py#L112-L123), [jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/pdf_to_images.py:L100–L108](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/pdf_to_images.py#L100-L108), [jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/write_ocr_md.py:L46–L47](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/write_ocr_md.py#L46-L47)

<!-- kb:knowledge owner=feature-local-doc-ocr-offline facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**管线结构与控制流**

ocr_offline.py 是主入口：collect_images 把输入分类为 PDF、单图/图片目录，PDF 分支先用 fitz 把各页渲染为 `<文件名>_pages/page_NN.png`，再逐页送 RapidOCR；图片分支直接逐图 OCR。每页结果经 _sort_boxes 做阅读顺序重排（按 y 聚类成行、行内按 x 排序），最后统一拼装为按页分节的 Markdown 落盘。依赖自检委托给同目录 setup.py 的 ensure_deps：它用 importlib.util.find_spec 对照 PACKAGES 白名单逐项检测缺失并自动 pip 安装；ocr_offline.py 只在 try/except 里调用它，若 setup 模块本身不可用则打警告跳过自检继续运行。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py:L93–L109](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py#L93-L109), [jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py:L169–L189](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py#L169-L189), [jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/setup.py:L41–L55](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/setup.py#L41-L55), [jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py:L22–L32](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py#L22-L32)

