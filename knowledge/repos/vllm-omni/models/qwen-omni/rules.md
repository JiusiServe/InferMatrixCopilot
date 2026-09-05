---
title: "Qwen-Omni 规则"
created: 2026-09-04
updated: 2026-09-05
type: rule
tags: [vllm-omni, models, qwen-omni]
sources: ["PR #5687", "PR #6284", "PR #6449", "PR #4322", "PR #6748", "PR #6886", "PR #7019", vllm_omni/config/pipeline_registry.py, vllm_omni/deploy/qwen3_omni_moe.yaml, vllm_omni/deploy/qwen3_omni_moe_thinking.yaml, vllm_omni/engine/stage_init_utils.py, vllm_omni/model_executor/models/qwen2_5_omni/qwen2_5_omni.py, vllm_omni/model_executor/models/qwen3_omni/quantization.py, vllm_omni/model_executor/models/qwen3_omni/qwen3_omni.py, vllm_omni/model_executor/models/qwen3_omni/qwen3_omni_moe_thinker.py, vllm_omni/quantization/component_config.py, tests/config/test_config_factory.py, tests/diffusion/quantization/test_component_routing.py, tests/engine/test_stage_engine_args.py, tests/model_executor/models/qwen3_omni/test_qwen3_omni_quantization.py]
confidence: high
---

# Qwen-Omni 规则

## QOMNI-1a — Qwen3-Omni Thinker MRoPE 必须保留 CUDA custom-op 边界

