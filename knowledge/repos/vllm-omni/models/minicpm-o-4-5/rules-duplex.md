---
title: "MiniCPM-o 4.5 native duplex 规则"
created: 2026-09-04
updated: 2026-09-04
type: rule
tags: [vllm-omni, models, model-executor]
sources: ["PR #6318", "PR #6346", "PR #6458", "PR #6619", vllm_omni/deploy/minicpmo_4_5.yaml, vllm_omni/experimental/fullduplex/minicpmo45/adapter.py, vllm_omni/experimental/fullduplex/minicpmo45/session.py, vllm_omni/experimental/fullduplex/openai/runtime_adapter.py, vllm_omni/experimental/fullduplex/openai/serving.py, vllm_omni/experimental/fullduplex/openai/session_runner.py, tests/config/test_config_factory.py, tests/entrypoints/openai_api/test_duplex_handler.py]
confidence: high
---

# MiniCPM-o 4.5 native duplex 规则

## MCPMO-4b — native duplex session update 必须如实拒绝不可重建的上下文

- 触发：运行中更新 MiniCPM-o native duplex 的 `instructions`/native-mode。
- 强制：MiniCPM-o 的 changed `instructions` 由 runtime adapter 返回
  `instructions_update_unsupported`，不能 ACK 成 `session.updated`；serving 层也在 native context
  已锁时拒绝 changed instructions。`native_context_locked` 仅在真实 native append 成功后设置，
  buffered、deferred 或失败 append 不锁。若创建时已给出 `minicpmo45_native_duplex`，后续改变该值
  返回 `native_duplex_mode_update_unsupported`。共享 helper 保持“值改变即错误”的 adapter 边界一致；
  PersonaPlex 的对应 persona/voice 合同见 [PPLEX-1c](../personaplex/rules.md#pplex-1c-persona-与-voice-在-session-创建后不可变)。
- 若以后改为允许任何会影响 `prefill_slots` 或 first-append context-token reservation 的更新，必须先
  重算并验证派生 reservation，再 ACK 并原子提交；资源不足时不得留下部分 mutation。这是现有拒绝
  行为所保留的安全边界，不是本提交新增的可变配置能力。
- 禁止：在 Stage0 已用旧 context 初始化后 ACK 变更；buffer/defer/reject append 提前锁定；用 mode
  flip 绕过锁。
- 验收：覆盖 post-lock changed/unchanged instructions、短 buffer 后 update 再 commit与 mode flip；
  拒绝时不发 runtime `session.update` signal，而 commit 仍可 flush 已缓冲音频。重建
  first-append token/prefill reservation 后允许变更是 PR body
  提到的后续 GPU-validated 工作，非本提交已实现语义。 ^[PR #6318]

## MCPMO-4c — native duplex Talker 必须按 generate_chunk 预算终止

- 触发：修改 MiniCPM-o native duplex Talker 的 `generate_chunk`、codec EOS 或请求级音频状态。
- 强制：每个 native duplex 请求按一次 chunk 的 26 个采样管理状态；adapter 只在 duplex runtime config 将 Talker `min_tokens` 设为 0，保留 chat YAML 的 whole-utterance floor；turn 边界 `min_tokens=0`，中间 chunk `min_tokens=max_tokens=26`，已转发 25 帧后强制下一个采样为 EOS，仅把非 EOS code 交给 Code2Wav。
- 禁止：只依赖 YAML `max_tokens` 维持 turn 边界；改变 chat 的 whole-utterance Talker floor；在中间 chunk 永久屏蔽 EOS；把终止采样再次作为普通 codec frame 输出。
- 验收：覆盖 prefill 边界元数据、step 24/25 的 mask/force EOS、runtime Stage 1 `min_tokens=0`、chat sampling control、simplex 不误触发以及多请求 delta/finished 对齐。^[PR #6346] ^[PR #6619]

## MCPMO-4e — shipping profile 必须共服 chat 与 native duplex

- 触发：修改任一 `minicpmo_4_5*.yaml`、duplex session placement 或 Stage 1 Talker 默认/运行时采样参数。
- 强制：所有 shipping profile 设置 `session_mode=duplex`、`active_stream_window=1`，且 `duplex_session.max_sessions` 与 Stage 0/1 的 `max_num_seqs` 容量一致；replica overlay 从 base 继承这些字段。YAML 保留 chat 的 Stage 1 `min_tokens=50` 与既有 codec 参数，native duplex adapter 仅在该 session 的 runtime config 覆盖 `min_tokens=0`。AR stage 保留默认 async scheduler。
- 禁止：恢复独立 `minicpmo_4_5_duplex.yaml`；在 replica overlay 重复并漂移 session 配置；为 duplex 全局关闭 async scheduling；或把 runtime-only floor 写回 YAML 而改变 chat TTS。
- 验收：展开四份 base profile 及三个 replica overlay，断言全部 duplex-enabled、窗口与 session capacity 正确；同一 server 分别验证 `/v1/realtime?duplex=1` 和 chat，前者 Stage 1 看到 `min_tokens=0`、后者仍看到 `50`。删除旧 overlay 是部署文件名迁移，外部显式引用必须同步更新。^[PR #6458] ^[PR #6619]
