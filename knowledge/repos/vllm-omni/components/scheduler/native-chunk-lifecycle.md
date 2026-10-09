---
title: "MRv2 native chunk 调度生命周期"
created: 2026-10-09
updated: 2026-10-09
type: guide
tags: [vllm-omni, components, scheduler]
sources:
  - "https://github.com/vllm-project/vllm-omni/pull/7781"
  - "https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/core/sched/omni_generation_scheduler.py"
  - "https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/core/sched/omni_scheduling_coordinator.py"
confidence: high
---

# MRv2 native chunk 调度生命周期

适用源码快照：`2e3c7fe2c171cd3429298094d175a64eacbdb341`。本页解释该版本的
共享 scheduler 实现，不更新 release baseline，也不替代后来版本的
[native admission 规则](rules-first-chunk-express.md)和
[stream terminal 规则](rules-stream-terminals.md)。connector 的存储、发送和异步输出所有权见
[共享 MRv2 runtime](../model-executor/mrv2-runtime.md)；模型帧语义见
[Qwen3-TTS pipeline](../../models/qwen3-tts/mrv2-pipeline.md)。

## flow

`OmniGenerationScheduler.schedule()` 先回收完成的 native chunk 执行槽，再调用
`_process_pending_omni_inputs()`；后者通过 `_consume_pending_connector_output()` 在调度线程
排空 inbox。该方法合并 metadata、ready、finished 和 full-payload receive 集合，过滤已取消
请求，然后调用 coordinator 更新 metadata 与 waiting/running 队列。生成 scheduler
选择当前可执行请求，`_wrap_omni_scheduler_output()` 将本步 terminal input ID 固定到输出，
再清除本步已消费的 ready/terminal 状态。

来源：[调度入口](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/core/sched/omni_generation_scheduler.py#L161-L175)、
[inbox 消费和 coordinator 调用](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/core/sched/omni_scheduler_mixin.py#L318-L373)、
[step 输出封装](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/core/sched/omni_scheduler_mixin.py#L554-L597)。

## api

`OmniConnectorOutput` 携带调度信号，后台 producer 只向 inbox 投递。
`get_scheduled_input_terminal_req_ids()` 取 terminal 集合与本步 scheduled ID 的交集；
`_input_execution_is_terminal()` 在 native 路径读取该 step 的 `input_terminal_req_ids`。
因此接收完成与当前执行完成是两个时间点：执行过程中到达的 EOF 不会把先前 chunk
追认为 terminal。legacy adapter 路径仍查询其 done 状态，不能混用两种判断。

来源：[terminal 快照](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/core/sched/omni_scheduling_coordinator.py#L401-L434)、
[执行完成判定](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/core/sched/omni_generation_scheduler.py#L60-L77)。

## configuration

native data plane 同时要求有效 V2 runner、`async_chunk` 和 pipeline 声明的
`supports_native_mrv2_data_plane`。选择来源和 profile 参数见
[MRv2 部署配置](../configuration/mrv2-profiles.md)。在该快照的 generation scheduler 中，
`retains_state_across_chunks` 决定 capacity 是按 chunk 复用还是为整个请求保留：
stateless codec 可归还执行槽，stateful codec 即使等待下一块仍占用 lifetime admission。
调度 `max_num_seqs` 是候选/执行容量，decoder graph bucket 是模型执行形状，两者不是同一参数。

来源：[native predicate](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/core/sched/omni_scheduling_coordinator.py#L23-L32)、
[chunk 与 lifetime admission](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/core/sched/omni_generation_scheduler.py#L112-L175)。

## dependencies

waiting 使用 vLLM `RequestQueue`，running 使用 Python list。coordinator 在两种容器中
分别调用 `remove_request()` 与 `remove()`，将缺输入请求放入对应暂存队列，恢复时保留
队列语义。coordinator 不执行 connector put/get；pending registration 通过 scheduler output
交给 runner。归还 native 执行槽也不释放模型请求 state 或 KV blocks；仍有 in-flight
token 的请求留在 running，避免 state 被提前复用。

来源：[pending registration](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/core/sched/omni_scheduling_coordinator.py#L69-L87)、
[queue 分派](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/core/sched/omni_scheduling_coordinator.py#L440-L488)、
[state 保留](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/core/sched/omni_generation_scheduler.py#L112-L133)。

## failure_modes

ready 事件可能晚于 request cleanup，故 inbox 消费时 metadata、`chunk_ready_req_ids`、
`chunk_finished_req_ids` 与 `stage_recv_req_ids` 都与 live requests 相交。running 和 restored waiting 两条 admission 路径都跳过
`num_in_flight_tokens > 0` 的 native 请求；重排不会清掉 `WAITING_FOR_CHUNK` 或 token
计数。generation 的空 prompt 不直接证明没有音频：若 terminal 输入还包含非空
`codes.audio`，它会用一个控制 token 调度一次；没有待处理 payload 才进入 finish。
该版本仍从 `code_predictor_codes` 构造 generation prompt，未实现通用 payload-native
readiness；不能把 pipeline capability 当作任意 payload key 已可调度的证明。

来源：[live ID 过滤](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/core/sched/omni_scheduler_mixin.py#L340-L373)、
[running 防重复](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/core/sched/omni_generation_scheduler.py#L190-L213)、
[waiting 与空尾块](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/core/sched/omni_generation_scheduler.py#L256-L285)、
[generation metadata](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/core/sched/omni_scheduling_coordinator.py#L385-L399)。

## tradeoffs

设计推断：stateless native chunk 归还执行槽，可让更多已就绪 stream 参与下一批，减少
等待输入请求对执行容量的占用；代价是 ready、in-flight、terminal 和模型 state 必须分开
维护。stateful codec 仍受保留容量约束，因此不能从 stateless 路径推导所有模型的并发收益。
源码提供调度机制，没有证明公平性、吞吐提升或 uninterrupted playback；这些需要固定
runner/profile、工作负载和硬件的测量。

推断依据：[capacity 分支](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/core/sched/omni_generation_scheduler.py#L242-L262)。

## validation

以下是该固定版本已检查的回归入口，本轮未执行 upstream CPU/GPU 测试：

- [ready inbox 回归](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/tests/core/sched/test_omni_scheduler_ready_inbox.py#L15-L38)：合并事件、过滤取消请求、一次消费。
- [queue 生命周期回归](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/tests/core/sched/test_omni_scheduling_coordinator.py#L102-L139)：native predicate、waiting 注册/就绪/terminal，以及非空 running list 的移除。
- [chunk admission 回归](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/tests/core/sched/test_generation_scheduler_restore.py#L122-L175)：native fixture 无新块不重执行、重排保留等待状态和计数；另一个 legacy adapter fixture 断言空 prompt 的非空 terminal codec payload 本步调度一个控制 token、不提前 finish，未验证跨步 native exactly-once。

这些定向断言不等于多 stage 压测、音质或吞吐验收。后续版本的 sender-only admission 与
empty-EOF receive gate 另由本页开头链接的当前规则约束，不把该历史快照外推为完整覆盖。
