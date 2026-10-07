---
title: "Deck Thumbnail Contact-Sheet Renderer：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L52-L55, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L109-L111, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L126-L127, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L58-L63, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L71-L78, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L114-L116, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L135-L140, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L22-L37, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L106-L112, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L135-L144, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L58-L78, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L89-L103, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L40-L45]
feature: "ppt-opc-thumbnail"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py"]
---

# Deck Thumbnail Contact-Sheet Renderer：实现深读

[功能概览](feature-ppt-opc-thumbnail.md) · [owner 入口](_index.md)

<!-- kb:depth feature=ppt-opc-thumbnail facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1edf5ab9002b0dadb5017494b1a33124d653f605b4217c13d1506f15ddf257fc -->
**CLI: positional deck, optional prefix (default "thumbnails"), --cols default 3; helpers raise ThumbnailError, main converts it to SystemExit**
argparse 定义 deck（必填）、prefix（默认 thumbnails）、--cols（默认 3）。程序输出经 _OUT logger（%(message)s 格式、propagate=False、stdout handler）走 stdout，诊断经 LOGGER 走 stderr；main 捕获 ThumbnailError 转为 SystemExit(str(exc))，__main__ 下 sys.exit(main())。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L22–L37](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py#L22-L37), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L106–L112](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py#L106-L112), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L135–L144](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py#L135-L144)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":37,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py","sha256":"68b1f344d8ac818a300b429b63bdb3d8e7cbdd1abaf2184155a256f6322836d5","start":22},{"end":112,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py","sha256":"de29889f072f89da8d0a7dd77c4161a09703ff434e2655e9cb2e7bcb89bfdca4","start":106},{"end":144,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py","sha256":"47b15972807c8bbf6fd51a5ae8356d245261be758991908624e28b47b2fa718b","start":135}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-opc-thumbnail facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=50ac166d7b9002beed2f02568d98e552ef8c5477092de060b78e5801a25a1c77 -->
**常量与 CLI 默认：prefix=thumbnails、cols=3、CELL_W=480、MAX_PER_SHEET=24**
输出前缀默认 “thumbnails”、列数默认 3；CELL_W=480px、LABEL_H=22、PAD=8 为模块常量；页数超过 MAX_PER_SHEET=24 时文件名追加 “-N” 后缀分片。运行时 soffice 转换 timeout=300 秒。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L52–L55](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py#L52-L55), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L109–L111](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py#L109-L111), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L126–L127](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py#L126-L127)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":55,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py","sha256":"bdd47db0c04de107c799c5ee795fdcc543a688d5426611e53372a94348525226","start":52},{"end":111,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py","sha256":"439d3ea0c0a9367cce8440b5e6dffd61105ec61a551bdcebc0a29dd9cfbf7375","start":109},{"end":127,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py","sha256":"0ff47a046c03d32e5c6176527461ae9212296a412e9f8f2e7b1c6c379ce647e5","start":126}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-opc-thumbnail facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=694b899913ff62c4fda1058f05f12d99c1385519236f6e98a486a91a54755015 -->
**soffice subprocess, delayed fitz import, and PIL (Image/ImageDraw) composition**
render_pages 以 find_soffice() 返回的可执行文件运行 `--headless --convert-to pdf`（check=True, capture_output, timeout=300 的 subprocess 参数），随后延迟 import fitz 并用 fitz + PIL Image 栅格化；build_sheet 用 Image.new/ImageDraw 拼网格。缺 soffice 或 PyMuPDF 分别抛出指明安装方式的 ThumbnailError。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L58–L78](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py#L58-L78), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L89–L103](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py#L89-L103)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":78,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py","sha256":"f3898d2a296992556ab8f8fe4141dc5776a016d33ff9679ce3ff5159ffc8081e","start":58},{"end":103,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py","sha256":"44deaeb6b4d7943912c8d72d19ce7c4ac173d1c32682e3249d29cc95a397bcec","start":89}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-opc-thumbnail facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=473d218bd28be2018b340939aed9e5cb7d3188c85f138a712734a8d962ccb370 -->
**ThumbnailError 路径：soffice 缺失、无 PDF、缺 PyMuPDF、deck 不存在**
find_soffice 找不到 soffice 或 mac 路径时抛 ThumbnailError；LibreOffice 未产出 PDF 文件、fitz ImportError、deck 非文件均抛 ThumbnailError；main() 将其转为 SystemExit(错误消息)，使 helper 保持可库用。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L58–L63](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py#L58-L63), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L71–L78](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py#L71-L78), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L114–L116](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py#L114-L116), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L135–L140](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py#L135-L140)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":63,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py","sha256":"ae8b8227c52e0354e5d236e270555778f37ae53a3257d83ed49727b6bbf45350","start":58},{"end":78,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py","sha256":"dcd4c2a0751f002762418a4ac19080a9c2b678d85c9f1feca5f645d200ff69de","start":71},{"end":116,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py","sha256":"ca8078db34e5b380b2dc05d53322701121b04912efcb01995837c5797990b8c0","start":114},{"end":140,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py","sha256":"6f15028eb641365326f47001592bf2f9f1e791290166d8f646ece8f7b7ef9c22","start":135}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-opc-thumbnail facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=35e5e4a3f08af0aa6a126159a3691b18d5fa85334e7714a4242d9d7c12df0739 -->
**Bundling rendering into helpers with ThumbnailError keeps library usability (inference), at the cost of external soffice/PyMuPDF requirements**
设计推断（非作者历史意图）：

收益（推断）：按 docstring L41–L45，helpers 抛 ThumbnailError 而非 SystemExit，使其可作为库复用。成本：必须找到 soffice 且 fitz 可导入，否则以 ThumbnailError 失败；L70 的 timeout=300 是传给 subprocess.run 的设置参数，本片证据不构成对实际耗时的硬性保证。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L40–L45](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py#L40-L45), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py:L58–L78](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py#L58-L78)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":45,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py","sha256":"5e435276235539457145807e968c49173197021459de3449cedf627710bd626d","start":40},{"end":78,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/thumbnail.py","sha256":"f3898d2a296992556ab8f8fe4141dc5776a016d33ff9679ce3ff5159ffc8081e","start":58}],"trace":[]} -->
<!-- /kb:depth -->
