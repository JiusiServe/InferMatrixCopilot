---
title: "plugin-creator 插件包脚手架初始化：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py:L184-L202, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py:L150-L181, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py:L184-L206, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py:L129-L131, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py:L91-L103, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py:L129-L147, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py:L158-L162]
feature: "plugin-package-initializer"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py"]
---

# plugin-creator 插件包脚手架初始化：实现深读

[功能概览](feature-plugin-package-initializer.md) · [owner 入口](_index.md)

<!-- kb:depth feature=plugin-package-initializer facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8eba93d78402711e0fafb656d53eaf84188a59906cd471174a68e193c359b9a6 -->
**main: 传入 kebab-case 名称时在 local plugin_packages 下创建含 manifest.json 与 README.md 的骨架目录**
main 校验 argv 长度后调用 resolve_init_target(sys.argv[1])，若名称匹配 NAME_RE 且 local/built_in 中均无同名目录，则 init_package 创建 pkg_dir（先 mkdir parents），写入由 MANIFEST_TEMPLATE 和 README_TEMPLATE 填充占位符得到的 manifest.json 与 README.md，通过 write_stdout 输出进度后返回 0。

来源：[jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py:L184–L202](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py#L184-L202), [jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py:L150–L181](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py#L150-L181)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":202,"path":"jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py","sha256":"209dacf3af83f6317274f2316d2874d853afbd27b0c4384ed84bea034a3717fe","start":184},{"end":181,"path":"jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py","sha256":"61b4420e43740a126665ac7efe1b320e89fcca4f5e4ea0d75333da7e5ecf4371","start":150}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=plugin-package-initializer facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3342b29bbb0f2718965f7fc6399d9da307d07c680ff758025bf2a5bc764c5ea0 -->
**接受 kebab-case 包名或显式路径参数，返回 int 状态码**
main() 在无参数时经 write_stdout 输出用法说明并 return 1；有参数时 resolve_init_target(sys.argv[1]) 接受包名或含分隔符的路径，init_package 成功后 return 0，ValueError 被捕获并把消息写到 stdout 后 return 1；脚本入口 raise SystemExit(main())。

来源：[jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py:L184–L206](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py#L184-L206), [jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py:L129–L131](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py#L129-L131)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":206,"path":"jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py","sha256":"0ecf630b999a12d89ecd8c9fc8ec5a5c64e50be5815bdf46248908ec239253ee","start":184},{"end":131,"path":"jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py","sha256":"a1fef105c606cb897ccbea88fdee0321d09884e70f57ec5b50dc42aeae08c9b6","start":129}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=plugin-package-initializer facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=33e1e66a3dc8e0af1961fb80ddc5039b2d506883ca42141f311c95218ca491f3 -->
**落盘根由 JIUWENSWARM_DATA_DIR 决定，未设置或空白时默认 ~/.jiuwenswarm**
get_jiuwenswarm_data_dir 读取环境变量 JIUWENSWARM_DATA_DIR 并 strip，非空则 Path(raw).expanduser()，否则 Path.home()/".jiuwenswarm"；local 目录固定追加 agent/workspace/plugins/plugin_packages/local。

来源：[jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py:L91–L103](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py#L91-L103)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":103,"path":"jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py","sha256":"f84197dec2c893cfd20dd576aa01a46eac5eeddfd229fe08873948b4a6774bde","start":91}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=plugin-package-initializer facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8fe627e7b33777f663a0310643090d55ade545abccba1d091b329ba6f76106c9 -->
**拒绝覆盖已有包换取安全，代价是需重命名或删除；显式路径绕过重名预检**
设计推断（非作者历史意图）：

收益（推断）：目标目录已存在时 raise 而非覆盖，避免破坏现有包，错误信息给出 rename/delete 两种出路。成本（推断）：按名创建前须先处理旧包；且含分隔符的显式路径分支只校验父目录必须是 local 目录，不执行 _assert_package_id_available 的 local/built_in 重名检查。

来源：[jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py:L129–L147](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py#L129-L147), [jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py:L158–L162](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py#L158-L162)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":147,"path":"jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py","sha256":"5ac0533a016be10557f87a5f0e3417a65e49ab10dfce60ab6412072b9d308bfd","start":129},{"end":162,"path":"jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py","sha256":"fc3947a0faba9a2466341893613e3fda95e8a8a5fa646c6e9f382e1f5fa05362","start":158}],"trace":[]} -->
<!-- /kb:depth -->
