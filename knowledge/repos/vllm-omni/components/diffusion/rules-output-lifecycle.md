---
title: "Diffusion output 与 multiprocess runtime 规则"
created: 2026-09-02
updated: 2026-09-26
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #5550", "PR #5864", "PR #5885", "PR #5978", "PR #6750", vllm_omni/diffusion/diffusion_engine.py, vllm_omni/diffusion/executor/multiproc_executor.py, vllm_omni/diffusion/inline_stage_diffusion_client.py, vllm_omni/diffusion/io_support.py, vllm_omni/diffusion/model_metadata.py, vllm_omni/diffusion/output_formatter.py, vllm_omni/diffusion/ipc.py, vllm_omni/diffusion/sched/request_scheduler.py, vllm_omni/diffusion/stage_diffusion_proc.py, vllm_omni/diffusion/utils/media_utils.py, vllm_omni/diffusion/worker/diffusion_worker.py, tests/diffusion/test_async_output_timeout.py, tests/diffusion/test_async_output_worker.py, tests/diffusion/test_diffusion_engine.py, tests/diffusion/test_diffusion_engine_cleanup.py, tests/diffusion/test_diffusion_ipc.py, tests/diffusion/test_inline_stage_diffusion_client.py, tests/diffusion/test_ipc_async.py, tests/diffusion/test_multiproc_engine_concurrency.py, tests/diffusion/test_result_pump.py, tests/diffusion/test_stage_diffusion_proc.py, tests/entrypoints/openai_api/test_video_server.py, "PR #6023", "PR #5983", "PR #4222", "PR #6094", "PR #6255", "PR #6288", "PR #6308", "PR #6499", "PR #6749", "PR #6847", "PR #6953", vllm_omni/diffusion/data.py, vllm_omni/diffusion/registry.py, vllm_omni/diffusion/models/diffusers_adapter/pipeline_utils.py, tests/diffusion/test_diffusion_output_formatter.py, tests/diffusion/test_diffusion_plugin_hooks.py, tests/entrypoints/openai_api/test_video_pipeline_capability.py, "PR #6294", "PR #6615", "PR #7126", "PR #7198", "PR #7986"]
confidence: high
---

# Diffusion output 与 multiprocess runtime 规则

## DIFF-1aa — Diffusers execution backend 不得冒充 native checkpoint identity

- 触发：修改 `diffusion_load_format`、custom pipeline 选择、checkpoint `model_class_name`、
  pre/post-process hook、request batching 能力或 frame interpolation。
- 强制：`uses_diffusers_adapter()` 只表示实际 execution backend；存在
  `custom_pipeline_args` 时 custom pipeline 优先并令其为 false，即使 load format 是 Diffusers。
  checkpoint 的 native `model_class_name` 继续承载 modality/capability metadata，但 effective
  Diffusers adapter 不运行 native pre/post hooks。batch capability 必须从实际 executor 派生：先
  custom pipeline，再 `DiffusersAdapterPipeline`，否则才查 native class。Diffusers adapter 收到
  frame interpolation 必须 fail fast，因为它交付的 frame 已完成 post-process。
- 禁止：从 checkpoint metadata 或 load format 单独推导 execution backend、native hooks 或 batching；
  custom pipeline 已接管时仍套 adapter hook；对 adapter output 静默二次 interpolation。
