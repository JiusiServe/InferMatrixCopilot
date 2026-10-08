# providers/base.py —— 规范

<!-- verified-against: 2026-10-09 -->

`provider 层契约 + 子进程机制 + 环境白名单 · refactor-status: ok`

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
`sanitized_env()`、`flatten_messages()`、`run_cli()`、`stream_cli()`。

`run_cli` 共用缓冲子进程与超时输出保留，`json_events` 读取容错 JSONL，
`bridge_server` 构造既有 stdio 桥接配置。Transport 仍自行选择命令、环境、
工作目录、认证、隔离和结果校验。`SessionUsage` 的原字段与默认值保持不变；
新增方法统一构造 Reply 和 AgentOutcome。

`stream_cli(cmd, *, cwd, env, deadline, input=None, idle_timeout_s=None,
on_line=None, termination_grace_s=0)` 返回 stdout、stderr、退出码和超时原因
（`idle` / `absolute` / None）。独立读取两个管道，stdin 也由独立线程写入；
阻塞输入和大量 stderr 不能绕过绝对截止时间。非空 stdout 行重置 idle；
非 JSON 行同样算活动。退出前排干管道，保留无换行尾部；超时或回调异常清理
进程树，回调失败不被清理错误掩盖。POSIX 用进程组，Windows 用 taskkill。
ZCode 流式归档和只读 JSON 会话复用它，事件协议仍由各调用方解析。

## 不变量（**C1**、**C4**、**E2**）
- **环境是白名单，不是黑名单**（`_ENV_KEEP` + `LC_`/`XDG_` 前缀）。厂商 CLI 必须保住
  自己的订阅认证（HOME 状态），但**绝不能继承我们的模型端点**：在这类机器上，被继承的
  `ANTHROPIC_BASE_URL` 指向一个网关，会**悄悄把厂商流量改道**。API key、gh token 和
  `CLAUDECODE` 这类宿主标记，出于同样理由一并丢弃。
- **绝不编造成本。** harness 报用量的方式参差不齐；缺失的数字保持 `0`，`cost_usd`
  保持 `None`，于是 metrics 记来源为 `"subscription"`，而不是发明一个 USD 数值。
  旧结果结构中的零计数不构成实际零费用的证明；预算绑定只能用可信原生用量结算。
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
stdlib + `..scopes.ToolScope`；`SessionUsage.reply/outcome` 在结果封装时惰性
引入 `..llm` / `..agent_loop` 的数据类型，不负责预算、模型或权限策略。

## 扩展点
新的能力标志加进 `ProviderSpec.capabilities`；新的会话上限加进 `AgentSessionRequest`。

## 测试
`test_providers.py`（环境白名单、spec 形状）与 `test_provider_process.py`
（双管道、UTF-8 尾部、阻塞 stdin、idle/absolute、回调失败和进程树清理）。

## 重构备注
`sanitized_env()` 和 `push.guard_push`、`scopes` 一样是安全原语 —— 保持它纯粹、无依赖。
**放宽 `_ENV_KEEP` 是一个安全决策，不是便利性决策。**

## 2026-09-28
`complete()` 接受 `effort`（推理强度）：codex 以 `-c model_reasoning_effort="<effort>"` 生效并校验取值；其他 transport 接受并忽略（模型 id 已决定推理预算）。

## 2026-09-30 单次调用花费阈值（不是硬上限）
`complete()` 接受 `max_budget_usd`，类属性 `stops_at_spend`（默认 False）声明 CLI 是否会在本次调用花费达到阈值后**不再发起**
新的 API 请求。越过阈值的那一个请求仍会完成并计费，所以超出量最多一个请求 —— 这是阈值，不是硬上限；
需要硬上限的调用方要预留"阈值 + 单个请求的最坏情况"。不支持的 transport 接受并忽略该参数，调用方必须先检查
`stops_at_spend`（知识服务的 gateway 会拒绝）。不得出现声称能硬性限制单次调用花费的属性。
`max_tokens` 对 CLI transport 不是花费上限。transport 报告的本次花费放在 `Reply.usage["cost_usd"]`（未知时不出现）。
