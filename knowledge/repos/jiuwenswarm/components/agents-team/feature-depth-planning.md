---
title: "任务规划与 Todo：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py:L86-L89, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py:L249-L261, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py:L426-L431, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py:L1-L84, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py:L91-L154, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py:L156-L169, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py:L104-L115, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py:L91-L115, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py:L234-L238, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agents/harness/code/test_code_task_planning_rail.py:L143-L210, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agents/harness/code/test_code_task_planning_rail.py:L558-L589]
feature: "planning"
entry_points: ["jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py"]
source_globs: ["jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py", "jiuwenswarm/agents/harness/common/*"]
---

# 任务规划与 Todo：实现深读

[功能概览](feature-planning.md) · [owner 入口](_index.md)

<!-- kb:depth feature=planning facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=96f05c2c56b897f3a9df0c13e3098acb5979ab2474abac508c1e5b69e81d2f64 -->
**用户消息进入时恢复 task_reminder 附件的调用链**
用户消息到达后，CodeTaskPlanningRail.on_user_message 调用 _restore_task_reminder_attachment，后者经 _session_id 取会话标识，再调用 _task_reminder_lock 获取该会话的 asyncio.Lock，确保恢复与节奏变更互斥；锁在 WeakValueDictionary 中按 session_id 惰性创建。

调用路径：`jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py`（`CodeTaskPlanningRail.on_user_message`） → `jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py`（`CodeTaskPlanningRail._restore_task_reminder_attachment`） → `jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py`（`CodeTaskPlanningRail._task_reminder_lock`）

