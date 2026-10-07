---
title: "本地离线 OCR 管线（RapidOCR：PDF/图片 → Markdown）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/pdf_to_images.py:L74-L92, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/pdf_to_images.py:L30-L36, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py:L129-L166, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py:L22-L29, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py:L147-L155, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/write_ocr_md.py:L22-L48, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/write_ocr_md.py:L51-L72, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/setup.py:L20-L38, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/setup.py:L41-L55, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/setup.py:L13-L18, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/SKILL.md:L135-L143]
feature: "local-doc-ocr-offline"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py", "jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/write_ocr_md.py", "jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/preprocess_img.py", "jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/pdf_to_images.py", "jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/setup.py"]
---

# 本地离线 OCR 管线（RapidOCR：PDF/图片 → Markdown）：实现深读

[功能概览](feature-local-doc-ocr-offline.md) · [owner 入口](_index.md)

<!-- kb:depth feature=local-doc-ocr-offline facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=de414d22fe038639361a0e7638038e18c92b0e67abd17a3c411108a64ecbbac8 -->
**ocr_offline.py main：解析参数 → 依赖自检 → 条件导入 RapidOCR → 构建引擎**
main() 先 argparse 解析 input/-o/-d/--no-preprocess/--start-page/--end-page/--boxes-json，调用 _ensure_deps()（返回值被忽略），随后 try 导入 rapidocr_onnxruntime.RapidOCR，导入成功则打印加载提示并构造 engine = RapidOCR()；再依据 args.out 是否为空决定默认输出名（目录输入时 out_md = <目录>/<stem>_OCR.md）。

