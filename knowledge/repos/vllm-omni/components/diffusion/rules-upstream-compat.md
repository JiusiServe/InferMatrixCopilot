---
title: "Diffusion upstream 兼容规则"
created: 2026-09-02
updated: 2026-09-02
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #5976", vllm_omni/diffusion/compile.py, vllm_omni/diffusion/distributed/parallel_state.py, vllm_omni/diffusion/layers/fused_moe.py, vllm_omni/diffusion/models/diffusers_adapter/pipeline_diffusers_adapter.py, vllm_omni/quantization/_copy_missing_attrs.py, tests/diffusion/test_compile.py, tests/e2e/accuracy/test_qwen_image.py]
confidence: high
---

# Diffusion upstream 兼容规则

## DIFF-4k — upstream API shim 与 accuracy backend 必须按能力而非名字对齐

- 触发：vLLM/torch bump 删除或重命名 MoE/quant/platform API，或 kernel hub 没有当前 image build。
- 强制：机械 shim 迁入 Omni 单一共享 owner（如 `copy_missing_attrs`、`is_interleaved`），全部 caller
  同步；MoE 使用 live factory 名，XPU op priority 使用 live provider 名。accuracy comparison 两侧
  必须走同一 attention capability chain；hub backend 不可用时 server/reference 一起降到 SDPA/native。
- 禁止：从已删除 upstream 私有 helper 导入；只让一侧 fallback；用 compile-vs-eager LPIPS 判断
  quantization 质量，或因 fallback 放宽所有 backend 的 gate。
- 验收：import/调用者 census 无旧 symbol；shared helper 保留 tensor attrs；backend probe 对可用/不可用
  分支断言两侧匹配，阈值只按实际 backend 分支选择；quant quality 两臂都 eager。真实硬件 accuracy
  仍是必要证据，单测不能证明质量门通过。^[PR #5976]

## DIFF-4l — regional compile wrapper 必须保留被检查 callable 的签名

- 触发：包装 regional-compiled `forward`，或升级会用 reflection 发现 DiT block 的 Cache-DiT。
- 强制：保留参数名和 return annotation；编译 callable 必须仍能被 `inspect.signature` 识别为原
  `forward` 合同。兼容修复若只剩签名透明性，compile failure 必须继续显式暴露。
- 禁止：用无签名的通用 `*args, **kwargs` wrapper；把已撤回的常驻 eager fallback 写成 active 行为；
  以进程能启动替代 Cache-DiT block discovery 验证。
- 验收：打开/关闭 Cache-DiT 都能匹配目标 block；测试冻结参数名与 return annotation，并让真实 lazy
  compile error 失败而非静默降级。^[PR #5976]
