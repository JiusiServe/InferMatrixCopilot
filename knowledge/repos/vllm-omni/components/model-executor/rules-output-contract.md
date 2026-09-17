---
title: "Omni 输出类型合同"
created: 2026-09-04
updated: 2026-09-17
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

## EXEC-7c — 已知 sample-rate 键必须按最新快照合并，不得当生成内容累积

- 触发：修改 `MultimodalPayload.merged_with`、DELTA/CUMULATIVE 音频输出合并，或 `sr`/`sample_rate`/`audio_sample_rate` 的分区与巩固。
- 强制：这三个键是 metadata 快照，不是 waveform 内容。合并前先从 incoming 捕获快照，再写入 metadata 分区一次；缺失键保留既有值。tensor/scalar 表示切换时必须从 tensors 分区移除同名残留。audio/latent 内容继续按既有策略累积。
- 禁止：把 sample-rate 追加成 list 直到 consolidate；让非终态 DELTA 输出保留增长的标量历史；在两边分区同时留下陈旧值。
- 验收：覆盖整数/标量/向量/metadata tensor、表示切换、缺键保留、self-merge、长 DELTA/CUMULATIVE 流与 abort 刷新；断言快照始终非 list 且 `payload[key] is payload.to_dict()[key]`。^[PR #7448]

## EXEC-7d — 张量累积策略必须按 (modality, key) 解析，codec 键不得套用波形默认

- 触发：修改 `get_accumulation_strategy`、`MultimodalPayload.consolidate_tensors`、`_consolidate_tensor_list`，或 AUDIO 模态下非波形键（如 `codes.audio`/`codes.ref`）的巩固。
- 强制：`consolidate_tensors` 接收 modality，并对每个 key 调用 `get_accumulation_strategy(modality, key)`。流水线通过 `register_key_accumulation_strategy` 注册覆盖；Qwen3-TTS 必须将 `codes.audio`→`CONCAT_DIM0`、`codes.ref`→`REPLACE`。`CONCAT_LAST` 失败仍可 flatten 后拼接；其他策略失败必须带 key 名 raise，不得静默 keep-last。
- 禁止：整 payload 共用单一 modality 默认；把 codec-frame 矩阵当 `CONCAT_LAST` 波形；把非 `audio` 键的 concat 失败吞成 keep-last。
- 验收：合成张量证明 `codes.audio` 沿 dim0 拼满、`codes.ref` 只保留一份，以及错误策略 raise；真实波形键仍走 `CONCAT_LAST`。^[PR #7608]
