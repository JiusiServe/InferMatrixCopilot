# llm.py —— 规范

<!-- verified-against: 2026-10-09 -->

`LOC ~540 · 引擎底座（传输层） · refactor-status: ok`

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
`anthropic` SDK；`openai` SDK；`config.py`、`budgeting.py`。不依赖 improve 领域账本。

## 扩展点
新 provider/端点 → 藏在本封装的构造函数之后；保持 `Reply`/`Block` 稳定，
这样没有任何调用方需要改。

## 测试
provider 选择与 OpenAI 工具翻译有单元测试；step/agent 测试使用 `ScriptedLLM`。

## 重构备注
**把 `Reply`/`Block` 契约当作接缝守住** —— 调用方绝不能看见 provider 专属类型。

## 自进化接入（2026-10-04）

绑定改进预算 governor 时，每次 API 请求先按最坏用量预留预算，再派发并结算；拒绝不会发出模型请求。成功、失败、模型不匹配均采集 trace/1，输入输出以脱敏 blob 引用保存；未绑定 store 或 governor 时保留原调用行为。

实际 dispatch 复用 `budgeting.call_budget`，由调用方通过 `bind_call_budget`
显式安装一个或多个账户，在 `finally` 中完成结算，包括中断退出。
派发前失败释放预留；已派发但费用未知时扣完整预留。缺失、空或无效 token 用量
不能当作零费用；可信用量已获得后，即使回调失败仍按真实费用结算。周账本按
reservation 身份幂等结算，真实超额先记账再 fail-closed，既有 `Reply.usage=None`
未知语义及 provider 传输、served-model 守卫保持不变。

`for_member` 只把成员参数转换为既有 `ResolvedTarget` 再委托 `for_target`，
不建立另一套 client 工厂或预算包装器。不同账户共享真实发送、回复和 usage 事实，
各自仍决定模型定价、额度、持久化与拒绝异常；本层不导入周预算策略。
已归一化 usage 在文本回调前记录，served-model 守卫在账本完成后执行，
因此回调或模型不匹配失败不能释放已支付调用的费用。
