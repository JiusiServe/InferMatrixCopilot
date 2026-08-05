---
title: "Distributed 传输规则"
created: 2026-08-05
updated: 2026-08-05
type: rule
tags: [vllm-omni, components, distributed]
sources: [vllm_omni/distributed/omni_connectors/adapter.py, vllm_omni/distributed/omni_connectors/kv_transfer_manager.py, vllm_omni/distributed/omni_connectors/transfer_adapter/chunk_transfer_adapter.py, tests/distributed/omni_connectors/test_kv_recv_tp_consensus.py, tests/distributed/omni_connectors/test_chunk_transfer_adapter.py]
confidence: high
---

# Distributed 传输规则

只有 `DIST-数字字母` 是本页可审计规则 ID。connector backend 的选择和端口分配见
[Distributed architecture](architecture.md) 与 [connector pitfalls](connector-pitfalls.md)。

## DIST-1a — TP KV receive 必须做全 rank 一致的成功/放弃决定

- 触发：纯 TP stage 接收 KV、CFG companion 参与 KV transfer，或 connector receive
  只在部分 rank 得到 state。
- 强制：只在 TP process group 内交换 receive state；任一 rank 发现 metadata、shape 或
  payload 不一致时，所有 rank 都走同一个 no-KV fallback，不能让部分 rank 继续 collective。
- 禁止：用本地 `if` 丢掉 KV 后仍让其他 rank进入 receive；使用 global world group 代替
  stage 的 TP group；把 companion 当成普通 stage-0-final request 静默跳过。
- 验收：模拟单 rank divergence，断言所有 TP rank 都放弃本次 KV 并保持后续 collective
  可继续；覆盖普通和 CFG companion 角色。

## DIST-1b — chunk transfer 要区分 upstream exhaustion 与本 stage 完成

- 触发：async-chunk/full-payload connector 传递空 segment、最后一个 chunk 或
  `WAITING_FOR_CHUNK`/active-window 状态。
- 强制：保留空 segment 的边界语义，区分 upstream 已耗尽和当前 stage 已生成完成；收到
  后续 chunk 时刷新 prefill/request state，并让 active-window admission 继续推进。
- 禁止：把空 segment 当作完成信号；用本 stage 的 generation completion 终止上游；在
  connector 没有新数据时无限占用 active window 或静默丢掉 terminal update。
- 验收：覆盖非空→空→非空、upstream exhaustion、stage completion、重复 terminal
  update 和窗口恢复；首批测试看 `test_chunk_transfer_adapter.py`。
