---
title: "Qwen-Omni 规则"
created: 2026-09-04
updated: 2026-09-04
type: rule
tags: [vllm-omni, models, qwen-omni]
sources: ["PR #5687", "PR #6449", vllm_omni/deploy/qwen3_omni_moe.yaml, vllm_omni/model_executor/models/qwen3_omni/quantization.py, vllm_omni/model_executor/models/qwen3_omni/qwen3_omni.py, vllm_omni/quantization/component_config.py, tests/config/test_config_factory.py, tests/diffusion/quantization/test_component_routing.py]
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
  `packed_modules_mapping`，供量化 scheme 匹配 fused module。
- 禁止：只映射一个 component wrapper 而给它标记为已映射；让 Thinker/Talker/Code2Wav 各自
  重复应用 stage mapper；因修复名称匹配而把 BF16 router/encoder 也纳入量化；或把该构造期
  映射修复描述成 quantization kernel / inference hot path 变化。
- 验收：以真实 component-wrapped `CompressedTensorsConfig`（含 `None` component 与 default）
  断言 `ignore` HF names 映射到最终路径；加载 AWQ checkpoint 时三 stage 都能完成 weight
  loading，且不出现缺模块/参数或 routed-expert quantized-weight 属性错误。^[PR #5687]
