---
title: "LingBot-Video"
created: 2026-08-10
updated: 2026-08-10
type: index
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/lingbot_video/, vllm_omni/model_extras/lingbot_video.py, vllm_omni/diffusion/registry.py, "PR #5311"]
---

# LingBot-Video

- registry architecture：`LingBotVideoPipeline`；dense 1.3B 与 MoE 30B-A3B checkpoint 共用
  pipeline，transformer 的 dense/MoE 实现不因 T2I/TI2V 接入而分叉。
- 模式：已有 T2V，加 T2I 与单图 TI2V；离线走共享 text-to-image/image-to-video prompt
  builder，在线分别走 `/v1/images/generations` 与 `/v1/videos`。
- 当前公开范围仅单 request、单 output、最多一张 reference image；Refiner、生产 serving 的
  SP/USP/HSDP/CFG parallel/VAE patch parallel、component/layerwise offload、EP/FusedMoE、
  FP8 experts 与 Cache-DiT 均未暴露或缺少已落地证据（内部 `_generate` 已有 CFG-parallel 参数，
  不能据此宣称 serving 可用）。
- owner 边界：共享入口传播/4xx 合同先查 [Serving rules](../../components/serving/rules.md)，
  通用 diffusion lifecycle 查 [Diffusion rules](../../components/diffusion/rules.md)，本模型的
  mode、帧数、图像条件和输出 key 查 [rules](rules.md)。

## 什么时候查这里

- PR 涉及 `lingbot_video`、`LingBotVideoPipeline`、T2I/T2V/TI2V 选择、LingBot 分辨率预设、
  causal-VAE 帧网格或首帧条件。
- 性能数字只能回到可复现 benchmark；本页不把 PR 的单机耗时/显存结果升级为 gate。
