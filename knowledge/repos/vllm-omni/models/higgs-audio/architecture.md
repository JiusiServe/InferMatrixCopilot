---
title: "Higgs-Audio 架构"
created: 2026-07-21
updated: 2026-07-21
type: architecture
tags: [vllm-omni, models]
sources: [vllm_omni/model_executor/models/higgs_audio_v3/higgs_audio_v3_talker.py, vllm_omni/model_executor/stage_input_processors/higgs_audio_v2.py, vllm_omni/model_executor/stage_input_processors/higgs_audio_v3.py, vllm_omni/deploy/README_higgs_audio_v3.md]
---

# Higgs-Audio 架构

事实在 `main @ 5d44868e` 复核;谱系/命名速览见 [index](_index.md)。

## 模型专有部分与共享模块的边界

- v2 专有：`higgs_audio_v2_talker.py`（复用 vLLM `LlamaModel`;DualFFN 按
  `audio_token_mask` 路由;独立 `audio_lm_head: Linear(hidden, 8×1026)`;
  `_apply_audio_mode_bias` 在音频 ramp 完成时强制 audio-eos——这就是 stop
  token 128012 的来源）。
- v3 专有：`higgs_audio_v3_talker.py`（复用 vLLM `Qwen3Model`;融合多
  codebook 嵌入/头,offset 查找+求和;批量 GPU delay 状态机;pinned staging +
  CUDA event 异步回读;本地 MLP CUDA graph 路径 + FlashInfer wrapper 解包）。
- 共享 codec 内核：`higgs_audio_decoder.py`（RVQ + Boson DAC,v3 直接 import
  v2 的类）;codes `[B,8,T]` → RVQ 求和 → DAC 反卷积 → 24 kHz PCM
  （25 fps × 960 hop）。
- 共享框架面：[Config 组件](../../components/config/architecture.md)、
  SharedMemoryConnector、`serving_speech.py`。

## 配置、checkpoint 和兼容范围

- prompt 形态不同：v2 走上游 HF processor（字节级一致的 system prompt;
  多说话人/`profile:`/长文分块被显式拒绝 4xx）;v3 用
  `<|tts|>/<|ref_text|>/<|ref_audio|>/<|text|>/<|audio|>` 模板,参考音频用
  `-100` 占位符在 prefill 换成 delay 编码后的融合嵌入。
- v3 config 从 checkpoint tokenizer 解析特殊 token 与 eos（缺失即 raise）。
- 采样注意（v2 YAML 注释记载,v3 未单独佐证）：greedy 会塌缩 codebook
  argmax——v2 必须采样（stage-0 参数 temp 1.0/top_p 0.95/top_k 50/seed 42）;
  两谱系 talker 都无 `torch.Generator` 用法,确定性只靠 seed。

## 从输入到输出的主要流程

1. Talker 以 delay-pattern 布局逐行出码;**去 delay 是 stage processor 的事,
   不是模型的事**（`stage_input_processors/higgs_audio_{v2,v3}.py`）。
2. 特殊码清理是**真实音质 bug 类别**：v2 sync 用 `clamp(0,1023)` 并去首尾帧
   `[:, 1:-1]`;v3 刻意改为 **de-delay 之后 `torch.where(越界→0)`,只去尾帧**
   ——因为 clamp 把 EOC 1025 变成合法码 1023,解码出可闻伪音。评审这段勿把
   where"简化"回 clamp。
3. 流式机制分代：v2 只有 chunk + 左上下文;v3 额外引入右扣留与首块 TTFA
   快路。v3 窗口数学（async_chunk,Q=8 个 codebook）：N 行原始码出
   `N−Q+1` 个 de-delay 帧;发射边界 `target_emit = total − H`（末次 H=0）;
   窗口覆盖 AR 行 `[emitted−L, target_emit+H+Q−1)`;Stage 1 掐头 `L×hop`、
   去尾 `H×hop`（L=左上下文 25,H=右扣留 4;`initial_codec_chunk_frames` 走
   TTFA 快路）。
4. Code2Wav 是**无 KV、纯 prompt 的 LLM_GENERATION stage**,吃 codebook-major
   扁平 token 流;`forward_chunk` 负责流式重叠修剪。

## 怎样验证功能、精度和性能

- 单元：`tests/unit/higgs_audio_v3/test_higgs_audio_v3.py`（无 GPU,AC-1..10:
  config/prompt/融合模块/delay/stage processor/registry）。
- e2e：v2 `tests/e2e/{offline_inference,online_serving}/test_higgs_audio_v2_expansion.py`;
  v3 `tests/e2e/online_serving/test_higgs_audio_v3.py`;perf
  `tests/dfx/perf/tests/test_higgs_audio_v3.json`;示例
  `examples/{offline_inference,online_serving}/text_to_speech/higgs_audio_v{2,3}/`。
- 已知未决：v2 YAML `async_chunk: false` 却配 `codec_streaming: true` 的
  运行期交互未追清;stage-1 注释"250-frame cap"疑似陈旧（实际 max_tokens
  1024）。
