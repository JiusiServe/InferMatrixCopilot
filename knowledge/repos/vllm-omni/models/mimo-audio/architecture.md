---
title: "MiMo-Audio 架构"
created: 2026-07-21
updated: 2026-07-21
type: architecture
tags: [vllm-omni, models]
sources: [vllm_omni/model_executor/models/mimo_audio/mimo_audio_llm.py, vllm_omni/model_executor/models/mimo_audio/mimo_audio_code2wav.py, vllm_omni/model_executor/models/mimo_audio/cuda_graph_decoder_wrapper.py, vllm_omni/model_executor/models/mimo_audio/modeling_audio_tokenizer.py, vllm_omni/model_executor/models/mimo_audio/quantization.py, vllm_omni/model_executor/stage_input_processors/mimo_audio.py, vllm_omni/model_executor/models/mimo_audio/config_mimo_audio.py]
---

# MiMo-Audio 架构

事实在 `main @ 5d44868e` 复核;入口/命名速览见 [index](_index.md)。

## 模型专有部分与共享模块的边界

- 专有 stage 0（`mimo_audio_llm.py`）：**融合 thinker+talker**——理解、文本、
  RVQ 码生成都在一个 AR stage（对照 [qwen-omni](../qwen-omni/_index.md) 的
  thinker/talker 分离);Qwen2 backbone + CUDA-graph 化的 local transformer
  （`MiMoLocalDecodeCudaGraph` 等,逐步产 RVQ 码）;自有采样器
  `MiMoSampler`/`MiMoLocalSamplerTensor`。
- 专有 stage 1（`mimo_audio_code2wav.py` + vendored
  `modeling_audio_tokenizer.py`/`quantization.py`）：VQ 反量化 → AudioDecoder
  → Vocos 声码器;`CUDAGraphMiMoDecoderWrapper` 把**整条解码路径**按
  (RVQ 深度, bucket) 捕获成 CUDA graph,非因果滑窗注意力掩码是静态张量、
  重放前原地更新;tokenizer worker 按 realpath 键进程级缓存（防多引擎重复
  加载多 GB tokenizer）。
- 共享：vLLM qwen2_audio 处理栈;worker-connector 全载荷面。

## 配置、checkpoint 和兼容范围

- checkpoint 合同：LLM `XiaomiMiMo/MiMo-Audio-7B-Instruct`（示例默认）;
  audio tokenizer **必须独立提供**（`XiaomiMiMo/MiMo-Audio-Tokenizer`,经
  `model_config.audio_tokenizer_path` 或 env,缺失 raise）;ASR
  `XiaomiMiMo/MiMo-V2.5-ASR` 共享同一 pipeline/类,serving 边界未决。
- 码组几何：每 AR 步出 `(8 通道 × 4 group)` 码块;wire 格式 = 加 pad 行后
  列主序展平;各 codebook 词表异构
  （`"1025-1025-129-129-129-129-129-129"`,各自有 zero-emb 下标）;delay
  pattern `0-7`。
- 关键常量（`config_mimo_audio.py`）：span 标记 151670/151672;
  `NO_INTERLEAVE_NEXT_TOKEN_ID=151671` 兼任 stage-0 stop token 与音频边界;
  `TEXT_GROUP_SIZE=5`。
- `model_stage` 环境变量优先于 `vllm_config.model_config.model_stage`
  （包装类 `__init__`）——调试/测试时注意环境泄漏。
- 模态边界：pin 上**只支持音频**——image/video 占位符字符串虽已声明,代码
  注释明示仅 audio 模态生效。

## 从输入到输出的主要流程

1. prefill 前处理 `interleave_5_and_5_in_span`：prompt id 按 5 文本+5 音频
   交错重组;音频占位 `<|sosp|><|empty|><|eosp|>`。
2. stage 0 逐步出 `(B,1,8,4)` 码块;文本经正常 detokenize 同时交付
   （双 final output）。
3. 交接双路径（`stage_input_processors/mimo_audio.py`）：async_chunk 逐步
   累积、按 `codec_chunk_frames` 冲刷（**完成时 `_flush_remaining_codes` 冲
   最后不满块——漏掉会截尾音频**）;sync 路径 `llm2code2wav_token_only` 只发
   零占位 prompt（让消费端分配槽位）,真码走 `llm2code2wav_full_payload` 的
   worker-connector 面（全零码行被过滤）。
4. **稳定性下限（音质 bug 类别）**：`codec_left_context_frames ≥ 40`——左
   上下文必须盖住 vocoder 注意力窗口（默认 `[40,10]`）,低于下限会被强制改写
   并告警;违反表现为 chunk 边界处声学状态重置/音色漂移。
   `MAX_CODE2WAV_TOKENS=18192` 硬顶,超限在 full_payload 中静默截断。

## 怎样验证功能、精度和性能

pin 上只有**功能面**验证入口;无精度基线或性能 gate 证据,下列测试不覆盖
精度/性能维度,相关结论需另行实测。

- 单元：`tests/model_executor/models/mimo_audio/`（batch decode、
  per-request 码隔离）、`tests/model_executor/stage_input_processors/`
  （`test_mimo_audio_flush_remaining_codes.py`、
  `test_mimo_audio_llm2code2wav.py`）。
- e2e：`tests/e2e/online_serving/test_mimo_audio_expansion.py`;离线示例
  `examples/offline_inference/mimo_audio/end2end.py`（tts_sft/理解/对话/
  多轮多题型）。
- 已知未决：MiMo-V2.5-ASR checkpoint 是否设计为 thinker-only 服务不可从
  pin 判定;stop token 151645 与 151671 的实际先后是运行期行为。
