---
title: "Qwen3-TTS MRv2 模型流水线"
created: 2026-10-09
updated: 2026-10-09
type: guide
tags: [vllm-omni, models, serving, qwen-omni]
sources:
  - https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/qwen3_tts/qwen3_tts_talker.py
  - https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/qwen3_tts/prompt_embeds_builder.py
  - https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/qwen3_tts/qwen3_tts_code2wav.py
  - https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/common/qwen3_code_predictor.py
  - https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/stage_input_processors/qwen3_tts.py
  - https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/qwen3_tts/tokenizer_12hz/modeling_qwen3_tts_tokenizer_v2.py
confidence: high
---

# Qwen3-TTS MRv2 模型流水线

本文说明 PR #7781 冻结 head `2e3c7fe2c171cd3429298094d175a64eacbdb341` 的模型接口和验证方法。
它是历史源码快照，不表示当前默认部署或后续 revision 的行为。共享机制见
[MRv2 runtime](../../components/model-executor/mrv2-runtime.md)、
[MRv2 profiles](../../components/configuration/mrv2-profiles.md)、
[native chunk lifecycle](../../components/scheduler/native-chunk-lifecycle.md)。
已有 ref-audio readiness、incremental decoder、adaptive ramp、silence ban 和 NPU 合同继续由
[模型规则](rules.md) 承载；后续改动见 [prompt preprocess](rules-prompt-preprocess.md)
和 [codec output](rules-codec-output.md)。

## flow

