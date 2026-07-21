---
title: "BAGEL 架构"
created: 2026-07-21
updated: 2026-07-21
type: architecture
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/model_executor/models/bagel/bagel.py, vllm_omni/diffusion/models/bagel/pipeline_bagel.py, vllm_omni/model_executor/stage_input_processors/bagel.py]
---

# BAGEL 架构

事实在 `main @ 5d44868e` 复核;行号随源码漂移,改代码前以当前版本为准。
本页只写数据流与合同,入口/变体速览见 [BAGEL index](_index.md);多 stage 共卡
显存预算见 [Config 规则 CONF-1a](../../components/config/rules.md)。

## 模型专有部分与共享模块的边界

- 专有 AR 侧（`model_executor/models/bagel/`）：`OmniBagelForConditionalGeneration`
  **继承上游 vLLM 的 `BagelForConditionalGeneration`**,加 VAE 编码器、
  `vae2llm`、时间嵌入,并给每个 decoder 层安装 MoT 生成分支权重
  （`_install_mot_modules`：`qkv_proj_moe_gen` 等）——目的是让 AR stage 产出
  与单 stage DiT **位级兼容的 KV**。
- 专有 DiT 侧（`diffusion/models/bagel/`）：`pipeline_bagel.py`（`BagelPipeline`,
  自带 Qwen2-MoT LLM/SigLIP-NaViT/tokenizer）、`bagel_transformer.py`
  （移植核,`NaiveCache`/`PackedAttentionMoT`/`Bagel`）、
  `autoencoder.py`（FLUX 风格 `DistributedAutoEncoder`）。
- 共享依赖：`CFGParallelMixin`、VAE patch-parallel、
  [Diffusion 组件](../../components/diffusion/_index.md);连接器
  SharedMemory（阈值 65,536 字节）/ Mooncake RDMA。

## 配置、checkpoint 和兼容范围

- 三形态差异（`bagel/pipeline.py` 三个冻结 `PipelineConfig`）：
  - `bagel`：thinker（LLM_AR,`final_output=True` 文本,KV `need_send_cache`,
    **prefill 完即传**）→ dit（DIFFUSION,`input_sources=(0,)`,
    `need_recv_cache`,`final_output=True` 图像）——两 stage 都是 final
    output(文本+图像双交付)。
  - `bagel_think`：同拓扑,但 companions 用 `expand_cfg_prompts_think`
    （`max_tokens=1`）且 **omni_kv_config 去掉 `kv_transfer_criteria`**——KV
    在 EOS 后才传,给 `<think>` 解码留时间。
  - `bagel_single_stage`：单 DIFFUSION stage,仅图像输出;`model_arch` 是 HF
    名 `BagelForConditionalGeneration`,按源码推断经
    `resolve_model_class_name` 从 checkpoint config 解析到 `BagelPipeline`
    （自足:t2i/i2i/i2t/t2t/think）——该解析链未 live 验证。
- 去噪不用 diffusers scheduler（`self.scheduler=None`,timestep-shift flow,
  默认 `num_timesteps=50, shift=3.0, cfg_text 4.0 / cfg_img 1.5`）。

## 从输入到输出的主要流程

以下 2–4 步描述**两 stage 变体**（`bagel`/`bagel_think`,think 变体的差异仅
在 companions 用 `expand_cfg_prompts_think` 且 KV 延后到 EOS）;
`bagel_single_stage` 不走 CFG 伴随请求与 KV 传输,理解+生成全在
`BagelPipeline` 内部完成。

1. `model_extras/bagel.py` 的 prompt builder 组 `<|im_start|>…` /
   `<|fim_middle|>`（i2i）请求。
2. `stage_input_processors/bagel.py::expand_cfg_prompts`：3 路 CFG
   （gen/cfg_text/cfg_img）实现为**伴随 AR 请求**（`__cfg_text`/`__cfg_img`
   后缀）。t2i：只建一个 cfg_text 伴随（无负向 prompt 时整个跳过）,cfg_img
   复用 gen KV;i2i：cfg_text（`<|fim_middle|>`+负向,保留图像）与 cfg_img
   （去 `<|fim_middle|>`,丢图像）两个伴随都建。
3. thinker 前传;img2img 时 VAE-latent token 走 `*_moe_gen` 复权重路径,并重写
   position id（VAE token 与分隔符都在 M、ViT token 在 M+1、后续文本
   M+2…）——**必须与单 stage DiT 的 rope 方案一致,否则传过去的 KV 不可用**。
4. DiT stage 用 `NaiveCache.from_object` 重建主 KV,`collect_cfg_kv_caches`
   收伴随 KV;`Bagel.generate_image` 去噪;可选轨迹记录
   （`return_trajectory_latents`,RL 用）→ PIL Image。
- RNG 陷阱：`_regen_init_noise_on_device` 按请求在 CUDA 上重播 init noise
  （对齐 Lance 噪声流）;`forward` 单 prompt（多了只取第一个并告警）;分辨率超
  `max_latent_size × latent_downsample` 直接 raise。

## 怎样验证功能、精度和性能

- 单元：`tests/diffusion/models/bagel/`（`test_naive_cache`、
  `test_combine_cfg`、`test_bagel_lora`、`test_trajectory_recording`）;
  连接器：`tests/distributed/omni_connectors/test_bagel_*_connector.py`。
- e2e：`tests/e2e/{offline_inference,online_serving}/test_bagel*.py`
  （含 expansion 与 multi_replicas）;perf 定义
  `tests/dfx/perf/tests/test_bagel_vllm_omni.json`;recipe
  `recipes/Bagel/BAGEL-7B-MoT.md`。
- 已知未决：`GEN_THINK_SYSTEM_PROMPT`/`VLM_THINK_SYSTEM_PROMPT` 在 pin 上无
  引用（疑似死代码）;single_stage 的 arch→类解析链未 live 验证。