- 验收：组合覆盖 native、Diffusers adapter、Diffusers load format + custom pipeline 三类配置，断言
  class identity 保留、hook 选择和 batch capability 跟随实际 executor；另验证所有 Diffusers pipeline
  对 interpolation 抛出明确错误。PR #6749 的自动化测试覆盖这些选择边界，但不证明任意第三方
  custom pipeline 或未来 Diffusers 版本兼容。^[PR #6749]

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
- 强制：per-request tensor view 的 IPC packing 必须按 `max(view_bytes, storage_bytes)` 判断并只把 view 内容放入 SHM；`execute_batch` 注册 split map 时必须在同一锁下接管早到的 batch output；`result_mq` 的 `COMPUTE_DONE` 与 `OUTPUT_READY` 写入必须串行化；result pump 必须先完成 SHM unpack，再在 `_futures_lock` 下原子 resolve waiter 或缓存 completed output；worker 执行 `sleep`/`handle_sleep_task` 和本地 sleep task 前必须等待 `drain_async_outputs()`。两个 `DiffusionEngine` wait 路径必须逐次解析 `VLLM_OMNI_ASYNC_OUTPUT_TIMEOUT`：正数 float 可覆盖 600s 默认值；无效值告警后回退默认值；超时日志必须给出可调的变量名与 executor bookkeeping。
- 禁止：按 view 大小判断而让共享 batch storage 被 pickle 重复发送；在 split map 建立前缓存一个无人消费的 batch-level output；让多个线程并发写单写者 `MessageQueue`；SHM unpack 期间释放 future 锁导致 waiter orphan；释放 device memory 时仍允许后台 D2H/SHM 线程读取源 tensor；把单 tensor storage-aware packing 当作 aggregate serialized message 已不会溢出的证明，也不得据此推断外部 HTTP 视频传输已优化；不得在 request path 因无效 timeout 环境值抛出异常，也不得只修改其中一个 wait 路径。
- 验收：覆盖 per-request shared-storage wire-size regression、早到和晚到的 batch `OUTPUT_READY`、已有 waiter 与缓存 future 的原子 resolution、并发 result queue writer 无 overlap、pending output 的 drain/timeout 及 sleep-before-drain 顺序；同时验证 non-sleep RPC 不 drain、SHM unpack/error path、超时诊断状态和 worker shutdown cleanup，以及两个 wait 路径的默认值、正数 integer/float override、逐次重读与非数/非正值的 warning+fallback。^[PR #6023] ^[PR #6255]

## DIFF-1r — 共享 Future resolve 必须对取消竞态 fail-safe

- 触发：修改 diffusion result pump、共享 `_rpc_futures`/`_output_futures`、`asyncio.wait_for()` 超时、请求 abort 或 shutdown future cleanup。\n- 强制：共享 Future 在 `done()` 检查后仍必须通过 `try_set_result`/`try_set_exception` 解析，并在 helper 内捕获 `concurrent.futures.InvalidStateError`，丢弃取消或已完成 Future 的晚到结果/异常，使 singleton pump 继续运行；仅 freshly-created 且尚未共享的本地 Future 可直接解析。\n- 禁止：把 `not fut.done()` 与 `set_result()`/`set_exception()` 当作原子操作；在共享 Future 上保留未保护的 resolve 调用；让取消竞态异常逃逸并杀死 result pump，随后仍以健康检查通过推断任务会完成。\n- 验收：用 `done()` 固定返回 false 但实际已取消的 racy Future 覆盖 `COMPUTE_DONE`、`OUTPUT_READY`、batch split 与 shutdown cleanup，断言 pump 不抛 `InvalidStateError`、取消 Future 保持取消、同批健康 Future 仍完成，并回归相邻并发测试。\n^[PR #5983]

## DIFF-1ab — spawned StageDiffusionProc 必须在 engine 前重载通用插件

- 触发：修改 `StageDiffusionProc.run_diffusion_proc`、spawned diffusion engine startup 或 general plugin loader。
- 强制：child 先安装 parent-death signal 与 SIGTERM/SIGINT handlers，再 `load_omni_general_plugins()`，最后构造 engine/proc；spawn fresh interpreter 不继承 parent plugin side effects。
- 禁止：在 parent import/pin 后假定 child 已注册 loader hook，或将此 ordering 外推为任意 plugin 或完整模型 startup 成功。
- 验收：mock parent-death signal、SIGTERM/SIGINT handlers、plugin reload 与 construction 的精确顺序；
  plugin failure 必须在 engine construction 前原样传播。GGUF child reload 仍须独立 full-model proof。^[PR #6750]

## DIFF-1s — diffusion output type 必须从模型声明闭合到 topology 与 formatter

- 触发：diffusion pipeline 产生 image/video/audio/action 等输出，或修改 model metadata、registry alias、topology `final_output_type`、formatter/post-process 与 multiprocess 传递路径。
- 强制：metadata 按 direct class → metadata alias → registry architecture class/alias → default
  的顺序解析；model class 与 registry alias 必须解析到同一 canonical output metadata。默认单
  stage config、multi-stage final stage、video endpoint capability 与 `OmniRequestOutput` formatter
  必须传播同一类型。未知模型才回 image；非媒体输出使用稳定的 `DiffusionOutput.output` key，并注册
  可跨 orchestrator multiprocess 边界解析的 module-level post-process callable。SANA 的
  `SanaVideoPipeline` 与 `SanaImageToVideoPipeline` 都必须 direct metadata 声明
  `final_output_type="video"`；这是 serving metadata 分类，非 I2V input schema、denoise、topology
  或 VAE 合同变更。LTX 的 `LTX2DistilledOneStagePipeline` 与显式
  `LTX2DistilledTwoStagePipeline` 必须都经 metadata alias 收敛到 canonical
  `LTX2DistilledPipeline` 的 video metadata；同一结论还必须在 registry
  architecture→pipeline class 解析路径成立。
- 禁止：只在 topology 标 video 但 formatter 仍发 image；要求每个 stage 都是 diffusion 才允许 video final；遗漏已注册 video alias 后静默回 image；用 ndarray 形状猜语义，或把局部 closure 作为跨进程 hook。
- 验收：逐个 canonical class/alias 断言 default 与 multi-stage final type，video/image endpoint 正负 capability 及最终 output type；action 另验证 post-process callable 可跨目标进程边界使用，最终 output 保留 stable key、shape、dtype 和有限性。PR #6953 的 CPU metadata unit test 只断言两种 SANA class 均分类为 video；PR #6847 的同类 CPU metadata test 只覆盖显式 LTX distilled two-stage alias 分类。两者都不是新的 endpoint、真实模型或 online/offline E2E 证据。^[PR #4222] ^[PR #5885] ^[PR #6847] ^[PR #6953]

## DIFF-4z — 全 rank RPC 必须执行，但仅 reply owner 保留输出

- 触发：RPC 在所有 rank 执行，而 `output_rank` 或 DP replica primary 决定唯一回复者；结果可能
  携带 device-resident diffusion 输出。
- 强制：所有应执行 rank 都调用目标方法以维持 collective 语义；`should_reply=false` 时在
  `_worker_busy_loop` 绑定返回值之前返回 `(None, False)`，只有回复 rank 保留并 enqueue 原结果。
- 禁止：因不回复而跳过执行，或把非回复 rank 的 device-resident 结果交回 busy loop 并保留到下次
  请求覆盖。
- 验收：非回复 rank 断言目标方法确实执行且返回 `None, False`；回复 rank 断言返回同一对象。测试
  必须覆盖实际采用的 reply-selection 形式。当前证据只覆盖 CPU 单元级返回所有权，不证明 GPU
  显存下降或真实多进程回收时序。^[PR #6989]

## DIFF-9a — 共享 PyAV 预构造帧 mux 必须闭合资源与音频时间零点

- 触发：修改共享 diffusion 的预构造 PyAV 视频帧 mux、可选音频 mux、container cleanup 或编码器异常传播。
- 强制：`mux_av_video_audio_bytes()` 必须在 context manager 内打开并配置 MP4 video/audio streams，消费 `Iterable[av.VideoFrame]` 后 flush video encoder；音频按 `fltp` 和 mono/stereo layout 构造，并以 `pts=0`、`time_base=1/sample_rate` 标记输入时间零点。`audio_sample_rate` 可为 `None`：仅在 audio waveform 存在时内部解析为 44.1 kHz，video-only 不创建 audio stream，也不需要采样率。成功和 generator、encoder、mux 异常都必须退出 context 关闭 container，同时原样传播原始错误。
- 禁止：在 generator 消费前或 context 外打开/使用 container；只在成功路径手工 close；吞掉帧生成或编码异常后静默改走其他 muxer；把 mock container cleanup 或单一 CPU 运行误认为完整跨硬件 A/V parity。
- 验收：测试覆盖预构造 `gbrp` 帧的 H.264 mux、无音频/mono/stereo 音频、`None` rate 的 video-only 与 audio 44.1 kHz default、AAC 首个有效 packet 的负 priming PTS、video flush 和 container close；让 frame generator 在中途抛错并断言 container 已关闭且异常 identity 保持，再用固定媒体输入执行 ffprobe 与完整 FFmpeg 解码。^[PR #6288] ^[PR #6499]

## DIFF-11a — 单 GPU diffusion executor 必须保持进程内故障与生命周期语义

- 触发：新增或修改单 GPU diffusion executor、inline worker RPC、设备故障处理或 executor shutdown 生命周期。
- 强制：单 GPU 的 `uni` 路径必须在 engine 进程内构造并驱动 `WorkerWrapperBase`，仍初始化一个 rank 的 distributed environment，但不得创建 worker subprocess、`MessageQueue` 或 IPC 输出段；`collective_rpc` 直接调用 worker，保留 reply-rank 的返回形状，recoverable request error 留在请求级，sticky accelerator fault 必须 latch executor failure、只触发一次 failure callback，并让 `check_health()` 抛出 `EngineDeadError`。
- 禁止：单 GPU 默认继续走 `mp`，多 GPU 选择 `uni`，把 inline `timeout` 描述成可强制的 RPC deadline，或把所有 worker exception 都升级为 engine death；设备上下文已中毒后不得继续报告健康，也不得让部分构造失败或重复 shutdown 遗留 worker、callback、缓存或 device allocation。
- 验收：覆盖 omitted/显式 backend/多 GPU 的选择矩阵、直接 RPC 与返回形状、recoverable error、CUDA/NPU sticky fault、callback once、health failure、部分构造 cleanup 和幂等 shutdown；真实单 GPU smoke 还须验证一 rank group、`InlineStageDiffusionClient`、真实 `DiffusionOutput` 流程、worker shutdown，以及固定 seed 下与 pinned `mp` 的输出一致性，mock 不能替代这些证据。 ^[PR #6308]

## DIFF-1ag — mid-stream interaction 必须经 modality handler 在 chunk 边界应用

- 触发：修改 `InteractionCoordinator`、`InteractionMixin`、`SupportsInteractionApply`、prompt/camera 等 interaction handler、chunk-boundary apply，或试图恢复 `PromptUpdateMixin`/`prompt_update.py`。
- 强制：runner 与 pipeline 共有同一 `InteractionCoordinator`；仅对已注册 modality 构造 handler；`enqueue` 按 modality 路由；`apply_at_chunk_boundary` 以稳定顺序推进（prompt 优先，再及其他 modality）；per-request session 落在 `StepRequestState.interaction_sessions`，chunk ACK 元数据写入 `interaction_chunk_metadata`。未注册 modality 必须 fail closed。当前公开行为保持 prompt-only，直到另有 PR 注册并验收非 prompt handler。
- 禁止：在 denoise 中途旁路 coordinator 直接改 `prompt_embeds`；在非 chunk 边界静默应用 interaction；未注册就接受 camera/`multi_modal_data`；或把内部 handler 重构当成用户 API 已扩展。
- 验收：覆盖 prompt enqueue→chunk-boundary apply→ACK event id、未注册 modality 拒绝，以及无 session 的 modality 跳过；不得用本框架落地证明 camera/MM 路径已可用。^[PR #6294]

## DIFF-1ai — 迁移后的视频输出必须以 typed `media` 为唯一能力信号

- 触发：修改 `DiffusionOutput`、device-side video postprocess、`video_output_transport`、
  runner 预 D2H 准备、worker IPC media envelope 或 engine finalizer 路由。
- 强制：迁移动画输出以 `DiffusionOutput.media`（`DiffusionMediaOutput`）为唯一能力信号，
  与 legacy `output` 以及 model-specific `post_process_func` 互斥。runner 在 normalize/
  request-split 之后、异步 D2H 之前完成 request-owned 准备：合格视频转 contiguous uint8
  `BTHWC`，或按策略保留已标 transport-ready 的 float；IPC 只接受 transport-ready 的
  版本化 `diffusion_media_v1` envelope；engine 走通用 media finalizer，绕过 legacy
  model postprocessor。`to_cpu=True` 前 media 必须已 prepared。feature 默认关闭，经
  `video_output_transport.enable_device_postprocess` 显式开启。合同违规 fail loud；
  OOM 可回退到 owned float 并告警，其他 runtime 错误仍传播。未迁移模型保持 legacy path。
- 禁止：对已迁移路径同时填充 `media` 与 legacy `output`；未准备就 D2H/to_cpu；把 HTTP
  sink、codec 策略或未迁移模型静默当作同一 Phase-1 合同。
- 验收：正负覆盖互斥字段、未 prepared `to_cpu`、IPC 拒收未就绪 media、opt-in 开关与
  OOM float fallback；至少一条迁移模型（如 WAN2.2 非 latent）走 typed path，一条未迁移
  模型仍走 legacy。^[PR #6615]

## DIFF-1aj — multiproc worker shutdown 必须升至 SIGKILL 并保留幸存者供重试

- 触发：修改 `_ExecutorShutdownCleaner`、diffusion worker process join/terminate/kill、
  worker monitor 与显式 `shutdown()` 的竞态，或 cleaner 持有的 process 引用生命周期。
- 强制：cleanup 按有界三阶段推进：cooperative join → `terminate`+join → `kill`+join；
  信号/join 的 `OSError` 不得中断 peer cleanup。最终仍存活的进程必须记 error（含 name/pid）
  并保留在 cleaner 上，供下一次显式 shutdown 重试，不得在第一次失败后丢弃引用。
  cleaner 用非阻塞锁，防止 monitor 与显式 shutdown 并发操作同一批 `Process`；二次进入
  直接返回。`broadcast_mq` 在 enqueue 成败后都要清空；result-pump/pending-future 清理
  仍在 `finally`。
- 禁止：只做 graceful+SIGTERM 后假定已退出；失败后清空 process 列表导致无法再 reap；
  把存活进程当作 GPU 内存已回收或 HWR/服务自动重启已完成。
- 验收：真实 CPU child（含忽略 SIGTERM）在 queue 失败时经 SIGKILL 退出并被 reap；合作
  退出路径 exit 0；覆盖 shared deadline、signal/join OSError 续跑、幸存者保留与并发
  cleaner。^[PR #7126]

## DIFF-1ai2 — 复合 mid-stream interaction 必须原子入队，非懒会话在 chunk0 前物化

- 触发：修改 `InteractionCoordinator.enqueue_parts`、`lazy_initialize_session`、camera/`multi_modal_data` 与 prompt 同事件入队、`synchronized_monotonic_time`，或 chunk-boundary apply 的 media/latent 计数。
- 强制：含多 modality 的同一事件先全部 `validate_payload`，再入队；任一路不支持或非法不得部分改队列。`received_at`/boundary 时钟经 rank 同步，使 USP/SP 分片共享同一到达时刻。`lazy_initialize_session=False` 的 handler（如 camera）必须在首个 denoise chunk 前 `maybe_prepare_initial_session`，即使尚无 client enqueue。chunk apply 区分 `num_media_frames` 与 `num_latent_frames`，需要者才 `peek_chunk_media`。
- 禁止：先入队再校验导致半更新；把未注册 camera 当已可用；懒会话与必须预创建会话混用同一 skip 逻辑；用未同步的 per-rank `time.monotonic()` 驱动跨分片时间线。
- 验收：复合 prompt+camera 原子成功/失败、未注册拒绝、非懒会话在 chunk0 前存在、介质计数字段传播。^[PR #7198]

## DIFF-1ak — inline DiffusionWorker 在 init_device 之后失败必须先 shutdown 再抛出

- 触发：修改 `DiffusionWorker.__init__` / `shutdown`、`WorkerWrapperBase` 自定义 pipeline 再初始化，或同一进程连续构造 sleep-enabled `uni`/`mp` worker。
- 强制：`init_device()` 已占用 process-global distributed / CuMem 后，runner 解析、load、LoRA 或 wrapper 再初始化失败必须调用幂等 `shutdown()` 再重抛**原始**异常。`shutdown` 先断开 model/LoRA/profiler/sleep-buffer/request-state 引用，再停 offloader 与 KV-transfer，best-effort 清 connector、A2A workspace 与 distributed state，只释放本 worker `_owns_sleep_pool` 的池，并同步/回收后检查 allocator。cleanup 自己失败不得遮蔽原始 init 异常。
- 禁止：构造失败后留下非空 model-parallel state，让下一实例撞 `model parallel state must be empty`；shutdown 后仍让 CuMem 跟踪的模型分配活着，让下一 sleep worker 撞 `Sleep mode can only be used for one instance per process`；依赖 wrapper 不可达来做确定性 teardown。
- 验收：覆盖 init-after-`init_device` 失败、wrapper 再初始化失败、cleanup 异常不改写根因、shutdown 幂等与所有权；不得把单次 AMD custom-pipeline 变绿外推为所有平台已无 leftover mapping。^[PR #7986]
