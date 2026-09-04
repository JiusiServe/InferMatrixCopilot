---
title: "Boogu-Image 规则"
created: 2026-09-05
updated: 2026-09-05
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #6701", docs/models/supported_models.md, recipes/Boogu/Boogu-Image.md, vllm_omni/config/omni_config.py, vllm_omni/diffusion/models/boogu_image/pipeline_boogu_image.py, vllm_omni/entrypoints/utils.py, tests/diffusion/models/boogu_image/test_pipeline_boogu_image.py, tests/entrypoints/test_utils.py, tests/e2e/online_serving/test_boogu_image_edit.py]
confidence: high
---

# Boogu-Image 规则

## BOOGU-1a — global revision 必须填入每个未显式设 revision 的 stage

- 触发：全局/stage checkpoint revision handoff、Boogu component loader 或 Edit-Turbo recipe 变更。
- 强制：global revision 只补入未显式声明 revision 的 resolved stage；effective revision 必须一致传播到
  transformer source/prefetch、scheduler、mLLM、processor 和 VAE loaders。
- 禁止：覆盖 stage explicit revision，或只让一个 component 使用 global revision 而其余悄然跟 default branch。
- 验收：分别覆盖 global fill 与 stage override，并断言六个 consumer 的 effective revision 一致。Edit-Turbo
  文档/测试仅覆盖 `Boogu/Boogu-Image-0.1-Edit-Turbo` 的 `hotfix-1k-20260708`、4 steps、guidance 1.0；
  不证明 distinct Turbo class、DMD/renoise、quality 或一般 registry claim。^[PR #6701]
