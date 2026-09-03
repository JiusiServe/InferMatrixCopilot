---
title: "Omni 输出类型合同"
created: 2026-09-04
updated: 2026-09-04
type: rule
tags: [vllm-omni, components, model-executor]
sources: ["PR #5146", "PR #6152", vllm_omni/outputs/]
confidence: high
---

# Omni 输出类型合同

`EXEC-7a`–`EXEC-7b`：Omni 输出必须是扁平的 `RequestOutput` 子类，并保持其字段与复制合同。触发条件与其余审查组见 [model-executor 共享规则](rules.md) 的 Direct 代码快速入口。

## EXEC-7a — Omni 输出必须是扁平的 RequestOutput 子类

- 触发：修改 `OmniRequestOutput`、stage output wrapping、`omni.generate()` 返回对象或其 serving/offline 消费者。
- 强制：`OmniRequestOutput` 必须继承 vLLM `RequestOutput` 并将继承字段作为 dataclass 字段直接声明；stage 原始输出必须通过 `from_stage_output()` 显式复制 `prompt`、`prompt_token_ids`、`outputs`、`finished` 等生成内容，源对象为 `OmniRequestOutput` 时再复制 diffusion 内容；消费者直接读取扁平字段，列表归一化只在真实列表边界完成。
- 禁止：重新引入 `request_output` 嵌套字段、动态 pass-through property、修改 dataclass 生成的 `__init__` 或递归 `unwrap` 兼容层；不得在 serving、example 或工具代码中恢复 `output.request_output` 访问。
- 验收：用真实 `RequestOutput` 和 `OmniRequestOutput` 分别验证 factory 复制的 prompt、token、outputs、finished 及 images/trajectory 内容；覆盖文本、音频、图像和 pipeline stage 的直接字段消费，并确认未完成 stage 的 `finished` 不被包装过程改写。^[PR #5146]

## EXEC-7b — OmniRequestOutput 必须保持 RequestOutput 字段与复制合同

- 触发：修改 `OmniRequestOutput`、升级 vLLM `RequestOutput`，或调整 `from_stage_output()` 的输出复制逻辑时。
- 强制：对照真实 `RequestOutput.__init__` 设置的全部公开属性，在 `OmniRequestOutput` 中以匹配的类型和默认值声明字段，并同步加入 `_REQUEST_OUTPUT_CONTENT_ATTRS`，确保 `from_stage_output()` 复制非空值。
- 禁止：只声明新字段而遗漏复制列表，或用手写的静态字段清单代替真实 `RequestOutput` 属性 parity 检查，导致 serving 所需的 connector metadata 或 cache accounting 静默丢失。
- 验收：用真实 `RequestOutput` 与 `OmniRequestOutput` 做属性 parity 测试；覆盖新字段默认值为 `None`，以及 `ec_transfer_params`、`num_cache_creation_tokens` 等非空值经 `from_stage_output()` 后保持不变。 ^[PR #6152]

相关执行流见 [model-executor architecture](architecture.md)；跨 stage 合同见 [bridge/batch 规则](rules-bridge-batch.md)。
