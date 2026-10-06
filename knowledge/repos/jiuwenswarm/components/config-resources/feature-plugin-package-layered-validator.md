---
title: "plugin-creator 插件包分层校验器（validate_plugin.py L0/L1/L2）"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L1-L15, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L955-L968, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py:L136-L217, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L157-L170, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L34-L44, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py:L100-L133, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py:L288-L306, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L823-L891, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L230-L246, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L258-L266, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L522-L543, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L648-L652, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L806-L891, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L513-L543, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L782-L798]
feature: "plugin-package-layered-validator"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py", "jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py"]
---

# plugin-creator 插件包分层校验器（validate_plugin.py L0/L1/L2）

<!-- kb:knowledge owner=feature-plugin-package-layered-validator facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**三层结构与进程边界**

校验分三层：L0 规范与质量（占位符残留、展示字段），L1 静态校验（加载阻塞项，纯 stdlib：json/ast/文件系统），L2 热加载由子进程运行 worker、主脚本只解析结果；L0/L1 都通过才执行 L2（validate_plugin.py:2-8, 955-963）。L1 对 manifest 声明的 tools/rails 类做 AST 级检查（继承基类、无参构造、ToolCard 字面量、运行时路径策略），路径解析规则对齐加载器 `_resolve_new_manifest_path`（validate_plugin.py:197-222, 722-745, 448-491）。进程隔离的动机是让 openjiuwen 的运行时副作用（Runner.resource_mgr、DeepAgent）完全留在 worker 子进程内，主脚本不 import openjiuwen（worker:2-5, validate_plugin.py:801-803）；worker 内部再分三段：搭最简 agent（失败算环境问题 skip）、真实 load_plugin（失败算包问题 fail）、对绑定的 Tool/Rail 做冒烟并卸载（worker:163-306）。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L1–L15](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py#L1-L15), [jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L955–L968](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py#L955-L968), [jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py:L136–L217](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py#L136-L217)

<!-- kb:knowledge owner=feature-plugin-package-layered-validator facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**配置项与环境变量**

唯一的运行时配置是环境变量 `JIUWENSWARM_DATA_DIR`：非默认实例由宿主注入，缺省回退到 `~/.jiuwenswarm`；它决定插件包的查找目录 `<data>/agent/workspace/plugins/plugin_packages/local`（validate_plugin.py:157-170）。其余行为由模块内常量固定：热加载 worker 超时 120 秒（HOT_LOAD_TIMEOUT_SEC），worker 路径取脚本同目录（validate_plugin.py:34-35）；TODO 扫描仅覆盖 .md/.py/.json 后缀并跳过 `__pycache__`/`.git`/`.state` 目录（validate_plugin.py:42-44）。CLI 层面用户只能通过 `--no-hot-load` 改变执行范围（validate_plugin.py:941-943）。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L157–L170](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py#L157-L170), [jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L34–L44](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py#L34-L44)

<!-- kb:knowledge owner=feature-plugin-package-layered-validator facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**测试与自校验入口**

在所提供的源码切片中没有针对这两个脚本的测试文件；可观察到的验证入口是脚本自身的自校验路径：L2 冒烟本身会用良性输入逐个调用 Tool.invoke 和每个 Rail callback（含对 exception 事件注入 RuntimeError），并核对卸载数量，等于把运行时契约作为可执行断言（worker:57-133, 229-301）。主脚本对 worker 输出协议做了防御性处理：未知 status、无 JSON、超时均转为 SKIP 而非崩溃（validate_plugin.py:806-891）。此为部分输入的观察；不能据此断言仓库中不存在其他测试。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py:L100–L133](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py#L100-L133), [jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py:L288–L306](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py#L288-L306), [jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L823–L891](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py#L823-L891)

<!-- kb:knowledge owner=feature-plugin-package-layered-validator facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**三层校验的实际覆盖范围**

L0 质量层扫描包内残留的 `[TODO` 占位符，但仅限 .md/.py/.json 后缀、跳过 `__pycache__`/`.git`/`.state` 目录且忽略读不了的文件；并校验 manifest 的 i18n 展示字段、tags/quick_inputs 恰好 3 项、`default_init_input` 与 `quick_inputs[0]` 的 en/zh 值一致、README.md 存在等。L1 静态层检查 manifest 基本项（package_type=plugin、source=local、id 等于目录名等）、skills 目录的 SKILL.md frontmatter，以及对 tools/rails 声明类做 AST 检查（继承基类、无参构造、async invoke、ToolCard 字面量的 id/name/input_params）；找不到 ToolCard 字面量或 input_params 不是字面量 dict 时只降级为 warning，且 `mcps` 仅在取值为真时才报错。L2 在子进程中经真实 `load_plugin` 链加载并对绑定的 Tool.invoke 和每个 Rail callback 做冒烟，最后核对卸载数量。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L230–L246](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py#L230-L246), [jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L258–L266](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py#L258-L266), [jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L522–L543](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py#L522-L543), [jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L648–L652](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py#L648-L652)

<!-- kb:knowledge owner=feature-plugin-package-layered-validator facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**进程隔离与静态近似带来的取舍**

Inference / 设计推断（非作者历史意图）：

成本侧：L2 依赖 openjiuwen 运行环境，环境问题（ImportError、agent 搭建失败、worker 崩溃/超时/无 JSON）会以有效 skip payload 或主脚本的防御分支转化为 SKIP，退出码仍为 1（PARTIAL），用户需要区分“包坏”与“环境不可用”。收益侧：主脚本完全不 import openjiuwen，运行时副作用隔离在子进程 worker 内，且 worker 用真实 load_plugin/unload_extension 链和 Tool.invoke、Rail callback 冒烟验证运行时契约。L1 选择 AST 近似而非导入执行：找不到字面量 ToolCard(...) 或 input_params 非字面量 dict 时只降级为 warning、放弃该项检查，换取纯 stdlib、无副作用且全量报错的安全性。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L806–L891](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py#L806-L891), [jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py:L136–L217](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py#L136-L217), [jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L513–L543](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py#L513-L543), [jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py:L782–L798](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py#L782-L798)

