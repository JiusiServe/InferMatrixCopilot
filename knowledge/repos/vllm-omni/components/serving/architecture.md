---
title: "Serving 共享架构"
created: 2026-07-10
updated: 2026-07-23
type: architecture
tags: [vllm-omni, components, serving]
sources: [vllm_omni/entrypoints/, vllm_omni/engine/orchestrator.py]
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

## 主要源码和调用入口

- `vllm_omni/entrypoints/openai/`：OpenAI-compatible HTTP 请求解析和响应。
- `vllm_omni/entrypoints/`：其他 online/offline 入口及 engine 边界。
- 请求协议对象：声明字段与兼容扩展的第一层 owner。
- engine、pipeline、prompt 和 sampling 参数：Serving 转换结果的最终 consumer。

## 请求参数怎样流动

```text
声明请求字段 ---------\
flattened client extras +--> 保留来源 -> 冲突/别名校验 -> 按 consumer 分流
raw nested compatibility /                         |-> prompt / control
canonical extra_args ------------------------------|-> sampling params
                                                   |-> model extra_args
```

来源信息只能在冲突检查之后丢弃。Common sampling 字段写入 sampling 参数；prompt 或控制字段进入对应 prompt/dispatcher；模型专属字段进入 `extra_args`。未知 root 字段按公开合同忽略或拒绝，不能因为与内部状态同名而被当成已支持字段。

## 调查顺序

1. 从用户实际入口确认请求字段和默认值。
2. 沿解析后的请求对象确认字段没有丢失或改义。
3. 用 server log 或真实请求证明命中了预期 engine/pipeline。
4. 只有字段已经正确到达模型层后，才把问题下钻到 component 或 model。

## 不在这里决定的事情

Serving 层不应该偷偷修正模型算法、制造静默 fallback，或用入口默认值掩盖下游配置错误。

源码目录会随版本演进，具体 owner path 在改代码前必须以目标仓库当前版本为准。

## 怎样验证

1. 为 flattened、nested、alias 和 canonical container 建立来源矩阵。
2. 重复的已消费字段必须产生可观察的 4xx；不重叠字段必须保留。
3. 每条生产 dispatcher 至少用一个非默认值断言最终 consumer。
4. 增加一个内部同名字段反例，防止内部 schema 扩张公开 API。
