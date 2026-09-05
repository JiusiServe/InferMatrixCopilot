---
title: "Serving session lifecycle 规则"
created: 2026-09-05
updated: 2026-09-05
type: rule
tags: [vllm-omni, components, serving]
sources: ["PR #6537", "PR #6354", vllm_omni/config/stage_config.py, vllm_omni/entrypoints/openai/api_server.py, vllm_omni/experimental/fullduplex/core/adapter.py, vllm_omni/experimental/fullduplex/core/runtime.py, vllm_omni/experimental/fullduplex/mage_vl/adapter.py, vllm_omni/experimental/fullduplex/mage_vl/serving/backend.py, vllm_omni/experimental/fullduplex/mage_vl/serving/server.py, tests/e2e/features/fullduplex/test_mage_vl_adapter.py, tests/e2e/features/fullduplex/test_mage_vl_serving.py, tests/e2e/online_serving/nemotron_voicechat_realtime_duplex.py]
confidence: high
---

# Serving session lifecycle 规则

## SERV-6h — deferred session cognition 必须保持 input responsiveness、response ownership、worker drain 与 cleanup

- 触发：共享 `DuplexAdapter`/`DuplexRuntime` lifecycle、deferred cognition/gate、full-duplex barge-in、
  shared-GPU `asyncio.to_thread` inference、disconnect/explicit close 或 session registry teardown 变化。
- 强制：昂贵的 deferred cognition 必须在 sole input reader 之外运行，完成 watcher 而不是 input
  consumption 才能发起 response；response start/replacement 通过一个 response lock 串行化，新 response
  以 stale epoch 加 cancellation 取代 live response。`response.cancel` 无论有无 in-flight response 都必须
  barge-in 并发出 cancelled acknowledgement。不可取消的 CUDA worker 在 asyncio wrapper cancellation 后仍须
  在 shield 下等待真实退出，且显式处理 `asyncio.CancelledError`，共享 inference lock 在 drain 前不得释放。
  deferred task 必须按 session 追踪；barge-in/disconnect cancel 并 drain，explicit graceful close 才调用
  `flush(session)`，随后 `on_close(session)` 释放 session state。shared lifecycle hook 必须对旧的
  duck-typed adapter 保持 optional/compatible；registry/lifespan close 必须 close runtime 并清空 lease。
- 禁止：在 reader path await gate/model cognition；copy 一份 model-specific serving loop/runtime；把 wrapper
  cancellation 当成 GPU worker 已停止；silent no-op `response.cancel`；遗留 gate task/queue/session map；或把
  Mage-specific flush/response-on-close policy 施加给 generic adapter。
- 验收：two-second synthetic gate 下 `response.cancelled` 在 0.5 seconds 内到达；并发 input/gate completion
  不得创建 duplicate response；cancel/disconnect/close 后无 worker/task、registry lease 或 session-state residue；
  explicit close 可 flush pending gate 再完成 response，disconnect 则 cancel；没有 lifecycle method 的既有
  adapter 行为不变。PR 的 CPU suite 证明 lifecycle contract；报告的 RTX 4090 run 只是 single-run functional
  evidence，不得外推 throughput、latency 或一般 hardware support。^[PR #6537]

## SERV-6i — optional duplex startup warmup 必须闭合 readiness、真实 transport 与 shutdown lifecycle

- 触发：duplex session startup warmup、`warmup_frames` 配置、realtime WebSocket admission，或 API-server
  shutdown 中的 warmup task 管理。
- 强制：`warmup_frames=0` 保持禁用；启用时先确认 `/health`，再用标记过的 self WebSocket 连接穿过实际
  `/v1/realtime` handler 和生产 session/stage path，完成 configured silent frames 后显式发送 session close。
  真实 client 在 warmup event 前等待，最多 120 seconds；无论成功、health timeout、缺 optional client
  dependency、protocol failure 或异常，warmup coroutine 都必须 set event。失败只记录并继续提供服务；
  server shutdown 必须 cancel 未完成的 warmup task。
- 禁止：用直接调用 model/adapter 代替实际 tagged WS path；bare WebSocket disconnect 后留下占用 session
  slot；因 warmup failure 拒绝服务或永久阻塞 real client；或在 shutdown 遗留 background warmup task。
- 验收：覆盖 disabled、health-then-self-WS ordering、warmup tag 绕过 admission gate、explicit close、
  success/failure 均 set event、real-client 120-second escape hatch，以及 shutdown cancellation。^[PR #6354]
