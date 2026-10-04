---
title: "SkillDev 创建、评测与打包边界：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skilldev/service.py:L44-L52, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skilldev/service.py:L65-L83, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skilldev/service.py:L328-L336, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skilldev/service.py:L92-L101, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skilldev/schema.py:L113-L122, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skilldev/pipeline.py:L74-L148, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skilldev/pipeline.py:L84-L101, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skilldev/pipeline.py:L131-L135, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skilldev/DESIGN.md:L464-L468, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skilldev/stages/improve_stage.py:L82-L84, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skilldev/stages/test_run_stage.py:L38-L41, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skilldev/pipeline.py:L68-L72, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skilldev/pipeline.py:L186-L194, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skilldev/deps.py:L35-L37, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skilldev/store.py:L7-L8, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_skilldev_schema_now_iso.py:L1-L25, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/skill/skilldev/schema.py:L647-L651]
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

<!-- kb:depth feature=skill-development facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0b08b389185a0141c0220399f124d6080c5356fd320a16e8d0e3e2b8926fbff4 -->
**run() 循环：非终态时执行当前阶段或命中挂起点暂停；退出循环后才排空 _event_queue 并 yield**
state.stage 非终态时循环：命中 SUSPENSION_POINTS 则 emit TODOS_UPDATE 与 CONFIRM_REQUEST、await _checkpoint() 后 break 暂停；否则（STAGE_HANDLERS 有该阶段 handler 时）ensure_local 取 workspace 构造 SkillDevContext，emit STAGE_CHANGED/TODOS_UPDATE，await handler.execute 后 stage=result.next_stage 并 checkpoint。经 break 或 while 条件退出后才排空 _event_queue 逐个 yield。

