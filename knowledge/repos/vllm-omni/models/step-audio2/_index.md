---
title: "Step-Audio2（音频 token 内嵌 LM 词表的语音对话）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models]
sources: [vllm_omni/model_executor/models/step_audio2/, vllm_omni/deploy/step_audio_2.yaml, vllm_omni/model_executor/stage_input_processors/step_audio2.py]
---

# Step-Audio2

以下事实在 `main @ 5d44868e` 复核。

## 名称与范围

- 正式名称 Step-Audio 2（StepFun;文档/示例 checkpoint
  `stepfun-ai/Step-Audio-2-mini`,YAML 不 pin;token 配置声明跨 mini/7B 不变）。
  **三个变体共用这一个 checkpoint 与同一份 thinker 代码——变体由 pipeline
  对象 + deploy YAML 决定,不是模型代码分支。**
- AR registry 五入口 → 三个类：包装
  `StepAudio2ForConditionalGeneration`（`StepAudio2ForCausalLM` 只是
  registry 架构别名,不是另一个 Python 类）、thinker、token2wav;
  **无 diffusion 入口**。
- pipeline key 两个：`step_audio_2`（thinker→token2wav,双 final:文本+音频）
  与 `step_audio_2_asr`（仅 thinker,text 出;**无 `hf_architectures`,不能被
  自动探测,只能靠 deploy YAML `pipeline:` 键显式选择**）。
- 入口路径：拓扑 `model_executor/models/step_audio2/pipeline.py`（注册于
  `config/pipeline_registry.py`）;桥
  `model_executor/stage_input_processors/step_audio2.py`。
- 依赖共享模块：[Config 组件](../../components/config/architecture.md);
  家族专属 reasoning parser（`vllm_omni/reasoning/step_audio_reasoning_parser.py`）;
  serving 双入口——chat completions **和** `/v1/audio/speech`
  （`serving_speech.py`）。
- 独有外部运行时依赖：`onnxruntime`、`s3tokenizer`、`flashcosyvoice`、
  `hyperpyyaml`（token2wav CosyVoice 栈）。

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| token 过滤桥、25+3 lookahead、流式状态 | [architecture](architecture.md) | 数据流与 reviewer 陷阱 |

## 配置与 checkpoint 差异（三变体）

- `step_audio_2.yaml`：顺序模式（`async_chunk: false`,Token2Wav 等完整
  token 集）;thinker TP2 于 "0,1",token2wav 在 "1"。
- `step_audio_2_async_chunk.yaml`：同拓扑改流式（每块 25+3 lookahead）,
  `max_num_batched_tokens` 缩小。
- `step_audio_2_asr.yaml`：`pipeline: step_audio_2_asr` 单 stage 转写。
- **三份 YAML 都没有 `connectors:` 段**（对照 higgs/mimo）——连接器走框架
  默认,评审连接器默认值改动时把本家族当受影响方。

## 什么时候查这里

- 审查 step_audio2 的 token 过滤/分块、CosyVoice 栈或 ASR 变体选择;跨家族
  读 connector meta 时注意本家族 `left_context_size` 的语义陷阱（见
  architecture）。
- 语义验收见 [model-validation](../../review/guides/model-validation.md)。
