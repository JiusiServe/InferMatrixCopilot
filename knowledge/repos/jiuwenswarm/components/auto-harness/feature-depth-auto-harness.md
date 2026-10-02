---
title: "Auto Harness 评测优化：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/auto_harness/service.py:L961-L980, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/auto_harness/service.py:L880-L958, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/auto_harness/scheduler.py:L355-L358, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/auto_harness/service.py:L1808-L1809, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L16099-L16099, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/AutoHarness.md:L113-L113, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_auto_harness_service_lifecycle.py:L96-L113, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/auto_harness/test_gitcode_issue_runner.py:L134-L137, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/auto_harness/service.py:L1215-L1230, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L13664-L13677, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/auto_harness/service.py:L2292-L2310, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/auto_harness/task_store.py:L367-L406]
feature: "auto-harness"
entry_points: ["jiuwenswarm/agents/harness/common/auto_harness/service.py"]
source_globs: ["jiuwenswarm/agents/harness/common/auto_harness/service.py", "jiuwenswarm/agents/harness/common/auto_harness/*"]
---

# Auto Harness 评测优化：实现深读

[功能概览](feature-auto-harness.md) · [owner 入口](_index.md)

<!-- kb:depth feature=auto-harness facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3ed54ef3378de2b3fdb41fd41a541fae7e877eb6141b80c41c815f3bc08c965f -->
**模型回退配置与环境变量**
当请求未携带 Model 时，AutoHarnessService._build_model_from_env 依次读取环境变量 API_KEY、API_BASE（回退 BASE_URL）、MODEL_NAME（回退 MODEL）；API_KEY 或 MODEL_NAME 缺失时记录 warning 并返回 None，否则以 temperature=0.95 构造 Model。git 分支默认值方面：git_base_branch 未设置时默认 "develop"，且 pipeline_preference 为 EXTENDED_EVOLVE_PIPELINE 时强制 "develop"；git_remote 未设置时默认 "origin"。