来源：[jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py:L86–L89](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py#L86-L89), [jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py:L249–L261](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py#L249-L261), [jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py:L426–L431](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py#L426-L431)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py","start":86,"end":89,"sha256":"f144d1004c650a948a4c876a516455d124cae0efba22e067830c768be7cefc8d"},{"path":"jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py","start":249,"end":261,"sha256":"629403dd874259f6f4fd1558d599e49f3db63c0d61458e847b3d6431e4906d99"},{"path":"jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py","start":426,"end":431,"sha256":"a8b3c26608ed6be4801b59cd9bfc8805b36d9a9f3565743b44beef62b6e7e4ce"}],"trace":[{"path":"jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py","symbol":"CodeTaskPlanningRail.on_user_message","start":86,"end":89},{"path":"jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py","symbol":"CodeTaskPlanningRail._restore_task_reminder_attachment","start":249,"end":261},{"path":"jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py","symbol":"CodeTaskPlanningRail._task_reminder_lock","start":426,"end":431}]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=planning facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0283b1de7bc1a55fa2dffa38b7739e22772749ae21331c5935b7f22c36cc3f71 -->
**提醒节奏构造参数默认 10/10 轮，会话数下限为 1**
构造参数 task_reminder_turns_since_management 与 task_reminder_turns_between_reminders 默认取常量 _TASK_REMINDER_TURNS_SINCE_MANAGEMENT=10 与 _TASK_REMINDER_TURNS_BETWEEN_REMINDERS=10；max_tracked_task_reminder_sessions 默认 1000 且经 max(1, ...) 取下限。生效条件是两个计数同时达到阈值才追加一次提醒，并把 turns_since_task_reminder 清零。

来源：[jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py:L1–L84](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py#L1-L84), [jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py:L91–L154](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py#L91-L154)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py","start":1,"end":84,"sha256":"cc04584af3b86200c1109c9993bb53f9f0fd69996b252fd3fe658c2f8357ef91"},{"path":"jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py","start":91,"end":154,"sha256":"b5d700641ca7794d2f763e55dc6e51c9d53e83bd9a8f73336d91a81ea02de50a"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=planning facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f1d25b0e2fd92982c8882409be4a1c0acac64f93b9fc5e1f1775fef3beb35daf -->
**继承 openjiuwen TaskPlanningRail 并复用 CodeTodo* 工具与提示附件管理器**
CodeTaskPlanningRail 继承 openjiuwen.harness.rails.task_planning_rail 的 TaskPlanningRail（构造先 super().__init__，after_tool_call 先调 super()），并从 jiuwenswarm 的 code_todo_tools 导入 CodeTodoCreate/Get/List/Modify 四个工具类用于注册。提醒附件经 agent.prompt_attachment_manager.add_section 写入，依赖 PromptAttachment/PromptAttachmentKind 等平台附件抽象。

来源：[jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py:L1–L84](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py#L1-L84), [jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py:L156–L169](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py#L156-L169), [jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py:L104–L115](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py#L104-L115)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py","start":1,"end":84,"sha256":"cc04584af3b86200c1109c9993bb53f9f0fd69996b252fd3fe658c2f8357ef91"},{"path":"jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py","start":156,"end":169,"sha256":"4c25db02fa74b21fb733be3509771e1e4fc626a00ce4b64206a544e22708edb1"},{"path":"jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py","start":104,"end":115,"sha256":"04d08937086f6b6f315e50ab1c92aea0d25c005b28077e647f02fe893ba42c6b"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=planning facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2eb1b97c72f2cc6bee50fdce9545d761b289c291526e460b62a61a37b34f01c0 -->
**缺少会话或附件管理器时静默跳过提醒逻辑**
before_model_call 在 session_id 为空、agent 无 prompt_attachment_manager 或找不到 todo 工具时直接 return，不追加提醒；_session_id 对没有 get_session_id 方法的 session 返回 None。同一会话的恢复与计数变更由 _task_reminder_lock 的 asyncio.Lock 串行化，锁对象经 WeakValueDictionary 惰性创建。

来源：[jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py:L91–L115](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py#L91-L115), [jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py:L234–L238](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py#L234-L238), [jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py:L426–L431](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py#L426-L431)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py","start":91,"end":115,"sha256":"2ec1213c859ce81aacfc92f3d10e4d96d435fa28933bd37868e3df99b91e6df7"},{"path":"jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py","start":234,"end":238,"sha256":"de19f0d587774bafa703bb470b616b49c118c69e3cc5ec577b9e6d88e095da87"},{"path":"jiuwenswarm/agents/harness/code/rails/code_task_planning_rail.py","start":426,"end":431,"sha256":"a8b3c26608ed6be4801b59cd9bfc8805b36d9a9f3565743b44beef62b6e7e4ce"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=planning facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f8ad5f4555c18c71f3ea30b1f41d08b2e742b4ec8b6e28129305b62220557b58 -->
**节奏投递与并发串行化的测试断言**
tests/unit_tests/agents/harness/code/test_code_task_planning_rail.py::test_code_task_planning_rail_injects_one_attachment_per_reminder_period 断言：该用例配置下连续 9 次 before_model_call 后 sync_to_context 均返回 None，第 10 次投递唯一 todo_reminder 附件（metadata["delivery_sequence"]==1，内容含 "todo_list to read the latest task state" 且不含具体 todo 项文本），再 9 轮后投递 delivery_sequence==2 的第二条且历史消息均不含 "no longer active"。test_code_task_planning_rail_serializes_overlapping_session_updates 用延迟的 add_section 断言并发两次 before_model_call 仅产出一条 delivery_sequence==1 的提醒且 state.turns_since_task_reminder==1，覆盖会话锁串行化。

来源：[tests/unit_tests/agents/harness/code/test_code_task_planning_rail.py:L143–L210](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agents/harness/code/test_code_task_planning_rail.py#L143-L210), [tests/unit_tests/agents/harness/code/test_code_task_planning_rail.py:L558–L589](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agents/harness/code/test_code_task_planning_rail.py#L558-L589)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":210,"path":"tests/unit_tests/agents/harness/code/test_code_task_planning_rail.py","sha256":"cc9fbef285bda53318999694df4c1006d02452588d8f639970510ffe413511b2","start":143},{"end":589,"path":"tests/unit_tests/agents/harness/code/test_code_task_planning_rail.py","sha256":"45a235755b3f0981a20bf54cc415b8425ef49a691db35e5397a9c95d80fcc15d","start":558}],"trace":[]} -->
<!-- /kb:depth -->
