---
title: "Distributed 传输规则"
created: 2026-08-05
updated: 2026-09-02
type: rule
tags: [vllm-omni, components, distributed]
sources: ["PR #5744", vllm_omni/distributed/omni_connectors/adapter.py, vllm_omni/distributed/omni_connectors/kv_transfer_manager.py, vllm_omni/distributed/omni_connectors/transfer_adapter/chunk_transfer_adapter.py, vllm_omni/worker/omni_connector_model_runner_mixin.py, tests/distributed/omni_connectors/test_kv_recv_tp_consensus.py, tests/distributed/omni_connectors/test_chunk_transfer_adapter.py, tests/worker/test_omni_connector_mixin.py]
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

## DIST-1c — payload connector 按 edge 所有权创建且不与 KV manager 捆绑

- 触发：修改 AR/DiT 解耦、stage connector role、`custom_process_next_stage_input_func`、
  runner connector 初始化或 KV-only edge。
- 强制：receiver/非 sender 即使无 downstream hook 也创建 payload connector；sender 只在
  `custom_process_next_stage_input_func` 是非空字符串时创建，空值或非字符串都表示
  KV manager 独自拥有该 edge。KV manager 与 payload connector 必须独立初始化和关闭。
- 禁止：不得只因已配 connector/role 就创建 payload transport；不得从“无 outgoing
  hook”推导 receiver 也不需要 connector；不得用 consumer-side hook 反推 sender 所有权。
- 验收：参数化锁定 sender+空/非字符串→不创建、sender+非空字符串→创建、
  receiver/非 sender+无 hook→创建，并覆盖安全 shutdown。Bagel/Hunyuan KV-only 和
  Qwen3-Omni/MiniCPM-o payload 路径各做真实拓扑 smoke。该矩阵不证明 issue #5595 中独立的
  shutdown/orphan 问题已解决。 ^[PR #5744]
