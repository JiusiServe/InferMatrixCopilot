---
title: "Qwen-Omni 规则"
created: 2026-09-04
updated: 2026-09-04
type: rule
tags: [vllm-omni, models, qwen-omni]
sources: ["PR #6449", vllm_omni/deploy/qwen3_omni_moe.yaml, tests/config/test_config_factory.py]
confidence: high
---

# Qwen-Omni 规则

## QOMNI-1a — Qwen3-Omni Thinker MRoPE 必须保留 CUDA custom-op 边界

- 触发：修改 `qwen3_omni_moe.yaml` 的 CUDA compilation 配置、Thinker MRoPE/RMSNorm 路径，或升级会改变 Inductor MRoPE fusion 的 vLLM 版本。
- 强制：CUDA platform overlay 仅为 Thinker stage 0 设置 `compilation_config.custom_ops: ["+rotary_embedding"]`，保持 MRoPE 在 CUDA/Triton custom-op 边界后；Talker/Code2Wav 与 CPU、MUSA、NPU、ROCm、XPU 配置不得继承此 override。
- 禁止：以全局 `enforce_eager` 取代窄 graph boundary；启用更宽的 Q/K norm-RoPE fusion flag；只检查 YAML 文本，或将 Thinker 数值稳定性外推为全部 Qwen stage/平台。
- 验收：经 `_apply_platform_overrides → merge_pipeline_deploy` 断言 CUDA 仅 stage 0 有该 custom op、其余 stage/平台均无；固定 seed 下与 eager oracle 的 thinker/talker/codec 离散轨迹必须完全一致，并验证生成 WAV 逐字节一致。相关配置展开见 [Configuration rules](../../components/configuration/rules.md)，家族 topology 见 [architecture](architecture.md)。^[PR #6449]
