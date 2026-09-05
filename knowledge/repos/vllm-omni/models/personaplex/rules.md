---
title: "PersonaPlex 规则"
created: 2026-09-02
updated: 2026-09-04
type: rule
tags: [vllm-omni, models, model-executor]
sources: ["PR #4771", "PR #6318", vllm_omni/experimental/fullduplex/personaplex/DESIGN.md, vllm_omni/experimental/fullduplex/personaplex/serving_adapter.py, vllm_omni/model_executor/stage_input_processors/personaplex.py, tests/e2e/features/fullduplex/, tests/entrypoints/openai_api/test_duplex_handler.py]
confidence: high
---

# PersonaPlex 规则

## Direct 代码快速入口

| PR 描述信号 | 规则 |
|---|---|
| frame/de-delay、session codec、persona/voice mutation | `PPLEX-1a`–`PPLEX-1c` |
| standalone lease | `PPLEX-2a` |
| checkpoint config 或 sampling capability | `PPLEX-3a`、`PPLEX-3b` |

只有 `PPLEX-数字字母` 是可审计规则 ID。

## PPLEX-1a — frame 与 de-delay 边界必须跨 chunk 连续

- 触发：PCM append、Mimi encode/decode、talker→code2wav processor 或 chunk flush。
- 强制：输入严格是 24 kHz mono float PCM；每个物理 append unit 是 1920 samples/80 ms，
  reservation 失败回滚相同 bytes 且不推进 frame cursor。acoustic de-delay 使用下一 frame
  构造 cb1..7，所以非 final chunk 必须保留最后 raw code frame 给下一 chunk。
- 禁止：按任意 client packet 直接推进模型；每 chunk 丢弃边界 frame；把空/全零/非有限
  audio 或只含 listen event 视为成功。
- 验收：覆盖 partial-frame final padding、prepare/submit/commit rollback、重复 operation id、
  跨两个 chunk 的 codebook 对齐与 frame/audio 时长计数。^[PR #4771]

## PPLEX-1b — codec 状态和容量以 session 身份隔离

- 触发：并发 session、slot reuse、abort/close、Stage 0/1 codec pool 或 admission 配置。
- 强制：Stage 0 encoder 按完整 `(session_id, incarnation)`、Stage 1 decoder 按稳定 request id
  独占；`duplex_session.max_sessions` 是 admission 与所有 codec pool 的单一容量源。cleanup
  只回收目标身份，replacement session 必须重建 voice/persona、PCM tail、Mimi state 与
  delayed frame。
- 禁止：在 connector extra 复制容量；共享卷积/KV state；timeout 后工作仍在运行却提前
  释放 slot。
- 验收：两 session 交错产生独立非空输出，第三个在上限处拒绝；关闭一条不改变另一条，
  replacement 用不同 persona 且无 state leak；异常、timeout、abort 路径无遗留。^[PR #4771]

## PPLEX-1c — persona 与 voice 在 session 创建后不可变

- 触发：PersonaPlex `session.update` 修改 `instructions` 或 `voice`。
- 强制：runtime adapter 对 changed persona/voice 分别返回 `persona_update_unsupported`/
  `voice_update_unsupported`；相同值可保留。PersonaPlex 还必须拒绝 MiniCPM-o 专属的
  `minicpmo45_native_duplex` client flag，不能让它改变 append path 或绕过 adapter。
- 禁止：ACK 变更却沿用旧 `personaplex_prefill_slots`；让 MiniCPM-o 的 `ref_audio` 检查抢先产生
  错误码；在未原子重建 persona/voice 派生 reservation 前开放更新。
- 验收：覆盖不同长度 persona、changed/unchanged voice 和 MiniCPM-o opt-out flag，断言命中
  PersonaPlex 专属 typed error，且并发 session、容量、reuse 与音频输出不回归。^[PR #6318]

## PPLEX-2a — standalone 单会话 lease 必须覆盖不可取消的线程调用

- 触发：standalone `DuplexServer`（`batch_size=1`）的 `/api/chat` 或
  `/v1/audio/duplex` disconnect、task cancellation 或快速重连；batched server 另由
  slot manager 的 lock/epoch 隔离并发会话。
- 强制：`asyncio` task 取消后，`asyncio.to_thread(session.feed)` 的 engine call 仍可能运行；
  lease 只能在 out-of-band completion event 证明调用结束后释放，否则继续持有/拒绝新连接。
  `open()`/`feed()` 不能与前 session 的 `step()` 在同一 engine 上并发。
- 禁止：把 `cancel(); await task` 返回当作 worker thread 已停止；在 finally 直接清 active
  lease，使新连接 reset 正被旧线程修改的 KV/cache。
- 验收：阻塞 feed 后 disconnect，并在其真实完成前 fast reconnect；新会话必须被拒绝或
  等待，完成后才能 acquire，且没有 CUDA crash 或跨 session state bleed。^[PR #4771]

## PPLEX-3a — empty checkpoint config 必须从 architecture 恢复本地 config

- 触发：HF config auto-detection、registry/pipeline 重命名或 staged arch override。
- 强制：两个 PersonaPlex architecture 都在 `_ARCH_TO_MODEL_TYPE` 映射到 `personaplex`，
  注册本地 `PersonaPlexConfig`；talker config 无 architectures 时补 stage-0 talker arch，
  code2wav arch 由 pipeline stage 显式给出。
- 禁止：假设空 `config.json` 能自动给出 model_type/architecture；要求用户手写 override。
- 验收：空 config fixture 从 talker/code2wav arch 都解析到 personaplex pipeline，两个 stage
  分别装载正确 class；未知 arch 明确失败。^[PR #4771]

## PPLEX-3b — sampling capability 必须如实保持 greedy-only

- 触发：serving/config CLI、runtime sampling params、text head 或 depformer decoding。
- 强制：该 pin 的 text 与 depformer 都走 greedy；unified Stage 0 固定 temperature 0、top-k 1、
  每 segment max_tokens 1。只有真实 sampling consumer 和质量验证到位后才暴露 temperature、
  top-k 或 seed。
- 禁止：保留无法关闭的 `--greedy` 或未被消费的 sampling knobs；把 continuous overlapping
  speech 宣称成 `supports_barge_in=true`。
- 验收：public capability/config 不出现 dead sampling controls，非 greedy 请求明确拒绝或
  归一化；capability 保持 `supports_barge_in=false`。^[PR #4771]
