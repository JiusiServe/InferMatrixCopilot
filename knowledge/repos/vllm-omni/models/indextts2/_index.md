---
title: "IndexTTS2（非流式两 stage,GPT talker + S2Mel/BigVGAN）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models]
sources: [vllm_omni/model_executor/models/indextts2/, vllm_omni/deploy/indextts2.yaml, vllm_omni/model_executor/stage_input_processors/indextts2.py]
---

# IndexTTS2

以下事实在 `main @ 5d44868e` 复核。

## 名称与范围

- 正式名称 IndexTTS-2（checkpoint `IndexTeam/IndexTTS-2`,YAML 头注/示例
  记载）;代码/家族别名 IndexTTS2;pipeline key `indextts2`。
- 模型 registry 两入口（**无 diffusion registry 入口**——S2Mel 的 DiT/流
  匹配是家族内代码;注意第二个入口是 LLM_GENERATION stage,不是 AR）：
  `IndexTTS2TalkerForConditionalGeneration`
  →（`indextts2`, `indextts2_talker`）;`IndexTTS2S2MelDecoder`
  →（`indextts2`, `indextts2_s2mel_decoder`）。
- 入口路径：registry `vllm_omni/model_executor/models/registry.py` 与
  `vllm_omni/config/pipeline_registry.py`;拓扑
  `vllm_omni/model_executor/models/indextts2/pipeline.py`;桥
  `vllm_omni/model_executor/stage_input_processors/indextts2.py`;serving
  适配 `vllm_omni/entrypoints/openai/tts_adapters/indextts2.py`;deploy
  `vllm_omni/deploy/indextts2{,_low_latency}.yaml`。
- pipeline key `indextts2`：talker（LLM_AR,GPT-2 系,文本→mel 码,latent 出,
  stop `[8193]`）→ S2Mel decoder（LLM_GENERATION,flow matching→mel→BigVGAN
  →音频）。两 stage 非流式拓扑：无 async_chunk 处理器,S2Mel 要整段 mel 码
  序列,connector 每请求一个全载荷。
- 依赖共享模块：vLLM 原生 GPT-2 块/PagedAttention（talker 基座）、
  SharedMemoryConnector、diffusion hub 预取锁（BigVGAN 懒加载守卫）、
  `utils/speaker_cache`、
  [Config 组件](../../components/config/architecture.md)。

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| 全载荷合同、脱离引擎的 tokenizer、hf_overrides 开关板 | [architecture](architecture.md) | 数据流与 reviewer 陷阱 |

## 配置与 checkpoint 差异

- 一个 pipeline key;`indextts2_low_latency.yaml` 是纯 deploy 变体,差异全在
  stage 0：FULL_DECODE_ONLY CUDA graph（capture sizes `[1,2,4,8,16]`,
  1 warmup）+ FLASHINFER + `async_scheduling: false`,批量包络
  `max_num_seqs` 4→16、gpu_mem 0.4→0.6、batched tokens 512→4096;stage 1 与
  connector 两份 YAML 逐字节一致。
- 两 stage 都 `skip_tokenizer_init: true` + `tokenizer: gpt2`（哑 tokenizer;
  真实分词在家族内 `IndexTTS2Tokenizer`/adapter 完成）。
- stage-0 采样带 **`repetition_penalty: 10.0`**——官方 IndexTTS2 行为的一
  部分,不是待修的"离谱默认值"。

## 什么时候查这里

- 审查 indextts2 的全载荷合同、tokenizer 旁路或 stage-1 hf_overrides 性能
  开关;想给它加流式先看 architecture 里的非流式根因。
- 语义验收见 [model-validation](../../review/guides/model-validation.md)。
