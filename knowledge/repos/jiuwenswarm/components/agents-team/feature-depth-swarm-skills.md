---
title: "团队技能与能力复用：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/skills.py:L93-L115, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/skills.py:L60-L90, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/assembly.py:L313-L318, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/utils.py:L1816-L1824, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/skills.py:L96-L110, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/skills.py:L18-L28, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/skills.py:L176-L190]
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
