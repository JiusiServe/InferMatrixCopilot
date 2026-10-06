---
title: "Borrowed RGB video encoding 规则"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, components]
sources: ["PR #7355"]
---

# Borrowed RGB video encoding 规则

## SERV-VIDEO-1a — Borrowed PyAV frame 必须有精确 eligibility 与最终配置来源

- 触发：修改 Videos API encoding options、remote diffusion metadata fallback 或 borrowed RGB frame生成。
- 强制：enable_borrowed_frames默认false；API先读effective diffusion config，remote metadata缺失时回读resolved diffusion stage的diffusion_config/engine_args。共享validation准备所有frames后，仅uint8、3D、末轴3且每帧pixel/channel strides=(3,1)进入from_numpy_buffer，允许row padding；其他输入走原planar/legacyfallback。音频mux/sample-rate/codec options保持，预编码bytes直接返回。
- 禁止：从metadata-onlyremoteclient丢掉明确stageoverride；对float/灰度/错stride借用；保留AVFrame却释放其backingstorage；把RGB→MP4的局部copy结果声称包括VAE/HTTP或所有shape性能提升。
- 验收：inline/remote配置、关闭开关、row-paddedRGB、非RGB/uint8、audio mux、preencodedbytes与持有frame跨引用释放回归；比较hash与完整MP4decode，小payload和coldregistration单独计时。 ^[PR #7355]
