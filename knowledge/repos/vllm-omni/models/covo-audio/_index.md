---
title: "Covo-Audio（腾讯融合 thinker/talker 语音对话）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models]
sources: [vllm_omni/model_executor/models/covo_audio/, vllm_omni/deploy/covo_audio.yaml, vllm_omni/config/pipeline_registry.py]
---

# Covo-Audio

以下事实在 `main @ 5d44868e` 复核（源码派生页,尚无本模型的运行经验沉淀）。

## 名称与范围

- 正式名称 Covo-Audio-Chat（腾讯）。AR registry 三个别名
  `CovoAudioForCausalLM`/`CovoAudioForConditionalGeneration`/`CovoAudioModel`
  映射同一类,另有 `CovoAudioLLMModel`、`CovoAudioCode2WavModel`;家族目录
  `vllm_omni/model_executor/models/covo_audio/`。
- pipeline key `covo_audio`：stage 0 `fused_thinker_talker`（LLM_AR,多模态入、
  latent 出,`ignore_eos: True`,stop 151645）→ stage 1 `code2wav`
  （LLM_GENERATION,音频）。
- 依赖共享模块：[Config 组件](../../components/config/architecture.md)、
  Whisper 风格音频编码（`covo_audio.py`,`MAX_AUDIO_TOKENS=188`,16× 下采样）。

## 结构与 serving

- `token2wav.py`（31 KB）是 DiT 风格 token→wav（TimestepEmbedder/FinalLayer/
  rotary attention）;`stage_input_processors/covo_audio.py` 提供
  `llm2code2wav_full_payload`/`llm2code2wav_token_only` 两种交接。
- **树内带二进制资产**：`speaker_prompt/{prompt_latent,prompt_token,speaker_embed}.npy`
  （~300 KB 默认说话人 prompt,模型目录里检入 npy 在全仓少见）。
- deploy `covo_audio.yaml` 未 pin checkpoint;stage 1 强制 `dtype: float32`
  （BigVGAN vocoder fp32 权重）且 `enforce_eager: true`——code2wav 里有
  GPU→CPU 同步 `int(code.flatten()[0])`,CUDA-graph capture 非法（YAML 注释）;
  标注 1×A100-80G 验证。

## 什么时候查这里

- 审查 covo_audio 的 stage 交接、speaker prompt 资产或 fp32/eager 约束改动;
  放宽 stage 1 eager/fp32 前先确认上述两条来源注释仍成立。
- 语义验收（plumbing≠语义）见
  [model-adaptation-guardrails](../../review/guides/model-adaptation-guardrails.md)。
