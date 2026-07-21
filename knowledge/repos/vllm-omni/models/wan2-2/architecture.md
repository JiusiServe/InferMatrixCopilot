---
title: "Wan 2.2 架构"
created: 2026-07-21
updated: 2026-07-21
type: architecture
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/wan2_2/pipeline_wan2_2.py, vllm_omni/diffusion/models/wan2_2/wan2_2_transformer.py, vllm_omni/diffusion/models/wan2_2/pipeline_wan2_2_s2v.py, vllm_omni/diffusion/models/dmd2/mixin.py]
---

# Wan 2.2 架构

事实在 `main @ 5d44868e` 复核;变体/入口速览见 [index](_index.md);共享
diffusion 设施见 [Diffusion 组件](../../components/diffusion/_index.md)。

## 模型专有部分与共享模块的边界

- `WanTransformer3DModel`：TP 化层 + `DistributedRMSNorm` + `_sp_plan`
  （rope 分/proj_out 收/逐块边界;为让 SP 能挂钩,专门造了
  `TimestepProjPrepare`/`OutputScaleShiftPrepare` 包装模块）;VACE 变体
  **重锚分片点**到 VACE context 汇入前的 Identity（不是 blocks.0）。
- S2V 栈（57 KB pipeline + 75 KB transformer）：wav2vec2 音频编码
  （捆绑 `wav2vec2-large-xlsr-53-english/`,缺了回退 facebook 仓）、
  `AudioInjector_WAN`、motion-frame AR 链（默认 73 motion/80 infer 帧,
  fps 16）、可选 pose 视频;支持 diffusers 与原始格式 checkpoint
  （T5→UMT5 state-dict 转换）;输出 `(video, audio, sr)` 三元组。
- 共享:UMT5 文本编码、`DistributedAutoencoderKLWan`
  （decode 前按 `latents_mean/std` 归一化）、CFG-parallel
  （wan 用 `cfg_normalize=False`）、`PipelineParallelMixin`（非末 PP stage
  返回 `IntermediateTensors`）。

## 配置、checkpoint 和兼容范围

- **双专家 boundary 合同**：去噪时 `t < boundary_timestep` 用
  `transformer_2`+`guidance_high`,否则 `transformer`+`guidance_low`;缺失
  专家回退到已加载者;`boundary_ratio` 同时是部分加载开关（见 index）。
- scheduler 分变体：T2V/I2V/VACE 按请求可重建——`sample_solver` unipc
  （默认,flow_shift 5.0）/ euler（自研 `WanEulerScheduler`）;S2V 固定
  FlowUniPC、flow_shift 3.0;DMD2 换 `DMD2EulerScheduler`（见下,且禁止被
  换回）。TI2V 的 `expand_timesteps` 做首帧掩码混合 + 按 patch 展开时间步。
- **DMD2 合同**（`dmd2/mixin.py`,mixin 必须在 MRO 前面）：
  `__init_dmd2__` 把 scheduler 换成 `DMD2EulerScheduler`
  （config 来自 `model_index.json["dmd2_config"]`,默认 4 步）;
  `_sanitize_dmd2_request` 强制步数/guidance、清负向 prompt、**并从
  extra_args 里剥掉 `sample_solver`/`flow_shift`**——防止基类把 scheduler
  换回去。给 DMD2 变体"加回 CFG/负向"的 PR 违反此合同。
- 量化:每 transformer 独立解析 `quantization_config`,双专家可各自量化。

## 从输入到输出的主要流程

1. pre-process 按变体:T2V/TI2V 可选图像（720×1280 面积,16 对齐）;I2V 必须
   图像（首帧 latent 通道拼接 + 可选 Wan2.1 式 CLIP image embeds）;VACE 接
   `image`/`reference_images`、`video`、`mask` 映进
   additional_information;S2V 需图像+音频,另接可选 `pose_video` 与
   `init_first_frame`。
2. 去噪:适用变体在 `transformer_2` 存在时按 boundary 切换专家（**S2V 单
   transformer,无 boundary**;VACE 两种形态都接受）;CFG 双分支跨 rank;RNG
   per-request generator。
3. `empty_cache()` → VAE decode（源注释:Wan2.2 易 OOM）→ post-process;
   可选**帧插值**（`interpolate_video_tensor`,报告
   `video_fps_multiplier`）只在 T2V/TI2V 的
   `get_wan22_post_process_func` 上有据,其他变体的 post 函数未见此路径。

## 怎样验证功能、精度和性能

可用验证面：unit 七个测试模块 + conftest
（`tests/diffusion/models/wan2_2/`,含 diffuse/quant/各变体 pipeline）、
e2e（t2v 离线/在线、W4A16）、**accuracy**
（`tests/e2e/accuracy/wan22_i2v/` 视频相似度对 diffusers CP 基线）、dfx
（perf/reliability/stability）。DMD2 变体无专属测试（pin 上未见）。

- 量化脚本 `examples/quantization/quantize_wan2_2_modelopt_fp8.py`;副本
  数据并行示例 `examples/online_serving/replica_data_parallel/wan2_2_ti2v_dp.yaml`。
- 已知未决：六架构如何按 checkpoint 选择（解析链在家族外）;
  `wan2_2_ti2v` key 是否用于 A14B 双专家 checkpoint 是配置惯例问题,代码不
  强制。
