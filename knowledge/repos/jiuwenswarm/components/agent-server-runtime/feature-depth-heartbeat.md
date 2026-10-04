---
title: "绑定会话的心跳续跑任务：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/heartbeat/proxy.py:L25-L66, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py:L71-L80, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py:L278-L380, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py:L452-L479, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_heartbeat_controller.py:L84-L90, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_heartbeat_store.py:L46-L58, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py:L453-L472, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py:L47-L48, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py:L453-L471, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/heartbeat/proxy.py:L22-L23, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/heartbeat/proxy.py:L133-L146, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/heartbeat/scheduler.py:L262-L304, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/heartbeat/scheduler.py:L314-L351, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/code/rails/heartbeat/scheduler.py:L605-L633]
feature: "heartbeat"
entry_points: ["jiuwenswarm/agents/harness/code/rails/heartbeat/models.py", "jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py", "jiuwenswarm/gateway/heartbeat/proxy.py"]
source_globs: ["jiuwenswarm/agents/harness/code/rails/heartbeat/models.py", "jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py", "jiuwenswarm/gateway/heartbeat/proxy.py"]
---

# 绑定会话的心跳续跑任务：实现深读

[功能概览](feature-heartbeat.md) · [owner 入口](_index.md)

<!-- kb:depth feature=heartbeat facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a4641059119698ec9d3d034a6f74d83580e9668a6d82411010a6a406c92a21ff -->
**网关代理的错误码到异常映射**
HeartbeatControllerProxy._request 把操作包装为 ReqMethod.HEARTBEAT_JOB 的 Message 经 agent_client 发送；响应失败时按 payload.code 映射异常：BAD_REQUEST→ValueError、FORBIDDEN→PermissionError、NOT_FOUND→KeyError、CONFLICT→RuntimeError、SERVICE_UNAVAILABLE→HeartbeatServiceUnavailableError。调用方需按这些异常类型处理失败。

