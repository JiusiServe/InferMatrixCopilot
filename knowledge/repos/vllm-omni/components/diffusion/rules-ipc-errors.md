---
title: "Diffusion IPC 与客户端错误规则"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #7812", "PR #8474"]
confidence: high
---

# Diffusion IPC 与客户端错误规则

## DIFF-IPC-1a — 无 peer 的 PUSH 发送不得阻塞 orchestrator，abort 必须保持 no-op 语义

- 触发：修改 StageDiffusionClient 的 shutdown/abort/add-request/collective-RPC 发送与死副本清理。
- 强制：shutdown 与 abort 使用 nonblocking send；无 peer/已 engine_dead 的 abort 返回，
  让 poll 路径观察死亡并驱逐副本，不能因 cleanup raise 而杀死整个 orchestrator。
  add-request/RPC 在 NOBLOCK+POLLOUT 重试中检查实际 subprocess liveness，进程死亡时
  raise EngineDeadError；只有成功发送后登记 pending RPC。
- 禁止：只读 monitor 的 `_engine_dead` flag 后继续 blocking send（进程可在两者之间死亡）；
  将 abort no-op 改成 raise；把 live-peer backpressure 说成无等待的成功；无 peer 测试只
  预置 dead flag，或忘了 close socket/context 让 pytest exit 挂住。
- 验收：dead flag 尚 false 但 subprocess 已退出时，shutdown/abort 有界返回且无异常，
  add-request/RPC 明确失败；live peer 保持发送；测试实际 return/error 并完整关闭 ZMQ
  context，避免只断言线程退出而漏掉错误。^[PR #7812]

## DIFF-ERROR-1a — single-GPU 与 non-step fallback 必须保留 pipeline 的 client status

- 触发：修改 UniProcDiffusionExecutor.execute_request、non-step runner fallback 或异常输出。
- 强制：pipeline 异常通过 DiffusionOutput.from_exception 构造，保留 OmniClientError 的
  4xx metadata；普通 RuntimeError 保持无 client status 并由上层作为 server error。
  与 multiprocess direct / stepwise / engine error path 使用同一分类。
- 禁止：只保存 str(exc) 使单 GPU 的 400/422 变成 500；因为请求失败就把 executor 标为
  永久死亡；只检查 error message 而不检查传至 API 的 status。
- 验收：single-GPU direct 的 422、non-step fallback 的 400 与 RuntimeError control，
  断言 status 到达输出/API，executor 仍可接下一请求；CPU/mock 不外推全部模型 GPU
  admission 路径的正确性。^[PR #8474]

共享 teardown 见 [输出生命周期](rules-output-lifecycle.md)；
公共 HTTP 错误与请求合同见 [Serving 规则](../serving/rules.md)。
