---
title: "MOSS-TTS 架构"
created: 2026-07-21
updated: 2026-07-21
type: architecture
tags: [vllm-omni, models]
sources: [vllm_omni/model_executor/models/moss_tts/modeling_moss_tts_talker.py, vllm_omni/model_executor/models/moss_tts/modeling_moss_tts_codec.py, vllm_omni/model_executor/models/moss_tts_nano/modeling_moss_tts_nano.py, vllm_omni/model_executor/models/moss_tts/pipeline.py, vllm_omni/model_executor/stage_input_processors/moss_tts.py, vllm_omni/deploy/moss_voice_generator.yaml]
---

# MOSS-TTS 架构

事实在 `main @ 5d44868e` 复核;变体/deploy 速查见 [index](_index.md)。

## 模型专有部分与共享模块的边界

- Delay talker：Qwen3 backbone + `(n_vq+1)` 并行头（头 0 = 文本 logits 驱动
  AR 调度;头 1..n_vq = 各 RVQ codebook 音频 logits）;delay pattern 由
  delay-slot token 触发,codebook *i* 落后 codebook 0 *i* 步。
- Realtime talker：**没有文本 LM 头**——喂给 vLLM 采样器的文本行是确定性
  合成的（`text_pad`/EOS）,真实音频采样在每步 4 层 local transformer 内;
  停止条件 codebook-0 == `AUDIO_EOS` 1026。
- Local talker（v1.5）：checkpoint 前缀 `transformer.*`;每帧走 1 层 GPT2 式
  depth transformer（runner 的 `talker_mtp` 路径）;checkpoint 的
  `text_lm_head` 加载但不用（binary 停止头判停）。
- 共享 codec `MossTTSCodecDecoder`：**同一解码器里装两代 audio tokenizer**
  （v1 24 kHz;v2 48 kHz 立体声,带 `RingKVCache` 流式基建）+ 两个 CUDA-graph
  wrapper（批解码 vs 流式解码）;按 codec checkpoint config 运行期选代。
- 共享框架面：[Config 组件](../../components/config/architecture.md)、
  SharedMemoryConnector、speaker cache（`reference_encoder.py`,树内注明援引
  Fish/CosyVoice3/Qwen3-TTS 先例）。

## 配置、checkpoint 和兼容范围

- Stage-0/1 合同：`(T, NQ)` 码网格,codebook-major 展平;**de-delay 与
  pad 行过滤在 stage input processor 做,不在模型里**（pad 码硬编码 1024）。
- CUDA-graph 安全不对称：8B delay talker 可开 stage-0 graph;VoiceGenerator
  必须 eager(每请求 GPU 缓冲不 graph 安全);codec graph 只在 `moss_tts.yaml`
  开。

## 从输入到输出的主要流程

1. talker 逐步出码;**delay talker 每步重发整个累积网格**——SIP 按上次长度
   做差分,只追加新尾行(否则平方级重复)。
2. **delay 路流式当前实质关闭**：`talker2codec_delay_async_chunk` 把
   `chunk_frames` 设为 `1 << 30`（只在完成时发射）,因为 codec 移植缺左上下文
   管线——尽管所有 delay YAML 都写着 `async_chunk: true` +
   `codec_streaming: true`。Realtime/Local 走 `talker2codec_raw_async_chunk`
   原始行路径,真流式。评审"顺手打开 delay 流式"的 PR 必须先补 codec 左上
   下文。
3. codec：RVQ 码 → 波形（v1 24 kHz 单声道 / v2 48 kHz 立体声,通道交错
   RVQ）;`_MossCodecStreamSession` 持每请求流态。
4. Nano：单 stage,`inference_stream()` 生成器内完成 AR+codec;eager
   （上游生成器未接 CUDA graph）。

## 怎样验证功能、精度和性能

- e2e：`tests/e2e/offline_inference/test_moss_tts_expansion.py`（delay）、
  `test_moss_tts_v1_5_expansion.py`（Local）、`test_moss_tts_realtime*.py`、
  `test_moss_tts_nano_expansion.py` + online 两份;示例
  `examples/offline_inference/text_to_speech/moss_tts{,_nano}/end2end.py`
  （前者手工构建 delay 网格,并内含六个两 stage 仓的 checkpoint→deploy
  权威映射）;recipe `recipes/OpenMOSS/MOSS-TTS.md`。
- 已知未决：delay 路下 connector 级 `codec_chunk_frames` 是否还有残余作用
  未追;`moss_tts_local_codec` 与 `moss_tts_codec` 在 serving 侧的分流细节
  未逐行读;v1/v2 tokenizer 运行期选代逻辑未细读。
