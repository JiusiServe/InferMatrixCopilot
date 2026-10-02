---
title: "Skill 自演进：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: ["openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/Skill自演进.md:L26-L41", "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/Skill自演进.md:L43-L43", "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/Skill自演进.md:L92-L110", "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/Skill自演进.md:L112-L125", "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/Skill自演进.md:L174-L185"]
feature: "skill-evolution"
entry_points: ["jiuwenswarm/server/runtime/agent_adapter/evolution_helpers.py"]
source_globs: ["jiuwenswarm/server/runtime/agent_adapter/evolution_helpers.py", "jiuwenswarm/agents/harness/common/rails/*"]
---

# Skill 自演进：实现深读

[功能概览](feature-skill-evolution.md) · [owner 入口](_index.md)

<!-- kb:depth feature=skill-evolution facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=71899ae281e16d5f65dca8ef4da5f523abbe99c2d4eee1b63ca00fc4d183835e -->
**`/evolve` 命令契约**
`/evolve <skill_name> [user_intent]` 的输入是已安装且对当前 Agent 可见的 Skill 名（可选 user_intent 指明改进意图），系统审查当前任务可用的对话与执行证据后返回“无需演进”或结构化改进提案，发起审查不代表一定生成或保存经验。调用方义务：开启 Skill 自演进，如需展示审批交互还需 `auto_save: false`。提案通过校验后，`auto_save: false` 进入用户审批（展示 target、section、reason、content），`true` 则跳过审批自动保存。

来源：[docs/zh/Skill自演进.md:L92–L110](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Skill%E8%87%AA%E6%BC%94%E8%BF%9B.md#L92-L110), [docs/zh/Skill自演进.md:L112–L125](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Skill%E8%87%AA%E6%BC%94%E8%BF%9B.md#L112-L125)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":110,"path":"docs/zh/Skill自演进.md","sha256":"df7011a6e420a45b298e18c55b0d91567cdbd663c2cfda13cc9f74b56aff054a","start":92},{"end":125,"path":"docs/zh/Skill自演进.md","sha256":"50a13a2e0e59b5d198477e33bbbd8e13126e352b2a7e9bcf17341e2e51c38d3c","start":112}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skill-evolution facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0477dc69d8e874aa5bbea7b3b47bd656cc6f4fa461237887edb1c19dfbe8f4e3 -->
**开关与默认值**
`react.evolution.skill_evolution` 默认 `false`，是统一开关，控制 Skill 演进、自动 Skill 创建建议及相关命令和工具的启用；`react.evolution.auto_save` 默认 `false`（YAML-only 高级选项，控制 Single Agent 与 Team Leader 的经验提交是否需用户审批），`react.evolution.review_feedback_min_confidence` 默认 `0.7`。关闭 `skill_evolution` 会禁用相关 Rails、自检提示、演进工具和 `/evolve` 命令，但不影响用户显式使用通用 `skill-creator` 或 `swarmskill-creator`。

来源：[docs/zh/Skill自演进.md:L26–L41](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Skill%E8%87%AA%E6%BC%94%E8%BF%9B.md#L26-L41), [docs/zh/Skill自演进.md:L43–L43](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Skill%E8%87%AA%E6%BC%94%E8%BF%9B.md#L43-L43)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":41,"path":"docs/zh/Skill自演进.md","sha256":"7d8619971259fea59eaf501fa8cf189c181525e7ab0147488ebd57b24d7692bd","start":26},{"end":43,"path":"docs/zh/Skill自演进.md","sha256":"cb974a71e233dafd773f2193fb98d545d2899950890b29437a52aef2951ee276","start":43}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skill-evolution facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c432729b48602cf6e29466cf9be330528de86dbee634b9d609899050d9f99898 -->
**经验存储与全局 Skill 库的耦合**
经验保存在 Skill 目录下的 `evolutions.json`（~/.jiuwenswarm/agent/workspace/skills/<skill_name>/，首次保存经验时动态创建，无已保存经验时可能不存在）；Agent Team 使用同一个全局 Skill 库，经验仍写入该路径，而成员可见的 Skill 由团队的可见性声明决定。因此团队与单 Agent 的演进经验共享同一物理库，但 Team 场景可演进的目标受 Team Skills 可见性约束。

来源：[docs/zh/Skill自演进.md:L174–L185](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Skill%E8%87%AA%E6%BC%94%E8%BF%9B.md#L174-L185)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":185,"path":"docs/zh/Skill自演进.md","sha256":"0a7b089fc5e11afefe90414e119d9a886d24ff09c52c4768d9383d3cf597bd91","start":174}],"trace":[]} -->
<!-- /kb:depth -->
