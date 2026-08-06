---
title: "ComfyUI vLLM-Omni 规则"
created: 2026-08-06
updated: 2026-08-06
type: rule
tags: [vllm-omni, components, serving]
sources: [apps/ComfyUI-vLLM-Omni/comfyui_vllm_omni/nodes.py, apps/ComfyUI-vLLM-Omni/comfyui_vllm_omni/utils/api_client.py, tests/e2e/features/comfyui/test_comfyui_integration.py, "PR #5756"]
confidence: high
---

# ComfyUI vLLM-Omni 规则

只有 `COMFY-数字字母` 是可审计规则 ID。

## Direct 代码快速入口

| PR 描述信号 | 规则组 | 第一批源码 |
|---|---|---|
| ComfyUI、T2VA/FL2VA/Ref2VA、frame/reference、multipart | COMFY-1a | `apps/ComfyUI-vLLM-Omni/comfyui_vllm_omni/nodes.py` → `utils/api_client.py` → integration tests |

## COMFY-1a — video mode 必须由互斥的 canonical 输入组合唯一决定

- 触发：ComfyUI video-generation node/client 修改 frame、image/audio/video references、
  mode 路由或 multipart 字段。
- 强制：先校验 frame 与所有 reference 互斥，再确定唯一模式：有 frame 走 FL2VA；frame
  和 references 都没有走 T2VA；reference-only 只接受“恰好一张图 + 一段音频”或“仅一个
  或多个视频”，并走 Ref2VA。图像写入 `input_reference`，音频写入
  `audio_reference`，视频按顺序重复写入 `input_references`。
- 禁止：视频与 image/audio 混用；frame 与 reference 同时发送；按字段遍历顺序覆盖已经
  选定的 mode；让 node 校验与 API client 使用不同的组合矩阵或字段名。
- 验收：node 和 client 都有非法组合负例；E2E 分别覆盖 T2VA、FL2VA、image+audio
  Ref2VA 和 multi-video Ref2VA，并断言最终 mode 与 multipart key/count。 ^[PR #5756]

owner 范围见 [ComfyUI index](_index.md)；服务端请求合同见
[Serving 规则](../serving/rules.md)，模型能力见 [MiniMax H3](../../models/minimax-h3/_index.md)。
