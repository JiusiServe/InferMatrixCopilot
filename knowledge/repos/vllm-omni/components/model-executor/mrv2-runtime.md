---
title: "MRV2 共享运行时与异步输出"
created: 2026-10-09
updated: 2026-10-09
type: guide
tags: [vllm-omni, components, model-executor]
sources: ["PR #7781", vllm_omni/worker_v2/omni_model_runner.py, vllm_omni/worker_v2/omni_ar_model_runner.py, vllm_omni/worker_v2/omni_generation_model_runner.py, vllm_omni/worker_v2/model_states/omni_model_state.py, vllm_omni/worker_v2/model_states/intermediate_buffer.py, vllm_omni/worker_v2/native_output_worker.py, vllm_omni/worker_v2/omni_data_plane.py, vllm_omni/worker_v2/delivery.py, vllm_omni/worker_v2/output_snapshot.py]
---

# MRV2 共享运行时与异步输出

本页解释 [PR #7781](https://github.com/vllm-project/vllm-omni/pull/7781) 的固定
head `2e3c7fe2c171cd3429298094d175a64eacbdb341` 中共享 `worker_v2` 的执行、
请求状态和输出交付。它是这个快照的功能说明，不替代索引里的已审计 main 清单，
也不表示其他模型已经完成 MRV2 验证。模型语义见
[Qwen3-TTS pipeline](../../models/qwen3-tts/mrv2-pipeline.md)，调度等待/恢复见
[native chunk 生命周期](../scheduler/native-chunk-lifecycle.md)，部署入口见
[MRV2 profiles](../configuration/mrv2-profiles.md)。

修改输出时以现有 [snapshot 规则](rules-output-snapshots.md) 和
[MRV2 output 规则](rules-mrv2-output-contracts.md) 为约束入口；本页说明数据关系，
不复制或重新定义规则。

## flow

`OmniGPUModelRunner._prepare_native_data_plane` 先接收本步调度结果：登记真实新请求
和 receiver，把自然完成 ID 交给 `request_terminal`，其余 finished ID 交给
`abort_requests`。warmup 请求不进入真实数据面。随后
`_sync_native_data_plane_payloads` 只为本步被调度且仍有 slot 的请求取出 payload，
写入中间 buffer。materialization/finalization 负责把已完成的 host token/payload
交给数据面；reservation 保持请求状态存活。
[源码：数据面准备与交付接口](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/worker_v2/omni_model_runner.py#L202-L276)

模型执行和输出交付拥有不同的寿命。`OmniAsyncOutput` 独立保存本步 request 切片
metadata，在 copy stream 上完成 D2H staging 并记录 event；deferred consumer
因而不会依赖下一步会改写的 batch metadata。
[源码：metadata 与 copy event](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/worker_v2/omni_ar_model_runner.py#L647-L747)

AR native materializer 通过单线程 FIFO 调用原始 `get_output`，把 host 数据放入数据面
队列；engine owner thread 消费 `NativeAsyncOutput` 时才读取 connector 通知。数据面
worker 按队列顺序调用 `complete_outputs`，等待 connector delivery 后释放 reservation；
所有 reservation 归零后自然 terminal 才可发送。调度侧怎样形成完成 ID 见
[native chunk 生命周期](../scheduler/native-chunk-lifecycle.md)。
[源码：materializer 与 owner-thread 消费](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/worker_v2/native_output_worker.py#L12-L99)、
[reservation 与 terminal fence](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/worker_v2/omni_data_plane.py#L249-L342)

## api

以下是 runner 内部协作接口，不是 OpenAI serving API；实现分别沿 flow、configuration
和 tradeoffs 的源码锚点读取。

| 接口 | 作用和数据归属 |
|---|---|
| `OmniIntermediateBuffer.add_request/gather/remove_request` | slot 保存请求字段；gather 按当前 batch mapping 排序；复用/释放同步维护 ID→slot。 |
| `update_gpu_tensor_rows` | 对 batch tensor 做一次 owned snapshot，再存每请求 row view。 |
| `update_owned_gpu_tensor_rows` | 接受生产者承诺之后不再改写的 tensor，直接共享 row view；view 保持 storage 存活。 |
| `reserve_outputs/complete_outputs/request_terminal` | 建立、完成和释放 deferred-output 生命周期；自然 terminal 等待已保留输出。 |
| `DeliveryTicket.wait/set_delivered/set_failed` | 单次 delivery 的完成接口；完成返回，失败/取消通过异常传播。 |
| `NativeAsyncOutput.get_output` | owner thread 消费最终结果/通知，缓存结果或异常，随后释放原 future/plane 引用。 |

共享扩展点按模型声明选择，不按 stage 名称或 architecture 白名单猜测：

- `init_omni_model_state` 只检查 `has_preprocess`、`has_postprocess`、
  `have_multimodal_outputs` 是否显式为 true；未声明则委托 upstream factory。
- `_returns_tuple` 决定 capture unwrap 与 FULL graph exclusion，stage 名称不参与判断。
- 有 `mtp` hook 的模型必须声明 string 或二元组 `mtp_output_key`；
  `mtp_disable_graph`、`mtp_graph_safe` 决定 wrapper 选择，没有共享 TTS output-key 默认值。
- generation 的 per-request list 约定长度为 `num_reqs`。payload builder 按请求位置逐项
  生成输出；非 dict payload 返回同样长度的 None 列表，保留 request cardinality。

对应 [state factory](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/worker_v2/model_states/__init__.py#L22-L43)、
[tuple 声明](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/worker_v2/omni_model_runner.py#L54-L81)、
[MTP 声明](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/worker_v2/model_states/omni_model_state.py#L193-L210) 和
[generation payload builder](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/worker_v2/omni_generation_model_runner.py#L542-L582)。
模型 hook、codec 字段和 MTP 采样含义归
[Qwen3-TTS pipeline](../../models/qwen3-tts/mrv2-pipeline.md)。

## configuration

数据面内部输出队列深度是 8，delivery timeout 默认 30 秒，shutdown timeout 默认 5 秒。
connector `extra.delivery_timeout_s` 可覆盖 delivery timeout，必须可转换为正数。
native materializer 容量取 `vllm_config.max_concurrent_batches`，缺省回落为 2；
仅用于具有 native data plane 且 TP=1 的 runner，多 rank executor 保留自己的消费和
reply-rank 所有权。runner 启动时拒绝 PP>1 与 prefill context parallel>1。
[源码：队列与 timeout](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/worker_v2/omni_data_plane.py#L69-L103)、
[materializer 条件与容量](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/worker_v2/omni_model_runner.py#L238-L251)、
[并行限制](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/worker_v2/omni_model_runner.py#L156-L167)

`model_runner`、pipeline capability、async-chunk 和 B2/B4 graph/batch profiles
由 [MRV2 profiles](../configuration/mrv2-profiles.md) 解释。模型专有的
`gpu_resident_buffer_keys` 决定哪些中间 tensor 留在设备：常规 update 对这些 key
做 detach/clone，其他 tensor 转为 contiguous CPU 数据；嵌套 key 可用二元组指定。
[源码：GPU key 与存储](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/worker_v2/model_states/intermediate_buffer.py#L106-L160)

## dependencies

共享 runner 继承 vLLM 原生 `GPUModelRunner`，使用其 `SchedulerOutput`、
`InputBatch`、sampler 和 graph descriptor；`OmniModelState` 继承 `DefaultModelState`，
配合 `RequestState`。这些是 upstream 内部接口，迁移版本需要核对符号、签名和状态寿命；
本快照的 import/继承关系不能证明任意 vLLM 版本兼容。
[源码：runner 依赖](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/worker_v2/omni_model_runner.py#L11-L59)、
[state 依赖](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/worker_v2/model_states/omni_model_state.py#L22-L87)

传输侧复用 `OmniConnectorModelRunnerMixin`，MRV2 在其上增加 request snapshot、
FIFO publication、delivery ticket 与发送锁；connector 负责实际 put/recv。GPU 输出
依赖 PyTorch stream/event 建立 producer→D2H→consumer 顺序。
`PackedOutputSnapshot` 按 dtype/device 合并 tensor leaves，保留 pytree/shape，
每个输出拥有自己的 host slab；异常 layout 或 quantized tensor 不进入打包。
[源码：数据面继承与初始化](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/worker_v2/omni_data_plane.py#L76-L91)、
[snapshot 打包](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/worker_v2/output_snapshot.py#L15-L78)

## failure_modes

取消可能早于模型 admission：`abort_requests` 对尚无 native request state 的 ID
仍清 receiver；对已登记请求清掉 reservations/pending terminal 后发送终止标记。
已提交的数据先占住 send lock，abort 无法抢到其前面。自然完成走 reservation fence；
用 abort 替代会改变交付语义。
[源码：取消与提交排序](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/worker_v2/omni_data_plane.py#L284-L342)

permanent delivery failure 或 timeout 会 quarantine 整个 manager，让所有未完成
票据失败并拒绝新票据；重复 terminal transition 返回 false。`wait` 使用 monotonic
期限，返回代表 delivery 完成，失败/取消抛出已记录异常。close 先尝试 drain，再在
finally 中关闭 output worker 和 connector；connector close 与 I/O 线程并发，join
受 deadline 限制。超时仍存活的线程会报错，这不保证 backend 阻塞调用已经物理取消。
[源码：ticket 与 quarantine](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/worker_v2/delivery.py#L34-L218)、
[有界关闭](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/worker_v2/omni_data_plane.py#L533-L604)

GPU row ownership 的成本见 [tradeoffs](#tradeoffs)。payload 里选出的 request list
元素拥有局部轴；frame 数碰巧等于 batch/padded token 数时，也不能再次按 token span
切片。错误的请求归属会把 reference codes 截短或混入其他请求。
[源码：request-local 切片](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/worker_v2/omni_ar_model_runner.py#L531-L578)

## tradeoffs

以下是由实现推导的取舍，不是性能测量结论。单线程 FIFO 保留 publication 顺序，
但慢 consumer 会产生队首等待；容量 semaphore 和有界队列把背压传回 submit/enqueue。
后台 materialization 可以重叠 CPU/D2H 工作，同时增加 future、host snapshot 和 request
reservation 的存活时间。quarantine 在交付顺序不确定时停止接收，影响整个 manager。
FIFO/quarantine 的实现见 [flow](#flow) 和 [failure_modes](#failure_modes)；
[enqueue 背压](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/worker_v2/omni_data_plane.py#L163-L185) 持续检查后台错误。

GPU-resident 状态减少反复搬运，但 owned storage 存活到请求 row 替换或 slot 释放。
owned marker 省去第二次 snapshot，也把“之后不再写入”的责任交给生产者；普通 tensor
继续复制，错误的请求轴长度显式拒绝。AR snapshot ring 复用 slot 前等待上次 copy event，
避免下一次 graph replay 覆盖尚未消费的数据。
[依据：buffer 生命周期](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/worker_v2/model_states/intermediate_buffer.py#L69-L104)、
[GPU row ownership](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/worker_v2/model_states/intermediate_buffer.py#L211-L265)、
[ring 复用](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/worker_v2/omni_ar_model_runner.py#L269-L292)

本次提取没有重跑 benchmark，runner 对吞吐或首音延迟的独立贡献仍未知。
PR 描述的历史 workload/profile 数字不能归因为单一共享 runner 改动；模型缓存、graph
shapes、部署拓扑和性能证据边界见 [Qwen3-TTS pipeline](../../models/qwen3-tts/mrv2-pipeline.md)
与 [MRV2 profiles](../configuration/mrv2-profiles.md)。

## validation

本页对固定 head 的源码和以下测试实现做了静态核验；本次知识提取没有执行 upstream
pytest、CUDA graph replay、真实 connector 故障注入或 benchmark。存在测试入口只表示
合同有可检查的用例，不表示在本次环境中通过。

| 验证目标 | 固定快照的测试入口与断言 |
|---|---|
| terminal、abort 与 deferred output | [`test_omni_data_plane.py` L185–244](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/tests/worker_v2/test_omni_data_plane.py#L185-L244)：自然 terminal 等 reservation、stale output 丢弃、abort 不越过已提交 send。 |
| transport failure、owner thread 与 admission 前取消 | [`test_omni_data_plane.py` L294–481](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/tests/worker_v2/test_omni_data_plane.py#L294-L481)：quarantine、timeout、取消、有界关闭、FIFO、thread affinity、错误缓存、TP gate 和 receiver-only cleanup。 |
| GPU row ownership 与 reorder | [`test_omni_model_state.py` L217–257](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/tests/worker_v2/test_omni_model_state.py#L217-L257)：owned/borrowed storage 地址、最后 token 与请求行映射。 |
| 跨步 snapshot 与 request-local 轴 | [`test_omni_ar_model_runner.py` L129–253](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/tests/worker_v2/test_omni_ar_model_runner.py#L129-L253)：storage 后续改写隔离、slot 上界与 mixed/padded batch 的 reference frame 不重切。 |

声明式 dispatch 还有 `test_capture_contract_uses_model_declaration`、
`test_init_model_state_factory_dispatches_omni_only` 和
`test_mtp_requires_model_declared_output_key` 用例。调度/profile 验证分别由
[native chunk 生命周期](../scheduler/native-chunk-lifecycle.md#validation) 和
[MRV2 profiles](../configuration/mrv2-profiles.md#validation) 维护；实际音频正确性、
continuity 与质量验证见 [Qwen3-TTS pipeline](../../models/qwen3-tts/mrv2-pipeline.md#validation)。
