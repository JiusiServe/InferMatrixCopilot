---
title: "XLSX 技能环境自检（doctor.py）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L104-L134, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L8-L11, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L105-L107, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L118-L130, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L133-L134, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L50-L61, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L64-L71, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L74-L93, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L56-L61, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L86-L101, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L115-L116, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L34-L37, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L86-L96]
feature: "xlsx-doctor-selfcheck"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py"]
---

# XLSX 技能环境自检（doctor.py）：实现深读

[功能概览](feature-xlsx-doctor-selfcheck.md) · [owner 入口](_index.md)

<!-- kb:depth feature=xlsx-doctor-selfcheck facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ec60a5e7237696d3662c383522dc5a8eafb0d6bbb7a38817b000cdcd7a37aa5e -->
**main 顺序执行四类检查并按 required 失败决定返回值**
main() 依次调用 check_python/check_py_deps/check_cli/check_cjk_font 填充 results；若没有任何 required 且 not ok 的项则局部返回 0，否则返回 1，由 __main__ 的 sys.exit 传出。

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L104–L134](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py#L104-L134)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":134,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py","sha256":"fbc323cb810172afc2588c2dea81adcf9e75a1dd8967bec2ee428f65d9802feb","start":104}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-doctor-selfcheck facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fd6bdf9eb29cedbb39daceaf61f72c23b778ce87bd85a33f871edc41f38d2ee0 -->
**doctor.py 命令行入口：--json 为唯一显式新增选项，输出两种格式并由 main 返回 0/1**
用法为 python3 doctor.py [--json]（L8–L11；argparse 默认还会提供 -h/--help）。默认打印人类可读的 PASS/FAIL/warn 报告；--json 时打印 {"ok":…,"results":[…]} 的 JSON（L118–L119）。main 在无必需项失败时返回 0，否则返回 1（L130），由 L133–L134 的 sys.exit 传出。

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L8–L11](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py#L8-L11), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L105–L107](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py#L105-L107), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L118–L130](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py#L118-L130), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L133–L134](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py#L133-L134)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":11,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py","sha256":"3e1e3adb670f2e7d5e2f0ddc492778938ae66137b5f1dd0a98f8ceb37dfa9b45","start":8},{"end":107,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py","sha256":"5a3beb81f587b2a6dac6b7acee91fd1f12ebb5a27c76165900f17a84ec724508","start":105},{"end":130,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py","sha256":"2c4e2d189742548100b914c3d080f8150b10d6cd9d4a75c1da8057d8bd6b939b","start":118},{"end":134,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py","sha256":"c86a687dc0735836998a4f2d1ad0536d34c088d503731b70989149cd3c97105a","start":133}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-doctor-selfcheck facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bd72aa27f91b686033c00f394c8184ad550467b5342413479b48aa4361523f5f -->
**依赖检测：Python 模块用 importlib 探测，CLI 工具用 shutil.which，字体依赖 fc-list**
check_py_deps 通过 importlib.import_module 逐个导入并读取 __version__（L51–L55）；check_cli 用 shutil.which 查找可执行文件（L64–L71）；check_cjk_font 在 fc-list 存在时调用 "fc-list :lang=zh family"（超时 20 秒）获取字体族（L77–L83）。若该调用抛出 Exception，会继续走 L86–L93 的回退扫描，因此单次 fc-list 失败不一定导致字体检查失败。

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L50–L61](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py#L50-L61), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L64–L71](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py#L64-L71), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L74–L93](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py#L74-L93)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":61,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py","sha256":"d8f1709e8ec43971ea184a00ca10ea834a8b6c9ba6520300ab3c0166bd857bd8","start":50},{"end":71,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py","sha256":"9506b9bfcc80e0aceb7c0314403bb9cdefa95ea2f43ed42caba51992156efa46","start":64},{"end":93,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py","sha256":"00b0eb2427d0d565cb08c914316e50afd938c28b41a556e9c701fe0f04483430","start":74}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-doctor-selfcheck facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=102cc46aa1b8644f6da552aa07ab15612bc1f77daf17101ac952f751269256e6 -->
**失败路径：模块导入抛 Exception 记录 pip 安装提示；字体未找到时记录诊断并计为必需失败**
导入失败时 except Exception 捕获，detail 写入 "missing (…); install: pip install <包名>"（L56–L61）。字体检查在 zh 查询无结果或抛异常且 fc-list 可用时，回退到全字体列表中按 CJK_FONT_HINTS 子串匹配（L86–L93）；仍无结果则 ok=False、required=True，detail 提示安装 google-noto-sans-cjk-fonts 并警告中文将渲染为方框（L94–L101）。任一 required 项 ok=False 使 main 返回 1（L115–L116、L130）。

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L56–L61](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py#L56-L61), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L86–L101](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py#L86-L101), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L115–L116](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py#L115-L116)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":61,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py","sha256":"8d4ff1bec1a2c45953d323233787e4f1f7293f60ef08758638751911d611e9f0","start":56},{"end":101,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py","sha256":"09a6d515a28dbac9352eea78d12bdc1229c3d84651336a0f5c2072233a31ef0b","start":86},{"end":116,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py","sha256":"08780b16e475ca0eb78dd43bfafee246a04468585ecc40ad82098357ec75383d","start":115}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xlsx-doctor-selfcheck facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=93ca7b33331054b6cdaee3d7361019f92950b4aa5177ea3a69bbeeb10dfadafd -->
**取舍：字体回退扫描用名称子串匹配，换取无 zh 元数据时的可用性，但不验证字形覆盖**
设计推断（非作者历史意图）：

推断：当 fc-list :lang=zh 无结果时，回退仅检查全字体列表是否包含 CJK_FONT_HINTS 中的名称子串（L88–L91），只要字体名命中即可通过（L94–L96）。好处是缺少语言元数据的系统仍能检出 CJK 字体；代价是该路径不确认字体实际覆盖中文字形。

来源：[jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L34–L37](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py#L34-L37), [jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py:L86–L96](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py#L86-L96)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":37,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py","sha256":"8de18d97e624ead5ef63e0d4e6a2a158be16fbeb50593b3a5ab6ae45a1f20d1e","start":34},{"end":96,"path":"jiuwenswarm/resources/agent/workspace/skills/xlsx/scripts/doctor.py","sha256":"2e5714bfbd25dfb32422b1e2bc20e56d114ee3a43cbacb57c4cda4babf336587","start":86}],"trace":[]} -->
<!-- /kb:depth -->
