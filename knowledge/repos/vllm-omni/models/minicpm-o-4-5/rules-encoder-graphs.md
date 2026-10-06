---
title: "MiniCPM-o 4.5 输入 encoder CUDA graph 合同"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, models, model-executor]
sources: ["PR #8332", vllm_omni/model_executor/models/minicpmo_4_5/encoder_cuda_graph.py, vllm_omni/model_executor/models/minicpmo_4_5/minicpmo_4_5_omni_llm.py]
confidence: high
---

# MiniCPM-o 4.5 输入 encoder CUDA graph 合同

## MCPMO-ENCODER-1a — exact-shape 输入图必须保留 packed batch、mask 与输出所有权

- 触发：修改 MiniCPM-o SigLIP 或 stateless Whisper/APM encoder 的 CUDA graph adapter。
- 强制：通过 upstream `SupportsEncoderCudaGraph` / `EncoderCudaGraphManager` 执行
  已完成 packing 的完整本地 batch，把它作为一个不可拆的 manager item；只 copy
  runner configuration，不改原配置或再做 manager-level DP。key 包含 CUDA stream
  与所有输入的 shape/dtype/device；每次 replay 更新静态输入与 mask，返回输出 clone。
- 强制：vision 只捕获 transformer stack；position/mask 的 host decisions 留在外面。
  audio 只捕获 stateless encoder、projection 与 pooling。CPU、training、grad/autocast、
  nested capture、padded FlashAttention vision、FP16 Whisper overflow guard、请求
  intermediate audio layer 与 stateful streaming audio 保持 eager；`enforce_eager` 优先禁用。
- 禁止：用 padding 扩大 exact-shape 接纳范围；把下一次 replay 可覆盖的输出 buffer
  直接保留为历史 embedding；将 Code2Wav continuation cache 当作 stateless input。
- 验收：变更同 shape 的内容/mask并保留前次 embedding，检查当前结果与历史值；比较
  vision/audio eager parity，覆盖各 eager 资格与多 stream buffer 隔离。CUDA 图的实际
  capture/replay 由 CUDA 测试验证，CPU eager 测试只证明自身分支。^[PR #8332]

## MCPMO-ENCODER-1b — 输入图接纳预算与 capture 失败必须分别处理

- 触发：修改 input encoder graph 的 admission、pool sharing、显存门限或失败恢复。
- 强制：默认同 shape/stream 第二次调用才 capture，每 encoder 最多 4 图，admission
  history 也有界；`max_graphs=0` 禁用，不 eviction/自动重捕。默认 1 GiB free-memory
  floor 只阻止新 capture，低于 floor 时已存在图继续 replay。门限不是显存预留或 fit 保证。
- 强制：同 encoder/device/replay stream 的 graphs 可共享 pool/capture stream；
  新 capture 等待旧 replay 及输出 clone 完成，随后 replay stream 等待 capture stream。
  不同 encoder 与 replay stream 隔离 mutable buffers；共享 pool 上的 graphs 不得并发。
- 强制：capture 异常原样传播并把该实例置为 terminal failed；后续调用拒绝继续 CUDA
  eager 或 retry capture，需重启 worker，可显式禁用 encoder graphs 后恢复。
- 禁止：把 warmup/capacity/memory miss 与可能污染 CUDA context 的 capture 异常合并
  为普通 eager fallback；把共享 pool 当成允许并行 replay 的保证。
- 验收：一次性 shape 不耗尽 capture slots；容量满、配置零与显存 floor 各自计数；
  低显存仍重放旧图；注入 capture failure 后第二次调用不再 capture/eager；晚 capture
  后任意顺序重放仍保留前次输出与 stream/encoder 隔离。性能证据需绑定最终 admission
  policy、exact head 与 workload，不能直接沿用较早 head 的数值。^[PR #8332]

Code2Wav 的 resident attention 与 stateful continuation 图见
[Whole-Euler 合同](rules-resident-graphs.md)。
