---
title: "解包 PPTX 幻灯片添加工具（opc/add_slide.py）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L167-L186, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L20-L48, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L108-L122, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L177-L182, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L133-L163, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L7-L9, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L104-L130, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L167-L173, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L13-L18, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L167-L171, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L84-L90, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L104-L112, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L154-L156]
feature: "opc-add-slide"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py"]
---

# 解包 PPTX 幻灯片添加工具（opc/add_slide.py）：实现深读

[功能概览](feature-opc-add-slide.md) · [owner 入口](_index.md)

<!-- kb:depth feature=opc-add-slide facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e19f9918af0c7366c9cf6d556c90e52e44e486950e4917992d906eb5f3bab37e -->
**layout 分支：写入空幻灯片与 .rels 后登记 content type 并挂入 presentation.xml**
source 以 slideLayout 开头且该 layout 文件存在时，写入 EMPTY_SLIDE 到 ppt/slides/slideN.xml、写 .rels 指向 ../slideLayouts/{source}，再调 _register_content_type 与 _register_in_presentation，返回两行摘要由 emit 输出到 stdout。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L104–L130](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py#L104-L130), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L167–L173](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py#L167-L173)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":130,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py","sha256":"27ba6553d982f245e674e4fb0c8c738e72f55f77590ffde673ee72d91833e2da","start":104},{"end":173,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py","sha256":"efe0235462980f7fd41c197a38a39f544d8110a695943daf21f538a699cdfd16","start":167}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=opc-add-slide facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d63884fcfaedfae8fe24465f7f89c770b042b47a2fe4b650771d1c48bfa73d6d -->
**CLI 契约：位置参数 unpacked 与 source；结果经 emit 写 stdout**
命令行需两个位置参数：unpacked 目录与 source（slideN.xml 复制或 slideLayoutN.xml 起新页）。add_slide 返回摘要字符串，emit 经 propagate=False 的 add_slide.out logger 以裸 %(message)s 格式写 stdout，诊断走 stderr 的另一 logger。main() 捕获 AddSlideError 转为 SystemExit；main 返回值仅在 __main__ 下交给 sys.exit。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L167–L186](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py#L167-L186), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L20–L48](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py#L20-L48)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":186,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py","sha256":"4e346cc4181c80b9e50c53a4990ed710a1a9ef771061494d712a48739cee577c","start":167},{"end":48,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py","sha256":"59c603c012b12df6283c062173ad2dd817d4afc8c28ec09d42cc870055b1fffe","start":20}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=opc-add-slide facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b8f011b9db844fb54d720c8960660758c0645ccd1e526d7486f4da9d9a30b310 -->
**仅用标准库、以纯文本替换修改解包 OPC 目录中的 XML**
仅导入 logging/argparse/re/shutil/sys/pathlib，无第三方依赖；对 [Content_Types].xml、presentation.xml.rels 和 presentation.xml 做 str.replace/re.sub 文本改写，若目标标记（如 </Types>、</Relationships>）不存在则替换不生效且不报错。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L13–L18](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py#L13-L18), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L133–L163](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py#L133-L163)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":18,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py","sha256":"494c23663fbf8db0496fbbc9868b26825e7a1eee8133246738528bb62281e665","start":13},{"end":163,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py","sha256":"05935dff056dd903f6fc578a387ba0f5a7fe8568038b5bfa1a6cf8a6239f7b02","start":133}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=opc-add-slide facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=26d65428d6b40414bf675ec2f90d960b55c4f38086c3e481c2e5827d43e9d6ae -->
**AddSlideError：源布局或源幻灯片缺失时抛出，main 转为 SystemExit(消息)**
source 以 slideLayout 开头且 layouts/source 不是文件时抛 AddSlideError("add_slide: no such layout: …")；否则 slides/source 不是文件时抛 "no such slide"。main() 捕获并 raise SystemExit(str(exc))，其余异常不在此处理。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L108–L122](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py#L108-L122), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L177–L182](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py#L177-L182)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":122,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py","sha256":"610885e874247a9cf58e7b138084cf333e03f2523b0ff5abef4223a1f13b68ec","start":108},{"end":182,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py","sha256":"124ef481a4f5726ee683eec21377e73c1d598eeadfc57d1c934ebae0ff7949ea","start":177}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=opc-add-slide facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=50b9e23189f25c7bd7ba782b6af29e084de67900acb8cb9cfe83ad5458febfce -->
**文本替换改包结构：零依赖、可独立运行的代价是对标记字面量敏感**
设计推断（非作者历史意图）：

（推断）收益：只用标准库字符串替换即可同时改部件、.rels、[Content_Types].xml 和 presentation.xml 的 sldIdLst（注释称四处任错即被 PowerPoint 判为损坏）；成本：若目标文件缺少被替换的字面闭合/包裹标记（如无 '</p:sldIdLst>' 且无 sldMasterIdLst 块），replace/re.sub 静默不生效，登记缺失而脚本仍返回成功摘要。sldId 取 max(used,255)+1 且下限 256 以满足编号空间要求。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L133–L163](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py#L133-L163), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L7–L9](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py#L7-L9)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":163,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py","sha256":"05935dff056dd903f6fc578a387ba0f5a7fe8568038b5bfa1a6cf8a6239f7b02","start":133},{"end":9,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py","sha256":"44850908ade9f0caa24ba8825d1b63ade9dcb7d4e437396d8437fb41612079ec","start":7}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=opc-add-slide facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=89de63a24a54e2c8b5ccec9d28f8b617515c7158bb263107d7d286f07ead40df -->
**仅两个位置参数、无自定义选项的 CLI，编号取自解包目录现状**
_run() 用 argparse 只定义位置参数 unpacked 与 source；所示片段无配置文件或环境变量读取，也未禁用 argparse 默认帮助项。幻灯片号取目录中已有 slideN.xml 的最大值加一（无则 1），sldId 取已有值最大值加一且下限 256；source 以 slideLayout 开头时要求该 layout 文件存在，否则抛 AddSlideError。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L167–L171](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py#L167-L171), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L84–L90](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py#L84-L90), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L104–L112](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py#L104-L112), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py:L154–L156](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py#L154-L156)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":171,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py","sha256":"da3c58aa1f256821030e013de840f399c4ce4135d4a2e2d9177a166ef6a041e4","start":167},{"end":90,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py","sha256":"2ca710307dc1c0bbd8aeb0321d931592f2163074b6d90af344c813bde2d17870","start":84},{"end":112,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py","sha256":"5516d15142fa25c7dfc8ae776001c0e51f6bfa84ac3c5ce8465e3293887b10e2","start":104},{"end":156,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/add_slide.py","sha256":"ed323395def74c63689885a1984528f53aa02a9ab065c7fa9328f4fc340aa008","start":154}],"trace":[]} -->
<!-- /kb:depth -->
