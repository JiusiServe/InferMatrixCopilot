---
title: "Qwen3-TTS 规则"
created: 2026-07-20
updated: 2026-09-02
type: rule
tags: [vllm-omni, models, serving, qwen-omni]
sources: ["PR #5157", "PR #5608"]
confidence: high
---

# Qwen3-TTS 规则

只有 `Q3TTS-数字字母` 是可审计规则 ID。

## Direct 代码快速入口

| PR 描述信号 | 规则组 | 第一批源码 |
|---|---|---|
| Qwen3-TTS、`qwen3_tts` pipeline | Q3TTS-1a/1b | `config/pipeline_registry.py::OMNI_PIPELINES["qwen3_tts"]`；`model_executor/models/qwen3_tts/pipeline.py` |
| `ref_audio`、x-vector、ICL、artifact-only reuse | Q3TTS-1a/1b | `entrypoints/openai/serving_speech.py::_qwen3_tts_can_use_ref_audio_artifact_only`、`_track_ref_audio_artifact_warmup`、`_mark_ref_audio_artifact_ready_for_request` |
| talker/code2wav、deferred audio codes | Model Executor / Scheduler 共享规则 | `model_executor/models/qwen3_tts/qwen3_tts_talker.py::Qwen3TTSTalkerForConditionalGeneration`、`qwen3_tts_code2wav.py::Qwen3TTSCode2Wav` |
| OpenAI speech adapter | Q3TTS-1a/1b + Serving | `entrypoints/openai/tts_adapters/qwen3_tts.py::Qwen3TTSAdapter` → `serving_speech.py` |
| NPU、RoPE、BNSD/BSND、`codec_chunk_ramp` | Q3TTS-2a | `platforms/npu/models/qwen3_tts_tokenizer_v2.py::_apply_rotary_pos_emb_npu` → `platforms/npu/layers/rotary_embedding.py::npu_rotary_mul_with_bsnd_fallback` |

## Q3TTS-1a — ref-audio readiness 按 mode/capability 隔离

- 触发：同一 `ref_audio` 在 x-vector-only 与 ICL 请求之间复用 artifact。
- 强制：x-vector-only artifact 只证明存在 speaker embedding，不能满足需要 `ref_code`
  的 ICL；ICL 请求遇到这种 artifact 时必须保留原始 audio 并重新计算。
- 禁止：仅按 `artifact_key` 标 ready 后剥离 `ref_audio`；worker 此时既没有 `ref_code`
  也没有输入可补算，会把请求错误升级为 engine failure。
- 验收：同一 audio 的 x-vector → ICL 顺序重新计算且 server 存活；x-vector → x-vector
  与 ICL → ICL 仍命中 artifact-only reuse。 ^[PR #5157]

## Q3TTS-1b — ICL 是能力超集，是否反向复用必须显式取舍

- 触发：用 `(artifact_key, x_vector_only)` 等 exact-mode key 简化 readiness。
- 强制：记录 ICL artifact 同时含 `ref_code` 与 speaker embedding，因此理论上可满足
  x-vector 请求；若选择 exact-mode 隔离，应把首次 ICL → x-vector 的一次重算视为已知
  非阻塞性能代价。
- 禁止：把该重算描述为正确性要求，或在未 profiling 前增加复杂 capability 状态机。
- 验收：顺序测试证明 ICL → x-vector 只多一次重算、输出正确且后续同模式复用恢复；
  若优化为 capability predicate，保留 x-vector artifact 不能服务 ICL 的单向边界。 ^[PR #5157]

## Q3TTS-2a — NPU RoPE 按真实 shape 在 BNSD 与 BSND fused path 间选择

- 触发：Qwen3-TTS 12 Hz tokenizer decoder 的 NPU RoPE，尤其启用短
  `codec_chunk_ramp` 且提高并发时的短序列 decode。
- 强制：`unsqueeze_dim=1` 的输入合同是 rank-4 BNSD `[B,N,S,D]`。只有
  `D` 为偶数、element size 有效且整除 32、`(D/2) % (32/element_size) == 0`，并且
  `B*N <= S*8` 时，才保持 BNSD fused fast path，cos/sin 在 axis 1 扩维。
- 强制：合法 rank-4 输入不满足上述 BNSD predicate 时，把 hidden states 以
  `transpose(1,2).contiguous()` 转成 BSND `[B,S,N,D]`，cos/sin 在 axis 2 扩维后调用同一 fused
  `torch_npu.npu_rotary_mul`，再 transpose 回 `[B,N,S,D]`。q 和 k 必须使用同一 helper；
  `unsqueeze_dim != 1` 的既有调用保持直接 fused 路径。
- 禁止：让短序列/高并发 shape 继续进入会拒绝它的 BNSD tiler；也不能为规避崩溃而让
  所有 shape 都承担 BSND transpose，丢掉已支持 shape 的 BNSD fast path。共享 helper 的
  路径是模型无关的，但此 pin 只证明 Qwen3-TTS tokenizer consumer，不能外推到其他模型。
- 验收：覆盖 `B*N == S*8` 不等式边界两侧、不同 dtype/alignment、rank-4 输入合同、非默认
  `unsqueeze_dim`，并把 BNSD fast path 与 BSND fallback 的 q/k 结果同 eager RoPE 做数值
  parity。当前测试只把一个 unsupported shape 的 cos/sin dispatch 期望改为 BSND axis，
  尚无专门的 supported/unsupported 边界矩阵或 eager 数值 parity。 ^[PR #5608]

共享 readiness/错误隔离规则见 [Serving rules](../../components/serving/rules.md)；
Qwen 家族入口见 [Qwen-Omni](../qwen-omni/_index.md)。
