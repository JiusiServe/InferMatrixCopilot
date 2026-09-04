---
title: "Diffusion output 与 multiprocess runtime 规则"
created: 2026-09-02
updated: 2026-09-04
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #5550", "PR #5864", "PR #5978", vllm_omni/diffusion/diffusion_engine.py, vllm_omni/diffusion/executor/multiproc_executor.py, vllm_omni/diffusion/inline_stage_diffusion_client.py, vllm_omni/diffusion/ipc.py, vllm_omni/diffusion/sched/request_scheduler.py, vllm_omni/diffusion/utils/media_utils.py, vllm_omni/diffusion/worker/diffusion_worker.py, tests/diffusion/test_async_output_worker.py, tests/diffusion/test_diffusion_engine.py, tests/diffusion/test_diffusion_engine_cleanup.py, tests/diffusion/test_diffusion_ipc.py, tests/diffusion/test_inline_stage_diffusion_client.py, tests/diffusion/test_ipc_async.py, tests/diffusion/test_multiproc_engine_concurrency.py, tests/diffusion/test_result_pump.py, tests/entrypoints/openai_api/test_video_server.py, "PR #6023", "PR #5983", "PR #4222", "PR #6094", "PR #6288"]
confidence: high
---

# Diffusion output 与 multiprocess runtime 规则

## DIFF-1d — async output 的 compute 与 output-ready 必须分成两个可观察阶段

- 触发：把 diffusion D2H/SHM packing 移到 worker 后台线程，或修改 result pump、`collective_rpc`、
  batch output split。
- 强制：GPU compute 完成只释放下一次 forward；最终输出必须等 side-stream event、D2H 和 SHM packing
  完成后再 resolve。每个 worker-owned result queue 由唯一 pump reader 分发，batch 结果按 request 映射
  拆分；step-mode 保留同步路径。
- 禁止：在 compute-done 时把未完成 device tensor 当最终 artifact；让多个线程同读一个 result queue；
  用同步 `.cpu()` 掩盖 stream ordering 或让下一 step 重写源 buffer。
