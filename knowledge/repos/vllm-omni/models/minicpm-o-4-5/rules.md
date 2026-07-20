---
title: "MiniCPM-o 4.5 规则"
created: 2026-07-20
updated: 2026-07-20
type: rule
tags: [vllm-omni, models, model-executor]
sources: ["PR #3642"]
confidence: high
---

# MiniCPM-o 4.5 规则

只有 `MCPMO-数字字母` 是可审计规则 ID。

## MCPMO-1a — trust_remote_code 服从用户选择

- 触发：API/CLI server 为 MiniCPM-o 加载 tokenizer、processor、config 或模型代码。
- 强制：只使用 CLI/配置解析后的 `trust_remote_code` 值，并沿所有入口传递。
- 禁止：模型特例无条件设置 `True`，绕过用户的安全选择。
- 验收：false 路径不执行 remote code，true 路径按显式授权加载；offline/online 语义一致。 ^[PR #3642]

## MCPMO-1b — TTS 依赖显式声明，初始化失败不得伪装为空音频

- 触发：可选 TTS extra、音频 backend 或模型初始化异常。
- 强制：缺包使用明确 extra/import 错误；只有确认为 ImportError 的可选能力才可按合同
  降级，其他初始化失败立即向上抛出。
- 禁止：catch-all 后返回空 waveform，让请求看似成功。
- 验收：缺 extra、坏配置和 backend 初始化失败分别得到可诊断错误；正常路径返回非空
  且格式正确的音频。 ^[PR #3642]

## MCPMO-2a — registry 使用 4.5 config/version predicate

- 触发：pipeline auto-detection 看到通用 `MiniCPMO` architecture。
- 强制：结合 4.5 专有 architecture/config 字段判定；旧 1.0/2.6 不得落入 4.5 pipeline。
- 禁止：仅用 architecture 集合相交。
- 验收：4.5、旧版和无版本字段 fixture 分别命中 4.5、旧 pipeline 或明确失败。 ^[PR #3642]

## MCPMO-3a — TTS stage 的 batch 能力与 runtime_info 消费一致

- 触发：talker/TTS stage 的 `max_num_seqs`、batching 或 runtime bridge。
- 强制：若实现只安全消费一条 runtime info，将上限设为 1；开放 batch 前逐请求处理并
  证明输出不串线。
- 禁止：读取 `runtime_info[0]` 后把请求 0 的音频广播到全批。
- 验收：两个不同文本/voice 的同批测试分别产生对应音频；未支持前配置拒绝 batch>1。 ^[PR #3642]

## MCPMO-3b — wrapper 接收 bridge 并显式包装 OmniOutput

- 触发：LLM/thinker → TTS stage handoff 或 TTS class 返回 waveform。
- 强制：stage wrapper 读取 runner 实际写入的 bridge 字段，模型输出包装到明确的
  `OmniOutput`/multimodal key。
- 禁止：直接 TTS class 不读 runtime bridge；返回 tuple 让 runner 猜它是 hidden state。
- 验收：真实 wrapper handoff 测试断言字段名、逐请求 shape、最终公开 payload。 ^[PR #3642]

共享 bridge/batch 规则见 [Model Executor rules](../../components/model-executor/rules.md)；
公开入口完整性见 [model adaptation guardrails](../../review/guides/model-adaptation-guardrails.md)。
