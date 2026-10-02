---
title: "SkillDev 创建、评测与打包边界：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skilldev/service.py:L44-L52, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skilldev/service.py:L65-L83, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skilldev/service.py:L328-L336, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skilldev/service.py:L92-L101, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skilldev/schema.py:L113-L122]
feature: "skill-development"
entry_points: ["jiuwenswarm/server/runtime/skill/skilldev/service.py", "jiuwenswarm/server/runtime/skill/skilldev/pipeline.py", "jiuwenswarm/server/runtime/skill/skilldev/deps.py", "jiuwenswarm/server/runtime/skill/skilldev/context.py"]
source_globs: ["jiuwenswarm/server/runtime/skill/skilldev/service.py", "jiuwenswarm/server/runtime/skill/skilldev/pipeline.py", "jiuwenswarm/server/runtime/skill/skilldev/deps.py", "jiuwenswarm/server/runtime/skill/skilldev/context.py"]
---

# SkillDev 创建、评测与打包边界：实现深读

[功能概览](feature-skill-development.md) · [owner 入口](_index.md)

<!-- kb:depth feature=skill-development facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=43c4ab75ec5f613eabfa2f48348f39fa65b3f3d7e5f0a5465d259fb315465449 -->
**handle() 的方法分发契约**
handle(request) 按 request.req_method 查 _METHOD_DISPATCH（7 个 skilldev.* 方法各映射一个 _handle_* 函数）；未知 method 产出一个 is_complete=True、payload 为 {event_type: "skilldev.error", error: ...} 的 AgentResponseChunk。handler 返回值既可以是 AsyncIterator（逐个 yield chunk），也可以是单个 AgentResponseChunk，调用方无需区分。

来源：[jiuwenswarm/server/runtime/skill/skilldev/service.py:L44–L52](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skilldev/service.py#L44-L52), [jiuwenswarm/server/runtime/skill/skilldev/service.py:L65–L83](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skilldev/service.py#L65-L83), [jiuwenswarm/server/runtime/skill/skilldev/service.py:L328–L336](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skilldev/service.py#L328-L336)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/server/runtime/skill/skilldev/service.py","start":44,"end":52,"sha256":"a7d58da663e8241670437e56528ce6bbadb05c5eead2bd1a722f7c2684c146d3"},{"path":"jiuwenswarm/server/runtime/skill/skilldev/service.py","start":65,"end":83,"sha256":"4026666c0893a6cf74ac008ec975af237f235feb8b627e7ac9281ca921f7c30c"},{"path":"jiuwenswarm/server/runtime/skill/skilldev/service.py","start":328,"end":336,"sha256":"d7ee23f939c89127270997d8a00b8df7b4307b5d278223d9246ad82aa6ae7973"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skill-development facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=638963778cc957f294d5fe9a1481c60697904e74b189c672a48a5e74c529754a -->
**SkillDevState 的默认值与 start 参数缺省**
新建任务时 SkillDevState 默认 stage=INIT、mode=CREATE、iteration=0（schema.py L117–L119）；_handle_start 从 params 填充 input，缺省为 query=""、tools=[]、resources=[]、existing_skill=None，因此仅传 query 即可发起 create 模式任务。

来源：[jiuwenswarm/server/runtime/skill/skilldev/service.py:L92–L101](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skilldev/service.py#L92-L101), [jiuwenswarm/server/runtime/skill/skilldev/schema.py:L113–L122](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skilldev/schema.py#L113-L122)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/server/runtime/skill/skilldev/service.py","start":92,"end":101,"sha256":"447eb4b4a31d8d4a1da9f86adf7b9ef201eafc524fcdb2bae55b5b175537fbd9"},{"path":"jiuwenswarm/server/runtime/skill/skilldev/schema.py","start":113,"end":122,"sha256":"8c06604fc75db7f9f6c1c121df75c47d3fba0650b22bc6e766d21a4e54c4aa61"}],"trace":[]} -->
<!-- /kb:depth -->
