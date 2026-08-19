# mcp_policy.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~141 · 安全原语（MCP 结构性门） · refactor-status: ok`

## 职责
从原始 MCP 输入**重新推导**出一个*安全的* `TaskSpec`，拒绝 MCP 面不被允许做的任何事
—— 这就是"宿主无法扩大服务端权限"的**结构性**保证。

## 公开契约
`enforce_mcp_policy(raw) -> TaskSpec`（拒绝时抛错）。

## 不变量（**C2**、**C3**、**A2**）
- **它跑两次，这是设计如此。** 一次在**边界**（server，工具被调用时），一次在
  **子进程**（**权威**，就在它读完 `request.json` 之后）。子进程这次复检之所以存在，
  是因为这条保证**不能依赖 `request.json` 未被篡改**：同用户的宿主进程完全可以在预约
  与执行之间把它改写。
- `kind` 必须 ∈ `READ_ONLY_KINDS`；`post` 被**硬置为 `False`**；`repo` 必须在 allowlist
  内；`pr`/`issue` 必须为正；未知 params 被**剥除**而不是透传。
- **允许集是 import 进来的，绝不重述。** 它直接引用 `task_spec.READ_ONLY_KINDS`，
  因此策略永远不会与任务模型漂移 —— 新增一个具备写能力的 kind，**无法**静默地把 MCP
  面放宽。
- MCP 宿主是**非交互**的：这里没有 `[y/N]`，所以本文件里任何逻辑都不得退化成"问用户"。

## 边界 —— 不属于这里
不执行 run；不调模型；不访问知识。

## 依赖（允许）
`..task_spec` + stdlib。一个叶子安全原语。

## 测试
`test_mcp.py`（篡改防御、只读工具集）。

## 重构备注
和 `push.guard_push`、`scopes` 一样，这是一个纯权限原语 —— 保持它无依赖。任何新的
"MCP 可达能力"都必须表达为对 `READ_ONLY_KINDS` 的修改，**而不是这里的一个特例**。
