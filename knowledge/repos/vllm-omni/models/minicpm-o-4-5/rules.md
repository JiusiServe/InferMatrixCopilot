---
title: "MiniCPM-o 4.5 规则"
created: 2026-07-20
updated: 2026-09-02
type: rule
tags: [vllm-omni, models, model-executor]
sources: ["PR #3642", "PR #5382", "PR #5638", "PR #6154", "PR #6170", "PR #6318", vllm_omni/model_executor/models/minicpmo_4_5/minicpmo_4_5_omni_llm.py, tests/model_executor/models/minicpmo_4_5/test_audio_chunk_mask.py]
confidence: high
---

# MiniCPM-o 4.5 规则

只有 `MCPMO-数字字母` 是可审计规则 ID。

## Direct 代码快速入口

| PR 描述信号 | 规则组 | 第一批源码 |
|---|---|---|
| MiniCPM-o 4.5、`minicpmo_4_5`、版本识别 | MCPMO-2a | `config/pipeline_registry.py::OMNI_PIPELINES["minicpmo_4_5"]` → `model_executor/models/minicpmo_4_5/pipeline.py`；`model_executor/models/registry.py::_OMNI_MODELS` |
| Whisper/APM、chunk attention mask、left context/lookahead | MCPMO-2b | `minicpmo_4_5_omni_llm.py::{get_audio_hidden_states,subsequent_chunk_mask}` → audio encoder；row-by-row oracle test |
| tokenizer/processor、`trust_remote_code` | MCPMO-1a | pipeline/config factory → `model_executor/models/minicpmo_4_5/` loader |
| TTS extra、backend 初始化、空音频 | MCPMO-1b | `minicpmo_4_5_omni_tts.py::MiniCPMO45OmniTTSForConditionalGeneration`、`minicpmo_4_5_token2wav.py::MiniCPMO45Token2wav` |
| Code2Wav TensorRT、DiT/Campplus、engine cache/profile | MCPMO-1c | `minicpmo_4_5_code2wav.py::MiniCPMO45Code2Wav` → `batched_token2wav.py::BatchedToken2Wav._estimator_step`；共享实现 `step_audio2/step_audio2_dit_trt.py` |
| batch、`runtime_info`、stage handoff | MCPMO-3a/3b | `stage_input_processors/minicpmo_4_5_omni.py` → `minicpmo_4_5_omni.py::MiniCPMO45OmniForConditionalGeneration` → TTS/code2wav |
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
