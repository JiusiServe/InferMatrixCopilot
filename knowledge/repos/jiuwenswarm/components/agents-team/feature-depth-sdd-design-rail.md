---
title: "DesignRail SDD 状态机（Spec-Driven Development）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L76-L92, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L91-L92, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/sdd/design_rail/test_config_loader.py:L46-L47, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/sdd/design_rail/test_config_loader.py:L76-L83, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/sdd/design_rail/test_design_rail_integration.py:L121-L127, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L62-L92, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py:L40-L51, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L85-L90, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py:L261-L264, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L140-L149, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L97-L149, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L186-L207]
feature: "sdd-design-rail"
entry_points: ["jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py", "jiuwenswarm/agents/harness/code/rails/sdd/design_rail/__init__.py", "jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py"]
source_globs: ["jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py", "jiuwenswarm/agents/harness/code/rails/sdd/design_rail/__init__.py", "jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py", "jiuwenswarm/agents/harness/code/rails/sdd/design_rail/skills/aet-req-analysis/scripts/assemble-checklist.mjs", "jiuwenswarm/agents/harness/code/rails/sdd/design_rail/skills/aet-req-analysis/scripts/assemble-template.mjs", "jiuwenswarm/agents/harness/code/rails/sdd/design_rail/skills/aet-req-design/scripts/assemble-checklist.mjs", "jiuwenswarm/agents/harness/code/rails/sdd/design_rail/skills/aet-req-design/scripts/assemble-template.mjs", "jiuwenswarm/agents/harness/code/rails/sdd/design_rail/config_loader.py", "jiuwenswarm/agents/harness/code/rails/sdd/__init__.py", "jiuwenswarm/agents/harness/code/rails/sdd/common/__init__.py"]
---

# DesignRail SDD 状态机（Spec-Driven Development）：实现深读

[功能概览](feature-sdd-design-rail.md) · [owner 入口](_index.md)

<!-- kb:depth feature=sdd-design-rail facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1896ebc0d3cbefe5e215ad8770bbf9536e63dec3aab3c44272637ff70a3c254d -->
**DesignRail.__init__：加载并校验 rail_pkg_dir/config.yaml，失败抛 ValueError**
构造函数把 rail_pkg_dir/project_dir/priority 传给 super()，随后 config_loader.load(rail_pkg_dir / "config.yaml") 并 validate（带 rail_pkg_dir）；result.ok 为假时 raise ValueError(f"DesignRail config validation failed: {result.errors}")。通过后 self.stages 取 cfg["stages"]（空 dict 兜底）。

