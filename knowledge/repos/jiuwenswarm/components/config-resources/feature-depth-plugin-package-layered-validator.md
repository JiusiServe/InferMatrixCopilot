---
title: "plugin-creator 插件包分层校验器（L0/L1/L2）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L937-L952, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py:L328-L344, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py:L370-L376, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L157-L182, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py:L136-L155, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/SKILL.md:L1-L167, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L856-L876, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py:L361-L368, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L969-L971, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py:L122-L133, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L933-L971, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L844-L891]
feature: "plugin-package-layered-validator"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py", "jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py"]
---

# plugin-creator 插件包分层校验器（L0/L1/L2）：实现深读

[功能概览](feature-plugin-package-layered-validator.md) · [owner 入口](_index.md)

<!-- kb:depth feature=plugin-package-layered-validator facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f546e46d655c78ceaba09a1a3d45951629c4579f01aa78ffa9ca554823d59bd9 -->
**main：三层校验的分支、渲染与本地返回值**
main() 解析 target 与 --no-hot-load；resolve_pkg 失败时输出 Error 并 return 1。随后 validate_static(pkg) 得到 L0/L1 两层；--no-hot-load 或 L0/L1 有 errors 时构造 LAYER_HOT_LOAD 的 Layer 并 skip，否则调用 validate_hot_load(pkg) 在子进程中跑 worker 并解析最后一行 JSON。三层经 layer.render() 与 _print_summary 写到 stdout，仅当三层 status 全为 "PASS" 才 return 0，否则 return 1（函数返回值，非进程退出码断言）。

