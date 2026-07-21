---
title: "Lance 架构"
created: 2026-07-21
updated: 2026-07-21
type: architecture
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/lance/pipeline_lance.py, vllm_omni/diffusion/models/lance/lance_transformer.py, vllm_omni/diffusion/models/lance/wan_vae.py, vllm_omni/diffusion/models/lance/prompts.py]
---

# Lance 架构

事实在 `main @ 5d44868e` 复核;checkpoint/差异速览见 [index](_index.md)。

## 模型专有部分与共享模块的边界

- 专有:`lance_transformer.py`（`LanceBagel(Bagel)`、3D 位置嵌入、
  `LanceQwen2_5_VLNaViTWrapper`、no-op connector——Qwen merger 已投影到 LLM
  hidden、零 ViT pos-embed——ViT 自带位置编码）;`wan_vae.py`
  （树内 Wan2.2 VAE 全实现,含 `decode_video`）;`prompts.py`
  （(task, modality)→system prompt 表,7 个键）。
- 继承:`BagelPipeline` 的生成机器（`Bagel.generate_image`
  timestep-shift flow 及其配套缓存路径）——**改
  [bagel](../bagel/architecture.md) 公共面必扫 lance**。
- LLM 构造要点:`Qwen2MoTForCausalLM` + `qk_norm=True` +
  `tie_word_embeddings=False`（checkpoint 有真 lm_head）+ 强制 mRoPE。
- 权重叠加（图像变体）:`Lance_3B/model.safetensors`（LLM+connectors）之上,
  `Qwen2.5-VL-ViT/vit.safetensors` 存在即覆盖（对齐上游分载 ViT 的做法）;
  视频变体从 `Lance_3B_Video/` 加载各自的 LLM 权重。

## 配置、checkpoint 和兼容范围

- latent 几何（从发布权重形状反推,页内证据链）：`vae2llm.weight=(2048,48)`
  ⇒ patch 1×1、z=48;`latent_pos_embed=(4096,2048)` ⇒ `max_latent_size 64`;
  视频 pos-embed `(31·64·64, 2048)` ⇒ 最多 31 latent 帧（≤121 RGB 帧,
  时间下采样 4）。
- 去噪参数按路由从 `extra_args` 读:`timestep_shift`（3.5）、
  `cfg_text_scale`（4.0;i2v 注释:改动小的编辑可拉到 10–15）。

## 从输入到输出的主要流程

1. `forward` 按 `modalities`+`multi_modal_data` 分七路（触发条件→handler）:
   `"video"`+`first_frame` → `_forward_i2v`;`"video"`+`video` →
   `_forward_video_edit`;仅 `"video"` → `_forward_t2v`;`"text"`+`video` →
   `_forward_x2t_video`;`"text"`+`image` → `_forward_x2t_image`;
   `"image"`+`img2img/image` → `_forward_image_edit`;其余默认 t2i 落回
   `BagelPipeline.forward`（注入 `cfg_img_scale=1.0` 等默认）。
   **没有 `stage_input_processors/lance.py`**——全部输入处理都在
   `LancePipeline.forward` 分派 + 各任务 prefill helper
   （`_raw_text_prefill`/`_vit_image_prefill`/`_vit_video_prefill`/
   `_vae_ref_prefill`）内完成。
2. prefill 分段重建 chat 模板（image_edit/video_edit）使 rope 位置与上游
   Lance 对齐;`_extract_user_instruction` 从渲染后模板抽回原始用户文本。
3. **CFG 是 BAGEL 式双 KV 上下文**（`cfg_text_context` 维护负向/无条件
   prompt 的第二套 past-KV,一起交给 `generate_image`）——**不是**
  CFGParallelMixin,无 rank 切分。
4. 视频路:3D latent + `LanceWanVAE.decode_video`。
- **bring-up 状态（pin 上如实记录,docstring 与代码有陈旧差）**：docstring
  称 t2i 端到端验证（B300,~6 s@1024²）、x2t 立即 EOS（缺 mRoPE 端到端位置
  id）、image_edit 卡在 VAE-prefill pos-embed 网格失配、"视频后续";但
  `_forward_t2v/_i2v/_video_edit/_x2t_video` 均已实现,init 日志称 t2v 已
  接线。**视频/编辑路的验证状态当作未确认**,评审勿据 docstring 或代码单方
  断言。

## 怎样验证功能、精度和性能

pin 上仅识别到一个 lance 测试路径
（`tests/e2e/online_serving/test_lance.py`,其路由覆盖面未从来源确认）;
示例 `examples/{offline_inference,online_serving}/lance/`（含 gradio）。
本次调查未发现精度基线或性能 gate——相关结论需另行实测。

- 已知未决：`get_lance_pre_process_func` 未注册是否有意;
  `Qwen2MoTConfig/ForCausalLM` 是 lance_transformer 定义还是从 bagel 转
  出口;x2t 路由的文本如何经 `final_output_type="image"` 的 stage 交付。
