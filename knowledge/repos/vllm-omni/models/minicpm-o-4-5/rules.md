---
title: "MiniCPM-o 4.5 规则"
created: 2026-07-20
updated: 2026-09-02
type: rule
tags: [vllm-omni, models, model-executor]
sources: ["PR #3642", "PR #5165", "PR #5382", "PR #5638", "PR #5792", "PR #5869", "PR #6154", "PR #6170", "PR #6318", vllm_omni/deploy/minicpmo_4_5.yaml, vllm_omni/model_executor/models/cosyvoice3/code2wav_core/hifigan.py, vllm_omni/model_executor/models/minicpmo_4_5/batched_token2wav.py, vllm_omni/model_executor/models/minicpmo_4_5/cuda_graph_wrapper.py, vllm_omni/model_executor/models/minicpmo_4_5/minicpmo_4_5_code2wav.py, vllm_omni/model_executor/models/minicpmo_4_5/minicpmo_4_5_omni_llm.py, vllm_omni/model_executor/models/minicpmo_4_5/minicpmo_4_5_omni_tts.py, tests/model_executor/models/minicpmo_4_5/test_audio_chunk_mask.py, tests/model_executor/models/minicpmo_4_5/test_code2wav_batching.py, tests/model_executor/models/minicpmo_4_5/test_cuda_graph_wrapper.py, tests/model_executor/models/minicpmo_4_5/test_pipeline.py, tests/model_executor/models/minicpmo_4_5/test_talker_batching.py, tests/model_executor/models/minicpmo_4_5/test_vision_flash_attention.py]
confidence: high
---

# MiniCPM-o 4.5 规则

只有 `MCPMO-数字字母` 是可审计规则 ID。

## Direct 代码快速入口

| PR 描述信号 | 规则组 | 第一批源码 |
|---|---|---|
| MiniCPM-o 4.5、`minicpmo_4_5`、版本识别 | MCPMO-2a | `config/pipeline_registry.py::OMNI_PIPELINES["minicpmo_4_5"]` → `model_executor/models/minicpmo_4_5/pipeline.py`；`model_executor/models/registry.py::_OMNI_MODELS` |
| Whisper/APM、chunk attention mask、left context/lookahead | MCPMO-2b | `minicpmo_4_5_omni_llm.py::{get_audio_hidden_states,subsequent_chunk_mask}` → audio encoder；row-by-row oracle test |
| SigLIP、FlashAttention、padding/unpad metadata、varlen vision | MCPMO-2c | `SiglipEncoder.forward` → `SiglipEncoderLayer` → `SiglipFlashAttention2._upad_input` |
| tokenizer/processor、`trust_remote_code` | MCPMO-1a | pipeline/config factory → `model_executor/models/minicpmo_4_5/` loader |
| TTS extra、backend 初始化、空音频 | MCPMO-1b | `minicpmo_4_5_omni_tts.py::MiniCPMO45OmniTTSForConditionalGeneration`、`minicpmo_4_5_token2wav.py::MiniCPMO45Token2wav` |
| Code2Wav TensorRT、DiT/Campplus、engine cache/profile | MCPMO-1c | `minicpmo_4_5_code2wav.py::MiniCPMO45Code2Wav` → `batched_token2wav.py::BatchedToken2Wav._estimator_step`；共享实现 `step_audio2/step_audio2_dit_trt.py` |
| HiFT CUDA Graph、chunk bucket、lazy capture、iSTFT | MCPMO-1d | `cuda_graph_wrapper.py::HiFTGraphWrapper` → `BatchedToken2Wav._hift_inference` → shared `HiFTGenerator` |
| batch、`runtime_info`、stage handoff | MCPMO-3a/3b | `stage_input_processors/minicpmo_4_5_omni.py` → `minicpmo_4_5_omni.py::MiniCPMO45OmniForConditionalGeneration` → TTS/code2wav |
| Talker codec sampling、repetition penalty、request RNG/compaction | MCPMO-3c | `minicpmo_4_5_omni_tts.py::{make_omni_output,_sample_audio_codes,_apply_batched_repetition_penalty}` → `test_talker_batching.py` |
| native duplex、Stage0 resume、LISTEN/SPEAK、server VAD | MCPMO-4a | `experimental/fullduplex/{minicpmo45,openai}/` → stage input processor |
| instructions/persona/voice/mode update、prefill slots、context lock | MCPMO-4b | `experimental/fullduplex/minicpmo45/session.py` → runtime adapter/session runner |

