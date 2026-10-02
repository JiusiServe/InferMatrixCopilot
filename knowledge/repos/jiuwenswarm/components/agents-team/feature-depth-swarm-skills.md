---
title: "团队技能与能力复用：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/skills.py:L93-L115, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/skills.py:L60-L90, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/assembly.py:L313-L318, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/utils.py:L1816-L1824, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/skills.py:L96-L110, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/skills.py:L18-L28, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/skills.py:L176-L190, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/skills.py:L176-L225, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/skills.py:L56-L57, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/skills.py:L155-L166, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/agents/swarm/test_skills_provider.py:L112-L130, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/agents/swarm/test_skills_provider.py:L27-L34, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/skills.py:L42-L52, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/skills.py:L118-L126]
feature: "swarm-skills"
entry_points: ["jiuwenswarm/agents/swarm/assembly.py", "jiuwenswarm/agents/swarm/providers/skills.py"]
source_globs: ["jiuwenswarm/agents/swarm/assembly.py", "jiuwenswarm/agents/swarm/providers/skills.py", "jiuwenswarm/agents/swarm/*"]
---

# 团队技能与能力复用：实现深读

[功能概览](feature-swarm-skills.md) · [owner 入口](_index.md)

<!-- kb:depth feature=swarm-skills facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4ba5a3a368f2013908973a75e536b13f01d12f286f3018e2c0458b743b395511 -->
**成员技能可见性的解析链路**
compose_member_skill_visibility(ctx) 拿到成员构建上下文后，第一步调用 build_member_skill_visibility_provider(ctx)：它用 ctx.resolve_member_skill_visibility_path() 求出成员可见性文档路径，取不到则返回 None；随后以成员路径、team_skill_visibility_path 和 team_id 为参数调用 openjiuwen 的 build_skill_visibility_provider 构造一个每次调用都重读元数据文件的 FileSkillVisibilityProvider。回到 compose_member_skill_visibility，provider 为 None 时返回 (set(), 全局禁用集)，否则调用 provider() 得到 (enabled, disabled) 名称集合，供只能接受名称集合的 Skill rail 使用。

调用路径：`jiuwenswarm/agents/swarm/providers/skills.py`（`compose_member_skill_visibility`） → `jiuwenswarm/agents/swarm/providers/skills.py`（`build_member_skill_visibility_provider`）

