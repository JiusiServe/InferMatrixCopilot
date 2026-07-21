---
title: "CosyVoice3 架构"
created: 2026-07-21
updated: 2026-07-21
type: architecture
tags: [vllm-omni, models]
sources: [vllm_omni/model_executor/models/cosyvoice3/cosyvoice3.py, vllm_omni/model_executor/models/cosyvoice3/cosyvoice3_code2wav.py, vllm_omni/model_executor/models/cosyvoice3/pipeline.py, vllm_omni/model_executor/stage_input_processors/cosyvoice3.py, vllm_omni/transformers_utils/configs/cosyvoice3.py, vllm_omni/deploy/cosyvoice3.yaml]
---

# CosyVoice3 架构

事实在 `main @ 5d44868e` 复核;入口/模式速览见 [index](_index.md)。

## 模型专有部分与共享模块的边界

- talker：`VLLMQwen2Encoder` → `TransformerLM` → `Qwen2LM` → `CosyVoice3LM`
  （Qwen2 系 AR,出 speech token）;参考音频条件作为多模态数据进入
  （自有 MultiModalProcessor）。
- code2wav：`CausalConditionalCFM`/`CausalMaskedDiffWithDiT`（流匹配,DiT
  估计器 import 自 `diffusion/models/cosyvoice3_audio/`）+
  `PreLookaheadLayer` + `CausalHiFTGenerator`（HiFT/NSF 声码器）+
  `CausalConvRNNF0Predictor`。
- **TRT 加速（本清单独有）**：campplus 说话人嵌入与 CFM DiT 估计器都可走
  TensorRT（启动时 ONNX→plan,按设备缓存 plan;campplus 有 CPU-ONNX 兜底）,
  统一由 `COSYVOICE3_TRT` 门控,默认开。
- 共享：diffusion Attention 层、SharedMemoryConnector、
  [Config 组件](../../components/config/architecture.md)。

## 配置、checkpoint 和兼容范围

- checkpoint：YAML 不 pin;离线示例仅以注释给出默认
  `FunAudioLLM/Fun-CosyVoice3-0.5B-2512`。
- config（`transformers_utils/configs/cosyvoice3.py`）：`eos_token_id` 默认
  6562;注释明确官方把 **所有 ≥ speech_token_size 的 token（6561–6760）都视
  为停止信号**;`sample_rate 24000`、hidden 896、heads 14 硬编码。
- **RAS 停止机制（停止失效 bug 类别）**：停止 token id **6562 接收 200 个
  停止 logit 的 logsumexp 合并分数**;YAML 的
  `repetition_penalty: 1.0001` 唯一存在理由是逼 vLLM 维护
  `output_token_ids` 让 RAS 生效——把它"归一化"成 1.0 会静默破坏停止。
- stage-1 的 `engine_output_type="latent"`（而非其他 TTS 家族的
  `"audio"`）与 `final_output_type="audio"` 并存——是刻意合同还是陈旧字段
  pin 上无注释,未决。

## 从输入到输出的主要流程

1. 文本 + 参考音频作为多模态条件进入（campplus 说话人嵌入与
   speech_feat/speech_token 条件张量打进 `additional_information`）。
2. talker AR 出 speech token（词表 6561,合并停止 6562）。
3. 交接双注册（**唯一同时注册两条交接的家族**,由 `deploy.async_chunk` 选）:
   - 流式 `talker2code2wav_async_chunk`：prompt 条件按 chunk 对齐
     （`prompt_token_pad`）,`codec_pre_lookahead_frames 3`,hop 以
     `codec_stream_scale_factor 2` 增长,上限 4× chunk;批发射的右 padding 先
     `unpad_prompt_conditioning` 剥掉。
   - 同步 `text2flow_full_payload`（生产侧全载荷）+ `text2flow_token_only`
     （消费侧占位）。
4. code2wav：flow-matching 解码器产出声学特征 → HiFT → 24 kHz 波形（TRT
   估计器与
   PyTorch DiT 之间的具体选路代码未逐行读,见文末未决项）。

## 怎样验证功能、精度和性能

本次调查识别到的验证入口都是**功能面**（e2e/SIP）;未发现精度基线或性能
gate（YAML 头注的 H100/H20-3e 连续性数字是部署调参记录,非精度基线）——
精度/性能结论需另行实测。

- e2e：`tests/e2e/offline_inference/test_cosyvoice3_expansion.py`、
  `tests/e2e/online_serving/test_cosyvoice3_tts_expansion.py`;SIP
  `tests/model_executor/stage_input_processors/test_cosyvoice3_stage_input_processors.py`
  （资产 `tests/assets/cosyvoice3/zero_shot_prompt.wav`）;示例
  `examples/{offline_inference,online_serving}/text_to_speech/cosyvoice3/`。
- 已知未决：6563–6760 的实际停止行为依赖 talker `compute_logits` 的合并
  逻辑（只略读）;NPU 侧 `cosyvoice2_dit_attn.py`（名字是 cosyvoice2）是否
  接到 v3 DiT 路径未追;code2wav 内 TRT/PyTorch 选择的具体代码未逐行读。
