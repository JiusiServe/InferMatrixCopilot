---
title: "ComfyUI 规则"
created: 2026-09-22
updated: 2026-09-22
type: rule
tags: [vllm-omni, components, serving]
sources: ["PR #5756"]
---

# ComfyUI 规则

## COMFY-1a — video mode 与 multipart 字段必须共享当前能力矩阵

- 触发：ComfyUI video node/client 修改 frame、image/audio/video references 或 mode。
- 强制：先按当前服务端和目标 checkpoint 的能力矩阵校验组合，再确定唯一 mode；node 与 client 使用同一矩阵，按服务端字段名和输入顺序编码 multipart。新增 first/last frame 或 reference 组合必须同步两端。
- 禁止：按字段遍历顺序覆盖 mode；把早期 MiniMax H3 的 reference 限制推广到所有模型或后续功能。
- 验收：每个当前支持的组合断言最终 mode、multipart key/count/order；相邻非法组合在发送前失败。^[PR #5756]
