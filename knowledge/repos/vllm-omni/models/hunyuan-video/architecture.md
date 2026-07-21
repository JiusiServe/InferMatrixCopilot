---
title: "HunyuanVideo-1.5 架构"
created: 2026-07-21
updated: 2026-07-21
type: architecture
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/hunyuan_video/pipeline_hunyuan_video_1_5.py, vllm_omni/diffusion/models/hunyuan_video/pipeline_hunyuan_video_1_5_i2v.py, vllm_omni/diffusion/models/hunyuan_video/hunyuan_video_15_transformer.py]
---

# HunyuanVideo-1.5 架构

事实在 `main @ 5d44868e` 复核;入口/变体速览见 [index](_index.md)。

## 模型专有部分与共享模块的边界

- 专有 transformer：`HunyuanVideo15Transformer3DModel`——54 个双流块 +
  token refiner + ByT5 文本投影 + 图像投影 + meanflow 能力的时间嵌入
  （`timestep_r`）;并行标记齐全（`_sp_plan` 分 rope/收 proj_out、
  `packed_modules_mapping`、`_cache_dit_adapter_config`
  `has_separate_cfg=True`、layerwise offload/HSDP 条件）。
- 双文本编码器：MLLM 路（Qwen2.5-VL 文本塔,取倒数第 3 层 hidden）+ glyph
  路（ByT5 只编码 prompt 引号内子串,无引号时喂 `(1,256,d)` 零张量）。
- VAE：`DistributedAutoencoderKLHunyuanVideo15`,**强制 fp32**;
  `flow_shift` 覆盖靠直写 `scheduler._shift`（属性无 setter）。
- 共享：[Diffusion 组件](../../components/diffusion/_index.md)的
  CFG-parallel（rank0 正/rank1 负 + all_gather）、SP 中央应用、瓦片/切片
  VAE 布线。

## 配置、checkpoint 和兼容范围

- **字节级模板陷阱**：MLLM 编码的 `crop_start=108` 依赖系统消息 tokenize
  后长度——**系统消息空白必须与 diffusers 字节一致**（源注释明示;偏离的
  运行期后果未在 pin 上实测）。
- DiT 输入 65 通道 = `cat([latents 32, cond_latents 32, mask 1])`;
  transformer 用 image_embeds 全零检测 T2V 模式。
- 权重加载混合两轨：transformer/text_encoder_2 走 ComponentSource +
  AutoWeightsLoader;其余 `from_pretrained`（带子目录预取,避 transformers v5
  多 worker 缓存竞态）。

## 从输入到输出的主要流程

1. 条件准备分支：T2V **无注册 pre-process**,直接构造全零
   `image_embeds`/`cond_latents`/`mask`（transformer 靠 image_embeds 全零
   检测 T2V 模式）;I2V pre-process 从 `max_area=480×832`、16 整除推 H/W,
   SigLIP 编码输入图 → `image_embeds`,首帧 VAE argmax latent×scale 进
   `cond_latents`,mask 帧 0 置 1、后续帧零。
2. 文本双路编码;线性 sigma `np.linspace(1.0, 0.0, steps+1)[:-1]`（去掉
   末端零）交给 scheduler 内部做 shift。
3. 去噪循环:CFG 经 `predict_noise_maybe_with_cfg`;meanflow 时每步传
   `timestep_r`（末步 0.0）;RNG 走 per-request generator +
   `randn_tensor`（generator 列表长度必须等于 batch）。
4. `empty_cache()` 后先 `latents / vae.config.scaling_factor` 再
   `vae.decode`（OOM 缓解与 wan2_2 同款）→
   `VideoProcessor(vae_scale_factor=16)` → 展平成 PIL 帧列表。

## 怎样验证功能、精度和性能

pin 上只有**功能面**验证入口;无精度基线或性能 gate 证据,相关结论需另行
实测。TP>1 的 54 块 DiT 未见 CI 覆盖（deploy 默认 TP1）。

- 单测：`tests/diffusion/models/hunyuan_video/test_hunyuan_video_quant_config_propagation.py`;
  e2e `tests/e2e/online_serving/test_hunyuan_video_15_expansion.py`;示例
  `examples/online_serving/{text_to_video,image_to_video}/run_server_hunyuan_video_15.sh`
  与对应 `run_curl_hunyuan_video_15.sh` 客户端脚本;量化脚本
  `examples/quantization/quantize_hunyuanvideo_15_modelopt_fp8.py`。
- 已知未决：checkpoint 如何选 I2V 架构（推测经 model_index.json
  `_class_name`,解析链未追）;serving 文档是否期待用户显式传 YAML。
