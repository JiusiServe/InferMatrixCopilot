---
title: "Qwen3-TTS 规则"
created: 2026-07-20
updated: 2026-09-04
type: rule
tags: [vllm-omni, models, serving, qwen-omni]
sources: ["PR #5157", "PR #5202", "PR #5608", vllm_omni/deploy/aura_omni.yaml, vllm_omni/deploy/qwen3_tts.yaml, vllm_omni/deploy/qwen3_tts_high_concurrency.yaml, vllm_omni/model_executor/models/aura_omni/pipeline.py, vllm_omni/model_executor/models/qwen3_tts/qwen3_tts_code2wav.py, vllm_omni/model_executor/models/qwen3_tts/segmented_graph_wrapper.py, vllm_omni/model_executor/models/qwen3_tts/tokenizer_12hz/modeling_qwen3_tts_tokenizer_v2.py, vllm_omni/model_executor/stage_input_processors/qwen3_tts.py, tests/model_executor/models/qwen3_tts/test_qwen3_tts_code2wav.py, tests/model_executor/models/qwen3_tts/test_qwen3_tts_incremental_decode.py, tests/model_executor/stage_input_processors/test_qwen3_tts_async_chunk.py, "PR #5048"]
confidence: high
---

# Qwen3-TTS 规则

只有 `Q3TTS-数字字母` 是可审计规则 ID。

## Direct 代码快速入口

| PR 描述信号 | 规则组 | 第一批源码 |
|---|---|---|
| Qwen3-TTS、`qwen3_tts` pipeline | Q3TTS-1a/1b | `config/pipeline_registry.py::OMNI_PIPELINES["qwen3_tts"]`；`model_executor/models/qwen3_tts/pipeline.py` |
| `ref_audio`、x-vector、ICL、artifact-only reuse | Q3TTS-1a/1b | `entrypoints/openai/serving_speech.py::_qwen3_tts_can_use_ref_audio_artifact_only`、`_track_ref_audio_artifact_warmup`、`_mark_ref_audio_artifact_ready_for_request` |
| talker/code2wav、delta frame、request cache、segmented graph | Q3TTS-3a/3b/3c/3d + Model Executor | `stage_input_processors/qwen3_tts.py::talker2code2wav_async_chunk` → `qwen3_tts_code2wav.py::Qwen3TTSCode2Wav` → `segmented_graph_wrapper.py` |
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

## Q3TTS-3a — async connector 只在首块传 prefix，后续只传 delta

- 触发：`async_chunk=true` 的 Talker→Code2Wav 分块、ICL reference code、
  x-vector-only 或 chunk ramp。
- 强制：首块包含有界 ICL ref prefix 和已完成 codec frames；后续块只传
  新完成 frames，`left_context_size=0`，依赖 Code2Wav 按 request 维护
  quantizer/conv/Transformer 状态。首个也是最后一个的短请求必须一次
  发出全长；空的 finished payload 仍携带 request ID 以便清理。
- 强制：async Code2Wav 缺 request ID 必须 fail fast；首个 ICL 状态若声明
  `ref_context_size` 却没有实际 prefix，也必须拒绝。非 async/stateless 路径
  继续传全序列，不要求 request ID。
