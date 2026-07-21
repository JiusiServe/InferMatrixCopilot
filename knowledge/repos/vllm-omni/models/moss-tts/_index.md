---
title: "MOSS-TTS 家族（Delay/Realtime/Local/Nano,一族八 deploy）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models]
sources: [vllm_omni/model_executor/models/registry.py, vllm_omni/config/pipeline_registry.py, vllm_omni/model_executor/models/moss_tts/, vllm_omni/model_executor/models/moss_tts_nano/, vllm_omni/model_executor/stage_input_processors/moss_tts.py, vllm_omni/deploy/moss_tts.yaml]
---

# MOSS-TTS 家族

以下事实在 `main @ 5d44868e` 复核。

## 名称与范围

- OpenMOSS 系 TTS 全家（两个家族目录 `moss_tts` + `moss_tts_nano`）。
  架构→类→checkpoint 映射：
  - `MossTTSDelayModel` → `MossTTSDelayTalkerForGeneration`,**一个架构服务
    4 个 HF 仓**：`OpenMOSS-Team/MOSS-TTS`（8B,n_vq=32）、
    `OpenMOSS-Team/MOSS-TTSD-v1.0`（对话）、`OpenMOSS-Team/MOSS-SoundEffect`、
    `OpenMOSS-Team/MOSS-VoiceGenerator`（1.7B）——仓间差异只在 HF config +
    deploy YAML（`moss_tts_80gb.yaml` 是 MOSS-TTS 的纯 deploy 变体）。
  - `MossTTSRealtime` → `MossTTSRealtimeTalkerForGeneration`
    （`OpenMOSS-Team/MOSS-TTS-Realtime`,1.7B）。
  - `MossTTSLocalModel` → `MossTTSLocalTalkerForGeneration`
    （`OpenMOSS-Team/MOSS-TTS-Local-Transformer-v1.5`）。
  - `MossTTSNanoForCausalLM` → `MossTTSNanoForGeneration`
    （`OpenMOSS-Team/MOSS-TTS-Nano`,0.1B,独立目录）。
  - stage-1 共用架构 `MossTTSCodecDecoder`（同名类）。
- pipeline key 四个（`moss_tts/pipeline.py` 与 `moss_tts_nano/pipeline.py`,
  注册于 `config/pipeline_registry.py`）：`moss_tts_delay` /
  `moss_tts_realtime`（model_stage 对 `moss_tts`→`moss_tts_codec`）/
  `moss_tts_local`（**独立 stage 名对** `moss_tts_local`→
  `moss_tts_local_codec`,serving 适配按此路由）/ `moss_tts_nano`
  （**单 stage**,AR LM+codec 全在 `forward()` 内以 VoxCPM 式
  `inference_stream()` 生成器跑,EOS id 2 由 compute_logits 强制）。
- 依赖共享模块：[Config 组件](../../components/config/architecture.md)、
  `utils/speaker_cache`、serving 适配
  `entrypoints/openai/tts_adapters/moss_tts.py`。

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| delay 生命周期、伪文本 logits、双代 tokenizer | [architecture](architecture.md) | 数据流与 reviewer 陷阱 |

## 配置与 checkpoint 差异（8 份 deploy 速查）

- `moss_tts.yaml`（8B,n_vq=32,24 kHz;**唯一开 codec CUDA graph 的变体**,
  stage1 `max_model_len 196608`——4096 帧×32 vq 会超 65536）;
  `moss_tts_80gb.yaml` 仅差 stage0 显存 0.85→0.60 + eager codec +
  `enable_flashinfer_autotune: false`（单卡 80 GB 装得下,#4643）。
- `moss_ttsd.yaml`（对话 TTS,n_vq=16）;`moss_sound_effect.yaml`
  （文描音效,无参考音频,~12.5 tok/s）;`moss_voice_generator.yaml`
  （1.7B 零样本声音设计,**stage0 强制 eager——自定义音频头+每请求 GPU 缓冲
  不 CUDA-graph 安全,FULL-decode 捕获会崩 worker**）。
- `moss_tts_realtime.yaml`（TTFB ~180 ms,`codec_chunk_frames 15`）;
  `moss_tts_local.yaml`（**48 kHz 立体声**,v2 tokenizer,首块 80 ms;顶层缺
  `trust_remote_code`,与其余变体不一致——pin 上未验证是否有意）;
  `moss_tts_nano.yaml`（L4 验证,无 connectors,`skip_mm_profiling`）。
- 权威 checkpoint→deploy 映射在
  `examples/offline_inference/text_to_speech/moss_tts/end2end.py`。

## 什么时候查这里

- 审查任一 MOSS 变体的码流、CUDA-graph 开关或 serving 适配;新增变体时先对
  这 8 份 YAML 的差异矩阵。
- 语义验收见 [model-validation](../../review/guides/model-validation.md)。
