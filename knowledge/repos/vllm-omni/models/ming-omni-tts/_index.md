---
title: "Ming-Omni-TTS"
created: 2026-07-20
updated: 2026-07-20
type: index
tags: [vllm-omni, models, model-executor]
sources: ["PR #4341", vllm_omni/model_executor/models/ming_tts/]
confidence: high
---

# Ming-Omni-TTS

## 名称、源码与变体

- 模型族：Ming-Omni-TTS；仓库目录/注册 key 使用 `ming_tts`，部署包含 dense
  `deploy/ming_tts.yaml` 与 MoE `deploy/ming_tts_moe.yaml`。
- 主实现：`vllm_omni/model_executor/models/ming_tts/`；stage input processor 在
  `model_executor/stage_input_processors/ming_tts.py`，speech serving adapter 在
  `entrypoints/openai/tts_adapters/ming_tts.py`。
- 共享 owner：[Model Executor](../../components/model-executor/_index.md) 和
  [Serving](../../components/serving/_index.md)。

## 从文本到音频

LLM/conditioning 产生 latent condition，CFM/DiT solver 运行 ODE/SDE 采样，Audio VAE
把 latent 解码为 waveform。CUDA Graph 路径必须复刻 eager solver 的 float32 状态、CFG
边界与最后一步更新；dense 模型不应因为 MoE-only 依赖的顶层 import 而不可导入。

具体不变量见 [rules](rules.md)；共享优化路径门禁见
[Diffusion rules](../../components/diffusion/rules.md)。

## 什么时候查这里

- 审查 Ming-TTS dense/MoE、CFM CUDA Graph、solver dtype、CFG 或 Audio VAE 输出。
- 通用公开 speech 参数与 streaming 错误转到 [Serving rules](../../components/serving/rules.md)。
