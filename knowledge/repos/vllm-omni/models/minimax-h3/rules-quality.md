---
title: "rules-quality 验证规则"
created: 2026-09-22
updated: 2026-09-22
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #5709"]
---

# rules-quality 验证规则

## MMH3-4a2 — official-reference oracle 必须 immutable 且覆盖两个 modality

- 触发：新增或修改 H3 official-reference accuracy test、golden、threshold 或支持声明。
- 强制：checkpoint 和 reference asset 分别 pin 到可解析的 immutable revision/digest；prompt、
  request 参数、执行 topology 与阈值绑定同一 exact case。video 做 metadata 与视觉相似度，
  audio 除 codec/rate/channel metadata 外还必须比较内容或质量。
- 禁止：用 `resolve/main` 作 golden；假定权重 revision 一定包含 asset；把 AAC/32 kHz/stereo
  metadata 通过当作 audio accuracy；用另一硬件的结果为当前 CI lane 背书。
- 验收：昂贵 server startup 前完成 revision/digest preflight；exact case 满足
  [DIFF-3a](../../components/diffusion/rules.md) 与 [VOMNI-CI-1b](../../ci/rules.md)，视觉和
  音频 scorer 都有正向结果及损坏单一 modality 的反例。 ^[PR #5709]
