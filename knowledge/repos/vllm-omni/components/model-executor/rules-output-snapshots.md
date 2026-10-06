---
title: "Async output snapshot 规则"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, components, model-executor]
sources: ["PR #8213"]
---

# Async output snapshot 规则


## EXEC-SNAPSHOT-1a — 打包异步输出必须保留 producer 与 consumer 的 storage 所有权

- 触发：修改PackedOutputSnapshot、dtype/device slab grouping、reuse_existing_storage或跨stream D2H。
- 强制：按dtype/device分组保持pytree/shape/requestorder；只有contiguous leaves共享同storage且offset连续匹配copyplan才可重用slab。slot复用需等上一consumer，copy stream需等producer_event；host slab每output自有。quantized/非strided走原per-tensorfallback。
- 禁止：把mutablegraph/slotview当owned snapshot；省略producerevent或在D2H完成前复用device；为打包改变dtype、request归属或叶子数值；已有ownedpacked输出再做重复GPUcopy。
- 验收：dtype/device混合、empty/非contiguous/quantizedfallback、错offset、reuseon/off、独立producerstream、延迟D2H与后续slotoverwrite都覆盖，retainedhostoutput仍与原snapshot逐值一致。 ^[PR #8213]
