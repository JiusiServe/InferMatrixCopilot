---
title: "YuE2 synthesis 与完成边界规则"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, models, model-executor]
sources: ["PR #8407"]
confidence: high
---

# YuE2 synthesis 与完成边界规则

## YUE2-SYNTH-1a — side-stream synthesis 的 HOLD、队列和 buffer lifetime 必须闭合

- 触发：修改 `_SynthesisJob`/`_SynthesisQueue`、HOLD budget、request admission 或 preemption history reconciliation。
- 强制：通过模型 opt-in hook 接收每个 request 的 sampling extra args/discard 状态；synthesis queue 串行运行 song job，并限制已提交但未完成的 work units。HOLD 只在 CUDA、预算和上下文 headroom 都允许时发出，HOLD 不进入 codec history；无 HOLD headroom 或预算用尽时允许在 finishing step 等待同一 synthesis queue。取消/错误后停止新提交，并在本 job 已提交 kernel 完成后才释放其 graphs、buffers 和 generator。
- 禁止：宣称 finishing step 永不阻塞；把整个 ODE/VAE pass 一次塞入 launch queue；用另一 song 的 stream-wide 完成代替本 job event；缺失 admission metadata 却把 forwarding stub 当作模型请求已正确建立的证明。
- 验收：覆盖 HOLD/zero-budget、排队取消、active 取消、history rollback 和资源回收；用实际模型 admission 测试与 eager/AR-graph、chunked/unchunked lifecycle case 分别证明路径，graph 声明须断言对应 replay counter。^[PR #8407]

## YUE2-SYNTH-1b — 完成音频必须跨过 scheduler 的终态确认边界

- 触发：修改 YuE2 `_ship_audio`、finished row、`end_len` 或完成 step 的 preemption/replay。
- 强制：保留已完成音频和对应终止 token，直到 scheduler 接受该 end boundary。若完成 step 的输出被丢弃、resumed row 的 accepted count 尚未到 `end_len`，重新交付保留的音频与 end token，复用已完成 synthesis；非丢弃的完整 accepted sequence 才能作为 history reconciliation 边界。
- 禁止：finished row 无条件跳过而连续输出零 token；在重新交付时再次运行 synthesis；把未确认的部分 recompute 当作完整 accepted history；finish/abort 后遗留 job 或 timing state。
- 验收：确定性回归让 scheduler 丢弃交付 step，恢复后仍得到同一音频/end token且只完成一次 synthesis；再覆盖真实 eager/graph preemption、取消与后续请求恢复。^[PR #8407]
