---
title: "GLM-Image token-ID handoff 规则"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #7843"]
confidence: high
---

# GLM-Image token-ID handoff 规则

## Direct 代码快速入口

| PR 描述信号 | 规则组 | 第一批源码 |
|---|---|---|
| TOKEN_IDS、generated/source IDs、AR→DiT、auxiliary hidden | `GLMIMAGE-IDS-1a`；共享 naming/accumulation 另查 [输出合同](../../components/model-executor/rules-output-contract.md) | `vllm_omni/model_executor/stage_input_processors/glm_image.py::ar2diffusion`；`vllm_omni/outputs/output_modality.py`、`vllm_omni/outputs/output_processor.py`；`tests/model_executor/stage_input_processors/test_glm_image.py` |

## GLMIMAGE-IDS-1a — generated IDs 与 source-image IDs 必须保留各自 handoff

- 触发：修改 GLM-Image engine_output_type、AR auxiliary output 或 ar2diffusion bridge。
- 强制：generated IDs 仍走 cumulative_token_ids，source-image IDs 保持 ids.prior_image；
  TOKEN_IDS 类型只改变共享 naming/retention，不为 GLM 另加 generic hidden 的特殊重命名。
  辅助 hidden 即使命名为 token_ids，值也仍是原 tensor，不能替代 bridge 的真实离散 IDs。
- 禁止：为 output-type 改名重写已正确的 ar2diffusion；把仅 eager 单 NVIDIA T2I/I2I 的
  matched PNG parity 视为 NPU/optional auxiliary producer 或全模式表示验证。
- 验收：T2I 与 I2I 分别断言 generated/source IDs 到达正确输入、EOS 处理与已有语义保持；
  若新增 auxiliary consumer，另核实其 dtype/shape/value 和命名含义。^[PR #7843]

共享 parsing 与 accumulation 见 [输出合同](../../components/model-executor/rules-output-contract.md)；
AR→DiT 数据流见 [模型架构](architecture.md)。
