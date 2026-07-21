---
title: "MammothModa2 架构"
created: 2026-07-21
updated: 2026-07-21
type: architecture
tags: [vllm-omni, models]
sources: [vllm_omni/model_executor/models/mammoth_moda2/mammoth_moda2.py, vllm_omni/diffusion/models/mammoth_moda2/pipeline_mammothmoda2_dit.py, vllm_omni/model_executor/stage_input_processors/mammoth_moda2.py]
---

# MammothModa2 架构

事实在 `main @ 5d44868e` 复核;行号随源码漂移,改代码前以当前版本为准。
入口/变体速览见 [MammothModa2 index](_index.md);语义验收方法见
[model-validation](../../review/guides/model-validation.md)。

## 模型专有部分与共享模块的边界

- 专有 AR：`mammoth_moda2.py`——**双词表 LM**（`extra_gen_vocab`:独立
  `gen_embed_tokens`/`gen_head`,base+gen logits 拼接以维持 vLLM "logits 维
  == 词表"不变量）;token 级双专家路由 `moe_forward`
  （生成 token 走 gen expert,层范围由 `"ffn_attention-14:28"` 风格串门控——
  是**确定性模态路由,不是学习型 router**）;`gen_token_mask` 随
  `IntermediateTensors` 过 PP。
- 继承的共享栈：AR 多模态类 subclass vLLM 的 Qwen2.5-VL
  （`Qwen2_5_VLForConditionalGeneration` + 对应 processor 族,换上
  MammothU tokenizer 与 `MammothModa2Qwen2ForCausalLM` 语言基座）;跨 stage
  交接责任在 AR runner（latent 导出）+
  `stage_input_processors/mammoth_moda2.py`。
- 专有 DiT：`diffusion/models/mammoth_moda2/`——Lumina2 系 DiT +
  **可选** Q-Former 条件精炼器（仅当 checkpoint 配置有
  `gen_image_condition_refiner_config` 时构建）+ 本地
  `FlowMatchEulerDiscreteScheduler` 移植 + 实值 RoPE（`rope_real.py`）。
  **RoPE 频表刻意取顶层 `config.gen_axes_lens` 而非 checkpoint 的
  `gen_dit_config.axes_lens`**（后者可小到 1024,不够 vLLM
  warmup/cudagraph 用——不要"简化"回去）。
- 权重卫生：AR stage 的 `hf_to_vllm_mapper` 丢弃 **`gen_transformer.` /
  `gen_vae.` / `gen_image_condition_refiner.`** 前缀（生成侧的双词表
  嵌入/头当然保留——那是 AR 自己的）;DiT stage 丢 `llm_model.*`;包装类以
  `ar.`/`dit.` 重前缀——各 stage 只加载共享 checkpoint 的自己那半。

## 配置、checkpoint 和兼容范围

- config 类 `Mammothmoda2Config`（`transformers_utils/configs/mammoth_moda2.py`）:
  嵌套 `llm_config` + 字典式 `gen_vae_config`/`gen_dit_config`（diffusers
  风格 dict,DiT 组件用 `from_config` 构建）。checkpoint
  `bytedance-research/MammothModa2-Preview`;两个 pipeline 变体同权重、
  不同拓扑（见 index）。
- `gen_vocab_start_index` 是**单一枢轴常量**：AR 掩码、logits 约束、DiT 条件
  拆分三处共用,改动必须三处同步。
- t2i prompt 由 `model_extras/mammothmodal2_preview.py` 组装
  （`<|image start|>{ar_width}*{ar_height}<|image token|>`,`_PATCH_SIZE=16`）;
  extra-body 面 `{text_guidance_scale, cfg_range, num_inference_steps}`。

## 从输入到输出的主要流程

1. AR 前传:t2i 请求做**网格约束解码**——每 `ar_width+1` 个 token 强制 EOL,
   行内经 logits mask 限制到视觉 token 区间;非 t2i 请求整个 gen 词表置
   −inf。逐步由 `runtime_additional_information` 驱动。
2. `ar2dit`（`stage_input_processors/mammoth_moda2.py`）：
   `full_token_ids = prompt + generated[:-1]`（末 token 无 hidden state,丢弃,
   有长度断言守护）;**要求 `completion_output.multimodal_output["latent"]`
   为全量 hidden states,缺失即 raise**——这份 latent 由 **AR runner**（不是
   AR 模型)在 stage 0 `engine_output_type="latent"` 下挂上;**以 float32
   连续张量跨进程**（numpy 序列化器无 bf16,DiT 侧再转）;文本/图像条件拆分
   推迟到 DiT 的 `_split_ar_conditions`（从 config token id 重建掩码）。
3. DiT（LLM_GENERATION runner 内）：caption embedder 重初始化为
   `RMSNorm+Linear(llm→dit)`;CFG 用 `text_guidance_scale`+`cfg_range` 窗口。
   pipeline 构造了 VAE、stage 1 声明 final 图像输出;去噪/VAE 解码/图像打包
   的逐步实现未逐行核对（见文末未决）。

## 怎样验证功能、精度和性能

pin 上只有**功能/config 面**的验证入口,没有专门的精度基线或性能 gate 证据;
精度/性能结论需另行实测。

- e2e：`tests/e2e/offline_inference/test_mammoth_moda2_expansion.py`
  （t2i + AR）;config 单测
  `tests/unit/mammoth_moda2/test_mammoth_moda2_config.py`;AR 图像理解示例
  `examples/offline_inference/mammothmodal2_preview/`。
- 已知未决：runner 侧把 hidden 打进 `multimodal_output["latent"]` 的确切
  代码位、`Mammoth2DecoderLayer` 每层 moe 布线、DiT 去噪逐步数学——分析时
  未逐行读,改这些区域先补读源码。
