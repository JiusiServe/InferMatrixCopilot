---
title: "平台后端合同"
created: 2026-09-04
updated: 2026-09-05
type: rule
tags: [vllm-omni, components, model-executor]
sources: ["PR #5886", "PR #6061", "PR #6096", vllm_omni/platforms/, "PR #5604", "PR #6293", "PR #5571", "vllm_omni/platforms/xpu/platform.py", "PR #5569", "vllm_omni/platforms/xpu/utils.py", "PR #5048", "PR #6350", "PR #6102", "PR #6563", "PR #6054", vllm_omni/platforms/npu/platform.py, tests/platforms/npu/test_diffusion_platform.py, tests/platforms/npu/test_diffusion_attn_backend_selector.py, "PR #6674", vllm_omni/platforms/npu/worker/npu_ar_model_runner.py, vllm_omni/platforms/npu/worker/npu_generation_model_runner.py, vllm_omni/platforms/npu/worker/npu_model_runner.py]
confidence: high
---

# 平台后端合同

`EXEC-10a`–`10e`、`EXEC-12a`–`EXEC-13h`：NPU 平台 runner 的 runtime mode 与 dummy-run 接口、ROCm 分页注意力的 packed KV varlen 路径，以及 NPU 模型补丁的注册与回归。触发条件与其余审查组见 [model-executor 共享规则](rules.md) 的 Direct 代码快速入口。

## EXEC-10a — NPU 平台 runner 必须保持 runtime mode 与 dummy-run 接口合同

