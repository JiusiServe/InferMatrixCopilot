---
title: "Diffusion tensor dtype 规则"
created: 2026-09-03
updated: 2026-09-03
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #5067", "PR #5068", "PR #5174", "PR #5981", "Issue #5880", vllm_omni/diffusion/layers/norm.py, tests/diffusion/layers/test_norm.py]
confidence: high
---

# Diffusion tensor dtype 规则

## DIFF-1c — runtime tensor 派生 consumer dtype，parameter 跟随 loader 构造上下文

- 触发：mixed precision pipeline 中新建 runtime mask/index/constant/buffer/precomputed tensor，或构造
  shared layer parameter。
- 强制：runtime tensor 从输入或目标权重派生 device/dtype，整数 index 显式使用 consumer 类型；
  graph/eager 与 batch reorder 后保持 shape、alias 和数值语义。parameter constructor 的
  `dtype=None` 则读取 `torch.get_default_dtype()`，但只依赖 loader 的
  `set_default_torch_dtype(od_config.dtype)` 构造作用域；显式 dtype 始终优先。RMSNorm parameter
  storage dtype 与 `forward_native` FP32 accumulation 是两个独立合同。
- 禁止：runtime temporary 依赖环境中不受控的 process-default fp32/CPU 或隐式 cast/move；但不能把
  这条禁令错用于 loader-scoped parameter construction。不得把 Python 参数默认写死 fp32 来绕过
  BF16 loader context，也不能只测 shape 而不执行真实 consumer。
- 验收：runtime 路径覆盖 BF16、错长、batch reorder 和 graph/eager；constructor 覆盖 loader-scoped
  BF16、FP32 与显式 override。shared RMSNorm 被 HunyuanImage3、Cosmos3、MiniMax-H3、Wan2.2、
  Z-Image 等消费，修复不能只跑一个模型。
- 证据边界：相同输入的 online/offline 与 retry 重复得到相同失败值，只支持“确定性数值漂移”；
  未绑定软件 commit、硬件与可复核 artifact 的截图不能建立跨硬件或 bit-exact parity。
  ^[PR #5067] ^[PR #5068] ^[PR #5174] ^[PR #5981]