来源：[jiuwenswarm/gateway/heartbeat/proxy.py:L25–L66](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/heartbeat/proxy.py#L25-L66)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/gateway/heartbeat/proxy.py","start":25,"end":66,"sha256":"3072ba086e6f9885e1798b209c991345dc4846bc70468183a31c26261e4f5b4b"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=heartbeat facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5f3e2b1aa893b23b1087f727ccea7e659acfadffb845b77fcbbb6e3e75ca3584 -->
**资源限制默认值与 config 覆盖**
controller 的 _DEFAULT_LIMITS 给出 max_active_jobs_per_session=5、max_active_jobs_global=100、min_interval_seconds=MIN_INTERVAL_SECONDS 等默认值，注释声明可被 config 覆盖；create_job 中 max_runs 缺省取 default_max_runs，source 缺省取 SOURCE_WEB_RPC（"web_rpc"）。

来源：[jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py:L71–L80](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py#L71-L80), [jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py:L278–L380](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py#L278-L380)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py","start":71,"end":80,"sha256":"d5ba92e0a7676926074cbe1efdbfc1d28f43836fef9d3466b90213f03d6a1a3e"},{"path":"jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py","start":278,"end":380,"sha256":"6bc2cf744cd9b34aadb82e20bb430ebfd5e4a88c017e6f4bf898e2a412fd8c16"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=heartbeat facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f00f807a18195e9465ba2f237e4a65df323cc0e5e6475b0c9a7575c4fff41e7b -->
**delete_job：无主任务抛 KeyError，有活跃 run 先取消，取消失败即中止删除**
`_owned_job` 返回 None 即抛 KeyError('job not found')；`run_state.current_run_id` 非空时先 `await _scheduler.cancel_run(job_id, pause_schedule=True)`，cancel_status=='failed' 则抛 RuntimeError 且不删除；否则 `_store.delete_job` 后 `await _scheduler.reload()`，本地返回 `{'deleted': bool(deleted)}`。

来源：[jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py:L452–L479](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py#L452-L479)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":479,"path":"jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py","sha256":"92c4c55dfe632609a931de6a46ff84d3a1f7b1fd696df9838333ecd64bb8f991","start":452}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=heartbeat facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ac2a00c294f08f05f81e5aaa041c33e4cdfb55eede031f83ec668aa110de3701 -->
**controller 守卫式联动 scheduler 与 store；网关代理仅持 agent_client 转发**
controller 导入 HeartbeatSchedulerService 与 HeartbeatJobStore；delete_job 仅在 run_state.current_run_id 非空时调 _scheduler.cancel_run(pause_schedule=True)，cancel_status=="failed" 即抛 RuntimeError 中止，否则 _store.delete_job 后再 _scheduler.reload()。网关 HeartbeatControllerProxy.__init__ 只保存 agent_client，delete_job 经 self._request("delete", channel_id="web") 转发。

来源：[jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py:L47–L48](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py#L47-L48), [jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py:L453–L471](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py#L453-L471), [jiuwenswarm/gateway/heartbeat/proxy.py:L22–L23](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/heartbeat/proxy.py#L22-L23), [jiuwenswarm/gateway/heartbeat/proxy.py:L133–L146](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/heartbeat/proxy.py#L133-L146)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":48,"path":"jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py","sha256":"40dfd04e2093eb82618c4bf2f5164e9f83a4be7a3a9458b535ae5e255de3fbc3","start":47},{"end":471,"path":"jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py","sha256":"600ac6d05ba0ca4782986747b2cbf2edc61d39d0c89ddb58013ffdc68d37a421","start":453},{"end":23,"path":"jiuwenswarm/gateway/heartbeat/proxy.py","sha256":"42a5a6b25ae090252341b9742d8d0ba18c5538474a28d79dafff0a4580c8682f","start":22},{"end":146,"path":"jiuwenswarm/gateway/heartbeat/proxy.py","sha256":"0d07aefdeeac5e92e827e0fe695f8f965c3489ea5c22c1cc93cbdc61a6b52cf5","start":133}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=heartbeat facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5bc113f9b1991642d59a14660f7ad88b061c4c71d8d5cfdcc3b0d169dc921769 -->
**delete_job：无主任务 KeyError；cancel_status=='failed' 时 RuntimeError 且跳过 store 删除**
delete_job 中 _owned_job 返回 None 抛 KeyError('job not found')；guard：current_run_id 非空且 cancel_result['cancel_status']=='failed' 时，在 self._store.delete_job 之前抛 RuntimeError("cannot delete heartbeat job while its active run could not be cancelled")，任务保留在 store。

来源：[jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py:L453–L472](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py#L453-L472)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":472,"path":"jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py","sha256":"176cd30e336ed1bbb10a4f3f7d0f4566207296bbe07861eeb2452c18af555d60","start":453}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=heartbeat facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9f1bfec4b4a45b706441c146f45b53681fe6cba249b14328cd9930f7d1375061 -->
**create 参数校验与新任务默认值有运行时断言测试**
`test_web_rpc_create_requires_channel_and_session` 用 pytest.raises 断言 `ctrl.create_job`(source='web_rpc') 缺 channel_id/session_id 分别抛 'channel_id is required'/'session_id is required'；`test_create_job_assigns_id_and_defaults` 断言 `store.create_job` 后 id 以 'hb_' 开头、status==STATUS_SCHEDULED、run_count==0、metadata['source']==SOURCE_AGENT_TOOL。

来源：[tests/unit_tests/agentserver/test_heartbeat_controller.py:L84–L90](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/test_heartbeat_controller.py#L84-L90), [tests/unit_tests/agentserver/test_heartbeat_store.py:L46–L58](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/test_heartbeat_store.py#L46-L58)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":90,"path":"tests/unit_tests/agentserver/test_heartbeat_controller.py","sha256":"2d3d0b6a766325d4f5cf42ab29bb45e9eb4925cb9ad92a216a527dfee42c3fef","start":84},{"end":58,"path":"tests/unit_tests/agentserver/test_heartbeat_store.py","sha256":"b734b37c7a67b7e8c4077dc6851cd9afc20b1af0adbca896e248f53ee2f29b82","start":46}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->

<!-- kb:depth feature=heartbeat facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8186e9ac75ef2ed7069df9374b806e9d6cc4ca59f092004f62a95766634eb6bf -->
**过会话/enabled/状态/queued/due 检查后未准入的到期任务：skip_and_reschedule 按 now 重算、不补跑**
设计推断（非作者历史意图）：

_handle_job_tick 经 suspended 会话、enabled、状态、queued-run 与 due 检查（L318–338）后，未准入任务才调用 skip_and_reschedule(reason="resource_admission_limit_exceeded")，next_run_at=compute_next_run(job,now)：interval 得 now+max(60,interval_seconds)，过期 once 得 None，cron 仅 next_cron_datetime 异常被捕获得 None（ZoneInfo 构造在 try 外）。推断：收益是默认 max_active_jobs_per_session=5、max_active_jobs_global=100 的准入控制，代价是该次到期执行被跳过且按 now 重算不补跑。

来源：[jiuwenswarm/agents/harness/code/rails/heartbeat/scheduler.py:L262–L304](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/heartbeat/scheduler.py#L262-L304), [jiuwenswarm/agents/harness/code/rails/heartbeat/scheduler.py:L314–L351](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/heartbeat/scheduler.py#L314-L351), [jiuwenswarm/agents/harness/code/rails/heartbeat/scheduler.py:L605–L633](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/heartbeat/scheduler.py#L605-L633)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":304,"path":"jiuwenswarm/agents/harness/code/rails/heartbeat/scheduler.py","sha256":"b8d4f6892e868383087162eab5eda29786177b5de813676042ee2f32784143b9","start":262},{"end":351,"path":"jiuwenswarm/agents/harness/code/rails/heartbeat/scheduler.py","sha256":"d0c33822617e2e94c40e71c77374ee98a83f4f45ddd09d8bd8b6ab620df7ab29","start":314},{"end":633,"path":"jiuwenswarm/agents/harness/code/rails/heartbeat/scheduler.py","sha256":"149087808604cdd4b9699f72ccd34da3b4711eb31fc5faf4eee0e87b1d0276ad","start":605}],"trace":[]} -->
<!-- /kb:depth -->
