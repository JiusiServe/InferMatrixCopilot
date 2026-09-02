---
title: "Ming-flash-omni（BailingMM2,4 拓扑全模态）"
created: 2026-07-21
updated: 2026-08-10
type: index
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/model_executor/models/ming_flash_omni/, vllm_omni/diffusion/models/ming_flash_omni/, vllm_omni/model_executor/stage_input_processors/ming_flash_omni.py, vllm_omni/entrypoints/openai/tts_adapters/ming_flash_omni_tts.py, "PR #5746"]
---

# Ming-flash-omni

以下事实在 `main @ 11f633aa` 复核。

## 名称与范围

- 蚂蚁/inclusionAI Ming 系全模态（文/图/视频/音频理解;文本、语音、图像
  输出）。HF 侧名字是 **BailingMM2**:野生 config.json 写
  `BailingMM2NativeForConditionalGeneration` / model_type
  `bailingmm_moe_v2_lite`——registry 别名 + `hf_architectures` +
  `diffusion/data.py` 特判三处共同把它路由到本家族。在线示例 serve 目标
  `Jonathan1909/Ming-flash-omni-2.0`（疑似个人 namespace,树内未记载官方仓
  来源,YAML 不 pin）。
- AR registry 四入口：复合类 `MingFlashOmniForConditionalGeneration`、
  thinker `MingFlashOmniThinkerForConditionalGeneration`、talker
  `MingFlashOmniTalkerForConditionalGeneration`,以及
  `BailingMM2NativeForConditionalGeneration`（**解析到复合类的别名**）;
  diffusion registry `MingImagePipeline`（`pipeline_ming_imagegen.py`,
  类继承自 `ZImagePipeline`——见 [z-image](../z-image/_index.md)）。
- **与 [ming-omni-tts](../ming-omni-tts/_index.md) 是两个家族**：`ming_tts`
  registry 入口属于后者,但共享
  `model_executor/models/common/ming/`（AudioVAE/DSP/DiT/FM）;
  **stage 名 `ming_tts` 在本家族 stage 1 被复用**——serving 按 arch 消歧,
  stage-key 路由的常驻 footgun。
- pipeline key 四个：`ming_flash_omni`（thinker+talker,文本+音频双 final）/
  `ming_flash_omni_tts`（仅 talker）/ `ming_flash_omni_thinker_only`
  （仅 thinker）/ `ming_flash_omni_image`（thinker latent → MingImagePipeline
  DIFFUSION）。
- 依赖共享模块：[Diffusion 组件](../../components/diffusion/_index.md)、
  [Config 组件](../../components/configuration/architecture.md)。

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| 文本桥 vs hidden 桥、CFG 伴随、ByT5 字形路径 | [architecture](architecture.md) | 数据流与 reviewer 陷阱 |
| speech API 的 detection/adapter union | [Serving SERV-5e](../../components/serving/rules.md#serv-5e-tts-detection-从-adapter-metadata-的有序并集派生) | `ming_tts` 消歧、请求校验和 prompt delegation |

## 配置与 checkpoint 差异

- 四份 deploy 全 `trust_remote_code`、`async_chunk: false`、仅 CUDA 验证。
  显存布局差异大:omni（TP4 + talker 共卡 GPU3 0.74/0.18,80 GB 卡验证）/
  tts（单卡 0.8）/ thinker_only（TP4 0.9）/ image（TP4 + DiT 独占 GPU4,
  `max_num_seqs: 2` 给 CFG 伴随请求留位,stage0 `max_tokens: 1` 纯 prefill）。
- 已知不一致（pin 上如实记录）：stage-0 `hf_config_name` 在
  omni/thinker_only 是 `llm_config`,在 image 拓扑却是 `thinker_config`,
  代码无解释;`fuse_allreduce_rms: false`（flashinfer 版本不匹配的
  workaround）。
- extra-body 面（注册在 arch key `MingImagePipeline`）:
  `{height,width,steps,cfg,seed,byte5_text,negative_prompt}`。

## 什么时候查这里

- 审查 ming_flash_omni 任一拓扑、BailingMM2 名字路由或 serving 消歧。talker-only speech
  已由 `MingFlashOmniTTSAdapter(stage_keys={"ming_tts"})` 负责请求校验和 prompt 构建；它继续
  调用 server 上的 `_build_ming_flash_omni_prompt()`，是提取而非 prompt 合同改写。检测端仍有
  同名高优先级 legacy detector 保护 `ming_tts` 与 Ming dense architecture 的消歧；不要因已注册
  adapter 就假定 legacy detector 已移除，也不要把模型分支重新塞回共享 dispatcher。此过渡态
  与 detection suite 的“legacy detector 不得同时有 adapter”不变量冲突；后续修复应把优先级
  转移给 adapter 并移除同名 legacy 条目，同时验证 Ming dense architecture 仍正确消歧。
- 语义验收见 [model-validation](../../review/guides/model-validation.md)。
