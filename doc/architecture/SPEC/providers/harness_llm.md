# providers/harness_llm.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~66 · 套在 harness 之上的 LLM 形状适配器（仅限无工具） · refactor-status: ok`

## 职责
让既有的 `llm.LLM` 调用点在 harness 后端下继续工作 —— **仅限无工具调用**。

## 功能
把 `HarnessTransport` 包成 `LLM` 的形状，于是那些持有 `LLM` 的调用方
（意图分类、ensemble reducer/merge、输出修复、chat）在 harness 后端下变成一次性的
CLI 调用。

## 公开契约
`HarnessLLM`（`available`、`for_target`、`for_member`、`create`）。

## 不变量（**C1**、**B1**）
- **任何带工具的调用都会抛错。** agent step 必须走 `run_session` —— 工具循环归 harness
  —— 而这里的一声大响，正是防止在厂商循环之外**悄悄再跑一个不受治理的第二工具循环**的
  守卫。**这就是本模块之所以长成这个形状的唯一理由。**
- 调用点不变：`create()` 保持签名，所以没有任何调用方需要知道当前是哪个后端。
- `for_member` 是 MoA 的接缝（混合成员在 api 后端的 run 内部骑上某个 harness）。

## 边界 —— 不属于这里
不做 agent step 委托（那是 `run_session`）；不做工具桥接。

## 依赖（允许）
`.base` + `..llm` 的类型。

## 测试
`test_providers.py`。

## 重构备注
**要顶住"为了方便加一条带工具路径"的冲动** —— 那会把这个类存在的意义（防止不受治理的
第二循环）原样请回来。
