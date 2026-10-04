---
title: "local-doc-ocr-scripts 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# local-doc-ocr-scripts 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=249e216f576c1fe88841a6865154431c838c6ca9dd7019569961c58b57b1f061 -->
**`jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py`**

- 调用入口 `ocr_image(engine, path, do_preprocess)`。
- 调用入口 `render_pdf(pdf, out_dir, dpi, start_page, end_page)`。
- 调用入口 `collect_images(inp)`。
- 调用入口 `main()`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import sys, os, json, argparse, datetime`；`from preprocess_img import preprocess, _estimate_skew`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py#L1-L238)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/pdf_to_images.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=53b1e04cf2634f605290f626fdff141113815772e591c434bd1d91cf6c54cf16 -->
**`jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/pdf_to_images.py`**

- 调用入口 `render_one(src, out_base, dpi, start_page, end_page, do_preprocess, tiles)`。
- 调用入口 `main()`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import sys, os, argparse`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/pdf_to_images.py#L1-L129)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/preprocess_img.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6afe4ce2b4577643e45826c5fa7d8ab85b637dd29d6f9cf3019ef20afd11ad73 -->
**`jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/preprocess_img.py`**

- 调用入口 `preprocess(img, do_deskew)`。
- 调用入口 `main()`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import sys, os, argparse`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/preprocess_img.py#L1-L76)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/setup.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=63d23bb1743f51a89f03eb485528163acf1882e726d3d653ebf03b04ec3169bf -->
**`jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/setup.py`**

- 调用入口 `ensure_deps()`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import importlib.util`；`import subprocess`；`import sys`。
- 模块级配置或常量名称：`PACKAGES`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/setup.py#L1-L59)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/write_ocr_md.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0a2a262906c5f17165101784f6e407f613ba9a53eca8f2c53e24b9fa1f2b753d -->
**`jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/write_ocr_md.py`**

- 调用入口 `build_md(data)`。
- 调用入口 `main()`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import sys, os, json, argparse, datetime`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/write_ocr_md.py#L1-L76)。
<!-- /kb:file -->