- 触发：平台 runner 覆盖 `dummy_run` 或接收 `cudagraph_runtime_mode`，而共享 runner 新增运行时参数或需要校验复合 runtime mode。
- 强制：平台 override 必须保留共享签名中的 `randomize_inputs` 默认值并将其传给 `maybe_randomize_inputs`；runtime mode 必须调用 `is_valid_runtime_mode()` 判断当前实例是否有效。
- 禁止：通过实例调用返回集合的 `valid_runtime_modes()` 冒充实例有效性校验，或因共享签名新增可选参数而让平台 override 产生接口漂移。
- 验收：对 base NPU runner 与 generation override 分别覆盖 `randomize_inputs` 的默认和显式路径，并用包含 `FULL_DECODE_ONLY` 等复合模式的正负用例断言 `is_valid_runtime_mode()` 的校验结果和签名 parity。 ^[PR #6096]

## EXEC-10b — XPU 异步 D2H 必须记录设备无关的 torch.Event

- 触发：修改 `XPUOmniPlatform.record_device_event()`，或修改使用通用 `torch.Stream.wait_event()` 门控异步 D2H 的 XPU 输出路径。
- 强制：在当前计算流上记录设备无关的 `torch.Event()`，再由通用 stream 等待该事件，使 accelerator hooks 建立计算流到侧流复制的依赖；保持与 CUDA、ROCm 平台一致。
- 禁止：向通用 `torch.Stream.wait_event()` 传递 `torch.xpu.Event()`，或通过零散的 `xpu.synchronize()` 掩盖事件类型不兼容造成的复制竞态。
- 验收：mock 测试断言 `torch.Event()` 被创建并记录且 `torch.xpu.Event()` 未被调用；XPU 硬件测试在计算流完成后让侧流执行 non-blocking D2H，等待侧流同步后断言 host tensor 全部保持预期值、无尾部图像损坏。 ^[PR #5571]

## EXEC-10c — XPU CUDA 兼容包装必须覆盖异步运行时接口

- 触发：XPU 等非 CUDA 平台复用 Omni AR 异步输出或 warm-up 路径，而共享 runner 调用了 `torch.cuda` 的 stream、event、device 或 graph 接口。
- 强制：在 `vllm_omni/platforms/xpu/utils.py::torch_cuda_wrapper()` 中集中把 CUDA-facing API 映射到 XPU；`current_stream`、`default_stream`、`stream`、`set_stream`、`set_device` 使用 `partial`，`Stream` 映射为 `torch.xpu.Stream`，`Event` 忽略 CUDA 专属 `blocking` 参数后构造 `torch.xpu.Event`；仅在 `supports_xpu_graph()` 为真时映射 graph、`CUDAGraph`、pool 和 capture 状态接口。
- 禁止：为适配 XPU 修改共享 `gpu_ar_model_runner.py`，或只映射 stream 而遗漏 `set_stream`、`set_device`、event 与受支持的 graph 接口；不得让通用 `torch.Stream.wait_event()` 接收不兼容的专用事件类型，也不得在不支持 XPU graph 时无条件安装 graph shim。
- 验收：XPU 平台测试进入 wrapper 后断言异步 runner 所需的 stream、event、device 和 graph 调用均路由到对应 XPU API，且不支持 graph 时保持禁用；Qwen3-TTS 等 AR-stage warm-up 与完整异步输出 smoke 在 XPU 上成功完成，同时 CUDA 路径和共享 runner 行为保持不变。^[PR #5569]

## EXEC-10d — GPU/NPU AR runner 必须镜像逐请求 logits metadata handoff

- 触发：AR 模型在 logits 计算中需要 runner 提供按 request 的 req_id 或其他逐请求 metadata，且 GPU 与 NPU 有独立的 execute/logits 路径。
- 强制：GPU/NPU runner 都必须在 `flush_pending_metadata` 后，以 logits 行顺序调用可选的 `set_batch_req_ids(req_ids[:num_reqs])`；仅在 `spec_decode_metadata is None` 时建立一行对应一个 request 的映射，并允许没有该 hook 的模型无操作通过。
- 禁止：只在 GPU 路径接入、在 metadata flush 前调用、把 padding/dummy request 传入 batch，或在 spec decode 的多行 request 映射下继续按位置记录 req_id。
- 验收：GPU 与 NPU 的测试分别断言 hook 的调用顺序、参数和 `num_reqs` 截断；覆盖无 hook 模型、mixed batch 与 spec decode，证明错误映射不会进入模型 logits mask。^[PR #5048]

## EXEC-12a — ROCm 分页注意力必须走 packed KV 的兼容 varlen 路径

- 触发：修改 `vllm_omni/experimental/ar_diffusion/kv_cache/paged_attention.py` 的 ROCm 分页注意力、AITER/`flash_attn` varlen kernel、`block_table` 映射或 KV block layout。
- 强制：ROCm 路径必须避开 CUDA 专用的 `vllm.vllm_flash_attn` 接口，优先解析 AITER、再回退到 `flash_attn`；依据每个请求的 `seq_lens` 构造 `cu_seqlens_k`，在 device 上按 `block_table` gather 可见 KV 为 packed tensors，并使用匹配的 query offsets、最大长度、`softmax_scale` 和 `causal` 参数调用 `flash_attn_varlen_func`。
- 禁止：复用 CUDA 专用的 `seqused_k`/`fa_version` 参数合同；直接把不兼容的 ROCm paged kernel 用于 AR-Diffusion 的 frame-aligned blocks；依赖 ROCm kernel 对 `block_table` 的隐式支持；丢失逐请求长度或把 KV gather 到 CPU 后再调用 kernel。
- 验收：在 ROCm GPU 上覆盖不同 history/action 长度、block table、请求长度和 `commit_current` 组合，与 dense reference 校验数值和输出 shape；分别验证 AITER 与 `flash_attn` fallback，确认 HIP 路径不导入 `vllm.vllm_flash_attn`，并确认 CUDA/CPU 路径行为不变。 ^[PR #5886]

## EXEC-13a — NPU 模型补丁必须由生产初始化路径注册并可回归

- 触发：在 NPU platform 初始化中加入模型专有 monkey patch、融合算子或其他必须全局启用的 model hook。
- 强制：把 hook 封装成幂等的 `apply_*_patch()`，在 `adapt_patch(is_global_patch=True)` 完成后由生产初始化路径显式调用；注册必须只指向目标模型 consumer，并保留非 NPU和其他模型路径。测试必须验证生产注册链，而不只直接调用 helper。
- 禁止：依赖 import side effect 或手工调用 helper 代替平台注册；只覆盖 patched function 的数值而不验证注册实际生效；把模型专有 patch 扩大到 MiniMax H3 DiT 或所有 NPU 模型。
- 验收：从 NPU 平台初始化/注册入口运行测试，断言目标 Qwen3-VL text encoder 的 consumer 已替换且重复初始化不重复 patch；随后用真实 consumer 覆盖至少一个 BNSD fast path、一个 BSND fallback 和 batched M-RoPE。^[PR #6061]

相关执行流见 [model-executor architecture](architecture.md)；跨 stage 合同见 [bridge/batch 规则](rules-bridge-batch.md)。

## EXEC-13b — NPU 精确形状图捕获必须隔离动态边界并失败即停

- 触发：修改 `vllm_omni/platforms/npu/graph_tools.py` 的 NPUGraph 捕获/重放、NPU 模型补丁的 tensor-only 子图，或 Token2Wav 图执行上下文。
- 强制：图缓存 key 必须同时包含 operation、缓存模式、所有输入的完整 shape、dtype 和 device；首次匹配调用先 eager 预热，再使用 vLLM global graph pool 捕获，后续重放前把当前值复制到静态输入，并在请求状态或 streaming cache 接管前 clone 持久化输出。Python metadata、CPU 频率张量、H2D、随机数和动态 state 必须留在 eager 边界；捕获失败后必须停止该 stage 进程。
- 禁止：捕获整个请求编排或包含动态 Python/RNG 状态的路径；使用无界 shape cache、绕过 global graph pool、在 nested capture 中重放、复用会被下一次重放覆盖的输出，或吞掉 capture、patch setup、SDPA context 的异常后继续运行。
- 验收：CPU/mock 测试覆盖 exact-signature dispatch、cached/uncached bucket、global graph pool、persistent-output ownership、capture failure fail-stop 和异常传播；A3 硬件测试分别比较 eager 与 uncached/cached NPUGraph 的输出、shape 和 cache，并核对图数量上限与 runtime preconditions。^[PR #5604]

## EXEC-13c — NPU 模型补丁必须避开平台构造期的 diffusion 导入回环

- 触发：NPU 平台注册模型专有 monkey patch，且该 patch 包会导入 diffusion pipeline/data 或依赖已完成初始化的平台状态。
- 强制：平台构造阶段只完成轻量、全局且无 diffusion 回环的 patch；将会加载模型 encoder/pipeline 的 patch 延迟到 `init_diffusion_model_runner_runtime`，并在 diffusion pipeline 加载前、平台对象已建立后，按既有顺序显式应用所有相关 patch。注册入口仍须幂等且只作用于目标 consumer。
- 禁止：在 NPU platform `__init__` 中导入或执行会经 `pipeline_registry` → `DiffusionOutput` 回环的模型 patch；依赖 import side effect；只移动一个 patch 而让同一模型的相关 patch 仍在过早阶段加载；把 NPU 时序修复外推为所有平台的通用行为。
- 验收：静态或子进程测试证明平台构造不会加载 MiniMax-H3 encoder/diffusion data，runtime hook 在 pipeline 加载前调用目标 patch 且保留其他 patch；验证重复初始化不重复 patch，并用真实 NPU consumer 覆盖 patch 生效路径。^[PR #6293]

## EXEC-13d — NPU diffusion fused MoE 必须在真实 runtime 注册 OOT 实现

- 触发：NPU diffusion 路径调用 fused MoE，而 vllm-ascend 的 OOT MoE 注册只在其 `NPUWorker.__init__` 中执行，导致 `RoutedExperts` 未注册或无法接收 `n_shared_experts`。
- 强制：在生产 `prepare_fused_moe_runtime()` 路径中幂等注册 `MoERunner` 与 `RoutedExperts`；注册前检查 `op_registry_oot`，已有名称必须保留其现有实现，并只依赖 diffusion config shim 实际提供的参数。
- 禁止：依赖 `NPUWorker` 初始化或 import side effect 建立 diffusion 注册；无条件注册完整 `REGISTERED_ASCEND_OPS` 表；重复调用触发注册断言，或让 `PluggableLayer` 回退到不兼容的上游实现。
- 验收：从真实 NPU diffusion runtime 覆盖首次和重复初始化，断言两个 OOT 名称均解析到可接受 `n_shared_experts` 的实现并完成 HunyuanImage3 fused-MoE accuracy/performance smoke；同时确认普通 NPU、非 NPU 和已完成 vllm-ascend 注册的路径不变。^[PR #6350]

## EXEC-13e — diffusion paged KV 必须经平台 native hook 闭合

- 触发：平台为 diffusion paged KV 增加或修改 BlockTables、native attention metadata builder，或 common adapter 需要支持 CUDA 与 NPU 的不同 native contract。
- 强制：common `OmniPlatform` 通过 `get_diffusion_kv_block_tables_cls()`、`build_diffusion_kv_attn_metadata()`、backend specialization 与 prewrite hook 提供默认 native 实现；NPU 必须返回 `AscendBlockTables`，把 `seq_lens_cpu` 转为 `seq_lens_np` 并使用 `AscendAttentionState.ChunkedPrefill`，在 spec discovery 前设 Ascend 支持的 block geometry，并为 FIA 在 piecewise segments 前恰好 prewrite complete K/V span。strict Ulysses 的 Ascend paged backend 必须绕开上游 PCP dispatch。common diffusion data plane 只调用 platform hooks，并在 layer registration 阶段验证 resolved backend 与 hook 能力。^[PR #6563]
- 禁止：在 common adapter 直接导入 `vllm_ascend` 或硬编码 CUDA `BlockTables`/metadata 假设；把 platform capability 延迟到首次 attention dispatch；平台未提供 native contract 时静默回退 dense 或继续占用 paged KV。
- 验收：default 与 NPU hook 的 class、metadata 参数、block geometry、prewrite 与 backend selection 通过 mock/contract 测试，unsupported hook/backend 在物理 cache allocation 前 fail fast；CUDA 与 NPU lane 分别验证 native metadata construction。硬件证据限于 PR 的 H200/910B request-mode lanes，不能推出其他平台、Ring/AllGather 或性能一般化。^[PR #6102] ^[PR #6563]

## EXEC-13f — NPU diffusion attention 必须只为会触达 MindIE-SD 的后端提前导入

- 触发：修改 `NPUOmniPlatform.get_diffusion_attn_backend_cls()` 的 diffusion attention backend 选择、NPU FlashAttention/RAINFUSION fallback，或 MindIE-SD custom-op 环境初始化。
- 强制：显式 `FLASH_ATTN`（包括在 NPU 上回退到本地 FlashAttention 的 `FLASH_ATTN_HUB` / `FLASH_ATTN_3_HUB`）和 `RAINFUSION_ATTN` 在 `mindiesd` 可发现时必须在 backend path 返回前导入它；后者的 dense FlashAttention fallback 会在 `start_step` 前或没有可稀疏化 video segment 的 layer 触达 MindIE-SD。该导入须早于任何会让 CANN 固化 custom-op registry 的 regInfo lookup，使 `mindiesd.env` 能先把 vendor dirs 写入 `ASCEND_CUSTOM_OPP_PATH`。
- 禁止：为 `TORCH_SDPA` 或其他不会到达 MindIE-SD kernel 的显式 backend 导入可选 `mindiesd`；不得把 optional-package 损坏扩散成这些 backend 的选择失败，也不得假定所有 RAINFUSION layer 都走 sparse path。
- 验收：CPU/mock selector test 应分别断言 FLASH、两个 hub FLASH fallback 与 RAINFUSION 触发 eager import，TORCH_SDPA 不触发；同时覆盖 `mindiesd` 缺失时显式 FLASH 仍解析、未选择 backend 时才在可用条件下默认 FLASH，否则回退 SDPA。该测试不运行 NPU/CANN，不证明 custom-op 注册、真实 kernel 或 Ascend 生产可用性。^[PR #6054]
## EXEC-10e — NPU runner 只能 shallow-copy 自己要改的 mutable map

- 触发：NPU AR/generation runner 在 `speculative_config.use_ngram_gpu()` 下把同一
  `SchedulerOutput` 交给会 trim invalid draft 的继承路径，或升级 upstream NPU runner ownership。
- 强制：AR 与 generation 两条路径都用 `dataclasses.replace` 浅拷贝外层 `SchedulerOutput`，且只
  `.copy()` 两个会被修改的 map：`num_scheduled_tokens` 与 `scheduled_spec_decode_tokens`；其他 immutable/
  tensor state 继续共享。vLLM-Ascend 0.28 已拥有 CUDAGraph/KV-scale handling 与 SP/flashcomm-v1 output
  gather 时，Omni 只保留自身 forwarding/output hooks，不重复 reset、calculate 或 gather。
- 禁止：原地修改 EngineCore-owned maps；`deepcopy(scheduler_output)`；只修 AR 或 generation 一侧；
  恢复已经上移给 upstream 的 KV-scale/CUDAGraph/SP gather，或把删除重复逻辑写成数值/性能已验证。
- 验收：ngram enabled 时两 runner 的 inherited mutation 都不改变原始两个 map，copy 仅隔离它们；
  disabled control 不额外复制。另以 owner/call-count 测试防止 duplicate KV-scale 与 SP gather。
  PR #6674 未新增这些专项执行测试；CPU/mock 也不证明真实 NPU parity。^[PR #6674]

## EXEC-13h — NPU profiling 只有 enabled 且 need_timing 才进入 timing path

- 触发：NPU runner profiling、model execute timing 或 vLLM 0.28 profiler API 对齐。
- 强制：AR 与 generation 都从同一 `profiling_chunk_config` 读取 gate；scheduler output 的
  `disable_profiling_timing` 先把当前 call 的 `need_timing` 置 false。只有 `enabled && need_timing`
  才启动/同步计时，并且只有同一 gate 成立才导出 `execution_time_ms`；其他调用保持 normal path。
- 禁止：仅因 profiler/config object 存在或 `need_timing=true` 就计时；profiling disabled 时创建 timing
  state；只在 start 处 gate、却无条件同步/导出，或将 gate 本身当作 NPU 性能结果。
- 验收：AR/generation 都覆盖 enabled+timed、disabled+timed、enabled+not-timed 及 per-output disable，
  断言 start/sync/export 一致。PR #6674 没有这些专项测试，属于后续验收要求。^[PR #6674]
