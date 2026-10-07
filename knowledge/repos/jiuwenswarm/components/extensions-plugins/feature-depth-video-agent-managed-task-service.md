---
title: "Voice/Video Duplex Managed Agent Task Service (Durable Queue, Concurrency, Uncertainty Semantics)：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/video_duplex/backend/tasks/service.py:L183-L210, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/video_duplex/backend/tasks/service.py:L491-L533, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/video_duplex/tests/backend/test_managed_tasks.py:L69-L84, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/video_duplex/backend/tasks/service.py:L79-L113, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/video_duplex/backend/task_adapter.py:L283-L293, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/video_duplex/backend/tasks/service.py:L582-L591]
feature: "video-agent-managed-task-service"
entry_points: ["jiuwenswarm/extensions/video_duplex/backend/tasks/service.py"]
source_globs: ["jiuwenswarm/extensions/video_duplex/backend/tasks/service.py", "jiuwenswarm/extensions/video_duplex/backend/tasks/rail.py"]
---

# Voice/Video Duplex Managed Agent Task Service (Durable Queue, Concurrency, Uncertainty Semantics)：实现深读

[功能概览](feature-video-agent-managed-task-service.md) · [owner 入口](_index.md)

<!-- kb:depth feature=video-agent-managed-task-service facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=54c1ac51db2c09d27cdeb6664e0a1a3dc07ad135afc05b07b4bc193fb6be9e48 -->
**kick() dispatches queued tasks up to concurrency after an immediate transaction snapshot**
When started and not closed, kick() reads all tasks in one store transaction, collects active ones (running/cancelling/unknown/waiting_user or already having a worker), then iterates tasks by position: once the count of active tasks that are not unknown and not settled waiting_user reaches self.concurrency it breaks; queued tasks not already in self.workers and passing _ready get an asyncio.create_task(self._drain(id)) worker registered in self.workers with a _worker_done callback.

来源：[jiuwenswarm/extensions/video_duplex/backend/tasks/service.py:L79–L113](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/tasks/service.py#L79-L113)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":113,"path":"jiuwenswarm/extensions/video_duplex/backend/tasks/service.py","sha256":"e8ed96546023b7cce71570bad986ba87dea9cb3f238c400655720e6f74ef6f02","start":79}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=video-agent-managed-task-service facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c3fea7c9a1c326fb2d4e8495b69f16ba8a434371ec46b5f8d014a84070870067 -->
**submit input contract: strict ValueError validation before persistence**
submit(owner, session, command_id, instruction, request=None) requires a string owner, non-empty session, non-blank instruction ≤16000 chars, boolean independent, and depends_on/resources lists ≤32 entries of non-blank strings ≤256 chars; violations raise ValueError.

来源：[jiuwenswarm/extensions/video_duplex/backend/tasks/service.py:L183–L210](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/tasks/service.py#L183-L210)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":210,"path":"jiuwenswarm/extensions/video_duplex/backend/tasks/service.py","sha256":"e2144c55b22a7e4e401723d4918edfb872da395a03603e3f6dcdbc0e11ecfcc6","start":183}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=video-agent-managed-task-service facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cde105d3527061ca736f81da35d661054a4261532b48c6e294aa27fd05e39c71 -->
**VideoSearchManager.service lazily builds TaskService with self.concurrency and a derived notification_timeout**
On first access the service property constructs TaskService(TaskStore(self.path or task_database()), AgentTaskExecutor(...), on_change=self.changed, concurrency=self.concurrency, notification_timeout=AGENT_QUERY_TIMEOUT + 2 * EVENT_SEND_TIMEOUT + 1), caching it in self._service. The shown lines do not establish defaults for self.concurrency or the timeout constants.

来源：[jiuwenswarm/extensions/video_duplex/backend/task_adapter.py:L283–L293](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/task_adapter.py#L283-L293)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":293,"path":"jiuwenswarm/extensions/video_duplex/backend/task_adapter.py","sha256":"6030ba762b730a3dadf3c6e411a58a11bf0ac27a222a93cc5ba0cf3e5f5eb317","start":283}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=video-agent-managed-task-service facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5c30753555304e36aab562e657b77fb3a160d0da3cc9454e0dc6b5d59d6ea413 -->
**answer() rejects stale questions and marks failed executor answers unknown**
answer raises ValueError("Question is no longer pending for this task") unless status is waiting_user with a matching pending interaction id; if executor.answer throws, it sets status="unknown" with the error (only while still running with same request_id) and re-raises.

来源：[jiuwenswarm/extensions/video_duplex/backend/tasks/service.py:L491–L533](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/tasks/service.py#L491-L533)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":533,"path":"jiuwenswarm/extensions/video_duplex/backend/tasks/service.py","sha256":"936bb6541c664ac48bf7b3a86557e864c53d4bc483bdcd3c850a83d276697864","start":491}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=video-agent-managed-task-service facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4ca262608d7f2a15f3e852d8003551a7187e36b2ed10caf04b9ee4fe776fc150 -->
**Latest-snapshot-only notifications avoid client backpressure at the cost of coalescing updates**
设计推断（非作者历史意图）：

_notify stores only the newest task snapshot per task id (pending_notifications[key] = task) and runs a single sender task per key; the comment states slow clients must not backpressure agent output or grow an unbounded queue. Inferred cost: intermediate snapshots between sends are overwritten, so a client may never see them.

来源：[jiuwenswarm/extensions/video_duplex/backend/tasks/service.py:L582–L591](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/tasks/service.py#L582-L591)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":591,"path":"jiuwenswarm/extensions/video_duplex/backend/tasks/service.py","sha256":"9be1ed8da478b9c1d7c12b9d2744badffe94f7c616175ad2e6f3ef80f6707bd6","start":582}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=video-agent-managed-task-service facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bb697419a83c7a62e473ba8d511a8cd56f63b06f45481cb8ec3ebe2d0a31cff9 -->
**Runtime test: retry dedup, conflict ValueError, owner/session scoping**
test_retry_conflict_scope_and_cancel_before_dispatch asserts submit with the same command_id and text returns the same id, differing text raises ValueError, wrong owner/session get/cancel raise ValueError, and cancel before dispatch never reaches the executor. NOT EXECUTED here.

来源：[jiuwenswarm/extensions/video_duplex/tests/backend/test_managed_tasks.py:L69–L84](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/tests/backend/test_managed_tasks.py#L69-L84)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":84,"path":"jiuwenswarm/extensions/video_duplex/tests/backend/test_managed_tasks.py","sha256":"4c21d515edfb0e9328504412a8dc50e8435ca34695929a2beb0f3f46b13a711b","start":69}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
