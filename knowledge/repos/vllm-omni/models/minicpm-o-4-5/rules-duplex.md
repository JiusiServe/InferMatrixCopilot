---
title: "MiniCPM-o 4.5 native duplex 规则"
created: 2026-09-04
updated: 2026-09-05
type: rule
tags: [vllm-omni, models, model-executor]
sources: ["PR #6318", "PR #6346", "PR #6404", "PR #6458", "PR #6619", "PR #6630", "PR #6678", "PR #6626", "PR #6767", vllm_omni/deploy/minicpmo_4_5.yaml, vllm_omni/model_executor/models/minicpmo_4_5/minicpmo_4_5_omni_tts.py, vllm_omni/model_executor/stage_input_processors/minicpmo_4_5_omni.py, tests/model_executor/models/minicpmo_4_5/test_talker_batching.py, vllm_omni/deploy/minicpmo_4_5_2gpu.yaml, vllm_omni/deploy/minicpmo_4_5_3gpu.yaml, vllm_omni/deploy/minicpmo_4_5_8x4090.yaml, vllm_omni/experimental/fullduplex/client.py, vllm_omni/experimental/fullduplex/minicpmo45/adapter.py, vllm_omni/experimental/fullduplex/minicpmo45/session.py, vllm_omni/experimental/fullduplex/minicpmo45/stage0.py, vllm_omni/experimental/fullduplex/openai/realtime_input.py, vllm_omni/experimental/fullduplex/openai/runtime_adapter.py, vllm_omni/experimental/fullduplex/openai/runtime_bridge.py, vllm_omni/experimental/fullduplex/openai/serving.py, vllm_omni/experimental/fullduplex/openai/session_runner.py, vllm_omni/experimental/fullduplex/video_stacking.py, tests/config/test_config_factory.py, tests/e2e/features/fullduplex/engine/test_duplex_deploy_config.py, tests/e2e/online_serving/helpers/minicpmo_4_5_duplex.py, tests/e2e/online_serving/test_minicpmo_4_5_duplex_expansion.py, tests/entrypoints/openai_api/test_duplex_handler.py]
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

## MCPMO-4d — auto-response silence continuation 必须有硬性终止与所有权 fence

