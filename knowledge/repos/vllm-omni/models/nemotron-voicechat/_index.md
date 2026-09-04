---
title: "NVIDIA Nemotron-Labs VoiceChat"
created: 2026-09-04
updated: 2026-09-04
type: index
tags: [vllm-omni, models, serving]
sources: ["PR #6089", vllm_omni/deploy/nemotron_labs_voicechat.yaml, vllm_omni/deploy/nemotron_labs_voicechat_duplex.yaml, vllm_omni/deploy/nemotron_labs_voicechat_streaming.yaml, vllm_omni/experimental/fullduplex/nemotron_voicechat/, vllm_omni/model_executor/models/nemotron_voicechat/, vllm_omni/model_executor/models/nemotron_voicechat/nemo_vendored/, vllm_omni/model_executor/models/nemotron_voicechat/nemo_vendored/asr/, vllm_omni/model_executor/stage_input_processors/nemotron_voicechat.py]
confidence: high
---

# NVIDIA Nemotron-Labs VoiceChat

## 正式名称与别名

- 知识树 owner：`models/nemotron-voicechat`；上游目录 `nemotron_voicechat`。
- pipeline registry key：`nemotron_labs_voicechat`；`nemotron_voicechat`（`vllm_omni/config/pipeline_registry.py`）。
- registry 登记的 architecture / stage key：`nemotron_voicechat_code2wav`；`nemotron_voicechat_talker`；`nemotron_voicechat_thinker`。

## 源码路径

共 30 个文件：

- `vllm_omni/deploy/nemotron_labs_voicechat.yaml`
- `vllm_omni/deploy/nemotron_labs_voicechat_duplex.yaml`
- `vllm_omni/deploy/nemotron_labs_voicechat_streaming.yaml`
- `vllm_omni/experimental/fullduplex/nemotron_voicechat/`
- `vllm_omni/model_executor/models/nemotron_voicechat/`
- `vllm_omni/model_executor/models/nemotron_voicechat/nemo_vendored/`
- `vllm_omni/model_executor/models/nemotron_voicechat/nemo_vendored/asr/`
- `vllm_omni/model_executor/stage_input_processors/nemotron_voicechat.py`

## 依赖的共享代码模块

- `vllm_omni/experimental/fullduplex/openai/` → [serving](../../components/serving/_index.md)
- `vllm_omni/core/sched/` → [scheduler](../../components/scheduler/_index.md)
- `vllm_omni/distributed/omni_connectors/` → [distributed](../../components/distributed/_index.md)
- `vllm_omni/model_executor/models/` → [model-executor](../../components/model-executor/_index.md)
- `vllm_omni/config/stage_config/` → [configuration](../../components/configuration/_index.md)

## checkpoint、尺寸与量化

- `nemotron_labs_voicechat.yaml`：NemotronVoiceChat-11B offline speech-to-speech deployment. 3 stages on one GPU: thinker (NemotronH AR) -> talker (EAR-TTS AR) -> code2wav (RVQ-VAE decode).

## 什么时候查这里

只查 NVIDIA Nemotron-Labs VoiceChat 专有的行为、常量、注册入口和验证合同。

## 不放什么

上面列出的共享模块的执行、调度、加载或 serving 合同属于
[components](../../components/_index.md)，这里只链接不复制；registry 快照和别名
清单见 [模型 catalog](../catalog.md)；一次性历史默认不落盘。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 原生 duplex、帧/工具合同与验证边界 | [Nemotron VoiceChat rules](rules.md) |