来源：[jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L76–L92](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py#L76-L92)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":92,"path":"jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py","sha256":"c09808fcb6629adf341731f323a1e7e5330102fe2ed40f908f158d69323eea79","start":76}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=sdd-design-rail facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3450f3612b1537460e8f52d3f1e1e01df8a2956b37dce297583cf61fef416cca -->
**priority：config.yaml 的 priority 覆盖构造参数，缺省回退构造参数**
self._priority = int(cfg.get("priority", priority))——config.yaml 中的 priority 优先，未配置时使用 __init__ 传入的 priority（测试中为 60）。

来源：[jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L91–L92](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py#L91-L92), [tests/unit_tests/sdd/design_rail/test_config_loader.py:L46–L47](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/sdd/design_rail/test_config_loader.py#L46-L47)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":92,"path":"jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py","sha256":"4130a75083dd6c9091cd29b410551bf7c2322f75013382f87cb0353561a3ac80","start":91},{"end":47,"path":"tests/unit_tests/sdd/design_rail/test_config_loader.py","sha256":"d4dceef18ac3ec2a5a8d542993e51e2c26349de3a43addbd6e36e91b5fb91b94","start":46}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=sdd-design-rail facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e77e926350a5e66f68671176e1d1c8e7e82d6f29705de0d8c393dbb2751c9805 -->
**DesignRail 继承 RailStateMachineBase，并在构造时依赖 config_loader 的 load+validate**
DesignRail 是 RailStateMachineBase 的子类（后者继承 openjiuwen 的 DeepAgentRail），构造函数调用 config_loader.load(rail_pkg_dir/config.yaml) 并用 validate(cfg, rail_pkg_dir=...) 校验后填充 self.stages。

来源：[jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L62–L92](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py#L62-L92), [jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py:L40–L51](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py#L40-L51)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":92,"path":"jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py","sha256":"6a6da7487fb8491484ecbbb83693dd0fab5bfd37841e10be13dfd51f183e64af","start":62},{"end":51,"path":"jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py","sha256":"525f9598fa933eadf795fa7850c23c4f2daee572d6062a98c5b2185bb27bd35e","start":40}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=sdd-design-rail facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6fc1990358083607e85ee3383fc6a5815021a8f2fcb6dce9c25114acf97a9e27 -->
**config 校验失败时构造函数抛 ValueError；advance 非法 stage 返回 ok=False 字典**
__init__ 中 validate 结果不 ok 时 raise ValueError（含 errors 列表）；_handle_advance 对非字符串或不属于 self.stages 的 stage 参数不抛异常，直接返回 {"ok": False, "error": f"invalid stage: {target!r}"} 交给调用方。

来源：[jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L85–L90](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py#L85-L90), [jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py:L261–L264](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py#L261-L264)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":90,"path":"jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py","sha256":"b62db4bbca9ff16769d2f84827ee4169088784f62144cbc18c0a4f4ed28fb823","start":85},{"end":264,"path":"jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py","sha256":"1e78eafccb7effd22447d298c6125d8809199d1b7cdae9ebeaecea84b3e6358c","start":261}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=sdd-design-rail facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0fe62041df063928cefd61cdadb62224e16f46da85a97512a65b676a3f30e712 -->
**approve 不自动转移：避免双重推进，代价是依赖 agent 主动调用 sdd_advance**
设计推断（非作者历史意图）：

源码注释说明：若 after_tool_call 在 approve 时自动转移，随后 agent 再调 sdd_advance 会因已在下一阶段收到 "not a valid next" 错误；因此选择只记日志。收益是状态转移单一来源，成本是推进必须依赖 agent 遵循 SKILL.md R4 指令显式调用工具（此依赖为对该注释的推断性复述）。

来源：[jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L140–L149](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py#L140-L149)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":149,"path":"jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py","sha256":"f41906019486518db19c53229b4e5c710c9404740bfb53b507d1d918171e7c1f","start":140}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=sdd-design-rail facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d70dc9d9f9535954d7547381094e433cd277c1d596d156df77e4da42d3298455 -->
**单元/集成测试在运行时断言 validate 拒绝路径与 _handle_advance 成功转移**
自动化运行时验证：test_validate_no_path_init_to_done 构造 done 不可达的配置，断言 result.ok is False 且错误含 "no_path_init_to_done"；集成测试用真实 config 构造 DesignRail 后调用 rail._handle_advance({"stage": "analysis_review"})，断言 result["ok"] is True 且 rail._stage == "analysis_review"。

来源：[tests/unit_tests/sdd/design_rail/test_config_loader.py:L76–L83](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/sdd/design_rail/test_config_loader.py#L76-L83), [tests/unit_tests/sdd/design_rail/test_design_rail_integration.py:L121–L127](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/sdd/design_rail/test_design_rail_integration.py#L121-L127)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":83,"path":"tests/unit_tests/sdd/design_rail/test_config_loader.py","sha256":"a747054cb0049a98f80bc8013e02a1b5ed96427ca90541cee928a06f8b921f9a","start":76},{"end":127,"path":"tests/unit_tests/sdd/design_rail/test_design_rail_integration.py","sha256":"23f285d07b152474a78171a58d2d6cb412371aec606e59575f85726d7863441b","start":121}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->

<!-- kb:depth feature=sdd-design-rail facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=05e06b8505082e4f86a40636424d7c8d80c0c8a6738865a5bce5e61902d6306e -->
**ask_user 回调在评审阶段对拒绝答案按 _rework_target 查表结果条件转移，批准则仅等待显式 sdd_advance**
after_tool_call 回调先取 ctx.inputs 的 tool_name，非 ask_user 直接返回；随后在 stage 为 done、stage 不在 _REWORK_TARGETS 键集或 answer 文本为空时跳过转移。对非空答案，_is_reject 用 _REJECT_PATTERNS 正则与 _REJECT_CJK 关键词判定拒绝；拒绝且 _rework_target（即 _REWORK_TARGETS.get(stage)）返回非 None 时调用 _transition_to(target)。批准分支不自动转移，仅记录日志并等待 agent 显式调用 sdd_advance。

来源：[jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L97–L149](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py#L97-L149), [jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py:L186–L207](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py#L186-L207)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":149,"path":"jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py","sha256":"f47c6daf6f2f27b65860ed8374bc2f1cba40bc35332dca53550fa1e3145aef28","start":97},{"end":207,"path":"jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py","sha256":"446f2729e5fdc09fbffee84e5e2efe8475cfd970c86dc9bd106c8fbba5d7982a","start":186}],"trace":[]} -->
<!-- /kb:depth -->