来源：[jiuwenswarm/agents/harness/common/auto_harness/service.py:L961–L980](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/service.py#L961-L980), [jiuwenswarm/agents/harness/common/auto_harness/service.py:L880–L958](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/service.py#L880-L958)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/auto_harness/service.py","start":961,"end":980,"sha256":"2b4aea00c9530897916b3acd5717c1167c24de61f14990a1168df9ffce9fc7ca"},{"path":"jiuwenswarm/agents/harness/common/auto_harness/service.py","start":880,"end":958,"sha256":"61014a73abf4d5d8f7239efc2d7b13acc6fd742f12444f53151cd6c2b93895cd"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=auto-harness facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f25ac01ec87ec805b3fb1b427f605bdcdbeda0116f958e046e67903f7c3394b0 -->
**cancel_session_run：查无活跃运行返回 False，否则置 cancelled、停编排器（该调用无 try/except）与任务后局部返回 True**
适配器 interrupt(cancel) 在 _auto_harness_service 非空且 has_active_run(request.session_id) 为真时调用 cancel_session_run：置 active_run.cancelled=True，orchestrator 非空则调用其 cancel()（此处无异常保护），task 未 done 则 task.cancel()，最后局部返回 True；查无活跃运行时返回 False。

来源：[jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L13664–L13677](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L13664-L13677), [jiuwenswarm/agents/harness/common/auto_harness/service.py:L2292–L2310](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/service.py#L2292-L2310)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":13677,"path":"jiuwenswarm/server/runtime/agent_adapter/interface_deep.py","sha256":"c9f57b26694c1a4773b9d7721f17f83a197cf02ce9c8c9b05d70623d93eb2631","start":13664},{"end":2310,"path":"jiuwenswarm/agents/harness/common/auto_harness/service.py","sha256":"a5ea264852ea0ad5d70235cd075dcafd5da6d6960fd04a55c3f775a1f145ab16","start":2292}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=auto-harness facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5f60069c184fc30c40ef765cc722d19e69cb143617b8d97a105dd49bea3311be -->
**TaskStore.get_logs：默认参数、未知任务守卫与 log_type == "current" 分支返回**
签名为 get_logs(task_id, log_type, history_index=-1, offset=0, limit=500)；task 不存在时返回 {"error": "任务不存在", "task_id": ...}。可见的 log_type == "current" 分支要求 task 的 current_execution_id，缺失时返回 {"error": "当前无正在执行的日志", "task_id": ...}；存在时经 asyncio.to_thread 读取 _runs_dir/<task_id>/<current_execution_id>/log.json，返回 logs、execution_id、type="current"、total_lines、is_running（status == "running"）、has_more（offset + len(logs) < total_lines）。

来源：[jiuwenswarm/agents/harness/common/auto_harness/task_store.py:L367–L406](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/task_store.py#L367-L406)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":406,"path":"jiuwenswarm/agents/harness/common/auto_harness/task_store.py","sha256":"02757fb0e05d6373d1f79a86b7a4b8b391f2a1acdf48e96d017736ab4eaf1a38","start":367}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=auto-harness facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=eb78ffe8440482252b0733feb4566e260dfa024c505cfe38eff15ff61f2c6168 -->
**Scheduler/service/orchestrator/AgentServer 适配器的直接耦合**
Scheduler 经 self._service.run() 复用 service 执行（注释明示定时运行无交互频道，故传 auto_accept=True）；service 的 chunk 来源耦合 orchestrator.run_session_stream；AgentServer deep 适配器在 interface_deep.py:16099 调用同一 run()。

来源：[jiuwenswarm/agents/harness/common/auto_harness/scheduler.py:L355–L358](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/scheduler.py#L355-L358), [jiuwenswarm/agents/harness/common/auto_harness/service.py:L1808–L1809](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/service.py#L1808-L1809), [jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L16099–L16099](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L16099-L16099)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":358,"path":"jiuwenswarm/agents/harness/common/auto_harness/scheduler.py","sha256":"e939aef7edf2db0800e0d6b0bab42ad9749ce37140aa8fdb0e4f5aa2be155097","start":355},{"end":1809,"path":"jiuwenswarm/agents/harness/common/auto_harness/service.py","sha256":"5d298c8930873baa7cfd3c3eb5407da01ebbcf55f7f195cedce898922f71fc50","start":1808},{"end":16099,"path":"jiuwenswarm/server/runtime/agent_adapter/interface_deep.py","sha256":"7740b7819af6398e24f1dc478d48adaf2a3ac15779a56c0ab305ce0c3a7a5db7","start":16099}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=auto-harness facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8abf690033583b731cb97e304fa591667051f54094daab5df6639b818a5b244e -->
**request_cancellation：orchestrator.cancel() 抛 Exception 时仅记日志并继续取消 producer_task**
触发条件为 orchestrator 非 None 且其 cancel() 抛出 Exception；except 分支以 logger.exception 记录 "[AutoHarnessService] Orchestrator cancellation failed"，异常不向外传播，随后仍对未 done 的 producer_task 调用 cancel()。

来源：[jiuwenswarm/agents/harness/common/auto_harness/service.py:L1215–L1230](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/service.py#L1215-L1230)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1230,"path":"jiuwenswarm/agents/harness/common/auto_harness/service.py","sha256":"5fa485781b4fd44989674055c5a4e6ed82080f618b13371dfb816d642449bc32","start":1215}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=auto-harness facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c75ea698b87294f88a3125de531a89f264a0bd7504b93540852d28fcc23240ff -->
**定时运行固定 auto_accept=True：无人值守收益 vs 放弃人工确认（代价为推断）**
设计推断（非作者历史意图）：

定时运行因"无交互频道"固定 auto_accept=True（源码注释），文档称扩展包默认自动激活生效、无需用户手动确认；收益是无人值守自动闭环，代价是缺少人工确认关口——代价权衡为我的推断。

来源：[jiuwenswarm/agents/harness/common/auto_harness/scheduler.py:L355–L358](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/scheduler.py#L355-L358), [docs/zh/AutoHarness.md:L113–L113](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/AutoHarness.md#L113-L113)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":358,"path":"jiuwenswarm/agents/harness/common/auto_harness/scheduler.py","sha256":"e939aef7edf2db0800e0d6b0bab42ad9749ce37140aa8fdb0e4f5aa2be155097","start":355},{"end":113,"path":"docs/zh/AutoHarness.md","sha256":"67e4e64b7ebc0e2352c4343e17b55917de7b97866ede1f4d08d4d83daea3c9e9","start":113}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=auto-harness facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5d2a06f273316a9c030a7d3b75bf0ab82e632eaa56a24614df25e64d6b332227 -->
**lifecycle 与 issue-runner 单测的运行时断言（未在本次执行）**
@pytest.mark.asyncio 的 lifecycle 用例真实调用 service._settle_owned_run，断言 producer_task.done() 且 isinstance(producer_task.exception(), RuntimeError)；issue runner 用例断言 dry_run 时 service.queries==[]（这些是测试源码中的断言，本次未执行）。

来源：[tests/unit_tests/agentserver/test_auto_harness_service_lifecycle.py:L96–L113](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/test_auto_harness_service_lifecycle.py#L96-L113), [tests/unit_tests/auto_harness/test_gitcode_issue_runner.py:L134–L137](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/auto_harness/test_gitcode_issue_runner.py#L134-L137)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":113,"path":"tests/unit_tests/agentserver/test_auto_harness_service_lifecycle.py","sha256":"a7d731f5ec213b66884dcdb41dcf8cba48d4d1de7b212ad4a03430f13e479682","start":96},{"end":137,"path":"tests/unit_tests/auto_harness/test_gitcode_issue_runner.py","sha256":"3ecfb5659401342a1bd4bc10def9e3dcd6b87accf87760cae5c5d10f404f5dea","start":134}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
