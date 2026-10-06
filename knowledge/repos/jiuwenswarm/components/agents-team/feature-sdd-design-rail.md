---
title: "DesignRail SDD 状态机（Spec-Driven Development）"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L2-L17, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py:L101-L137, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py:L255-L301, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/sdd/design_rail/__init__.py:L4-L12, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py:L297-L333, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L36-L53, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/sdd/design_rail/skills/aet-req-analysis/scripts/assemble-template.mjs:L14-L20, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L48-L53, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L141-L149, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py:L8-L13, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/sdd/design_rail/config_loader.py:L58-L72, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py:L255-L264, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py:L343-L365, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L70-L92, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L97-L149]
feature: "sdd-design-rail"
entry_points: ["jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py", "jiuwenswarm/agents/harness/code/rails/sdd/design_rail/__init__.py", "jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py"]
source_globs: ["jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py", "jiuwenswarm/agents/harness/code/rails/sdd/design_rail/__init__.py", "jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py", "jiuwenswarm/agents/harness/code/rails/sdd/design_rail/skills/aet-req-analysis/scripts/assemble-checklist.mjs", "jiuwenswarm/agents/harness/code/rails/sdd/design_rail/skills/aet-req-analysis/scripts/assemble-template.mjs", "jiuwenswarm/agents/harness/code/rails/sdd/design_rail/skills/aet-req-design/scripts/assemble-checklist.mjs", "jiuwenswarm/agents/harness/code/rails/sdd/design_rail/skills/aet-req-design/scripts/assemble-template.mjs", "jiuwenswarm/agents/harness/code/rails/sdd/design_rail/config_loader.py", "jiuwenswarm/agents/harness/code/rails/sdd/__init__.py", "jiuwenswarm/agents/harness/code/rails/sdd/common/__init__.py"]
---

# DesignRail SDD 状态机（Spec-Driven Development）

<!-- kb:knowledge owner=feature-sdd-design-rail facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**职责分层与控制流**

DesignRail 只贡献 SDD 特有部分：6 阶段流（init→analysis→analysis_review→design→design_review→done，来自 config.yaml）、skills/ 下的方法论、以及 ask_user 评审处理；状态存取、sdd_advance 注册、方法论注入、产物门禁、feature 名解析全部由 RailStateMachineBase 提供。控制流是回调环：before_model_call 每次模型调用前先移除旧 prompt 段再注入当前阶段的 SKILL.md 方法论（无 skill 的阶段注入 bootstrap，done 不注入）；LLM 调用 sdd_advance 触发 _handle_advance 校验 next 边与产物存在性后迁移 `self._stage`（纯内存态），下一轮 before_model_call 注入新阶段方法论。

Sources / 来源：[jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L2–L17](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py#L2-L17), [jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py:L101–L137](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py#L101-L137), [jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py:L255–L301](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py#L255-L301)

<!-- kb:knowledge owner=feature-sdd-design-rail facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**支持的行为与依赖**

已实现的行为包括：产物门禁（前进前当前阶段声明的 artifacts 必须存在于 `.aet/features/<feature>/design/`，feature 取最新修改的 `.aet/features/` 子目录）；从 done 重置开启新流程（可选 feature_name，先做路径安全校验再建目录）；评审 reject 关键词启发式（中英词表 + ASCII 词边界正则，避免 "project" 误匹配 "reject"）。挂载条件是 code mode 且 `modes.code.sdd.enabled=true`，由 `JiuwenSwarmCodeAdapter._build_design_rail` 构建。技能包内含 Node 脚本 assemble-template.mjs / assemble-checklist.mjs，按 项目custom→项目aet→用户custom→用户aet→内置 五级搜索序组装模板，占位符 `{{component,level}}` 展开并自动编号章节。

Sources / 来源：[jiuwenswarm/agents/harness/code/rails/sdd/design_rail/__init__.py:L4–L12](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/design_rail/__init__.py#L4-L12), [jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py:L297–L333](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py#L297-L333), [jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L36–L53](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py#L36-L53), [jiuwenswarm/agents/harness/code/rails/sdd/design_rail/skills/aet-req-analysis/scripts/assemble-template.mjs:L14–L20](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/design_rail/skills/aet-req-analysis/scripts/assemble-template.mjs#L14-L20)

<!-- kb:knowledge owner=feature-sdd-design-rail facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**设计取舍**

Inference / 设计推断（非作者历史意图）：

返工边不放进声明式配置：config.yaml 的 `stages.<name>.next` 只列前进边，返工映射硬编码在 `_REWORK_TARGETS`，代码注释明确要求新增 *_review 阶段时必须同步更新该映射——配置简洁但引入了隐式耦合（inference 依据注释）。approve 分支不自动迁移是防双推进：after_tool_call 迁移后 Agent 再调 sdd_advance 会因已在下一阶段而报 "not a valid next"，故依赖 SKILL.md 的 R4 步骤让 Agent 显式调用（代码注释给出该理由）。状态纯内存、无持久化（基类 docstring 声明），换取简单但会话内有效。

Sources / 来源：[jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L48–L53](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py#L48-L53), [jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L141–L149](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py#L141-L149), [jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py:L8–L13](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py#L8-L13)

<!-- kb:knowledge owner=feature-sdd-design-rail facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**验证机制**

本批输入未展示任何 pytest 测试文件，可证实的验证机制是运行时校验：config_loader.validate 聚合全部错误（不短路上报）返回 ValidationResult，DesignRail 构造失败即阻止挂载（BC-005：拒绝挂载并回退普通 Code 模式）；_handle_advance 对非法 stage、非法 next、缺失产物分别返回 `{"ok": false, "error": ...}` 字典而非抛异常（注释声明永不崩溃工具调用）；_transition_to 校验目标在 stages 中防止状态机卡死。测试入口的覆盖情况在所示证据中无法确认。

Sources / 来源：[jiuwenswarm/agents/harness/code/rails/sdd/design_rail/config_loader.py:L58–L72](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/design_rail/config_loader.py#L58-L72), [jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py:L255–L264](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py#L255-L264), [jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py:L343–L365](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py#L343-L365)

<!-- kb:knowledge owner=feature-sdd-design-rail facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**公开入口与生命周期**

DesignRail 的公开入口是关键字专属构造器 `DesignRail(*, rail_pkg_dir, project_dir, priority=60)`：构造时加载并校验 rail 包内的 config.yaml，校验失败直接抛 ValueError，让构建方（BC-005）拒绝挂载，Agent 永远不会装载损坏的状态机；成功后 `self.stages` 取自配置，`priority` 可被配置中的 `priority` 键覆盖。第二个入口是 `after_tool_call(ctx)`：仅当工具名为 `ask_user` 且当前阶段是评审阶段（analysis_review/design_review）时才处理确认点——含拒绝关键词（中英词表，ASCII 用词边界正则）的答案按 `_REWORK_TARGETS` 迁回对应生产阶段；approve 不自动迁移，等 Agent 显式调用 sdd_advance（避免双推进）；答案为空（失败/非交互）则不迁移。

Sources / 来源：[jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L70–L92](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py#L70-L92), [jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L97–L149](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py#L97-L149)

