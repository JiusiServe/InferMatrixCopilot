---
title: "vLLM-Omni apps 与 tooling 规则"
created: 2026-09-02
updated: 2026-09-02
type: rule
tags: [vllm-omni]
sources: ["PR #5756", apps/ComfyUI-vLLM-Omni/comfyui_vllm_omni/nodes.py, apps/ComfyUI-vLLM-Omni/comfyui_vllm_omni/utils/api_client.py, apps/ComfyUI-vLLM-Omni/comfyui_vllm_omni/utils/models.py, apps/ComfyUI-vLLM-Omni/comfyui_vllm_omni/utils/types.py, tests/e2e/features/comfyui/test_comfyui_integration.py]
confidence: high
---

# Apps 与 tooling 规则

只有 `OMNI-TOOL-数字字母` 是可审计规则 ID。

## Direct 代码快速入口

| PR 描述信号 | 规则 | 第一批源码 |
|---|---|---|
| ComfyUI video node、frame/reference、multipart payload | `OMNI-TOOL-1a` | `nodes.py` → `utils/types.py` → `utils/api_client.py` |
| ComfyUI model path、partition、params builder | `OMNI-TOOL-1b` | `utils/models.py` → `utils/api_client.py` → integration test |

## OMNI-TOOL-1a — reference 输入状态与 multipart 字段必须一起验证

- 触发：修改 ComfyUI video node 的 `frame`、`references`、task 选择或上传字段。
- 强制：无输入路由到 `t2va`，仅 `frame` 路由到 `fl2va`，仅 `references` 路由到
  `ref2va`，并在发请求前拒绝 frame/reference 同时存在。Ref2VA 只接受“一张图像 + 一段
  音频”或“一到两个纯视频”；不得把 video 与 image/audio reference 混用。
- payload：frame/image 使用 `input_reference`，audio 使用 JSON `audio_reference`，每段
  video 分别追加一个 `input_references`；model task 必须通过 `extra_params` 到达参数 builder。
- 验收：公开 node 到 API client 的测试分别覆盖三条 task 分支、互斥/数量错误，以及最终
  `multimodal_data` 和请求参数；只测 validator helper 不算端到端证据。 ^[PR #5756]

## OMNI-TOOL-1b — model lookup 不得丢失本地路径中的 partition

- 触发：增加 model family、`/FL2VA` 或 `/Ref2VA` partition，或修改参数 builder dispatch。
- 强制：lookup 同时支持 Hub ID 和任意父目录下以 `MiniMax-H3/FL2VA|Ref2VA` 结尾的本地
  路径；归一化路径时必须保留 family/partition 后缀，不能只取 basename。builder 调用必须
  使用其 keyword-only `extra_params` 合同。
- MiniMax H3 的 `flow_shift` 保持顶层字段，`audio_flow_shift` 和 `task` 放在
  `extra_params`；内部 `type` 只在 model dispatch 完成后移除。
- 验收：Hub ID、本地绝对路径及两个 partition 都命中同一 model spec，并断言 builder 收到
  正确 keyword 和最终字段层级。PR review 曾直接发现 basename lookup 与错误 builder keyword，
  因此这两项必须作为回归 fence。 ^[PR #5756]
