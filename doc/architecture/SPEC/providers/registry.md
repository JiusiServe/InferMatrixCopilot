# providers/registry.py —— 规范

<!-- verified-against: 2026-08-26 -->

`LOC ~107 · 后端解析（唯一那张表） · refactor-status: ok`

## 职责
"够到一个模型"的所有方式的**唯一一张表**，以及从配置到 transport 的唯一解析路径。

## 功能
声明 `PROVIDERS`（五条 `ProviderSpec`：`api`、`cursor`、`claude-code`、`codex`、
`deepseek`），从 `Settings.strict_backend` 解析出被选中的那个，并为 harness 类型返回
一个 `HarnessTransport`。已声明但尚未发布的后端住在 `_UNSHIPPED` 里，抛出指向里程碑的
错误，而不是返回一个根本跑不起来的 transport。

## 公开契约
`PROVIDERS`、`resolve_provider(settings)`、`transport_for(settings)`、
`transport_for_id(settings, provider_id)`。

## 不变量（**C2**、**B1**）
- **模型缺省值是注册表数据，不是 transport 里的字面量。**
  `ProviderSpec.default_model` 声明某后端在 `STRICT_BACKEND_MODEL` 缺省时服务的模型（订阅制 CLI 为空 —— 它们自己挑）。
  它由 `Settings.tier_target` 解析，于是**请求的模型**与**实际服务的模型**在 target、`DSH_MODEL`、
  构造参数和 trace 里是同一个字符串；放进 transport 会让 target 继续报 `""`，而那正是
  不变量 7 要防的贴错标签。
- **唯一一条解析路径。** 原有的裸 API 路径就是这张表里的 provider `api` —— 不是一条
  平行分支。用 `api` 时，行为与注册表出现之前**逐字节一致**（平价棘轮）。
- **未知 id 绝不静默解析。** `resolve_provider` 抛错并列出合法集合；`Settings` 也在
  前面先拒一次。两层，因为 `.env` 里的一个拼写错误**不该**启动一次注定失败的 run。
- **`api` 没有 transport。** `transport_for_id` 对它抛错是**设计如此**：API 路径的解析
  仍然归 `Settings.tier_target`/`llm.LLM`。
- **未发布 ≠ 坏掉。** `_UNSHIPPED` 里的 id 会抛出点名其里程碑的 `NotImplementedError`，
  于是 `strict_readiness`/doctor 报"尚未发布"，而不是跑到一半失败。
- `transport_for_id` 解析的是**显式** id，与本次 run 的 `STRICT_BACKEND` 无关 ——
  这正是 MoA harness 成员在 api 后端的 run 内部骑上某个 harness 所用的接缝。

## 边界 —— 不属于这里
不含 transport 实现（各自归 `providers/<id>.py`）；不处理凭据；不做模型选择
（那是 `Settings.tier_target`）。

## 依赖（允许）
仅 `.base`。transport 模块在 `transport_for_id` 内部**惰性 import**，这样装某个后端的
SDK 永远不会成为使用另一个后端的前提。

## 扩展点
加一条 `ProviderSpec` + 一个 `HarnessTransport` 子类 + `transport_for_id` 里的一个分支。
transport 还没就绪时，先登记进 `_UNSHIPPED`。

## 测试
`test_providers.py`；逐后端的
`test_provider_{cursor,claude_code,codex,deepseek}.py`。

## 重构备注
`transport_for_id` 的 if 链是唯一会随后端数量增长的地方；用 id → import 路径的 dict
能消掉分支，但会掩盖惰性 import 的意图。**在它超过约 8 条之前，保持链式写法。**