## MCPMO-1a — trust_remote_code 服从用户选择

- 触发：API/CLI server 为 MiniCPM-o 加载 tokenizer、processor、config 或模型代码。
- 强制：只使用 CLI/配置解析后的 `trust_remote_code` 值，并沿所有入口传递。
- 禁止：模型特例无条件设置 `True`，绕过用户的安全选择。
- 验收：false 路径不执行 remote code，true 路径按显式授权加载；offline/online 语义一致。 ^[PR #3642]

## MCPMO-1b — TTS 依赖显式声明，初始化失败不得伪装为空音频

- 触发：可选 TTS extra、音频 backend 或模型初始化异常。
- 强制：缺包使用明确 extra/import 错误；只有确认为 ImportError 的可选能力才可按合同
  降级，其他初始化失败立即向上抛出。
- 禁止：catch-all 后返回空 waveform，让请求看似成功。
- 验收：缺 extra、坏配置和 backend 初始化失败分别得到可诊断错误；正常路径返回非空
  且格式正确的音频。 ^[PR #3642]

## MCPMO-1c — Code2Wav TensorRT 是 CUDA-only 的显式可逆替换

- 触发：`token2wav_trt` / `MINICPMO_TOKEN2WAV_TRT=1`，或修改 Code2Wav 的 DiT、
  Campplus、ONNX/TRT engine cache 与 optimization profile。
- 强制：所有平台都先构造树内 `MiniCPMO45Token2wav`；开关只在 CUDA 同时启用 DiT
  estimator 与 Campplus 的 TensorRT 路径，非 CUDA 忽略开关，关闭开关保留完整 torch
  路径。DiT 只替换 `BatchedToken2Wav._estimator_step` 的逐步 estimator 调用，encoder 与
  HiFT 仍走 torch；engine 在调用者当前 CUDA stream 上执行。
- 强制：强类型精度来自所选 dtype 的 ONNX graph，export 深拷贝已加载 DiT 后再 cast，
  不改变 live torch estimator 的 dtype。ONNX cache 是动态、可移植 graph；plan cache key
  必须精确包含 depth、dtype、`token2wav_trt_max_batch`、GPU SM 与 TensorRT version。
- 强制：ONNX/plan 首次生成使用 PID 唯一临时文件并原子替换；step 在执行前检查 profile：
  batch 上限为配置值且包含 classifier-free guidance 展开的 `2B`，chunk 固定上限 3000，
  attention cache 固定上限 1000，越界给出可操作错误。Campplus 合同保持 `[T,80]` →
  `[1,192]` fp32，并从 `_resolve_model_dir()` 已解析的本地模型目录取资产。
- 禁止：把共享 `step_audio2_dit_trt.py` 的存在解释成 Step-Audio2 用户自动获得 TRT；
  当前开关只由 MiniCPM-o wiring 调用。也禁止把讨论中的通用 vocoder backend 当成已实现。
- 验收：分别覆盖关闭/开启、非 CUDA 忽略、torch/TRT 数值与音频 parity、首次构建和 cache
  复用、不同 SM 不共享 plan、CFG 后 batch 越界以及 chunk/cache 越界。PR 未新增自动化测试，
  因而这些仍是后续改动必须补证的验证缺口。 ^[PR #5638]

## MCPMO-1d — HiFT graph 只捕获稳定 pre-iSTFT 子图并限界 shape cache

- 触发：`enable_hift_graph`、capture batch/chunk 配置、HiFT inference 分段或 streaming cache shape。
- 强制：只在 parameter device 为 CUDA 时启用；非 CUDA 回 eager。capture bucket 由 codec chunk、
  left context、Flow lookahead、token→mel ratio 与 mel/source cache 推导；启动预捕 uncached/cached
  shape，未知 final shape 最多 lazy capture 8 个，超限或无可容纳 batch 时回 eager。active stream
  capture 中禁止嵌套 capture/replay并回 eager；静态输入先清零再复制真实 batch，输出 slice 后 clone。
- 强制：graph 只覆盖 `_inference_pre_istft`；`torch.istft` 的 NOLA CPU-GPU sync 与 waveform clamp
  留在 eager `_finalize_decode`。HiFT window/harmonic IDs 必须是随 module device 移动的 non-persistent
  buffers。开关独立于 stage `enforce_eager`；四份 bundled MiniCPM-o deploy 默认开启。
- 禁止：无 connector 配置、非正 chunk、负 left context、source/mel cache 不整除时静默 capture；
  将未来 `initial_codec_chunk_frames` 当已预捕（当前会 lazy capture）；把 lazy graph limit 说成总显存
  上界，因为启动 graphs、global pool、static tensors 与其他 graph owners 仍驻留。active-capture
  分支虽绕过 nested replay，却调用包含 NOLA sync 的完整 eager decode；未做真实 outer-graph 测试前，
  不能把日志中的 “fallback” 当成可捕获保证。custom `capture_batch_sizes` 也尚未校验正数/去重。
- 验收：CUDA test 比较 cached/uncached graph 与 eager，CPU/mock 覆盖 lazy capture/limit fallback，
  deploy test 固定默认开关；另测非 CUDA disable、invalid config、unsupported batch、nested capture 和
  variable final chunk。static input/output 与 lazy graph map 为无锁可变状态；并发 replay/capture 需先
  证明被上层串行化或增加互斥与重叠调用测试。PR 的单 A800 profile 约 30→5 ms/chunk、
  250→43 ms/request，只绑定部分 graph、
  单 prompt/commit `8fa28d88`，无 repeats/端到端质量，不能泛化为稳定 speedup。^[PR #5869]

## MCPMO-2a — registry 使用 4.5 config/version predicate

- 触发：pipeline auto-detection 看到通用 `MiniCPMO` architecture。
- 强制：结合 4.5 专有 architecture/config 字段判定；旧 1.0/2.6 不得落入 4.5 pipeline。
- 禁止：仅用 architecture 集合相交。
- 验收：4.5、旧版和无版本字段 fixture 分别命中 4.5、旧 pipeline 或明确失败。 ^[PR #3642]

## MCPMO-2b — audio chunk mask 向量化必须保持逐行边界语义

- 触发：修改 Whisper/APM `subsequent_chunk_mask`、chunk size、left-context 或 lookahead。
- 强制：对每个 query row，end 保持 `min((row // chunk_size + 1) * chunk_size +
  num_lookhead, size)`；`num_left_chunks < 0` 从 key 0 开始，否则 start 保持
  `max((row // chunk_size - num_left_chunks) * chunk_size, 0)`。可用 query/key index
  broadcast 一次构造 dense bool `[T,T]` mask，但不得改变 caller 与 padding mask 的 OR/取反语义。
- 禁止：把移除 O(T) Python row loop 描述成移除 O(T²) mask storage/attention；把 reviewer
  建议的 `@staticmethod` 当成已合并（目标仍保留 instance-method interface）；或声称所有 TTFT
  case 都改善。PR 自己记录短输入/较大 batch 的 scheduler noise 会淹没局部节省。
- 验收：row-by-row oracle 覆盖 size 0、chunk 边界两侧、无限/有限/零 left context 与 lookahead，
  并在真实 caller 组合 padding mask。目标提交的 CPU 参数化测试覆盖 216 组纯 mask parity，
  但不覆盖 CUDA kernel 数、完整 audio embedding 或 serving。PR 的 CUDA timing/bitwise embedding
  证据来自 `ee33954dff27da317be597449a6c1b5a5df4052b`，不是 merge target `9235b0ae` 的复测，
  因而只能作为外部局部性能证据。^[PR #5382]

## MCPMO-2c — vision unpadding metadata 只在同一次 encoder forward 内复用

- 触发：修改 MiniCPM-o 4.5 SigLIP FlashAttention mask、`_get_unpad_data`、Q/K/V layout 或
  encoder layer 调用链。
- 强制：只有 FlashAttention2 且 `attention_mask is not None` 时，`SiglipEncoder.forward` 才从
  当前 mask 计算一次 `(indices, cu_seqlens, max_seqlen)`，并把同一 tuple identity 传给该次
  forward 的所有 encoder layers。下一次 forward 必须从新 mask 重算；不得做 global、实例级或
  cross-request cache。直接调用 `SiglipFlashAttention2` 且未传 metadata 时，`_upad_input` 保留
  per-call fallback；dense mask=None path 不计算 metadata。显式传入的 metadata 不会校验是否与
  `attention_mask` 匹配，因此 custom/direct caller 必须成对持有；安全 owner 是 encoder 当前
  forward 的 mask，禁止外部或 stale cache。
- 强制：metadata 复用必须保持 padded batch 输出与逐 sample unpadded、以及逐 layer 重算 path
  数值一致。Q/K/V projection 的 view→transpose→transpose 原本就形成共享 projection storage 的
  contiguous BSHD；本 PR 没改 layout，新 storage/stride test 只是冻结该既有 zero-copy 合同，
  不能把它计入 metadata 优化收益。
- 禁止：把 mask shape 相同当成内容相同而跨 forward 复用；将该局部优化泛化成 dense image、
  equal-length video、端到端 serving 或 throughput 提升。review 中短暂加入的 profiler scripts/raw
  JSON 已在 final commit history 删除，不是仓库内可复现 benchmark fixture。
- 验收：CPU spy 覆盖 padded 一次、dense 零次、不同 mask 重算与 tuple identity；L4/FA2 BF16
  覆盖 encoder reuse 对 per-layer recompute bitwise parity、unpadded 对 eager、两种 padding 程度
  对逐 sample unpadded（容差 2e-2）。PR 的 2×RTX PRO 6000 Blackwell、27 layers、5 warmups、
  30 paired samples 中 varlen 约 21.697→13.790 ms / 22.162→14.113 ms，只绑定测试 commit
  `895cb303`、该环境与 vision-encoder latency；作者说明 rebase 后 source-file hash 未变，但它
  仍不是 merge target 的 end-to-end 复测。dense/equal-length video 不计算 metadata且近零变化。
  当前测试未覆盖 `gradient_checkpointing and training`：新 tuple（两 tensor + Python int）会作为
  位置参数穿过 `_gradient_checkpointing_func`，补该 path 前不能假设训练/checkpoint 兼容。
  ^[PR #5165]

## MCPMO-3a — TTS stage 的 batch 能力与 runtime_info 消费一致

- 触发：talker/TTS stage 的 `max_num_seqs`、batching 或 runtime bridge。
- 强制：若实现只安全消费一条 runtime info，将上限设为 1；开放 batch 前逐请求处理并
  证明输出不串线。
- 禁止：读取 `runtime_info[0]` 后把请求 0 的音频广播到全批。
- 验收：两个不同文本/voice 的同批测试分别产生对应音频；未支持前配置拒绝 batch>1。 ^[PR #3642]

## MCPMO-3b — wrapper 接收 bridge 并显式包装 OmniOutput

- 触发：LLM/thinker → TTS stage handoff 或 TTS class 返回 waveform。
- 强制：stage wrapper 读取 runner 实际写入的 bridge 字段，模型输出包装到明确的
  `OmniOutput`/multimodal key。
- 禁止：直接 TTS class 不读 runtime bridge；返回 tuple 让 runner 猜它是 hidden state。
- 验收：真实 wrapper handoff 测试断言字段名、逐请求 shape、最终公开 payload。 ^[PR #3642]

## MCPMO-3c — Talker 批量 logit 处理必须保留逐请求采样与输出索引

- 触发：修改 Talker `make_omni_output`、codec projection、repetition penalty、top-k/top-p、
  multinomial、terminal 或 compaction。
- 强制：只把有效 span、未 finished 且 sampling-eligible 的 row 收集为 pending samples；一次批量
  执行 head projection、frequency-aware repetition penalty、top-k/top-p 与 softmax。每个 pending
  item 必须携带原 `output_index`、request ID、history、step 与 state，采样结果再按该原索引写回
  codec delta、terminal 和 stop row。无效 info/span 与 incomplete prefill 保持 continue、空 delta，
  且不推进 request RNG/state；此前或本次 terminal 的请求才 stop。
- RNG：`torch.multinomial` 每次只接收一个 generator，因此必须保留逐 row 调用各自 request-local
  generator；禁止为了完全向量化而改成共享 generator。batch reorder、其他请求结束和 compaction
  均不得改变单请求序列。所有 row 采完后再把 concatenated tensor 一次搬到 CPU `.tolist()`，
  避免逐请求 `.item()` 同步。
- workspace：repetition penalty 可保留 full-batch logits/result，但 encoded history 与
  `bincount` 必须最多按 16 rows 分块；token 编码为 `token + local_row*vocab`，count minlength
  只到 `chunk_rows*vocab`，使 int64 count 临时空间不随总并发一次放大。penalty=1 与空 batch
  保持 fast path，logits 必须为 2D且 histories/request IDs/steps 与 batch row 数一致。
- 验收：逐 row oracle 对比正负 logits 与空 history，跨 16/16/1 chunk 固定 bincount workspace；
  reorder、compaction 与 standalone 对照 request RNG；mixed eligible/ineligible/finished rows 断言
  原索引 delta、stop、EOS/min/max token、duplex metadata 和只调用一次 batched sampler。CPU 单测
  证明这些离散合同，但没有硬件上的 batched GEMM/logit 与旧 serial GEMV 数值/音频 parity；PR
  也没有 NPU concurrency 1/4 的 latency、吞吐或内存数据，因此不得宣称性能或质量不变/提升。
  ^[PR #5792]

## MCPMO-4a — native duplex 保留可恢复 Stage0，VAD 只作显式策略

- 触发：MiniCPM-o native duplex 的连续音频、LISTEN/SPEAK handoff 或 server VAD interruption。
- 强制：模型说话时仍把音频单元追加到同一可恢复 Stage0，保留 KV/runtime state 和上一
  terminator；LISTEN 是成功且不需要 Talker hidden state，SPEAK 才转交 Talker。server VAD
  hard cancellation 必须显式 opt-in，阈值不得落到使 silence branch 不可达的边界。
- 禁止：用 server VAD cancellation 冒充 native interruption；每轮重建 Stage0；让 LISTEN 因
  无 Talker payload 失败。
- 验收：native case 完成响应≥2、cancel/truncate=0、listen≥1；opt-in hard interrupt 恰好一次
  terminal、fence 后无 stale delta、保留打断语句且后续响应成功。 ^[PR #6154] ^[PR #6170]

## MCPMO-4b — session update 与派生 reservation 原子提交

- 触发：运行中更新 instructions、persona、voice、native mode 或影响 prefill slot 的字段。
- 强制：先重算并验证 `prefill_slots`/first-append context tokens 等派生状态，再 ACK 并原子提交；
  `native_context_locked` 只在真实 append 成功后设置。route-defining native mode 在 session 内不可变。
- 禁止：buffered/deferred/rejected append 提前锁定；配置已变而 reservation 保持旧值；用
  true→false 绕过 native context lock。
- 验收：成功更新同时改变派生状态；资源不足时无部分 mutation；buffer/defer/reject 均不锁，
  append 成功才锁，mode flip 明确拒绝。 ^[PR #6318]

共享 bridge/batch 规则见 [Model Executor rules](../../components/model-executor/rules.md)；
公开入口完整性见 [model adaptation guardrails](../../review/guides/model-adaptation-guardrails.md)。
