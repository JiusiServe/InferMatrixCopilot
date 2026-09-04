---
title: "MiMo-Audio（融合 thinker+talker 单 AR stage 语音模型）"
created: 2026-07-21
updated: 2026-09-04
type: index
tags: [vllm-omni, models]
sources: ["PR #6559", recipes/XiaomiMiMo/MiMo-Audio.md, vllm_omni/model_executor/models/mimo_audio/, vllm_omni/deploy/mimo_audio.yaml, vllm_omni/deploy/mimo_audio_5090d.yaml, vllm_omni/model_executor/stage_input_processors/mimo_audio.py]
---

# MiMo-Audio

以下运行时事实在 `main @ 5d44868e` 复核；recipe/deploy 增量在 `main @ 816335cb` 复核。

## 名称与范围

- 正式名称 MiMo-Audio（Xiaomi）。示例默认 `XiaomiMiMo/MiMo-Audio-7B-Instruct`;
  audio tokenizer 是独立 checkpoint `XiaomiMiMo/MiMo-Audio-Tokenizer`,路径
  取 `model_config.audio_tokenizer_path`,环境变量
  `MIMO_AUDIO_TOKENIZER_PATH` 为替代来源,缺失即 raise——**永不从 LLM
  checkpoint 加载**;ASR 变体 checkpoint `XiaomiMiMo/MiMo-V2.5-ASR`（文档
  记载）,共享同一个类与同一条 pipeline,其 stage-1 预期行为 pin 上不可判定。
- AR registry 四入口：公开架构键 `MiMoAudioModel` 与
  `MiMoV2ASRForCausalLM` **都解析到 `MiMoAudioForConditionalGeneration`**
  （pin 上 ASR 名字只有命名差异,全仓 3 处引用,无 ASR 专属代码路径/deploy）;
  内部 stage 架构 `MiMoAudioLLMModel` → `MiMoAudioLLMForConditionalGeneration`、
  `MiMoAudioToken2WavModel` → `MiMoAudioToken2WavForConditionalGenerationVLLM`,
  由包装类按 stage 实例化,不是 HF config 名;**stage 1 无独立
  `model_arch`,由包装类解析**。
- pipeline key `mimo_audio`：stage 0 `fused_thinker_talker`（LLM_AR,
  **文本也是 final output**）→ stage 1 `code2wav`（LLM_GENERATION,音频）。
  **`MiMoAudioConfig` 继承 Qwen2Config,HF model_type 报 `qwen2`**——
  model_type 自动探测无法区分,靠 `hf_architectures` 匹配。
- 入口路径：registry `vllm_omni/model_executor/models/registry.py` 与
  `vllm_omni/config/pipeline_registry.py`;拓扑
  `vllm_omni/model_executor/models/mimo_audio/pipeline.py`;桥
  `vllm_omni/model_executor/stage_input_processors/mimo_audio.py`。
- 依赖共享模块：vLLM qwen2_audio 处理栈、SharedMemoryConnector、
  [Config 组件](../../components/configuration/architecture.md)。

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| 5+5 交错、码组几何、双 CUDA-graph、稳定性下限 | [architecture](architecture.md) | 数据流与 reviewer 陷阱 |

## 配置与 checkpoint 差异

- 默认 `mimo_audio.yaml` 是 `async_chunk: true` 单卡侧写；头注给出 legacy 双卡
  sync 模式的 `--stage-overrides` 用法，连接器为 `codec_chunk_frames 30` /
  `codec_left_context_frames 40`。PR #6559 另加模型专用
  `mimo_audio_5090d.yaml`：同一 GPU 上 stage 0/1 的 `0.78`/`0.12` 显存比例、
  `TRITON_ATTN`、eager、无 prefix cache 与 disabled FlashInfer autotune。它是社区在
  1× RTX 5090D 32 GB 的离线 `tts_sft` 观察，不是通用 Blackwell、在线服务或所有
  MiMo-Audio task 的运行时支持声明。
- 该 recipe 的 CPU tokenizer 省显存路径依赖 PR #6539（或等效 tokenizer-device
  修复）；目标 pin 没有合入该运行时修复。因此不能把 `MIMO_AUDIO_TOKENIZER_DEVICE=cpu`
  当作此版本无条件可用的默认能力，也不能从 recipe 的配置外推性能、音质或其他 SKU。
- 在线 serving 必须带 MiMo 自己的 `chat_template.jinja`
  （`examples/online_serving/mimo_audio/`）。
- 已知常量不一致（pin 上如实记录）：`MAX_CODE2WAV_TOKENS=18192` 与 stage-1
  `max_tokens 18192`,但默认侧写 stage-1 `max_model_len` 是 8192——从配置看
  单卡 async-chunk **似乎**依赖分块维持在 8192 内（配置推断,未经运行验证）,
  "keep in sync" 注释并未字面成立。

## 什么时候查这里

- 审查 mimo_audio 的码流分块、vocoder 上下文窗口或 CUDA graph 改动;ASR
  checkpoint 相关 PR 先确认是否真的存在 ASR 专属路径（pin 上没有）。
- 语义验收见 [model-validation](../../review/guides/model-validation.md)。
