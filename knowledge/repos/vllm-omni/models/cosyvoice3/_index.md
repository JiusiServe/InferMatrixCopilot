---
title: "CosyVoice3（单架构双 stage,RAS 合并停止,TRT 加速）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models]
sources: [vllm_omni/model_executor/models/cosyvoice3/, vllm_omni/deploy/cosyvoice3.yaml, vllm_omni/model_executor/stage_input_processors/cosyvoice3.py]
---

# CosyVoice3

以下事实在 `main @ 5d44868e` 复核。

## 名称与范围

- 正式名称 CosyVoice3（FunAudioLLM;示例注释默认
  `FunAudioLLM/Fun-CosyVoice3-0.5B-2512`,YAML 不 pin）,代码/pipeline 标识
  `cosyvoice3`,无其他别名。
- **单 registry 入口服务两个 stage**：`CosyVoice3Model`
  →（`cosyvoice3`, `cosyvoice3`）,`__init__` 按 `model_stage` 分发
  （`cosyvoice3_talker` → Qwen2 系 LM;`cosyvoice3_code2wav` → CFM+DiT+HiFT;
  其他 raise）——**stage 1 没有独立 `model_arch`**。改 vLLM 模型加载/
  `model_stage` 管线的 rebase 最先撞上本家族。
- stage 拓扑：stage 0 talker（LLM_AR,`owns_tokenizer`,
  `engine_output_type="latent"`）→ stage 1 code2wav（LLM_GENERATION,
  `engine_output_type` 也写 `"latent"`——见 architecture 的未决项,
  `final_output_type="audio"`）;两 stage 复用同一 pipeline 级架构。
- DiT 估计器住在 `diffusion/models/cosyvoice3_audio/cosyvoice3_dit.py` 但
  **不在 diffusion registry**——被 code2wav 直接 import（借 diffusion
  Attention 优化后端,绕开 registry;pin 上唯一 importer）。
- 入口路径：拓扑 `model_executor/models/cosyvoice3/pipeline.py`;桥
  `model_executor/stage_input_processors/cosyvoice3.py`;serving 适配
  `entrypoints/openai/tts_adapters/cosyvoice3.py`;TRT
  `flow_estimator_trt.py`/`speaker_embedding_trt.py`。
- 依赖共享模块：[Diffusion 组件](../../components/diffusion/_index.md)的
  Attention 层、SharedMemoryConnector（stage 间码流）、
  [Config 组件](../../components/config/architecture.md)。

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| RAS 停止机制、双交接注册、TRT 门 | [architecture](architecture.md) | 数据流与 reviewer 陷阱 |

## 配置与 checkpoint 差异

- 单 pipeline key + 单 deploy;变体轴是**运行模式**：async_chunk 流式
  （默认）/ `--no-async-chunk` 同步全载荷 / `COSYVOICE3_TRT` 开关
  （**默认开**,`export COSYVOICE3_TRT=0` 关闭）。
- `cosyvoice3.yaml`：全局 `dtype: float32`（本清单唯一全局 fp32 家族）;
  code2wav `enforce_eager`（动态卷积形状不吃 CUDA graph）;头注给出
  **GPU 级调参警告**——默认（seqs 8/chunk 15）按 H100 调（c=4 约 100%
  流式连续性）,同配置 H20-3e 约 78%、更小 batch/chunk 约 86%（头注近似
  数字,按工况波动）;慢卡先降 `max_num_seqs`/`codec_chunk_frames`,
  `connector_get_sleep_s` 是最后手段。
- pin 上 **无 recipe 文件**（moss/fish/indextts2 都有）。

## 什么时候查这里

- 审查 cosyvoice3 的停止逻辑、流式 chunk 数学或 TRT 引擎构建;跨 GPU 部署
  性能问题先读 YAML 头注的连续性数据。
- 语义验收见 [model-validation](../../review/guides/model-validation.md)。
