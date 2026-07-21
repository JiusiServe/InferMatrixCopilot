---
title: "Lance（BAGEL 谱系统一模型,单 DIFFUSION stage 全模态）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/lance/, vllm_omni/model_executor/models/lance/pipeline.py, vllm_omni/deploy/lance.yaml]
---

# Lance

以下事实在 `main @ 5d44868e` 复核。

## 名称与范围

- 正式名称 Lance（ByteDance;无其他文档化别名——`lance` 是 pipeline key/
  家族名,`LancePipeline` 是 registry 架构键,不是模型别名）。BAGEL 谱系
  （Mixture-of-Transformers）落在 Qwen2.5-VL-3B 骨架上;checkpoint
  `bytedance-research/Lance`（子目录:`Lance_3B/` 图像 LLM、
  `Lance_3B_Video/` 视频 LLM、`Qwen2.5-VL-ViT/vit.safetensors`、
  `Wan2.2_VAE.pth`;`--model` 可指仓根或子目录,有向上回溯逻辑）。
- diffusion registry：`LancePipeline` →
  （`lance`, `pipeline_lance`, `LancePipeline`）,
  **继承 `BagelPipeline`**（见 [bagel](../bagel/_index.md)）但**刻意不调用
  其 `__init__`**——构造全换 Lance 部件,生成机器全继承。post-process 是
  identity（直接出 PIL);pre-process 函数存在但**未注册**（pin 上死代码）。
- **在 OMNI_PIPELINES 有 key `lance` 但没有 AR stage**：单 stage 拓扑
  `stage_id=0`/`model_stage="dit"`/DIFFUSION/`final_output=True`
  （`final_output_type="image"`）,**无任何 stage 交接**;AR（Qwen2-MoT LLM）
  住在 diffusion stage 里。`hf_architectures=()` 为空,且 checkpoint
  config.json **没有 `model_type`**——`lance.yaml` 纯粹是 pipeline 选择器
  （自动加载,`default_deploy_config_name`）。两 stage 拆分按 docstring 留待
  上游 LanceConfig/Processor 注册后续 PR。
- 与 BAGEL 的差异（家族 `__init__` 自述）：mRoPE backbone（强制
  `mrope_section [16,24,24]`）、Qwen2.5-VL ViT 换 SigLIP、**Wan2.2 VAE 换
  BAGEL AE**（树内独立实现 `wan_vae.py`,不是 wan2_2 家族的 diffusers
  `AutoencoderKLWan`,无 DistributedVaeMixin——`vae_patch_parallel_size` 对
  lance 无效）、3D latent 位置嵌入（视频）。
- 依赖共享模块：bagel 家族的 `Bagel.generate_image` 去噪
  （`scheduler=None`,timestep-shift flow）、
  [Diffusion 组件](../../components/diffusion/_index.md)。

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| 任务路由、双 KV CFG、latent 几何、bring-up 状态 | [architecture](architecture.md) | 数据流与 reviewer 陷阱 |

## 配置与 checkpoint 差异

- `lance.yaml`：单卡 eager 单 stage,无 TP/SP/CFG-parallel 旋钮。
- 图像 vs 视频是 **checkpoint 变体**（`Lance_3B` vs `Lance_3B_Video`,
  `_select_video_variant` 按路径后缀或 `od_config.extra["lance_video"]`）;
  七条任务路由是**同一 registry 架构下的运行期分派**,不是 registry 变体。
- 关键默认:`num_timesteps 30`、`timestep_shift 3.5`、`cfg_text_scale 4.0`;
  `latent_patch_size=1`（Wan VAE 内部 patch 化,**无 BAGEL 的 2×2 unfold**,
  z=48——从权重形状验证）。

## 什么时候查这里

- 审查 lance 的任务路由、Bagel 公共面变更的连带影响或视频路径成熟度;
  **bring-up 状态注意**:docstring 与代码有陈旧差（详见 architecture）。
- 语义验收见 [model-validation](../../review/guides/model-validation.md)。
