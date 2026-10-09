---
title: "Z-Image TeaCache 校准合同"
created: 2026-10-09
updated: 2026-10-09
type: rule
tags: [vllm-omni, models]
sources: ["PR #8408"]
confidence: high
---

# Z-Image TeaCache 校准合同

## ZIMAGE-1a — TeaCache 系数只用于已校准 checkpoint 与输入域

- 触发：修改 Z-Image TeaCache polynomial、threshold、adapter registry 或校准 hook。
- 强制：使用 Z-Image-Turbo 自身拟合系数，不借用 Qwen-Image 系数；现有拟合测量域为 input relative L1 0.024–0.336，threshold 默认 0.2。同 pipeline 类的其他 checkpoint 不自动获得校准保证。DataCollectionHook 初始化时解析并校验 extractor，未知模型在 forward 前失败。
- 禁止：把 polynomial 在测量域外的行为当作安全保证，或把 borrowed coefficients 的功能可跑说成可靠加速；从够步数模型的收益外推 distilled 短步数。
- 验收：测试系数与 Qwen 不同、默认 config/threshold 和 adapter 注册；更换 checkpoint/输入域/threshold 时重做同 workload 的质量与命中率校准，记录域外风险及 hardware/head。 ^[PR #8408]
