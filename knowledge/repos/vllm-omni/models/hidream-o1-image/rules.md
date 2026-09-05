---
title: "HiDream-O1 Image 规则"
created: 2026-09-04
updated: 2026-09-04
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #5194", "vllm_omni/diffusion/models/hidream_o1_image/hidream_o1_image_transformer.py", "vllm_omni/diffusion/models/hidream_o1_image/pipeline_hidream_o1_image.py", "vllm_omni/diffusion/data.py", "vllm_omni/diffusion/registry.py"]
confidence: high
---

# HiDream-O1 Image 规则

## Direct 代码快速入口

| PR 描述信号 | 规则 |
|---|---|
| request geometry、mixed attention、TP、Cache-DiT 或 patch output | `HIDREAMO1-1a` |

HiDream-O1 Image 的模型专属约束集中在本页；模型 registry signature、共享 attention backend 及通用 Cache-DiT lifecycle 不在此重复展开。

## HIDREAMO1-1a — HiDream-O1 Image pipeline 请求、并行与输出合同

- 触发：修改 HiDream-O1 Image 的分辨率、prompt/图像 token 构造、采样限制、TP、`_dit_modules`、Cache-DiT 或 patch 输出后处理。
- 强制：仅支持 BF16、单 prompt、单输出和 `cfg_parallel_size<=1`；将请求尺寸吸附到 `PREDEFINED_RESOLUTIONS`，以 32 为 patch size；文本行保持 causal、timestep/image 行保持 full attention，并遵守 [DIFF-1z](../../components/diffusion/rules-attention.md)。TP 路径必须使用 vLLM parallel layers；`_dit_modules` 固定指向 `model.model.language_model`，Cache-DiT 使用 `ForwardPattern.Pattern_3` 与 `has_separate_cfg=True`；post-process 必须按 patch 布局还原 RGB 图像。
- 禁止：把任意请求宽高当作 checkpoint 原生尺寸；接受多 prompt、多输出、显式 latents/timesteps、CFG parallel 或图片编辑输入；把 `model.model.language_model` 的 Cache-DiT target 替换成不存在的顶层 transformer；仅凭进程启动或 shape 正确宣称 TP、缓存和输出语义已验证。
- 验收：覆盖尺寸吸附、BF16/批量/不支持参数的 fail-fast、混合 attention 与 RGB 尺寸检查；以固定 prompt、seed=42、2048x2048、50 steps、guidance=5、TP=2 在 2x H100 上回归无缓存与 Cache-DiT，断言 nested target、输出质量阈值和资源/延迟证据均绑定该 exact case。^[PR #5194]

共享混合 attention 合同见 [DIFF-1z](../../components/diffusion/rules-attention.md)，自动解析与 registry 合同见 [DIFF-4t](../../components/diffusion/rules-system-runtime.md)。