stage 0 AR Talker 产生 RVQ codec，stage 1 generation Code2Wav 输出音频；两者都声明支持
native MRv2 data plane。`deploy.async_chunk` 选择分块或全载荷路径，默认 deploy 名称仍是
`qwen3_tts.yaml`。[源码：pipeline](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/qwen3_tts/pipeline.py#L30-L73)。

MRv2 prefill 保留完整 prompt embedding 和 reference codes，后续 prefill 只切片已有 buffer；
decode batch 可消费 runner 已准备的 embeddings，组合上一 Talker hidden 与当前 text step。
[源码：prefill](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/qwen3_tts/qwen3_tts_talker.py#L920-L980)。

模型专用 batch chunk builder 将同一步的有效 codec frame 和首次 reference codes 按 device
合并，每个非 CPU device 至多一次 cohort D2H，再沿用 scalar builder 的边界和 metadata。
Code2Wav 将 CPU codes 打包成 pinned `[B,Q,F]` buffer 后一次 non-blocking H2D，保留逐请求真实
frame lengths。[源码：batch transfer](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/stage_input_processors/qwen3_tts.py#L424-L507)、
[decoder staging](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/qwen3_tts/qwen3_tts_code2wav.py#L456-L477)。

## api

| 接口 | 输入与结果 |
|---|---|
| `preprocess_batch_mrv2` | 当前 `req_infos`、device → 批量准备新 prefill slots |
| `preprocess_decode_batch_mrv2` | IDs、prepared embeddings、`req_infos` → embeddings、past hidden、text step、updates |
| `postprocess_batch_mrv2` | hidden states、last-token indices → 一次 `index_select` 的 `OwnedBatchTensor` |
| `mrv2_sampling_context` | 请求顺序、generated-token counts → sampling 作用域的 silence mask |

owned gather 新分配结果，buffer 保存 row views 可省第二次 snapshot。`mtp` 沿用 `talker_mtp`；
其 output-key、graph-safe、per-row-generator capability 读取 V1 canonical 字段，使平台 patch
同时生效。[源码：batch hooks](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/qwen3_tts/qwen3_tts_talker.py#L1181-L1267)、
[MTP aliases](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/qwen3_tts/qwen3_tts_talker.py#L1558-L1573)。

Code2Wav 的非空 `codes.audio` 是 authoritative native input，scheduler token IDs 可只是控制槽位。
predictor 接受 `[B,G-1,V]` 的 `sample_uniforms`；此 shape 合同不证明最终 PCM parity。
[源码：native input](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/qwen3_tts/qwen3_tts_code2wav.py#L36-L69)、
[sampling input](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/common/qwen3_code_predictor.py#L1081-L1107)。

## configuration

| 控制项 | 此快照的含义 |
|---|---|
| `use_v2_model_runner` | 额外保持 `codes.ref`、`embed.prefill`、`meta.codec_frame_valid` 的 GPU residency；V1 保持原策略 |
| connector `extra.ref_audio_artifact_cache_max_entries` | 默认 1024；整数解析失败或负数时报错；0 禁用 worker cache |
| `code_predictor_prefix_graphs` | 非 NPU 可启用短 prefix re-prefill；predictor-owned graphs 还要求 wrapper `use_cuda_graphs` |
| execution buckets | MRv2 对齐外层 capture sizes，并加入 batch 1/max；在首次 warmup 前声明 |

对应源码见 [residency/cache capacity](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/qwen3_tts/qwen3_tts_talker.py#L50-L120)、
[outer buckets](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/qwen3_tts/qwen3_tts_talker.py#L511-L524)、
[prefix switches](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/common/qwen3_code_predictor.py#L685-L707)。
完整 profile 继承与 server/worker cache 协调分别见共享配置页和
[reference audio cache](../../components/serving/reference-audio-cache.md)。

## dependencies

prefix re-prefill 与 predictor-owned graph 分离，使外层 MRv2 capture 可录制短 compiled forward。
已 warmup 后声明未覆盖 bucket 会报错；compile cache allowance 随 batch/prefix 组合扩大，
non-CPU warmup 完成后同步，再让 capture/serving 复用 static buffer。
[源码：bucket/warmup](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/common/qwen3_code_predictor.py#L875-L980)。

tokenizer 只对 implicit-position stateless call 缓存 broadcastable sliding mask，key 包含 length、
dtype、device、attention implementation；placement/dtype 变化清空缓存。显式 positions、
cache positions、prepared mask 或 incremental/cache-enabled call 走 live/prepared path。
按 Transformers signature 选择 `input_embeds`/`inputs_embeds`。
[源码：mask cache/path](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/qwen3_tts/tokenizer_12hz/modeling_qwen3_tts_tokenizer_v2.py#L533-L661)。

production `enable_cudagraph` 导入 `segmented_graph_wrapper`；同 PR 修改的 legacy wrapper
按最小 `(batch*frames,batch,frames)` 选择 containing capture，补齐并 trim 两轴。legacy 的
padded-batch 测试不能替代 production async/adaptive graph 证据。
[源码：production import](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/qwen3_tts/tokenizer_12hz/modeling_qwen3_tts_tokenizer_v2.py#L1000-L1037)、
[legacy selection](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/qwen3_tts/cuda_graph_decoder_wrapper.py#L230-L245)。

## failure_modes

`codec_frame_valid` 描述已处理的 input token；decode 按 `0 <= token < codebook_vocab_size`
计算。consumer 对多行 span 取最后 validity，因而刚采到 EOS 时仍保留前一 token 的真实 frame。
显式 true 允许有效零码；只有旧 producer 缺字段时才 fallback `frame.any()`，该 fallback 无法
区分零码与 padding。[源码：decode validity](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/qwen3_tts/qwen3_tts_talker.py#L1056-L1090)、
[consumer](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/stage_input_processors/qwen3_tts.py#L65-L103)。

async ref 使用请求 metadata 位只发布一次，包括 KV-resumed 首次 decode；无 ref 的请求仍占
batch-aligned 空 entry。emitted-frame counter 抑制重复 callback，terminal 只 flush 未发余帧，
无新帧时发 empty-finished sentinel。segment/request cleanup 见共享生命周期页。
[源码：ref publication](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/qwen3_tts/qwen3_tts_talker.py#L768-L783)、
[repeat suppression](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/stage_input_processors/qwen3_tts.py#L209-L221)。
API 节的 sampling context 在 `finally` 清空 silence mask，避免污染随后 prompt logprobs；
词表和 x-vector-only 范围沿用模型规则。

## tradeoffs

GPU residency/cache 减少往返传输但保留更多 device memory，LRU 按 entries 而非 bytes 限制。
Base text/ref-text 的有效 ragged IDs 一次打包 pinned buffer，传到目标设备后按请求切片。
decoder 只 clone 被选 request 的 KV rows，再 deepcopy 其余 metadata，保留独立 ownership。
[源码：artifact LRU](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/qwen3_tts/prompt_embeds_builder.py#L636-L666)、
[packed IDs](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/qwen3_tts/prompt_embeds_builder.py#L876-L902)、
[selected KV clone](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/model_executor/models/qwen3_tts/tokenizer_12hz/modeling_qwen3_tts_tokenizer_v2.py#L1465-L1477)。

性能需区分硬件、revision 和 decoder batch；以下是作者报告的历史测量，本次未复跑或核验
raw logs。body 声明的 `b9648399` head 与其 `500f5626` + cleanup 测量不同，
均不是冻结 `2e3c7fe2` 的实测结果。

| 对照 | 观察与证据边界 |
|---|---|
| [早期 H200 whole-PR](https://github.com/vllm-project/vllm-omni/pull/7781#issuecomment-5736514458) | main `d4ffde1a6` + cache patches 对 PR `500f5626` + cleanup/B2；1/2 张 H200。包含共享优化；单卡有失败且 underrun 增加，不是 runner-only 或当前 head 证明 |
| [H100 同 revision B2](https://github.com/vllm-project/vllm-omni/pull/7781#issuecomment-5737185088) | `b9648399` V2/V1：C64 吞吐 -2.6%，C128 pooled +1.1% 受 V1 failed round 影响；V2 首包更慢。whole-PR 对旧 main 还含 256→1024 cache 差异 |
| [H200 同 revision B8](https://github.com/vllm-project/vllm-omni/pull/7781#issuecomment-5740198338) | `b9648399`，limit 32、B8、C128、无 MPS：V2 +15.4%，首包更慢；B8 比 B4 多约 5.2 GiB。V2/B2→V2/B8 改变 decoder 调优，不能作为只切换 runner 的收益 |
| [较新 H100 B8](https://github.com/vllm-project/vllm-omni/pull/7781#issuecomment-5748583581) | `035669872b308a505a7d534b59c4760e2f659b46`，文中称 `63948114` production tree 相同；两边都加临时 scheduler patch。C64/C128 吞吐 +17.8%/+18.1%，8704 timed requests 全成功，首包中位数仍更高 |

较新 B8 使用 H100 80GB、vLLM 0.29.0、Base 1.7B、Seed-TTS English 1088、无 MPS，
fresh-server V2–V1–V1–V2，每组排除完整 warmup 后测两轮，未做音质评分。
该次未修改 V2 因 running-list queue API mismatch 在 warmup 崩溃（0/1088 成功），
没有未修改 timed rounds。两臂相同临时 patch 的结果不能证明冻结 head 的吞吐或可靠性；
first-audio latency、内存和 playback deficit 应与吞吐一起比较。

## validation

本次检查冻结 head 的测试源码，未运行上游单测、GPU 实验或 real-weight e2e。
实测时绑定实际 revision、硬件与配置，分开报告下列证据：

| 测试入口 | 此快照检查的行为 |
|---|---|
| [async chunk tests](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/tests/model_executor/stage_input_processors/test_qwen3_tts_async_chunk.py#L39-L359) | 重复 callback/terminal flush、authoritative validity、EOS 后保留最后 frame、batch/scalar parity |
| [reference output tests](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/tests/model_executor/models/qwen3_tts/test_qwen3_tts_talker_ref_codes.py#L109-L145) | resumed request ref 只发布一次、逐请求 validity |
| [H100 async output test](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/tests/model_executor/models/qwen3_tts/test_qwen3_tts_output_async_cuda.py#L19-L55) | output construction 不等待此前 forward、CPU/CUDA validity 值保持 |
| [L4 capture tests](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/tests/model_executor/models/qwen3_tts/test_qwen3_tts_stateless_capture.py#L21-L100) | implicit/explicit positions 真正 capture 并消费新输入；production segmented waveform capture |

进一步验证可覆盖 prepared-embedding reuse、owned tails、silence mask 作用域、bucket 声明边界
和 seeded PCM。小型 decoder capture 只覆盖指定 mask/shape 的数值 replay，不能证明完整
checkpoint 音质、跨平台性能或任意 position pattern。legacy padded-batch 与 production
segmented 测试需独立报告；已有 adaptive graph 限制不能从 legacy containing-bucket 支持推断已解。
