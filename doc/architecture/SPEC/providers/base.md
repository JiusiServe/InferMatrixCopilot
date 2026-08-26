# providers/base.py —— 规范

<!-- verified-against: 2026-08-26 -->

`LOC ~161 · provider 层契约 + 子进程环境白名单 · refactor-status: ok`

## 职责
每个 provider 都要实现的那组契约，以及决定"厂商 CLI 子进程继承什么环境"的安全原语。

## 功能
定义两种 provider kind（`api` —— 无状态 completions，工具循环归**我们的**
`agent_loop`；`harness` —— 自带工具循环的厂商 agent，所以接缝是**一整个 step**）、
请求/用量数据类、带共享二进制解析的 `HarnessTransport` 基类，以及 `sanitized_env()`。

## 公开契约
<!-- default_model: 见 registry 规范的同名不变量 —— 声明在 ProviderSpec 上，由
     Settings.tier_target 解析，transport 只做防御性兜底。 -->
`ProviderSpec`、`AgentSessionRequest`、`SessionUsage`、`HarnessTransport`
（`cli_path`、`require_cli`、`auth_gap`、`run_session`、`complete`）、
`sanitized_env()`、`flatten_messages()`。

## 不变量（**C1**、**C4**、**E2**）
- **环境是白名单，不是黑名单**（`_ENV_KEEP` + `LC_`/`XDG_` 前缀）。厂商 CLI 必须保住
  自己的订阅认证（HOME 状态），但**绝不能继承我们的模型端点**：在这类机器上，被继承的
  `ANTHROPIC_BASE_URL` 指向一个网关，会**悄悄把厂商流量改道**。API key、gh token 和
  `CLAUDECODE` 这类宿主标记，出于同样理由一并丢弃。
- **绝不编造成本。** harness 报用量的方式参差不齐；缺失的数字保持 `0`，`cost_usd`
  保持 `None`，于是 metrics 记来源为 `"subscription"`，而不是发明一个 USD 数值。
- **接缝是一整个 step。** `run_session` 收到的是 `run_agent` **本来会收到的同一个
  prompt 包**（契约 `system` + 渲染后的 dispatch context），所以 harness 跑的是同一场
  评审，而不是另一场。
- `flatten_messages` **只用于无工具**对话 —— 由调用方保证。把带工具的对话拍平会**静默
  丢掉 tool result**。
- `auth_gap()` 返回 `None` 表示"未知或没问题"，**绝不表示"已验证良好"**：没有廉价检查
  手段的 transport，应当让 run **大声失败**，而不是断言一个它并没有测过的就绪状态。

## 边界 —— 不属于这里
不含厂商专属的调用方式（归各 transport）；不含注册表；不为 `api` 解析凭据
（那是 `Settings`）。

## 依赖（允许）
stdlib + `..scopes.ToolScope`。它是一个叶子契约模块。

## 扩展点
新的能力标志加进 `ProviderSpec.capabilities`；新的会话上限加进 `AgentSessionRequest`。

## 测试
`test_providers.py`（环境白名单、spec 形状）。

## 重构备注
`sanitized_env()` 和 `push.guard_push`、`scopes` 一样是安全原语 —— 保持它纯粹、无依赖。
**放宽 `_ENV_KEEP` 是一个安全决策，不是便利性决策。**