来源：[jiuwenswarm/agents/swarm/providers/skills.py:L93–L115](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/skills.py#L93-L115), [jiuwenswarm/agents/swarm/providers/skills.py:L60–L90](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/skills.py#L60-L90)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/swarm/providers/skills.py","start":93,"end":115,"sha256":"efa9d14847a9d862980b252b6d1844b6eb2dafba1b566f3ae650fd337ded4581"},{"path":"jiuwenswarm/agents/swarm/providers/skills.py","start":60,"end":90,"sha256":"a4b9861708a64f39d7d93fd2b3348e4b966be09d39041ae57756099c5ad00369"}],"trace":[{"path":"jiuwenswarm/agents/swarm/providers/skills.py","symbol":"compose_member_skill_visibility","start":112,"end":114},{"path":"jiuwenswarm/agents/swarm/providers/skills.py","symbol":"build_member_skill_visibility_provider","start":84,"end":90}]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=swarm-skills facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=329eba69e1fbf3f2c9cd788cf479e7b8d1843e54c8b5bb084e0260d6ed80c58e -->
**全局技能库目录的指向时机与默认值**
enrich_team_spec_for_swarm 在构建任何成员之前调用 configure_global_skills_dir(get_agent_skills_dir())，把 openjiuwen 的唯一 Skill 库指向平台目录，默认路径为 ~/.jiuwenswarm/agent/workspace/skills（get_agent_workspace_dir()/skills）；不调用则 openjiuwen 回退到 ~/.openjiuwen/workspace/skills，两侧读到不同库。另一处语义默认：skills-visibility.json 中空 allow 列表表示“继承整个库”而非“全部禁用”，且 disabled 恒压过 enabled。

来源：[jiuwenswarm/agents/swarm/assembly.py:L313–L318](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/assembly.py#L313-L318), [jiuwenswarm/common/utils.py:L1816–L1824](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/utils.py#L1816-L1824), [jiuwenswarm/agents/swarm/providers/skills.py:L96–L110](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/skills.py#L96-L110)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/swarm/assembly.py","start":313,"end":318,"sha256":"480039429f7a37adea9f51fcb91e6628126905d4702c0b670dc5e9b25b55b828"},{"path":"jiuwenswarm/common/utils.py","start":1816,"end":1824,"sha256":"2fafb1938cc8c02d020440f61748f8a758d4e0c81096c6da661e519294d513dc"},{"path":"jiuwenswarm/agents/swarm/providers/skills.py","start":96,"end":110,"sha256":"89ae83e6900a25615fa33d956b1dae3689f3bd416c1253eee5891bf3e64cf69a"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=swarm-skills facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=78693ce2df8258ac57e5bc130d526d9d1768534b9feb0576e46b95cd0cb44c56 -->
**单一物理技能库 + 元数据可见性（而非每成员副本）**
设计推断（非作者历史意图）：

推断：技能只存一份物理库，可见性是 skills-visibility.json 元数据，收益是授权变更在运行时生效且跨进程重读即可见；代价是安装不自动扩展 allow-list——空 allow-list 的成员继承全库，而带显式 allow-list 的成员安装新技能后必须被显式授予才可见。模块文档还给出单一 seeder 的理由：第二个写入者会与属主 rail 争抢同一文件锁且跳过规则会漂移。

来源：[jiuwenswarm/agents/swarm/providers/skills.py:L18–L28](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/skills.py#L18-L28), [jiuwenswarm/agents/swarm/providers/skills.py:L176–L190](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/skills.py#L176-L190), [jiuwenswarm/agents/swarm/providers/skills.py:L93–L115](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/skills.py#L93-L115)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/swarm/providers/skills.py","start":18,"end":28,"sha256":"ab5d53d6d229c824fcbeb6fe3dee1e4bc3d92b46403dc7a5c2914504bffc0fc9"},{"path":"jiuwenswarm/agents/swarm/providers/skills.py","start":176,"end":190,"sha256":"26b3dbe9cbabea2985a80bd4bdb98e243b2f42794977763c66740ab13d35e6ee"},{"path":"jiuwenswarm/agents/swarm/providers/skills.py","start":93,"end":115,"sha256":"efa9d14847a9d862980b252b6d1844b6eb2dafba1b566f3ae650fd337ded4581"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=swarm-skills facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2bc232d4fa07dfd8b5411a06e10578e59d19a4446ce1e33dcad719495e4853b2 -->
**build_member_skill_toolkit：无 workspace 返回 None，正常返回绑定共享库的 rail**
Provider 工厂 build_member_skill_toolkit(params, ctx)（注册名 swarm.member_skill_toolkit）不消费任何 params 键，契约上仅为保留签名。MemberSkillToolkitInput.resolve 后若 workspace_root 为空立即返回 None（该成员跳过此能力，调用方必须容忍 None）；否则返回绑定共享 agent workspace 的 MemberSkillToolkitRail，可见性文档路径仅在构建日志中出现，从不写入。

来源：[jiuwenswarm/agents/swarm/providers/skills.py:L176–L225](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/skills.py#L176-L225), [jiuwenswarm/agents/swarm/providers/skills.py:L56–L57](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/skills.py#L56-L57), [jiuwenswarm/agents/swarm/providers/skills.py:L155–L166](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/skills.py#L155-L166)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":225,"path":"jiuwenswarm/agents/swarm/providers/skills.py","sha256":"9690a19800b4e16d53b5784c162e18a046c709ed1aff4f9d856954f7469e594d","start":176},{"end":57,"path":"jiuwenswarm/agents/swarm/providers/skills.py","sha256":"351dfe25e5ecd43deff7f0615a29642ea5a5e014989f04b8e85dc4f5f41b4662","start":56},{"end":166,"path":"jiuwenswarm/agents/swarm/providers/skills.py","sha256":"112823c4ca64c1b3b671252eddece0d8646f0eb7dbfbea6418ecbbce2c504449","start":155}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=swarm-skills facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7217c298419b88b7e4b696cbe9bc6cbc5e34a3af6fe665481e5b4743de7fc841 -->
**组合语义测试：allow 取并集，deny 并集叠加全局禁用**
入口 tests/agents/swarm/test_skills_provider.py::test_compose_skill_visibility_unions_allow_and_prefers_deny 构造 member（allow=[alpha,shared]、deny=[member-denied]）与 team（allow=[beta,shared]、deny=[team-denied]）两份 SkillVisibility，调用 openjiuwen 的 compose_skill_visibility(member, team, ["globally-disabled"])，断言 enabled == {alpha,beta,shared}、disabled == {member-denied,team-denied,globally-disabled}。此处仅描述断言内容，不代表该测试此刻已被执行通过。

来源：[tests/agents/swarm/test_skills_provider.py:L112–L130](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/agents/swarm/test_skills_provider.py#L112-L130), [tests/agents/swarm/test_skills_provider.py:L27–L34](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/agents/swarm/test_skills_provider.py#L27-L34)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":130,"path":"tests/agents/swarm/test_skills_provider.py","sha256":"e485decce76d8524a77fee7140d523c67abd21174ea37bde88b07a9ed5f97a86","start":112},{"end":34,"path":"tests/agents/swarm/test_skills_provider.py","sha256":"c18ab3976a537e6c71b9d0fe9c7db7587e2ad6b15788de64bbf1cd809a19f174","start":27}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=swarm-skills facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b0bf15c882720a5d264a9efe9f0eaadeae30bda9cf5a286f34812d02557690bf -->
**skills provider 依赖 openjiuwen 可见性原语；load_execution_disabled_skills 懒导入**
providers/skills.py 模块级从 openjiuwen.agent_teams.skill 导入 FileSkillVisibilityProvider/build_skill_visibility_provider，并依赖 MemberSkillToolkitRail 与 SkillManager；_load_global_disabled_skills 延迟导入 jiuwenswarm.server.runtime.skill 的 load_execution_disabled_skills，docstring 注明以免 provider 模块在 import 期拖入 skill 运行时包。

来源：[jiuwenswarm/agents/swarm/providers/skills.py:L42–L52](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/skills.py#L42-L52), [jiuwenswarm/agents/swarm/providers/skills.py:L118–L126](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/skills.py#L118-L126)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":52,"path":"jiuwenswarm/agents/swarm/providers/skills.py","sha256":"bc939c36f89b2f5c9fb6c10afd9b19ea6762ac263b229aaee43f40331dc98bf9","start":42},{"end":126,"path":"jiuwenswarm/agents/swarm/providers/skills.py","sha256":"fc6877e9bdb211a851b811dde62a1dcef42c621f8e6852207395ce372b3dcefe","start":118}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=swarm-skills facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b366d701caeed2966acacff04e506466838c9ef7119a37b1b236c67d458d0cc3 -->
**build_member_skill_toolkit：workspace_root 为空时返回 None；SkillManager 构建抛异常仅告警并以 manager=None 继续**
触发一：解析出的 workspace_root 为空值，`if not root_path` 守卫直接 return None，该成员跳过技能工具包。触发二：SkillManager(workspace_dir=...) 构建抛异常，被 except Exception 捕获后仅记录 warning，仍返回 manager=None 的 MemberSkillToolkitRail。

来源：[jiuwenswarm/agents/swarm/providers/skills.py:L176–L225](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/skills.py#L176-L225)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":225,"path":"jiuwenswarm/agents/swarm/providers/skills.py","sha256":"9690a19800b4e16d53b5784c162e18a046c709ed1aff4f9d856954f7469e594d","start":176}],"trace":[]} -->
<!-- /kb:depth -->
