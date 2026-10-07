---
title: "Agent 模板分层校验器（L0 规范 / L1 静态 AST / L2 子进程编排）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py:L949-L987, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_hot_load_worker.py:L328-L376, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_hot_load_worker.py:L140-L155, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py:L971-L987, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py:L151-L153, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py:L164-L173, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py:L956-L959, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py:L971-L977]
feature: "agent-template-layered-validation"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py", "jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_hot_load_worker.py"]
---

# Agent 模板分层校验器（L0 规范 / L1 静态 AST / L2 子进程编排）：实现深读

[功能概览](feature-agent-template-layered-validation.md) · [owner 入口](_index.md)

<!-- kb:depth feature=agent-template-layered-validation facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=beebdfe67d9b2a4a65bda891993b3b7059b86c3e421a8bcaf4b8dffa98db3afc -->
**main()：解析包目录后按层执行，热加载在静态错误时被跳过**
validate_template.py 的 main() 先 resolve_pkg 解析目标；validate_static 得到 quality/static 两层；若 --no-hot-load 或任一层有 errors，热加载层记录 skip 原因而非执行；随后逐层 render 输出并 _print_summary，仅当三层 status 均为 PASS 才返回 0，否则返回 1。

来源：[jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py:L949–L987](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py#L949-L987)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":987,"path":"jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py","sha256":"9cef9a704e28964d3e2366c5f62fc6537d4054d6b6d892b26b6afed9869ad35b","start":949}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=agent-template-layered-validation facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=da44366d324a3412137c931bf4949292ee79c43493d849e57613cd29cdb568c7 -->
**worker 子进程契约：单个包目录参数，stdout 输出 JSON 结果并按 status 返回 0/1/2**
validate_hot_load_worker.py 的 main() 要求 sys.argv 恰好为 2 个（脚本 + 包目录），否则打印 skip JSON 并返回 2；包目录不存在同样返回 2；结果以 json.dumps(result, ensure_ascii=False) 写到 stdout，status 为 pass 返回 0、fail 返回 1、其余（skip）返回 2。

来源：[jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_hot_load_worker.py:L328–L376](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_hot_load_worker.py#L328-L376)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":376,"path":"jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_hot_load_worker.py","sha256":"769686e82c4b0caaa8a83b90b2ef848e97980172433e0bcf810e210fa5a58042","start":328}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=agent-template-layered-validation facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=18288a5ca73ce7215f21a7e83114ea6b01396d9360ae8bd394132d065960908c -->
**数据目录默认 ~/.jiuwenswarm，target 先按路径再按 local/ 目录名解析，--no-hot-load 只跑 L0+L1**
get_jiuwenswarm_data_dir 在 raw 为真时对其 expanduser，否则默认 Path.home()/".jiuwenswarm"（所示行未给出 raw 的来源）。resolve_pkg 优先把 expanduser 后已是目录的参数 resolve 返回，否则尝试 local 模板目录下的同名目录，两处都不是目录时抛 FileNotFoundError。main 的 --no-hot-load（store_true）使 L2 直接记 skip（“已通过 --no-hot-load 显式跳过”），仅执行 L0+L1。

来源：[jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py:L151–L153](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py#L151-L153), [jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py:L164–L173](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py#L164-L173), [jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py:L956–L959](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py#L956-L959), [jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py:L971–L977](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py#L971-L977)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":153,"path":"jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py","sha256":"33a60e0c2dcb8649b8ed615e42b48eeec986ba6fceca56ae1bfd6e40f79a9b31","start":151},{"end":173,"path":"jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py","sha256":"b9d90c57e42a939b5d886dee2ba3d4595aabf07b2e80c269d2a15bc598d945fd","start":164},{"end":959,"path":"jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py","sha256":"8a098a646eca27c7b735650697cdb83cbed0f382ff1aa6477dcd66c9ad36bf48","start":956},{"end":977,"path":"jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py","sha256":"bcae895fa25e5b0311c6370e5162a13211c4ecb275e5776b925f04b0c1fee8b2","start":971}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=agent-template-layered-validation facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=126afbe18c64251faf9b34a1651d1d26f7559dc6ba1b8e0e12d0ad3d86567c56 -->
**L2 热加载硬依赖 openjiuwen；导入失败被判为环境问题（skip）而非包问题**
worker 在执行真实加载链前导入 openjiuwen.core/harness 的 AgentCard、DeepAgent、Workspace 等符号；ImportError 时直接返回 _result("skip")，skip_fix 提示改用 JiuwenSwarm 的 venv python 重跑且这不是包的问题。

来源：[jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_hot_load_worker.py:L140–L155](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_hot_load_worker.py#L140-L155)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":155,"path":"jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_hot_load_worker.py","sha256":"7af2fef9a559738a088b7a13455ef571f15c5fa352ccf416e4815936e0b354e5","start":140}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=agent-template-layered-validation facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e0a7a6b9cf6c6ef45f5a38b59a9ab1d08a05f7d0ec7cd4588543a2388c9b833f -->
**静态错误即跳过热加载：快速反馈的代价是静态失败时无运行时证据**
设计推断（非作者历史意图）：

main() 在 quality.errors 或 static.errors 非空时让热加载层 skip（提示先修 L0/L1 再重跑），这缩短了坏包的验证循环，但意味着静态未通过时本实现不产出任何热加载层的运行时结论。

来源：[jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py:L971–L987](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py#L971-L987)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":987,"path":"jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py","sha256":"11fd878365ed062163e5221f39456219a5c365ce1c98c3e2e04e943e9fb883d3","start":971}],"trace":[]} -->
<!-- /kb:depth -->
