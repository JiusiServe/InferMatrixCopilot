---
title: "Nemotron VoiceChat 规则"
created: 2026-09-04
updated: 2026-09-05
type: rule
tags: [vllm-omni, models, serving]
sources: ["PR #6089", vllm_omni/deploy/nemotron_labs_voicechat_duplex.yaml, vllm_omni/experimental/fullduplex/nemotron_voicechat/, vllm_omni/experimental/fullduplex/openai/, vllm_omni/core/sched/omni_ar_scheduler.py, vllm_omni/distributed/omni_connectors/transfer_adapter/chunk_transfer_adapter.py, vllm_omni/model_executor/models/nemotron_voicechat/, vllm_omni/model_executor/stage_input_processors/nemotron_voicechat.py, tests/e2e/features/fullduplex/nemotron_voicechat/, tests/e2e/online_serving/test_nemotron_voicechat_duplex.py, "PR #6831"]
confidence: high
---

# Nemotron VoiceChat 规则

只有 `NVC-数字字母` 是本页可审计规则 ID。

## NVC-1a — 原生 duplex 是 frame-locked、可恢复的三 stage 数据面

- 触发：修改 duplex deploy、native runtime extension、Stage-0 append，或 Thinker→Talker→Code2Wav handoff。
- 强制：只接受每 80 ms 一帧的 1280-sample/16 kHz PCM 输入；Stage 0 跨 wake 保留可恢复 request，text/function side channel 只消费 scheduler 在本次 wake 冻结的 `new_token_ids`。Talker 的累计 code history 在送入有状态 Code2Wav 前只传未见 suffix；native `codec_streaming` 可在当前累计 timeline 耗尽时结束一个 segment，offline async-stream 则必须同时等 `upstream_finished`，包括零进度 wake。共享的下游 receiver requeue/cleanup 遵循 [SCHED-5g](../../components/scheduler/rules.md#sched-5g-resumable-async-chunk-终态清理必须以-live-queue-所有权为准)。
- 禁止：把 scheduler segment finish 当作 codec stream lifetime finish；重放累计 code prefix 到 causal codec cache；从 `supports_core_resumable_request` 推出公开 reusable KV lease（该 adapter 明确 `supports_core_kv_lease=false`）。
- 验收：固定 PCM contract、append/runtime contract、scheduler resume 和 data-plane tests 均须通过；offline async-stream completion 也须保持既有终端语义。^[PR #6089]

## NVC-1b — native 工具调用由客户端执行，失败投递必须可重试

- 触发：修改 `AVAILABLE_TOOLS`/`TOOLCALL`/`TOOL_RESPONSE` prompt、Realtime `function_call_output` 或 runtime update。
- 强制：服务器只验证、排队并 frame-locked reinject 客户端拥有的 function result，绝不执行任意工具；允许多个到达重叠的 result 形成有序 batch。仅在 runtime update 成功且已发出 `conversation.item.created` 后记录 call output，以便投递失败后同一 `call_id` 可重试。
- 禁止：第二个 tool result 抛出 stage-fatal 异常；在 delivery 前写 duplicate-output ledger；把 client tool result 解释为 server-side execution authorization。
- 验收：覆盖多个 response batch、duplicate/invalid output、delivery failure 后 retry 与 realtime event ordering。^[PR #6089]

## NVC-1c — codec suffix 状态必须随 request lifetime 回收

- 触发：修改 `talker2code2wav_async_chunk` 的 cumulative-history slicing、causal codec cache，或 native session abort。
- 强制：按 external request ID 记录已见 frame 数和有状态 decoder cache，只把累计 code history 的未见 suffix 送入 decoder；abort/terminal cleanup 必须同时清除 processor payload、chunk watermark 和 codec state，使复用同一 external ID 的新 request 从首帧开始。共享 sender-generation fence 遵循 [DIST-1h](../../components/distributed/rules.md#dist-1h-abort-不能让旧-sender-generation-复活)。
- 禁止：每次 wake 重放累计 prefix；abort 后继承旧 `frames_seen`/cache；把普通 scheduler segment finish 当成 native codec lifetime finish。
- 验收：覆盖累计输入只解码 suffix、segment 边界保留 cache、abort 清空后同 ID 首帧不混入旧 codes，以及 pending/in-flight sender race 的共享回归。^[PR #6089]

## NVC-1d — full-model 音频证据和部署声明必须限界

- 触发：修改 full-model E2E gate、Buildkite selection、duplex profile 或 stall-diagnostic timeout ordering。
- 强制：full-model probe 除 response/event 完成外，至少断言 PCM RMS floor、最小 audio packet 数和与 input frame 数相关的 duration/bytes；offline streaming 要比较其原有完整 audio contract。profile 的 `max_num_seqs: 1` 只证明默认 admission 配置。stall diagnostic 用 test-local server 240 秒 deadline 与 client 300 秒 wait，使 stage diagnostics 先于 client expiry；healthy run 不应触达任一 deadline。
- 禁止：用非空 bytes、约 1 LSB 的 RMS 或文本成功证明音频可用；把作者在 H200 实测、generic nightly selector 或 YAML 存在写成 Buildkite pass、wall-clock realtime、确定性 barge-in 或跨硬件保证。不得把 240 秒写成生产模型设置、把 `FINISHED_ERROR` 称作 client error delivery，或声称 #6816 已修复。
- 验收：PR 作者报告 targeted H200 suite 306 passed，reviewer 后续报告 399 CPU tests、offline WAV byte-identical 和 native duplex non-silent audio；这些是提交时证据，当前 KB validation 不能复现真实 checkpoint/H200 E2E。Buildkite 改动只把既有 AMD-ready 步骤的超时从 20 分钟增至 45 分钟，不新增该模型专属 pipeline。^[PR #6089]
- stall diagnostic 的验收固定 server 240/client 300，复现 stall 时 server 先记录 full request ID 并标记 `FINISHED_ERROR`，之后 bare client `TimeoutError` 才到期；同时正常 run 仍有 audio。reviewer 已复现该 ordering，仍未证明 client error event。^[PR #6831]
