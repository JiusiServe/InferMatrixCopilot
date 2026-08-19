# providers/claude_code.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~205 · harness transport（Claude 订阅） · refactor-status: ok`

## 职责
在订阅认证下，通过 `claude` CLI 跑完**一整个** agent step。

## 功能
headless `claude -p`，用 `--max-turns` 承载我们的迭代预算，**按名字禁用**内置工具，
通过生成的 MCP 配置接入 scoped 工具桥，并从 JSON 结果里解析回 `modelUsage`/成本。

## 公开契约
`ClaudeCodeTransport`（`run_session`、`complete`）、`spec = PROVIDERS["claude-code"]`。

## 不变量（**C1**、**C2**、**E2**）
- **内置工具是被禁用的，不只是"没用到"**（`_BUILTIN_DENY`）。这就是能力标志
  `builtin_tools_off` 所宣称的预防型控制；一旦这份 deny 列表与 CLI 的工具名对不上，
  控制就会**悄悄变弱**，所以它被写死在一个常量里。
- 桥 MCP server 是**唯一**被提供的工具面（`_BRIDGE_SERVER = "infermatrix-tools"`），
  因此每次调用仍然经过 `tools.dispatch`。
- `--max-turns` 把我们的迭代预算映射到厂商原生的上限 —— 预算由 **harness 强制**，
  而不只是在 prompt 里请求。
- 用量按模型上报（`modelUsage`），且**只有 CLI 真的报了成本时才记录**
  （见 `base.md`：绝不编造）。
- 桥的活动按行偏移量从 `bridge_trace.jsonl` 读取，于是第二个进程永远不会与父进程的
  `run_trace.jsonl` 交错。

## 边界 —— 不属于这里
不决定注册表归属；不构造 scope（那归 step）；不处理凭据 —— 订阅认证住在 CLI 自己的
HOME 状态里，**本代码库从不接触它**。

## 依赖（允许）
stdlib + `.base` + `..agent_loop.AgentOutcome` + `..llm` 的类型。

## 测试
`test_provider_claude_code.py`。

## 重构备注
三个 transport（`claude_code`、`codex`、`cursor`）形状相似，但**恰恰在治理不同的地方
不同** —— 要顶住把它们合并成一个参数化类的冲动：**那些差异本身就是安全姿态**。