- 触发：修改 MiniCPM-o native duplex auto-response 的 silence continuation、`force_listen`、LISTEN 事件或 response close。
- 强制：auto-response 以 64 个 one-second continuation unit 为上限，普通 response 保持 8 个单位上限；前 63 个 auto payload 保持既有语义，第 64 个请求 `force_listen`。边界 LISTEN 不得再走 non-terminal auto reschedule，而必须结束当前 response 并保留 resumable Stage-0 request；模型忽略提示时，下一次 continuation 尝试不得 append，而发出 `response.listen` 与恰好一个 `response.done`。fallback 在跨 `send_json` await 前后必须同时验证 epoch 和 active response owner，防止 barge-in 打开的新 response 被旧 response 的终止路径关闭。
- 禁止：让 auto-response 因 `force_listen` 仅为 logit hint 而无限续跑；在已达边界后继续 append；清除 resumable request；或在 await 后未复核 session/response 所有权即结束 response。
- 验收：覆盖 64 次 append、最后一次 `force_listen`、第 65 次无 append 且仅一次 terminal protocol pair、边界 model LISTEN 的 terminal path，以及 LISTEN send 期间 barge-in/new epoch 不被 stale fallback 关闭。单元覆盖证明协议与 race fence；PR 的 H800 lifecycle run 混合了其他改动且有 `audio_clipped` artifact，不作为音频质量或性能证据。^[PR #6630]
- 已知边界：terminalization 保留 data-plane request，而 `active_response_id is None` 时不走 model-turn owner guard；同一 request/turn 的 late SPEAK 仍可能新建第二个 response。该 reviewer nit 在本提交中未修复，不能把“恰好一个 `response.done`”外推成后续迟到事件也被永久抑制；若补齐，需显式拒绝 bound 后的 late SPEAK 并覆盖回归。^[PR #6630]

## MCPMO-4e — shipping profile 必须共服 chat 与 native duplex

- 触发：修改任一 `minicpmo_4_5*.yaml`、duplex session placement 或 Stage 1 Talker 默认/运行时采样参数。
- 强制：所有 shipping profile 设置 `session_mode=duplex`，且 `active_stream_window` 只限制
  first-packet admission，不是 session lifetime cap。default/2gpu/3gpu profile 的 window、
  `duplex_session.max_sessions` 与 Stage 0/1 `max_num_seqs` 均为 4；8×4090 profile 因 24GB
  资源边界保持 window/stage capacity 1，并沿用 default session capacity 1。replica overlay 从 base
  继承这些字段。YAML 保留 chat 的 Stage 1 `min_tokens=50` 与既有 codec 参数，native duplex adapter
  仅在该 session 的 runtime config 覆盖 `min_tokens=0`；AR stage 保留默认 async scheduler。^[PR #6767]
- 禁止：恢复独立 `minicpmo_4_5_duplex.yaml`；在 replica overlay 重复并漂移 session 配置；为 duplex 全局关闭 async scheduling；或把 runtime-only floor 写回 YAML 而改变 chat TTS。
- 验收：展开四份 base profile 及三个 replica overlay，断言全部 duplex-enabled、窗口与 session capacity 正确；同一 server 分别验证 `/v1/realtime?duplex=1` 和 chat，前者 Stage 1 看到 `min_tokens=0`、后者仍看到 `50`。删除旧 overlay 是部署文件名迁移，外部显式引用必须同步更新。PR #6767 的 L20X concurrency=4 观察只证明该精确 profile/workload 的 first-packet admission，不构成通用吞吐、延迟或硬件保证。^[PR #6458] ^[PR #6619] ^[PR #6767]

- admission/expiry E2E probe 必须从实际启动的 deploy YAML 经
  `load_deploy_config(...).duplex_session.max_sessions` 取得 admission limit，不能保留
  硬编码容量或在 test helper 重做 YAML merge/default/validation；这样 base-config overlay
  与未声明 `duplex_session` 时的 server 语义保持一致。CPU 守卫至少覆盖 shipping base 的
  显式容量、未声明字段的 default，及一个从 base 继承容量的 overlay；live probe 再验证在
  该 limit 后收到 capacity error。^[PR #6678]

## MCPMO-4f — omni video frame 必须随其关闭的 audio unit 原子进入 Stage 0

- 触发：修改 MiniCPM-o Realtime duplex 的 camera/video append、Stage 0 streaming prefill、vision embedding，或视频 demo/client 的 audio-frame interleave。
- 强制：client 以累计 appended PCM 的 unit boundary 绑定 frame `k`：首个 unit 在约 `1030 ms`（`first_chunk_ms=1035` 对齐 160-sample hop 后），后续每 `1000 ms`；frame 只能附在**关闭 unit `k`**的 append，不能在早期 append 暂存或跨 append carry。视频短于音频时保持最后一帧，单张 still 同样重复。`stack_frames=2` 是 previous+current 的两张图；整个 append 的 `frame_list` 都属于它关闭的一个 unit，顺序为 `<unit>`、每张各自 `<image>` + 64 vision embeddings + `</image>`、再 audio。vision hidden states 在拼入 token embedding 前转为 token-embedding dtype。
- 拒绝：携 frame 但没有关闭 model unit 的 append 必须显式失败，且不推进 `audio_chunk_idx`；不能只丢帧后继续音频。Realtime wire 每 append 最多两张图，stacked composite 不改变一秒 audio cadence。视频 demo 同时传 `--input-wav` 和 `--input-video` 时，外部 WAV 覆盖视频 soundtrack 且决定 frame timeline/duration。
- 验收：覆盖 frame 0 不早于约 1030 ms、每个 frame `k` 绑定其 closing append、无跨 append carry、short/still hold-last、`[f0]`/`[f0,f1]`/`[f1,f2]` stacked 序列、双图 marker/128 embedding 布局、no-unit rejection 不推进 audio index、dtype 对齐，以及 silent video + external WAV。Daily-Omni pack-mode 测试只覆盖数据包装边界，不能替代 Realtime session 或 Stage 0 验证。^[PR #6404]

## MCPMO-4g — native duplex Stage 1 rollover 只重算 Talker context

- 触发：修改 native-duplex Talker 长上下文、`attention_type=sliding_recompute`、async-chunk
  prompt replacement、codec repetition penalty 或 receive-side request registration。
- 强制：sliding recompute 只由 Stage 1 Talker checkpoint/config 的显式
  `attention_type="sliding_recompute"` 启用；native duplex 本身不能覆盖 checkpoint policy。effective
  context limit 取正的 vLLM `max_model_len` 与 TTS `max_position_embeddings` 的较小值；每个新 condition
  必须声明正整数 `next_stage_generation_tokens=26`，fresh/sliding prompt 加 reserve 都不得越界。
- 强制：rollover 仅保留前一 condition、该段已确认且不含 EOS/非法值的至多 25 个 codec ids、当前
  condition；condition sequence 必须单调连续。replacement 在 scheduler thread 原子清空旧 output/KV
  prompt ownership、重建 block hashes 并回到 admission；model 以相同 sequence 验证/replay frozen
  embeddings，repetition penalty 只继承最近 16 个 codes。turn boundary 不得跨 turn recompute。
- 禁止：让 Stage 0 或非显式 Talker 进入 sliding window；从 placeholder/未确认 token 构造 rollover；
  累积全部 codec history；在 receiver thread 直接改 scheduler token counters；异常后跳过已消费 chunk
  继续运行。任一缺失 metadata、跳号、超长、EOS/非法 codec 或 prompt-length mismatch 必须记录为
  receive failure，并由 scheduler 将仍存活 request 置为 `FINISHED_ERROR`。
- 验收：覆盖 first condition、连续 rollover、same-condition replay、turn reset、limit/reserve 边界、
  confirmed-placeholder 裁剪、EOS/非法/跳号/缺 metadata 拒绝、latest-16 penalty 与 cleanup/ID reuse；
  scheduler 必须只处理当前 live request。目标合入的 CPU/unit tests 证明状态机与 fencing；PR 最终
  real-weight E2E 未全绿，不能据此声称音频质量、长会话稳定性或跨硬件支持。^[PR #6626]
- 已知边界：Stage 0 vision encode 失败虽返回 failed prefill 且不推进 `audio_chunk_idx`，但 `preprocess()` 仍可能 fallback 到原 input ids/embeddings；保留的 scheduler span/KV 或 `num_computed_tokens` 是否推进尚未 abort/rollback 证明。另一个 fast/malformed client 的 pending-frame queue 仍未封顶。两者都是未合入 follow-up，不得写成此 frame-binding 修复已解决。此前 NPUGraph / soft-interrupt 范围已从本 PR 移除。^[PR #6404]