来源：[jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L933–L971](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py#L933-L971), [jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L844–L891](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py#L844-L891)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":971,"path":"jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py","sha256":"06a5cfad89506dda9b6f48e41d61d60e467864376c6eebb94bca40bb7272599a","start":933},{"end":891,"path":"jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py","sha256":"de6f314356557c341b00360c52d89da0ff9c8d59460a65a8502fd8e8af803d94","start":844}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=plugin-package-layered-validator facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e40c797b765f6e9fd16e559ac814c17e45b20cb6ae7c1034dd4fe733a6ca62fc -->
**CLI：位置参数 target + --no-hot-load；找不到目录时输出 Error 并局部返回 1**
validate_plugin.py 接受一个位置参数 target（包目录绝对路径，或 local/ 下的 plugin-name）和 --no-hot-load 开关；resolve_pkg 抛 FileNotFoundError 时 write_stdout("Error: ...") 并 return 1（局部返回值，非进程级断言）。热加载 worker 是独立入口：要求恰好一个参数 <package-dir>，向 stdout 输出一行 JSON 结果，status 为 pass/fail/其他时分别返回 0/1/2。

来源：[jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L937–L952](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py#L937-L952), [jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py:L328–L344](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py#L328-L344), [jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py:L370–L376](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py#L370-L376)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":952,"path":"jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py","sha256":"87ec9d59652a5cd25a64ba3400e5137b93b5d9af53e4010d7fa12605a64c17a3","start":937},{"end":344,"path":"jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py","sha256":"bf975fd01cde308fd621e69d1d3bf8f3b49ba865861ca3eaa5c15a85772d73cf","start":328},{"end":376,"path":"jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py","sha256":"26118efc5af5fc8245f1b289f0fb2561fee78f9295d54dd9a165bbd23bc02133","start":370}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=plugin-package-layered-validator facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=09d73332b24e51857b0812f5953d59f16fc400afd8135291e00ff2bd68890e94 -->
**数据目录默认 ~/.jiuwenswarm，JIUWENSWARM_DATA_DIR 覆盖**
get_jiuwenswarm_data_dir 读取非空 JIUWENSWARM_DATA_DIR（expanduser），否则用 ~/.jiuwenswarm；resolve_pkg 先按参数找目录，找不到再到 local/ 下找，仍无则抛 FileNotFoundError。

来源：[jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L157–L182](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py#L157-L182)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":182,"path":"jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py","sha256":"ef0674b56bd1d434dee2d0c4329e4b0d002990c0d004ebbbf48358231de3177c","start":157}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=plugin-package-layered-validator facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=69363cedbee362dd1f42b77d59143aa47d478128defa7c07cde6d79de2c4d12d -->
**L2 依赖 openjiuwen 运行时，ImportError 产生该次 skip 结果**
worker 在 _hot_load 内导入 openjiuwen 的 Runner/DeepAgent/Workspace 等；ImportError 时返回 skip 结果并提示换 JiuwenSwarm 的 venv python 重跑，本次不产出包级判定。

来源：[jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py:L136–L155](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py#L136-L155)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":155,"path":"jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py","sha256":"f883dfa4ee39e25d91b9d4055266bf0d5620f23a16fe5897e383af5b5c37cef4","start":136}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=plugin-package-layered-validator facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=740801ca5714dd885e4f07fcff0812097c79a4149d7918b10b5184ac65d55ce9 -->
**热加载 worker 超时或无法启动时父层记录 SKIP 并返回该层**
父脚本 subprocess.run 带 timeout=HOT_LOAD_TIMEOUT_SEC、check=False；捕获 subprocess.TimeoutExpired 与 OSError 时调用 layer.skip 记录原因与修复提示并 return layer，不抛异常。worker 侧 asyncio.run(_hot_load) 抛出的异常被捕获并转为 status="skip" 的结果。

来源：[jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L856–L876](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py#L856-L876), [jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py:L361–L368](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py#L361-L368)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":876,"path":"jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py","sha256":"2f8710066cae4b6e76b80379001e32a89646f104593211d4f8c1a186ec71117b","start":856},{"end":368,"path":"jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py","sha256":"583fd9c9324a0bd5660aaa2f630f5d8259b41d13b68e590fdd6ee451f1dbf67f","start":361}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=plugin-package-layered-validator facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1067602df56e6ec77dcaf20c54b679922e78d71c6048b10146fe71e5e16a8eb0 -->
**子进程隔离+超时换取环境故障表现为 SKIP 而非错误**
设计推断（非作者历史意图）：

（推断）收益：热加载在子进程中执行并受 HOT_LOAD_TIMEOUT_SEC 约束，包内 import/绑定卡住不会无限阻塞校验；代价：超时/启动失败被记为 SKIP，而 970 行要求所有层 status == "PASS" 才返回 0，故基础设施故障同样导致整体返回 1，无法通过校验。另注意 _smoke_rail_callbacks 中单个回调抛异常是逐项记录为 error，不是整体 skip。

来源：[jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L856–L876](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py#L856-L876), [jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L969–L971](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py#L969-L971), [jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py:L122–L133](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py#L122-L133)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":876,"path":"jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py","sha256":"2f8710066cae4b6e76b80379001e32a89646f104593211d4f8c1a186ec71117b","start":856},{"end":971,"path":"jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py","sha256":"f92b688fb90ade55be6714beca9c67fbd30b79e67d874f3cbd0a2626504379bd","start":969},{"end":133,"path":"jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py","sha256":"2a9838e9496832f75003cd237e2f619c18141ba589607b6671e1262ef3fde722","start":122}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=plugin-package-layered-validator facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=84fe78274b0d81e64e681ad263986062df7d8cd723e790cc43437593c54d90b8 -->
**文档规定须跑到 RESULT: PASS 才能注册（未执行）**
文档中的人工验收步骤（本轮未执行）：

SKILL.md 要求 create/update 都执行 scripts/validate_plugin.py，L0/L1/L2 依次运行，须以 JiuwenSwarm 环境 python 达到 RESULT: PASS，L2 失败或未执行均不能 register。此为文档化手工流程，本次未执行。

来源：[jiuwenswarm/resources/agent/workspace/skills/plugin-creator/SKILL.md:L1–L167](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/SKILL.md#L1-L167)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":167,"path":"jiuwenswarm/resources/agent/workspace/skills/plugin-creator/SKILL.md","sha256":"378760e95fc640f495bedc9684fe2569b91a06e3091475c2ab14e42d8c8ac356","start":1}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