- 验收：覆盖 compute-done、output-ready、RPC error、batch split、queue cleanup 与非 CUDA/step-mode
  fallback。^[PR #5864]

## DIFF-1g — 每个 worker result queue 必须有唯一 reader 与显式 SHM owner

- 触发：request-mode worker result queue、async pump、multi-rank reply 或 tensor/NumPy SHM serialization。
- 强制：每个 worker 创建独立 result queue，executor 为每个 queue 建唯一 pump；RPC/output future 按
  envelope ID 路由，DP reply 保留 rank tag。递归 pack/unpack 必须覆盖 tagged/RPC envelope、nested
  dict/list/tuple、tensor 与大于 1MB 的 non-object ndarray；reader copy 后 close+unlink segment。
- 禁止：多个 worker 共写一个 queue 后假设 reply 不冲突；pump 与同步 caller 同读；object ndarray
  进入 raw SHM；只释放顶层 handle 而泄漏 nested segment。
- 验收：真实 spawn workers 各建 queue，传 nested tensor/video/audio ndarray，验证 tag/order/dtype/value，
  所有 pump 停止、queue 关闭、SHM name 不再可 attach。当前测试覆盖成功 round-trip；partial pack、
  unpack/copy 异常时已创建 segment 的回收仍缺 fault-injection。^[PR #5864]

## DIFF-1h — request-mode shutdown 必须幂等、有界且按 engine→task/IPC 顺序完成

- 触发：worker async-output thread、executor process cleanup、inline client 或 orchestrator pre-mark shutdown。
- 强制：worker 用 sentinel 停 async thread，并证明 thread 已停止后才 teardown 它仍可能访问的
  model/queue/SHM；executor 以全局 deadline join 全部 workers，统一 terminate survivors，再 join
  pumps/fail futures。inline client 区分 shutting-down 与
  shutdown-complete，在 lock 内先 close engine 再等待 thread-pool；调用方复用 sampling params 时在 task
  启动前同步 clone。
- 禁止：把 orchestrator 的 pre-mark 当作 teardown 已完成；每 worker 单独耗完整 timeout；先等待可能
  阻塞在 engine RPC 的 executor 再 close engine；二次 shutdown 重复释放。
- 验收：normal、worker shutdown exception、premarked、concurrent/repeated shutdown、blocked RPC、async
  output active 与 forced termination 都验证无 live thread/process/queue/SHM，future 到达终态。目标常量
  为 worker 15s 全局 join、5s terminate grace、async thread 10s、pump 2s；async thread 超时仍存活时
  虽保留 result queue，却仍先调用 `worker.shutdown()`，model teardown 可能与 live output thread 竞态，
  且没有后续强制 thread/SHM/queue 回收证明。final 2×B300 rerun提供一次普通 TP2 与
  DLO DP2 clean exit，但不替代 fault matrix。^[PR #5864]

## DIFF-1j — Engine 构造失败必须释放已启动的 Executor

- 触发：`DiffusionEngine.__init__` 在 executor 已启动后初始化 Scheduler、runtime state、execute
  function 或 logging。
- 强制：任一步失败都 best-effort 关闭已赋值 Scheduler、shutdown executor，再原样重抛根因；
  cleanup 异常只能记录。此时同步状态可能尚未建立，不能调用完整 `close()`。
- 禁止：构造异常直接逃逸并遗留 worker/monitor/GPU allocation，或用 cleanup 异常遮蔽初始错误。
- 验收：注入 Scheduler initialization failure，断言 close/shutdown 各一次且异常 identity 不变；
  另覆盖 cleanup 自身失败不遮蔽根因。^[PR #5550]

## DIFF-2k — DLO AllGather DP wave 必须完整兼容或不可复用地 fail closed

- 触发：DLO+AllGather、DP>1 允许 concurrent request，或修改 multi-rank `execute_model` RPC。
- 强制：只在 DLO+AllGather+DP>1 放宽 single-request pipeline admission；preflight 复用完整
  `RequestBatchSamplingParamsKey`，另比较 canonical `extra_args` 并拒绝空 prompt。shape、CFG、denoise
  schedule、output count、LoRA 与任何 future control-flow 字段必须相同；prompt/token length 和
  seed/generator 可不同。multi-rank reply 按 `dp_rank` tag 排序，step mode 从
  `dp_rank * (TP*SP*PP*CFG)` 选择 replica primary result queue。
- 禁止：为凑 wave 静默改变用户 wait 配置；用 step count+extra_args 代替完整 key；partial collective
  timeout 后复用 process group。少于 DP 个 request 时 rank 以 `dp_rank % len(reqs)` 重复执行已有 request，
  只消费前 request-count 个排序输出；这是 correctness fallback 与额外计算，不得称为满 DP throughput。
- 验收：完整/partial wave、mismatch shape/CFG/steps/output/LoRA/extra_args、空 prompt、不同 seed/token
  length、rank tag 重排与 primary-rank topology 都覆盖；timeout 必须将 engine 标记失败、同步 shutdown
  并通知 failure callback。timeout 默认 600s 且在 import 时从 env 读取，不是 request deadline。final
  2×B300 evidence 覆盖 ordinary TP2 与 H3 DLO DP2 的错误 wave→同 engine recovery→无 active child；
  仍只绑定 eager+CUDNN exact topology，不能推广到一般 DP/SP 或替代 per-replica SP/mmap redesign。
  ^[PR #5864]

## DIFF-1i — AAC mux 必须显式标记输入时间零点

- 触发：修改共享 mux 的 audio-frame timestamp、codec/container 或 video API 输出。
- 强制：共享 `mux_video_audio_bytes()` 在构造 AAC frame 时设 `pts=0`、
  `time_base=1/sample_rate`，让 MP4 以负 priming timestamp 表达 encoder delay，
  避免把 delay 暴露成前导静音。这是共享 mux caller 的 blast radius，不是
  MiniMax H3 专属。
- 禁止：从负 AAC packet PTS 外推其他 codec/container、audio sample/duration/
  content、唇音同步或完整 A/V alignment。
- 验收：目标 focused test 解 mux 后断言第一个有 PTS 的 AAC packet `PTS<0`；
  样本和 A/V 对齐结论仍需独立的端到端波形/时序验收。^[PR #5978]

## DIFF-1q — request-mode async output 交付必须覆盖传输、竞态与生命周期

- 触发：修改 request-mode diffusion 的 async D2H/SHM output、`MessageQueue` 写入、batch split、result pump、future bookkeeping，或 worker 的 sleep/内存释放生命周期。
- 强制：per-request tensor view 的 IPC packing 必须按 `max(view_bytes, storage_bytes)` 判断并只把 view 内容放入 SHM；`execute_batch` 注册 split map 时必须在同一锁下接管早到的 batch output；`result_mq` 的 `COMPUTE_DONE` 与 `OUTPUT_READY` 写入必须串行化；result pump 必须先完成 SHM unpack，再在 `_futures_lock` 下原子 resolve waiter 或缓存 completed output；worker 执行 `sleep`/`handle_sleep_task` 和本地 sleep task 前必须等待 `drain_async_outputs()`，并在 `_ASYNC_OUTPUT_TIMEOUT` 超时日志中输出 executor bookkeeping。
- 禁止：按 view 大小判断而让共享 batch storage 被 pickle 重复发送；在 split map 建立前缓存一个无人消费的 batch-level output；让多个线程并发写单写者 `MessageQueue`；SHM unpack 期间释放 future 锁导致 waiter orphan；释放 device memory 时仍允许后台 D2H/SHM 线程读取源 tensor；把单 tensor storage-aware packing 当作 aggregate serialized message 已不会溢出的证明，也不得据此推断外部 HTTP 视频传输已优化。
- 验收：覆盖 per-request shared-storage wire-size regression、早到和晚到的 batch `OUTPUT_READY`、已有 waiter 与缓存 future 的原子 resolution、并发 result queue writer 无 overlap、pending output 的 drain/timeout 及 sleep-before-drain 顺序；同时验证 non-sleep RPC 不 drain、SHM unpack/error path、超时诊断状态和 worker shutdown cleanup。^[PR #6023]

## DIFF-1r — 共享 Future resolve 必须对取消竞态 fail-safe

- 触发：修改 diffusion result pump、共享 `_rpc_futures`/`_output_futures`、`asyncio.wait_for()` 超时、请求 abort 或 shutdown future cleanup。\n- 强制：共享 Future 在 `done()` 检查后仍必须通过 `try_set_result`/`try_set_exception` 解析，并在 helper 内捕获 `concurrent.futures.InvalidStateError`，丢弃取消或已完成 Future 的晚到结果/异常，使 singleton pump 继续运行；仅 freshly-created 且尚未共享的本地 Future 可直接解析。\n- 禁止：把 `not fut.done()` 与 `set_result()`/`set_exception()` 当作原子操作；在共享 Future 上保留未保护的 resolve 调用；让取消竞态异常逃逸并杀死 result pump，随后仍以健康检查通过推断任务会完成。\n- 验收：用 `done()` 固定返回 false 但实际已取消的 racy Future 覆盖 `COMPUTE_DONE`、`OUTPUT_READY`、batch split 与 shutdown cleanup，断言 pump 不抛 `InvalidStateError`、取消 Future 保持取消、同批健康 Future 仍完成，并回归相邻并发测试。\n^[PR #5983]

## DIFF-1s — 非媒体 diffusion 输出必须显式闭合 output type 与 post-process

- 触发：diffusion pipeline 产生 action 等非 image/video 输出，或修改 registry 中的 `final_output_type`、post-process hook 与 multiprocess 传递路径。
- 强制：topology 的 `final_output_type` 必须与 pipeline 实际产物一致；非媒体输出使用稳定的 `DiffusionOutput.output` key，并注册可跨 orchestrator multiprocess 边界解析的 module-level post-process callable；没有变换时显式使用 identity hook。
- 禁止：沿用 image 默认类型、用输出 ndarray 形状猜测语义、把 action 路由成 image/video，或把局部 closure 作为跨进程 post-process hook。
- 验收：registry 能解析 pipeline 与 post-process callable，callable 可被目标进程边界使用，最终 engine output 保留稳定 key，并由端到端测试断言 action shape、dtype 和有限性。^[PR #4222]

## DIFF-9a — 共享 PyAV 预构造帧 mux 必须闭合资源与音频时间零点

- 触发：修改共享 diffusion 的预构造 PyAV 视频帧 mux、可选音频 mux、container cleanup 或编码器异常传播。
- 强制：`mux_av_video_audio_bytes()` 必须在 context manager 内打开并配置 MP4 video/audio streams，消费 `Iterable[av.VideoFrame]` 后 flush video encoder；音频按 `fltp` 和 mono/stereo layout 构造，并以 `pts=0`、`time_base=1/sample_rate` 标记输入时间零点。成功和 generator、encoder、mux 异常都必须退出 context 关闭 container，同时原样传播原始错误。
- 禁止：在 generator 消费前或 context 外打开/使用 container；只在成功路径手工 close；吞掉帧生成或编码异常后静默改走其他 muxer；把 mock container cleanup 或单一 CPU 运行误认为完整跨硬件 A/V parity。
- 验收：测试覆盖预构造 `gbrp` 帧的 H.264 mux、无音频/mono/stereo 音频、AAC 首个有效 packet 的负 priming PTS、video flush 和 container close；让 frame generator 在中途抛错并断言 container 已关闭且异常 identity 保持，再用固定媒体输入执行 ffprobe 与完整 FFmpeg 解码。^[PR #6288]