- 验收：ICL/xvec、ramp/固定 initial chunk、首块即 final、空 EOF、丢失
  request ID/ref prefix，并证明后续 payload 没有重发旧 frames。 ^[PR #5202]

## Q3TTS-3b — decoder state 必须以 scheduler ID 定位且在所有终止边界释放

- 强制：正常 runner 调用用 `request_ids` 中的 scheduler/internal ID 作 cache key，
  因为 `on_requests_finished()` 接收的是同一 ID；payload/external `meta.request_id`
  仅作 direct-forward 与 CUDA Graph dummy run 没有 runner ID 时的 fallback。
- 强制：正常 `finished`、resumable `is_segment_finished`、空/无效最后载荷
  和 scheduler abort 都要清理；segment 边界后不得继承上一段 KV/conv/
  quantizer 状态。dummy ID 需显式 `_is_dummy_run`；decoder dummy path 与正在
  进行的外层 CUDA Graph capture 必须走 exact decode，且 dummy replay/fallback
  不得污染运行统计。
- 边界：`_decoder_state_cache_warn_entries=512` 是 warning threshold，不是容量
  上限；为保持 active request 正确性不做 LRU eviction。因此 ID mapping 与
  abort cleanup 是防止 GPU state 无界增长的必要合同，不能用“有 512 上限”
  掩盖泄漏。
- 验收：internal/external ID 不同的 abort、finished/segment-finished、dummy direct call、
  空/非法 row 并存的 batch。目标 pin 没有专门让 Code2Wav cache 在
  `is_segment_finished` 后清空的 focused test，该边界仍需补齐。 ^[PR #5202]

## Q3TTS-3c — compacted batch 必须保持原 request slot，输出长度归 decoder

- 强制：有状态请求按 mode（ICL/xvec）、phase（first/growing/rolling）、
  target suffix shape 分组，再恢复到原 request slot；一个 right-padded
  `[B,Q,F]` 输入必须同时传真实 lengths 和对齐的 state list。跳过空/
  malformed row 后的 stateless leading-context trim 必须经 `valid_indices[row]`
  回到原 batch 位置，不得用 compacted row 直接索引 metadata。
- 强制：decoder 返回每请求精确长度的 waveform list；stateless 分支移除
  right padding/内部 overlap，Code2Wav 只再移除 scheduler 声明的 leading ref
  context。这一 stateless 合同也影响使用 `Qwen3TTSCode2Wav` 的 Aura-Omni，
  不能只测 Qwen3-TTS async 路径。
- 验收：覆盖 empty/malformed row 与有效 ICL row 混合、variable prefix
  left-padding mask、mixed-phase slot restoration，以及 stateless ref-audio leak/
  short-row tail 回归。^[PR #5202]

## Q3TTS-3d — eager 与 CUDA Graph 必须共用可达 phase 合同

- 触发：修改 segmented graph、first/growing/rolling phase、chunk ramp、capture
  shape/batch bucket 或 eager fallback。
- 强制：无 ramp 时 phase 从 `initial_codec_chunk_frames`、`codec_chunk_frames`、
  decoder `sliding_window` 派生；有 ramp 时用实际 delta。async 忽略
  `decode_cudagraph_capture_sizes`；stateless 用默认 shape 与配置额外 shape 的
  **union**。`decode_cudagraph_batch_sizes` 只限 graph bucket，`decode_batch_max_size`
  只拆 eager stateful group（0 表示不限），两者不可混同。
  旧 `decode_compile_shapes`/`decode_batch_bucket_frames` 已不再被 Qwen3 Code2Wav
  消费，不得将遗留 YAML 字段当作有效调优。
- 降级：不支持的 phase/shape 或 graph 启用失败要 fallback eager 而不得
  返空；ROCm/NPU/enforce-eager 都依赖 eager 合同，不能把 CUDA-only 测试
  外推为跨平台验证。
- 精度：增量解码与 full decode 数值接近但不保证 bit-exact，shape、
  layout 和 contiguity 均可引入小浮点差异。验收要覆盖 eager/graph、
  ICL/xvec、first/growing/rolling、partial-final trim、缺失 capture 与 graph-enable
  失败。^[PR #5202]
  最终 pin 没有 PR body 早期描述的 `_last_output_audio_length`；真实合同是
  exact-length `list[Tensor]` 加 Code2Wav 的 stateless leading-context trim。

## PR #5202 性能证据边界

- 作者基准是单张 RTX 3090 24 GB、vLLM 0.26.0、Omni
  `b8edbc8d`、Seed-TTS 32 prompts、concurrency 1/2/4/8/16、batch-size-1 graph
  capture；cached RTF 从 `0.222` 至 `0.718`，相对 baseline 报告吞吐改善
  `10.3%/20.2%/31.1%/40.4%/34.1%`，mean WER `0.0089`。这是特定
  配置与数据集证据，无 raw result 链接/重复次数或方差，不可当作
  通用 SLA。PR 自报 focused tests `34+22+101 passed`，同时保留一个
  未改动的 log-capture 失败，不得记为全绿。
  该 `b8edbc8d` 是 pre-merge 基准 SHA，不是目标 `4f9b6507` 的性能证明。
- 最终 reviewer 在 H20、vLLM 0.26.0 上用 current main `12a5f6fb`
  对照 head `c63c2efc`，8.08 s clone reference 的输出前缀相关系数为
  base `-0.0034/+0.0028`、head `+0.0005/-0.0038`，支持“未重现
  reference-audio leak”。该单请求 A/B 不覆盖 compacted-batch index fix，
  它的证据来自新单元测试，不得混为硬件验证。

共享 readiness/错误隔离规则见 [Serving rules](../../components/serving/rules.md)；
Qwen 家族入口见 [Qwen-Omni](../qwen-omni/_index.md)。

## Q3TTS-4a — silence codec ban 必须按 checkpoint 词表和 x-vector-only mode 生效

- 触发：修改 Qwen3-TTS Base voice-clone 的 leading silence 行为、`silence_ban_frames`、talker codec mask 或 x-vector/ICL mode resolution。
- 强制：默认 `silence_ban_frames=0`；加载 checkpoint 后通过 `_encode_ref_audio_batch` 编码多种静音样本并只收集 codebook-0 ids，词表为空、越界或明显过大时记录 warning、清空启用值并禁用功能。decode 时只对 Base 的 x-vector-only request 在前 N 个 history steps 屏蔽派生 ids；mode resolution 必须与 prompt builder 一致，`voice_clone_prompt.icl_mode` 覆盖和未记录 mode 都要正确处理。
- 禁止：硬编码当前 checkpoint 的 12 个 token、把 mask 施加到 ICL 或非 Base 请求、对不可信派生词表只做部分 masking，或把经验值 `N=3` 当成跨 checkpoint 的固定最优参数。
- 验收：覆盖默认关闭、有效派生、空/越界/ oversized 派生和 encoder failure；覆盖 step 边界、mixed x-vector/ICL batch、ICL 与非目标请求保持未修改，以及实际 stage 配置能到达 talker。^[PR #5048]
