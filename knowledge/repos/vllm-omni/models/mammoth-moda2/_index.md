---
title: "MammothModa2（AR→DiT,但 DiT 是 LLM_GENERATION stage）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models]
sources: [vllm_omni/model_executor/models/mammoth_moda2/, vllm_omni/diffusion/models/mammoth_moda2/, vllm_omni/deploy/mammoth_moda2.yaml]
---

# MammothModa2

以下事实在 `main @ 5d44868e` 复核。

## 名称与范围

- 正式名称 MammothModa2-Preview（ByteDance Research;recipe
  `bytedance-research/MammothModa2-Preview`）。
- AR registry 五个入口（`mammoth_moda2` 家族;**无 diffusion registry 入口**）:
  MoE 文本基座 `MammothModa2Qwen2ForCausalLM`、AR 多模态
  `MammothModa2ARForConditionalGeneration`、DiT `MammothModa2DiTPipeline`
  （经 15 行 shim 转到 `diffusion/models/mammoth_moda2/`）、路由包装
  `MammothModa2ForConditionalGeneration`（按 `model_stage` 分发 ar/dit;
  `"vae"` 保留并 raise）+ HF 别名 `Mammothmoda2Model`。
- pipeline key 两个：`mammoth_moda2`——stage 0 AR（LLM_AR,
  `engine_output_type="latent"`）→ stage 1 DiT（LLM_GENERATION,
  `input_sources=(0,)`,经 `stage_input_processors/mammoth_moda2.py::ar2dit`
  交接,图像出）;`mammoth_moda2_ar`——仅 stage 0,文本出。**两 key 同架构
  同权重**,但拓扑不同：AR-only 把流水线截断到 stage 0、final 输出改为
  text、无 latent 导出要求;deploy 侧参数也不同（AR-only
  `max_num_seqs 16` vs 全拓扑 stage0 100/stage1 1）。
- checkpoint：`bytedance-research/MammothModa2-Preview`（recipe/示例记载,
  YAML 不 pin）。
- 依赖共享模块：AR 侧继承 vLLM Qwen2.5-VL 栈（processor/模型基类,加
  MammothU tokenizer）;AR runner 的 latent 导出;
  `stage_input_processors/mammoth_moda2.py`;
  [Config 组件](../../components/config/architecture.md)。t2i 走共享示例
  `examples/offline_inference/text_to_image/`,AR-only 示例在
  `examples/offline_inference/mammothmodal2_preview/`。

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| 双词表/网格约束解码/latent 交接 | [architecture](architecture.md) | 数据流与 reviewer 陷阱 |

## 配置与 checkpoint 差异

- **stage 1 不是 diffusion-engine stage**：`LLM_GENERATION` 里跑
  `VllmConfig` 版 DiT——cache-dit/SP/OmniDiffusionRequest 都不适用;
  `num_inference_steps` 必须走 extra_body（`--num-inference-steps` 旗标到不了
  DiT,`model_extras/mammothmodal2_preview.py` 注释明示）。
- `mammoth_moda2.yaml`：两 stage 同卡（AR 0.5 + DiT 0.3 显存配比,均 eager）;
  DiT 默认 `text_guidance_scale 9.0`/`cfg_range [0,1]`/`steps 50`;
  **无负向 prompt 路径**。

## 什么时候查这里

- 审查 mammoth_moda2 的双词表、约束解码或 AR↔DiT 交接;评审"diffusion 引擎
  统一改造"时本家族是必须点名的例外。
- 语义验收见 [model-validation](../../review/guides/model-validation.md)。
