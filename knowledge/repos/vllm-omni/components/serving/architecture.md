---
title: "Serving 共享架构"
created: 2026-07-10
updated: 2026-09-02
type: architecture
tags: [vllm-omni, components, serving]
sources: ["PR #5085", vllm_omni/entrypoints/, vllm_omni/entrypoints/openai/video_api_utils.py, vllm_omni/engine/orchestrator.py, tests/entrypoints/openai_api/test_video_server.py]
---

# Serving 共享架构

## 职责和边界

Serving 层把用户输入转换成内部请求，选择 online/offline 执行入口，并把参数交给实际 engine 或 pipeline。它也是 CLI、HTTP 和兼容 API 之间保持行为一致的责任边界。

## 当前源码入口（main @ 238fc0a6 复核；此前亦在 dev/vllm-align @ 4f2b32c 验证，结果一致）

- 用户入口：`vllm_omni/entrypoints/` — `omni.py` / `async_omni.py` / `omni_base.py`（offline 与
  async 入口）、`cli/`、`openai/`（OpenAI-compatible API）、`openpi/`、`pd_utils.py`、
  `stage_utils.py`、`client_request_state.py`。
- engine 边界：`vllm_omni/engine/` — `orchestrator.py` + `orchestrator_monitor.py`（阶段编排）、
  `async_omni_engine.py`、`stage_engine_core_client.py` / `stage_engine_core_proc.py`（stage
  engine core）、`stage_pool.py` / `stage_runtime.py`（stage 生命周期）、`output_processor.py`、
  `membership_controller.py`。

Serving 只公开有明确请求语义和下游 consumer 的字段。Sampling dataclass、engine state 或 pipeline state 可以包含 tensor、KV 状态和运行时中间量，但这些内部字段不会因此自动成为请求字段。

Video reference 字节在 `video_api_utils.py` 通过 vLLM `VIDEO_LOADER_REGISTRY` 的
`omni` backend 解码。该 backend 只定义顺序 first-N/last-N 帧索引，`_decode_video_bytes`
将 `max_frames` 映射为 `num_frames`，从 loader metadata 恢复 fps，并将数组转为 RGB
PIL frames。当前 loader 调用固定 `backend="pyav"`；注册表复用不等于用户已能
选择 opencv/torchcodec 等 decoder。

## 主要源码和调用入口

- `vllm_omni/entrypoints/openai/`：OpenAI-compatible HTTP 请求解析和响应。
- `vllm_omni/entrypoints/`：其他 online/offline 入口及 engine 边界。
- 请求协议对象：声明字段与兼容扩展的第一层 owner。
- engine、pipeline、prompt 和 sampling 参数：Serving 转换结果的最终 consumer。

## 请求参数怎样流动

```text
声明请求字段 ----------------\
flattened client extras --------\
raw nested compatibility --------+-> 未修改请求的来源快照
canonical / legacy containers ---/             |
                                               |-> 当前 RFC slice 的来源校验
                                               |      |-> normalized model extra_args
                                               |      \-> bounded consumer view
                                               |
                                               \-> 既有 pure / mixed dispatcher
                                                      |-> prompt / control
                                                      |-> AR metadata
                                                      \-> diffusion sampling params
```

来源信息只能在冲突检查之后丢弃。Request-extra slice 在 serving 对请求写回默认值、preprocess、decode 和 dispatcher 分支之前产出两个不同用途的结果：模型专属字段进入 normalized `extra_args`；common sampling 字段和既有 service controls 进入限定字段的 consumer view。Pure、mixed 和 AR sampling 路径只消费这个 view，不再读取 raw extras。

字段 owner 必须互斥。若 registry 声明字段与既有 service control 重名，例如 `negative_prompt`，该字段仍参与跨来源冲突检查，但只由 service-control consumer view 持有，不能同时作为 model `extra_args` 再登记一次。未知 root 字段按公开合同忽略或拒绝，不能因为与内部状态同名而被当成已支持字段。

逐 stage 用户 overrides、topology、模型能力和部署/YAML stage defaults 有各自既有 owner；除非目标 RFC 明确改变这些合同，request-extra normalization 不应把它们收进新的全请求 compiler。Single owner 的含义是“当前 slice 的语义只有一个 owner”，不是“所有相邻职责必须合并成一个对象”。

## 调查顺序

1. 从用户实际入口确认请求字段和默认值。
2. 沿解析后的请求对象确认字段没有丢失或改义。
3. 用 server log 或真实请求证明命中了预期 engine/pipeline。
4. 只有字段已经正确到达模型层后，才把问题下钻到 component 或 model。

## 不在这里决定的事情

Serving 层不应该偷偷修正模型算法、制造静默 fallback，或用入口默认值掩盖下游配置错误。

源码目录会随版本演进，具体 owner path 在改代码前必须以目标仓库当前版本为准。

## 怎样验证

1. 为当前 RFC slice 实际接受的声明字段、flattened、nested 和 canonical/legacy container 维护可执行的来源矩阵；未被 slice 拥有的逐 stage、topology、capability 和 server defaults 明确标为不在范围内。
2. 重复的已消费字段必须产生可观察的 4xx；不重叠字段必须保留。
3. 每条生产 dispatcher 用真实请求对象断言 normalization boundary 只运行一次、失败发生在 preprocess/decode/engine 前，并以 root control + nested extras 断言最终 consumer。
4. 增加一个内部同名字段反例，防止内部 schema 扩张公开 API；helper mock 不能代替生产入口证明。
