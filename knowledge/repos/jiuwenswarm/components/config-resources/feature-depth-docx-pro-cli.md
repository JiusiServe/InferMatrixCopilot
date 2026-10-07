---
title: "docx-pro Word 文档操作 CLI：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py:L404-L421, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_replace.py:L212-L236, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/setup_check.py:L9-L26, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py:L31-L31, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py:L174-L179, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py:L414-L421, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py:L424-L425]
feature: "docx-pro-cli"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py", "jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/setup_check.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py", "jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/setup_check.py", "jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_replace.py", "jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/renderer.py", "jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/md_export.py"]
---

# docx-pro Word 文档操作 CLI：实现深读

[功能概览](feature-docx-pro-cli.md) · [owner 入口](_index.md)

<!-- kb:depth feature=docx-pro-cli facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c1080cda570a0e6a8024598d70069f41b746b9c94ec70423937b54dfde633102 -->
**main 解析参数并按存在性检查后分发到 args.func 的局部返回**
main 先对 json/md/docx/map 中非空且非 "-" 的路径做存在性检查（缺失则记录并返回 2），否则返回 args.func(args)；分发函数抛 FileNotFoundError/ValueError 时同样记录并返回 2。

来源：[jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py:L404–L421](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py#L404-L421)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":421,"path":"jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py","sha256":"b3b576baef96b2810255fffdc6bb8724b7cd4274e631f8337442f44aa94d3045","start":404}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=docx-pro-cli facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3051f72cb997541fa8ddd9d1f7a4b6a143658baa33d550f731d502bc54df3fa7 -->
**replace_in_docx 的 options 默认值：scope=all、case_sensitive=True、verify=True**
options.get 取默认 scope="all"、case_sensitive=True、dry_run=False、verify=True；scope="body" 时 _target_parts 只保留 REPLACE_BODY_PARTS 内的部件，否则按白名单加 .xml 前缀扩展。

来源：[jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_replace.py:L212–L236](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_replace.py#L212-L236)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":236,"path":"jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_replace.py","sha256":"d58470a428c4b8fb8273f6568ca9f086d10e10d2eeb61f2c5381694b685f9652","start":212}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=docx-pro-cli facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ed773b1e00e9cb74fbbc25ab8854138575f77f3a0ce63a4b407267dc6df7f66a -->
**docx-pro 脚本依赖 python-docx 并提供 setup_check 自检**
设计推断（非作者历史意图）：

setup_check.check 尝试 import docx 与 docx.shared，ImportError/异常时返回 False；docx_pro.py 将脚本目录加入 sys.path（推断：便于导入同目录模块）。

来源：[jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/setup_check.py:L9–L26](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/setup_check.py#L9-L26), [jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py:L31–L31](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py#L31-L31)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":26,"path":"jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/setup_check.py","sha256":"a8786044127ec0f66a85c6d43a118502407678141cf074af28d80f72e452836a","start":9},{"end":31,"path":"jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py","sha256":"dd9a75b6458672f02edb541a314c2e9b50ed2b0dd79d72edcd8161a59be8ce20","start":31}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=docx-pro-cli facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=00503c2a2dbc7b3255d0f879e7147450ed066c7a24915ed717d981d5a6ad4036 -->
**cmd_replace 对同路径覆盖返回 2，main 捕获两类异常返回 2**
输出文件绝对路径等于输入时报 "输出文件不得覆盖输入文件" 并返回 2；main 捕获 FileNotFoundError/ValueError 记录 "[错误]" 后返回 2。返回值是局部返回，非进程退出码证明。

来源：[jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py:L174–L179](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py#L174-L179), [jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py:L414–L421](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py#L414-L421)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":179,"path":"jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py","sha256":"33b4e0c2a0ef72097e3e52cce22d84e0620df250dbc5e1dcb912f16f7891a73b","start":174},{"end":421,"path":"jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py","sha256":"8cd4e00cc21990076e6aa167ade390b2950d8c82c1a2f7c97935099f4d172bb5","start":414}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=docx-pro-cli facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4fd01f0755b9c74a0d90db79b6917378cabe693afc3bd45b8c9866e3b7a51334 -->
**main 仅捕获分发调用的 FileNotFoundError/ValueError 并返回 2：统一局部返回码，代价是仅凭返回值无法区分错误类型**
设计推断（非作者历史意图）：

main 对 args.func(args) 的返回值原样透传，并仅将 FileNotFoundError 与 ValueError 两类异常记录 '[错误]' 后返回 2。收益是这两类常见错误有统一的局部返回值 2；成本是调用方仅凭该返回值无法区分是缺文件还是非法参数，且其他类型异常不在捕获之列（推断）。此为函数返回值，不构成进程退出码证明（尽管 __main__ 下 sys.exit(main()) 会传递它）。

来源：[jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py:L404–L421](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py#L404-L421), [jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py:L424–L425](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py#L424-L425)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":421,"path":"jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py","sha256":"b3b576baef96b2810255fffdc6bb8724b7cd4274e631f8337442f44aa94d3045","start":404},{"end":425,"path":"jiuwenswarm/resources/agent/workspace/skills/docx-pro/scripts/docx_pro.py","sha256":"c86a687dc0735836998a4f2d1ad0536d34c088d503731b70989149cd3c97105a","start":424}],"trace":[]} -->
<!-- /kb:depth -->