- 触发：修改 `qwen3_omni_moe.yaml` 的 CUDA compilation 配置、Thinker MRoPE/RMSNorm 路径，或升级会改变 Inductor MRoPE fusion 的 vLLM 版本。
- 强制：CUDA platform overlay 仅为 Thinker stage 0 设置 `compilation_config.custom_ops: ["+rotary_embedding"]`，保持 MRoPE 在 CUDA/Triton custom-op 边界后；Talker/Code2Wav 与 CPU、MUSA、NPU、ROCm、XPU 配置不得继承此 override。
- 禁止：以全局 `enforce_eager` 取代窄 graph boundary；启用更宽的 Q/K norm-RoPE fusion flag；只检查 YAML 文本，或将 Thinker 数值稳定性外推为全部 Qwen stage/平台。
- 验收：经 `_apply_platform_overrides → merge_pipeline_deploy` 断言 CUDA 仅 stage 0 有该 custom op、其余 stage/平台均无；固定 seed 下与 eager oracle 的 thinker/talker/codec 离散轨迹必须完全一致，并验证生成 WAV 逐字节一致。相关配置展开见 [Configuration rules](../../components/configuration/rules.md)，家族 topology 见 [architecture](architecture.md)。^[PR #6449]

## QOMNI-1b — Qwen3-Omni 嵌套 stage 的量化名称只能在统一 wrapper 映射一次

- 触发：修改 Qwen3-Omni 的 `SupportsQuant`、`WeightsMapper`、compressed-tensors/AWQ
  ignore/exclude 名称，或 Thinker、Talker、Code2Wav 的嵌套模型构造。
- 强制：在统一 Qwen3-Omni wrapper 暴露 checkpoint 到最终嵌套模块路径的映射，并先对完整
  quantization config 执行一次映射；`ComponentQuantizationConfig` 必须递归映射每个非空
  component 和 default config。子 stage 检测到该映射后不得再次改写名称，但仍须合并自己的
  `packed_modules_mapping`，供量化 scheme 匹配 fused module。该嵌套 metadata 是 optional：outer-map-once
  marker 已存在时，缺少 attribute 必须 no-op；存在且非空时才 merge，且不得清掉 outer marker。
- 禁止：只映射一个 component wrapper 而给它标记为已映射；让 Thinker/Talker/Code2Wav 各自
  重复应用 stage mapper；因修复名称匹配而把 BF16 router/encoder 也纳入量化；或把该构造期
  映射修复描述成 quantization kernel / inference hot path 变化。
- 验收：以真实 component-wrapped `CompressedTensorsConfig`（含 `None` component 与 default）
  断言 `ignore` HF names 映射到最终路径；加载 AWQ checkpoint 时三 stage 都能完成 weight
  loading，且不出现缺模块/参数或 routed-expert quantized-weight 属性错误。CPU regression 还必须覆盖
  missing quant config、outer-mapped Talker-style model 缺 `packed_modules_mapping` 的 no-op、及 present
  mapping merge；这只是 mapping/metadata contract，不是 quant scheme、kernel、quality 或 performance
  evidence。^[PR #5687] ^[PR #6748]

## QOMNI-1c — Instruct 的 thinker-only deploy 必须选择静态 pipeline key

- 触发：修改 Qwen3-Omni 的 pipeline registry、`qwen3_omni_moe_thinking.yaml`，或依赖
  `enable_audio_output` 自动拓扑选择的 serve/config-factory 路径。
- 强制：需要 Instruct 权重只加载 Thinker 时，deploy YAML 必须显式设
  `pipeline: qwen3_omni_moe_thinker_only`；该 registry key 必须直接绑定静态单 stage
  text→text `PipelineConfig`，不能重新进入由 HF config 决定全三 stage 的
  `qwen3_omni_moe` resolver。没有显式 YAML 的 Captioner/Thinking checkpoint 继续由 resolver
  自动选择 thinker-only 拓扑。
- 禁止：把 Instruct 的 `enable_audio_output` 当作 thinker-only 的充分条件；只修改 YAML 而未
  注册静态 key；或以 key 存在/原始 YAML 替代最终 resolved pipeline 的断言。
- 验收：分别以 Instruct 和 Thinking/Captioner HF config 经 `StageConfigFactory` 加载该 YAML，
  断言同一 `qwen3_omni_moe_thinker_only` pipeline、仅一个 Thinker stage 和 text output；同时
  直接解析该 key，断言其对象身份为 registry 的静态 `PipelineConfig` 而非 resolver 结果。PR
  只有这类配置单元测试，未提供真实 `vllm serve`、质量、性能或资源证据。^[PR #6284]

## QOMNI-1d — audio encoder TP 必须按 head divisibility 局部回退

- 触发：修改 Qwen3-Omni audio encoder 的 attention/FFN parallel linear、`encoder_attention_heads`，或其 global tensor-parallel 初始化。
- 强制：以 `encoder_attention_heads % global_tp_size` 判定该 audio-encoder layer 是否可分片。可整除时保持 global TP；不可整除时仅该 encoder layer 的 attention QKV、attention output projection、FC1 和 FC2 都以 `disable_tp=True` 构造，且 local attention head count 按 effective TP=1 计算。
- 禁止：仅关闭 QKV 或仅修正 `num_local_heads` 而让 output/FFN 仍分片；把这项 fallback 扩大为整个 Qwen3-Omni 模型关闭 TP；或把 PR 的 TP1/2/4/8 手工音频请求、MI350x full-workload throughput 数字归因于该 fallback。
- 验收：分别覆盖 heads 可被和不可被 global TP 整除的构造，断言四个 linear 的 `disable_tp` 一致、attention local-head count 正确，且 encoder 外的 Thinker/Talker TP 配置未被此条件改写。PR 仅报告手工请求与整体 workload 测量，未给出该局部回退的独立性能或质量证明。^[PR #4322]

## QOMNI-1e — Qwen2.5-Omni code2wav 缺失时必须 soft-fail，不能复活跨 stage 的旧 speech helper

- 触发：修改 Qwen2.5-Omni 的 `generate_audio`、`_codec_to_audio`、`_init_token2wav_model`、weight loading、Talker sampling/logits，或 Thinker/Talker/Code2Wav 的 staged 构造。
- 强制：`_codec_to_audio` 在 `token2wav` 缺失时必须直接返回 `None`；`_init_token2wav_model` 只能由持有已解析 `hf_model_folder` 的 Token2Wav weight-loading 路径调用；语音生成维持 Thinker → Talker → Code2Wav 的 stage handoff。
- 禁止：无参数调用 `_init_token2wav_model()`；恢复 `generate_speech` 或 `_convert_to_codec_tokens`；仅 thread `sampling_metadata` 就声称修复旧 helper（其 Talker `compute_logits` 调用仍带已失效的额外参数）；或让单一 wrapper 违反 staged ownership 而同时拥有 Talker 和 Token2Wav。
- 验收：目标树中不存在两个已删除 helper 或无参数 initializer call；`token2wav is None` 的 `_codec_to_audio` 路径返回 `None` 而非 `TypeError`；Token2Wav load path 仍向 initializer 传入解析后的 HF directory。PR 未新增测试或 E2E，故这些是静态/call-site 合同，不构成运行时、音频质量或性能证据。^[PR #6886]

## QOMNI-1f — Qwen3-Omni MoE 默认值必须走显式 backend 合同

- 触发：修改 Qwen3-Omni Thinker/Talker 的 MoE backend、`qwen3_omni_moe.yaml`、stage-engine argument finalization，或迁移旧的环境变量 workaround。
- 强制：仅当 `model_arch` 为 `Qwen3OmniMoeForConditionalGeneration` 且已解析的 `moe_backend` 为缺失或 `auto` 时，finalization 才默认写入 `triton`；任何显式 backend 必须原样保留。随仓库发布的 `qwen3_omni_moe.yaml` 必须在 Thinker stage 0 和 Talker stage 1 都显式 pin `moe_backend: triton`；Code2Wav 不继承该模型专属 MoE 设置。
- 禁止：通过 `VLLM_USE_FLASHINFER_MOE_FP16` 或其他 process-wide 环境变量选择 backend；把默认值写成覆盖用户/deploy 显式选择；只改 deploy YAML 却不覆盖 legacy 与 typed builder 的最终 engine args。
- 验收：以 Qwen3-Omni default 和一个显式 backend control，分别经 `build_legacy_engine_args_dict` 与 `build_engine_args_dict_from_omni_stage_config` 断言最终 `moe_backend`；默认两路径均为 `triton`，显式值不变。helper 单测只能补充分支覆盖，不能代替 builder-level assertion。PR 只提供 compile/Ruff/diff 检查及因缺少 `torch` 未运行的 targeted pytest，故不构成 GPU 稳定性、性能或音频质量证据。^[PR #7019]