来源：[jiuwenswarm/server/runtime/skill/skilldev/pipeline.py:L74–L148](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skilldev/pipeline.py#L74-L148)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":148,"path":"jiuwenswarm/server/runtime/skill/skilldev/pipeline.py","sha256":"66531adb1e10ac5ae0cea9951ce7ac56e7c9bbbc2b67c51c684e4f04a9fbb28c","start":74}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skill-development facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=15a52c19a4bc84cd29439a2a5985e831d60e2b61e622e8e37e016a224d83f7f8 -->
**SkillDevPipeline._checkpoint 经注入 SkillDevDeps 耦合状态持久化与工作区同步（存储可替换）**
_checkpoint 先 await self._deps.state_store.save_state(task_id, state)，再 await self._deps.workspace_provider.sync_to_remote(task_id)；两项耦合均经由 __init__ 注入的 SkillDevDeps，store.py 文档注明当前实现为本地 state.json、可替换 Redis 而接口不变。

来源：[jiuwenswarm/server/runtime/skill/skilldev/pipeline.py:L68–L72](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skilldev/pipeline.py#L68-L72), [jiuwenswarm/server/runtime/skill/skilldev/pipeline.py:L186–L194](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skilldev/pipeline.py#L186-L194), [jiuwenswarm/server/runtime/skill/skilldev/deps.py:L35–L37](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skilldev/deps.py#L35-L37), [jiuwenswarm/server/runtime/skill/skilldev/store.py:L7–L8](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skilldev/store.py#L7-L8)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":72,"path":"jiuwenswarm/server/runtime/skill/skilldev/pipeline.py","sha256":"971d0791356535845c7a989c7fd5001c07e4b32b916c1d5902e3f9523bd0e13a","start":68},{"end":194,"path":"jiuwenswarm/server/runtime/skill/skilldev/pipeline.py","sha256":"99acf8ea574cf7518078ec851f3893155585145a2f72537415f5be294e451849","start":186},{"end":37,"path":"jiuwenswarm/server/runtime/skill/skilldev/deps.py","sha256":"b364ee9280e2ac525450bc783d44335f64a4976c1a451841a4bfabdbec1becd2","start":35},{"end":8,"path":"jiuwenswarm/server/runtime/skill/skilldev/store.py","sha256":"668575afc9938e37b9e3cfbd763c4da1a620b84dbd063a9308b927fde47dff25","start":7}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skill-development facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bc0e1916a15f553c7513e76af4c12f027cd4dc75dc10339337cfc4f90cdc01d7 -->
**IMPROVE feedback_history 为空或 TEST_RUN evals 缺失时 execute 抛 ValueError**
ImproveStageHandler.execute 在 ctx.state.feedback_history 为空时 raise ValueError("IMPROVE 阶段缺少反馈历史，请先完成 REVIEW 阶段")；TestRunStageHandler 在 state.evals 无用例时同样 raise ValueError；两处分支均不返回 StageResult。

来源：[jiuwenswarm/server/runtime/skill/skilldev/stages/improve_stage.py:L82–L84](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skilldev/stages/improve_stage.py#L82-L84), [jiuwenswarm/server/runtime/skill/skilldev/stages/test_run_stage.py:L38–L41](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skilldev/stages/test_run_stage.py#L38-L41)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":84,"path":"jiuwenswarm/server/runtime/skill/skilldev/stages/improve_stage.py","sha256":"b6dd9c6bfe41abb95f80d2339bc3f5801487a8b63adf7bf3e5fe4f4b55796065","start":82},{"end":41,"path":"jiuwenswarm/server/runtime/skill/skilldev/stages/test_run_stage.py","sha256":"52f64aa99ab0095b58647ca12cd1e5083914420ad068a901c2c3605eb073200f","start":38}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skill-development facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=69e4d9e19bff784f77b92eaf5a6a662600b246d76615bfb97208874cce9d5c87 -->
**挂起点与每阶段推进均 checkpoint（DESIGN：序列化到 state.json 供 respond 恢复）；代价是额外持久化（推断）**
设计推断（非作者历史意图）：

pipeline 在挂起点（L100）与每阶段成功推进后（L135）都 await _checkpoint()；DESIGN.md 记载 _checkpoint() 在每个阶段边界将 State 序列化到 state.json、_handle_respond 从 state.json 加载恢复。推断：收益是任务可在挂起点跨请求续跑；成本是每次阶段迁移都多一次状态序列化开销。

来源：[jiuwenswarm/server/runtime/skill/skilldev/pipeline.py:L84–L101](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skilldev/pipeline.py#L84-L101), [jiuwenswarm/server/runtime/skill/skilldev/pipeline.py:L131–L135](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skilldev/pipeline.py#L131-L135), [jiuwenswarm/server/runtime/skill/skilldev/DESIGN.md:L464–L468](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skilldev/DESIGN.md#L464-L468)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":101,"path":"jiuwenswarm/server/runtime/skill/skilldev/pipeline.py","sha256":"ec98c5fce618f2a7e95ab8a615fb2a98a188dbb695aee9fb91e226fa7872bcda","start":84},{"end":135,"path":"jiuwenswarm/server/runtime/skill/skilldev/pipeline.py","sha256":"3652e49e609a82894db32c19c385132085f2dc29fce720067f1650cf6e553158","start":131},{"end":468,"path":"jiuwenswarm/server/runtime/skill/skilldev/DESIGN.md","sha256":"d9776b8d7d83748df1c676e96c765fcd07a973e1f9238bfd2ea0f86a19bad789","start":464}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skill-development facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b1443af68928524a0f7006a23354d8cd01c8cf64daadac2cd44204c887bdd5f8 -->
**SkillDev schema._now_iso 的格式与 UTC 范围断言（helper 级单测）**
test_now_iso_format_and_no_deprecation_warning 直接导入 jiuwenswarm.server.runtime.skill.skilldev.schema._now_iso，在调用前后记录 UTC 时间并捕获 DeprecationWarning；断言返回值匹配 YYYY-MM-DDTHH:MM:SSZ 正则、无该类警告，且解析后时间位于 before 与 after 之间。该测试仅覆盖此 helper，未在本轮执行，不触及技能生成、评测或打包流程。

来源：[tests/unit_tests/agentserver/test_skilldev_schema_now_iso.py:L1–L25](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/test_skilldev_schema_now_iso.py#L1-L25), [jiuwenswarm/server/runtime/skill/skilldev/schema.py:L647–L651](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skilldev/schema.py#L647-L651)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":25,"path":"tests/unit_tests/agentserver/test_skilldev_schema_now_iso.py","sha256":"f81b26a5a030713e281232d500c92ea39dda48b88f5ef1f4263ef7490b5bab0e","start":1},{"end":651,"path":"jiuwenswarm/server/runtime/skill/skilldev/schema.py","sha256":"27f7a5a0c874745bc768ebbec5bb4d82693a80051b7037249e441a0e8d2aabd3","start":647}],"trace":[],"validation_kind":"helper_unit"} -->
<!-- /kb:depth -->