来源：[jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py:L129–L166](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py#L129-L166)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":166,"path":"jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py","sha256":"87dcb943b731f1a67778c1eef21430f5a5a5d4d7ad3cd2f873a578398be0aa18","start":129}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=local-doc-ocr-offline facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6e8a9da615644c59f820b29d2d60c12372f7d17ffc52f469d41917d128a223af -->
**write_ocr_md.py 的 JSON 输入契约与缺省输出命名**
main() 接受 JSON 文件路径或 '-'（读 stdin），json.loads 后交给 build_md(data)。data 缺省 source 为「（未知来源）」、engine 为「多模态读图（本机模型）」、pages 为空列表；每页 label 缺省「未命名」、text 缺省空串（空文本渲染为「（本页未识别到内容）」）。未指定 -o 时按 source 同名生成 _OCR.md（stdin 时固定 ocr_OCR.md），写入后打印 DONE 行。调用方需提供可解析的 JSON。

来源：[jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/write_ocr_md.py:L22–L48](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/write_ocr_md.py#L22-L48), [jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/write_ocr_md.py:L51–L72](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/write_ocr_md.py#L51-L72)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":48,"path":"jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/write_ocr_md.py","sha256":"43907fa5f7f82ba5713f3b6fca6ad9cc0e511e769ab3f7404a102997b5dfd3d4","start":22},{"end":72,"path":"jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/write_ocr_md.py","sha256":"9585de3316f924d23e8e4f3eb1bf31292db5fa6dae89135c38e3c7fa431b4c9a","start":51}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=local-doc-ocr-offline facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e177e7752f01ff3516ef63fc173cabf67b671dab913daff5ac258a482a28b235 -->
**pdf_to_images 默认 dpi=300、tiles=0，页范围由 render_one 夹紧**
argparse 默认 `-d/--dpi` 为 300、`-t/--tiles` 为 0（不切块）、`--start-page`/`--end-page` 为 None；render_one 内 `s = max(1, start_page or 1)`、`e = min(n, end_page or n)`，未指定时覆盖第 1 页到末页，输出目录默认在 PDF 同目录建 `<文件名>_pages`。

来源：[jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/pdf_to_images.py:L74–L92](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/pdf_to_images.py#L74-L92), [jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/pdf_to_images.py:L30–L36](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/pdf_to_images.py#L30-L36)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":92,"path":"jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/pdf_to_images.py","sha256":"e8a7fc6675e6dc78f89e91f1dad5e3629769b397f99c2adc5adbdc50e7c820e8","start":74},{"end":36,"path":"jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/pdf_to_images.py","sha256":"e99ccde074d8f63563dbec4817629f29a5a6bf909bc54f1b09a82d715fd11273","start":30}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=local-doc-ocr-offline facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7babbb28d145f57a222a9c4b726f2578548e3c9924cf806ae3e5880f668a24c0 -->
**依赖自检异常仅告警返回 False；rapidocr 导入失败才 sys.exit(1)**
ocr_offline._ensure_deps 捕获任何异常后 stderr 写 [warn] 并返回 False；main() L148 调用时不接收返回值，真正的退出分支是 L150-155 的 ImportError：打印 ERROR 与 pip install -r requirements.txt 提示并 sys.exit(1)。

来源：[jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py:L22–L29](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py#L22-L29), [jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py:L147–L155](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py#L147-L155)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":29,"path":"jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py","sha256":"ac99ae64ef278d941be2dc64991695c3d78d79f1daf6cadc2c0a342d9e406d5b","start":22},{"end":155,"path":"jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py","sha256":"adccb2112b56eb516f5da3eba1739992141f9f42acea34e874806e3a7a8c425b","start":147}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=local-doc-ocr-offline facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1e769a41978c0793792f5bf6eb2d534ee1cfe7a760a49d6841d17389afa3826f -->
**清华镜像优先、CalledProcessError 后无 -i 重试的安装顺序**
设计推断（非作者历史意图）：

_install_one 按 _MIRRORS 顺序尝试：先带 `-i https://pypi.tuna.tsinghua.edu.cn/simple`，仅当 subprocess.run(check=True) 抛 CalledProcessError 时换下一个源；第二个源命令不带 -i，实际来源由本机 pip 配置决定，代码不保证官方 PyPI。每次命令固定 `--retries 5 --timeout 60`。收益（推断）：国内镜像通常更快；代价：首个源非退出码失败（如网络异常抛其他异常）不触发兜底，直接传播。

来源：[jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/setup.py:L20–L38](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/setup.py#L20-L38)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":38,"path":"jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/setup.py","sha256":"72aecb2b0cc83b8bab7a8b4a22e9a93f2c86cf5bda6004062455bc5e08bbb7ff","start":20}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=local-doc-ocr-offline facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=da4c5e4c7742b2995f374d4e6aa60e579385e9c9402ba5170dbcda061b358e0a -->
**ensure_deps 白名单依赖检测与 all() 短路自动安装**
ocr_offline 的 main 调 _ensure_deps() 但忽略其返回值，随后自行尝试 from rapidocr_onnxruntime import RapidOCR，ImportError 时打印安装提示并以 sys.exit(1) 退出（ocr_offline.py:L147–L155）。_ensure_deps 导入 setup 并返回 setup.ensure_deps()，任何异常仅写 stderr 告警并返回 False（L22–L29）。ensure_deps 用 importlib.util.find_spec 按 PACKAGES（rapidocr_onnxruntime/pymupdf/pillow/numpy）检测缺失；L50 的 all(_install_one(pkg) for pkg in missing) 因生成器短路，某个包安装返回假值后其余缺失包不再尝试安装，此时仅打印手动 pip install 提示并返回 False（setup.py:L41–L55、L13–L18）。

来源：[jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py:L147–L155](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py#L147-L155), [jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py:L22–L29](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py#L22-L29), [jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/setup.py:L41–L55](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/setup.py#L41-L55), [jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/setup.py:L13–L18](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/setup.py#L13-L18)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":155,"path":"jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py","sha256":"adccb2112b56eb516f5da3eba1739992141f9f42acea34e874806e3a7a8c425b","start":147},{"end":29,"path":"jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/ocr_offline.py","sha256":"ac99ae64ef278d941be2dc64991695c3d78d79f1daf6cadc2c0a342d9e406d5b","start":22},{"end":55,"path":"jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/setup.py","sha256":"b91f1a7d8bfdd4414084859240654e83acae8976fdafd2031f3135c942d0a09a","start":41},{"end":18,"path":"jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/scripts/setup.py","sha256":"c7b0f5b596498a465094e0946a528568866952e16075aa8c779c2855b6a4d344","start":13}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=local-doc-ocr-offline facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f7a50bb17063cf4cb2cbe07a21602143992e108fe82c5916ccb9aef91a3045ba -->
**SKILL.md 记录的两条手动验证命令（未执行）**
文档中的人工验收步骤（本轮未执行）：

SKILL.md「快速验证」给出两条手动命令及预期结果：路线 A 运行 python scripts/ocr_offline.py "测试.pdf" 直接产出 Markdown；路线 B 运行 python scripts/pdf_to_images.py "测试.pdf" -o "./pages" 先渲染，再由多模态 Agent 读取 ./pages/page_01.png 验证。这是文档记载的手动流程，本次未执行；所供证据中未展示针对该功能的自动化断言。

来源：[jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/SKILL.md:L135–L143](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/SKILL.md#L135-L143)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":143,"path":"jiuwenswarm/resources/agent/workspace/skills/local-doc-ocr/SKILL.md","sha256":"2cbcd8fe46d12a231bb6e2c8c87aaa20c62e61436a8e56f44c5a5c7f1a2317f9","start":135}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
