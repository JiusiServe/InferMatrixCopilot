# llm.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~452 · 引擎底座（传输层） · refactor-status: ok`

## 职责
provider 中立的 LLM 客户端封装。它支持 Anthropic Messages 和 OpenAI Chat Completions，
包含各自的 Base URL 覆盖。

## 功能
封装 `messages.create`，暴露可用性，把回复归一化成 `Reply`/`Block`，
并从模型文本里解析 JSON。

## 公开契约
`LLM(settings)`，带 `available`、`create(system, messages, tools?, model?,
max_tokens?, on_text?) -> Reply`；以及 `Reply`、`Block`、`parse_json_reply`。

## 不变量
- 没有 key/端点时 `available` 为 false；调用方必须**降级**（记 `capability_gap`），
  而不是崩溃（**E2**）。
- 不可信内容的围栏是**调用方**的职责，不在这里（**C7** 住在 agent_runtime）。
- **逐档端点。** `eco` 和 `performance` 各自解析自己的模型、base URL 和 key，
  所以便宜档完全可以住在另一个网关上。**便宜模型仍然永远不会扩大权限** ——
  `mode` 与 `tier` 正交（见 `task_spec.md`）。
- **fail-closed 的 served-model 守卫**：如果端点报告服务的模型与请求不符，那是**错误**，
  不是静默替换 —— **一条跑在未申明模型上的评测臂，就是一次作废的测量**。
- 捕获 `cache_read_input_tokens` 供计费/缓存分析；调用方和测试 fake **永不接触 SDK
  类型**，只接触归一化后的 `Reply`/`Block`。
- **harness 后端不走这里**：它们经 `providers/harness_llm.py` 完全绕过 `create()`，
  而那个类在被传入 tools 时会抛错。

## 边界 —— 不属于这里
不含 prompt、不含策略、除传输层外不做重试。**不是放任务/仓库逻辑的地方。**

## 依赖（允许）
`anthropic` SDK；`openai` SDK；`config.py`。

## 扩展点
新 provider/端点 → 藏在本封装的构造函数之后；保持 `Reply`/`Block` 稳定，
这样没有任何调用方需要改。

## 测试
provider 选择与 OpenAI 工具翻译有单元测试；step/agent 测试使用 `ScriptedLLM`。

## 重构备注
**把 `Reply`/`Block` 契约当作接缝守住** —— 调用方绝不能看见 provider 专属类型。
