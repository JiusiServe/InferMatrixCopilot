---
title: "MiniCPM-o 4.5 Code2Wav CUDA graph 规则"
created: 2026-09-04
updated: 2026-09-04
type: rule
tags: [vllm-omni, models, model-executor]
sources: [vllm_omni/model_executor/models/cosyvoice3/code2wav_core/hifigan.py, vllm_omni/model_executor/models/minicpmo_4_5/batched_token2wav.py, vllm_omni/model_executor/models/minicpmo_4_5/cuda_graph_wrapper.py, tests/model_executor/models/minicpmo_4_5/test_cfm_graph_capture_gating.py, tests/model_executor/models/minicpmo_4_5/test_cuda_graph_wrapper.py, "PR #5869", "PR #6082", "PR #6587"]
confidence: high
---

# MiniCPM-o 4.5 Code2Wav CUDA graph 规则

## MCPMO-1d — HiFT graph 只捕获稳定 pre-iSTFT 子图并限界 shape cache

- 触发：`enable_hift_graph`、capture batch/chunk 配置、HiFT inference 分段或 streaming cache shape。
- 强制：只在 parameter device 为 CUDA 时启用；非 CUDA 回 eager。capture bucket 由 codec chunk、left context、Flow lookahead、token→mel ratio 与 mel/source cache 推导；启动预捕 uncached/cached shape，未知 final shape 最多 lazy capture 8 个，超限或无可容纳 batch 时回 eager。active stream capture 中禁止嵌套 capture/replay并回 eager；静态输入先清零再复制真实 batch，输出 slice 后 clone。
- 强制：graph 只覆盖 `_inference_pre_istft`；`torch.istft` 的 NOLA CPU-GPU sync 与 waveform clamp 留在 eager `_finalize_decode`。HiFT window/harmonic IDs 必须是随 module device 移动的 non-persistent buffers。开关独立于 stage `enforce_eager`；四份 bundled MiniCPM-o deploy 默认开启。
- 禁止：无 connector 配置、非正 chunk、负 left context、source/mel cache 不整除时静默 capture；将未来 `initial_codec_chunk_frames` 当已预捕（当前会 lazy capture）；把 lazy graph limit 说成总显存上界，因为启动 graphs、global pool、static tensors 与其他 graph owners 仍驻留。active-capture 分支虽绕过 nested replay，却调用包含 NOLA sync 的完整 eager decode；未做真实 outer-graph 测试前，不能把日志中的 “fallback” 当成可捕获保证。custom `capture_batch_sizes` 也尚未校验正数/去重。
- 验收：CUDA test 比较 cached/uncached graph 与 eager，CPU/mock 覆盖 lazy capture/limit fallback，deploy test 固定默认开关；另测非 CUDA disable、invalid config、unsupported batch、nested capture 和 variable final chunk。static input/output 与 lazy graph map 为无锁可变状态；并发 replay/capture 需先证明被上层串行化或增加互斥与重叠调用测试。PR 的单 A800 profile 约 30→5 ms/chunk、250→43 ms/request，只绑定部分 graph、单 prompt/commit `8fa28d88`，无 repeats/端到端质量，不能泛化为稳定 speedup。^[PR #5869]

## MCPMO-1e — CFM DiT CUDA Graph 必须按 shape 整代退休并保持 eager parity

- 触发：修改 MiniCPM-o 4.5 Code2Wav CFM DiT estimator 的 CUDA Graph 开关、`blocks_forward_chunk` graph target、按 shape 捕获/重放、cache retirement 或 eager fallback。
- 强制：仅在 CUDA 且显式启用时捕获 `estimator.blocks_forward_chunk`；`t_embedder`、`torch.cat`、`expand`、buffer 准备和 10-step Euler loop 保持 eager。graph key 必须包含所有输入的 shape、dtype 和 device；`cnn_cache=None` 与 `att_cache=None` 转为 graph 可接受的零值时，必须保持与 eager `[None] * depth` 的首 chunk 数值语义，重放结果和 cache 输出需 clone。
- 强制：`cfm_max_graphs` 是一代的有界容量。满载遇到新 shape 时，先同步，再只对本 wrapper 拥有的全部 `CUDAGraph` 调用 `reset()` 并清空 cache，随后捕获新一代的首图；绝不可逐 entry/LRU eviction。不得进行 process-wide cuBLAS workspace 清理或 `empty_cache()`：HiFT 等共享 global graph pool 的存活图不属于 CFM 的退休范围。`max_graphs <= 0` 必须禁用捕获并 eager。
- 强制：warmup 或 capture 发生异常时，在该 wrapper 的剩余生命周期内保持禁用并退休其自有 generation；不能在可能脏的 capture stream/allocator 状态继续捕获。无法由 key 重建的 dtype 仅标记该 shape eager，不得禁用其他可捕获 shape；capture admission 不得依赖 device free-memory。维护固定字段的 calls/hits/captures/flushes/eager 累计 telemetry。
- 禁止：捕获整个 `_estimator_step` 或手写替代 graph target；使用无界 shape cache、逐图 eviction、跨 owner 的 process-wide cleanup，或在 nested capture 中重放；捕获失败后伪装成功；把 CFM graph 的配置、性能或 parity 结论外推到 HiFT、encoder、TRT 或其他模型。
- 验收：CUDA 测试覆盖 uncached/cached shape 的 graph/eager 数值 parity、`None` cache parity、lazy capture、整代 flush 后 HiFT replay parity、capture/warmup failure 后不再 capture、unsupported dtype shape-local eager 与 `max_graphs <= 0` eager；CPU/mock 覆盖 active capture/non-CUDA、free-memory 非 gating、telemetry 和 inert non-CUDA memory reporting，并确认 deploy 配置值实际到达 estimator。^[PR #6082] ^[PR #6587]
