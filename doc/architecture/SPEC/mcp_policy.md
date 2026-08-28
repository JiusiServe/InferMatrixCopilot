# mcp_policy.py —— 规范

<!-- verified-against: 2026-08-28 -->

`LOC ~254 · 安全原语（MCP 结构性门） · refactor-status: ok`

## 职责
从原始 MCP 输入**重新推导**出一个*安全的* `TaskSpec`，拒绝 MCP 面不被允许做的任何事
—— 这就是"宿主无法扩大服务端权限"的**结构性**保证。

## 公开契约
`enforce_mcp_policy(raw) -> TaskSpec`（拒绝时抛错）；
`enforce_strict_review_policy(raw) -> TaskSpec`（Strict 兼容路径：限
`pr_review`、强制 `mode="eco"`）；
`authorize_repo_path(repo, raw_path, settings) -> str`（对调用方提供的
checkout 路径做**身份 + 圈禁**双重校验，返回 canonical 路径）。

## 不变量（**C2**、**C3**、**A2**）
- **它跑两次，这是设计如此。** 一次在**边界**（server，工具被调用时），一次在
  **子进程**（**权威**，就在它读完 `request.json` 之后）。子进程这次复检之所以存在，
  是因为这条保证**不能依赖 `request.json` 未被篡改**：同用户的宿主进程完全可以在预约
  与执行之间把它改写。
- `kind` 必须 ∈ `READ_ONLY_KINDS`；`post` 被**硬置为 `False`**；`repo` 必须在 allowlist
  内；`pr`/`issue` 必须为正；未知 params 被**剥除**而不是透传。
- **Strict 路径上 `post` 是被拒绝，不是被恢复。** 这条路径曾经"共享门里
  强制 `post=False`、事后把调用方原值放回去"，使 Strict 成为唯一能发布的
  MCP 面。显式 `post=True` 现在直接抛 `PolicyError` —— 移除这个恢复不是
  制造异常，而是消灭一个异常（`mcp_server` 侧的 `ALLOW_POST="0"` 环境闸
  与此呼应，双闸同向）。
- **`expected_head_sha` 只收全长 SHA**：经 `task_spec.FULL_SHA_RE`
  （import，绝不重述正则）校验后随 `TaskSpec` 冻结；短 SHA / 非十六进制
  被拒绝，空串 = 不钉快照。
- **`authorize_repo_path` 双重校验、fail-closed**：(1) **身份** ——
  checkout 的 `origin` remote 必须解析为该 alias 配置的 GitHub 全名
  （经 `intent` 的 remote/identity helper）；(2) **圈禁** —— canonical
  路径必须落在 `settings.allowed_repo_roots` 之下（默认 = 只有已配置的
  checkout 本身，最小权限）。身份无法验证 = 拒绝，绝不假定。它是
  `TaskSpec.repo_path` 的一等入口 —— **不要**把它塞进 `_ALLOWED_PARAMS`。
- **允许集是 import 进来的，绝不重述。** 它直接引用 `task_spec.READ_ONLY_KINDS`，
  因此策略永远不会与任务模型漂移 —— 新增一个具备写能力的 kind，**无法**静默地把 MCP
  面放宽。
- MCP 宿主是**非交互**的：这里没有 `[y/N]`，所以本文件里任何逻辑都不得退化成"问用户"。

## 边界 —— 不属于这里
不执行 run；不调模型；不访问知识。

## 依赖（允许）
`..task_spec` + stdlib；外加 `authorize_repo_path` 内部**函数级**引入的
`.intent`（remote→GitHub 身份解析）—— 与 `config.md` 记录函数级 import 的
方式一致的刻意例外：身份判定必须与 intent 的 URL 路由用同一套解析，
否则两处各养一份就会漂移。模块导入期仍然只依赖 task_spec + stdlib。

## 测试
`test_mcp.py`（篡改防御、只读工具集、`expected_head_sha` 贯穿与短 SHA 拒绝、
Strict 显式 post 被拒）；`test_contract.py`（repo_path 身份不符 / 圈外 /
身份不可验证均拒绝；冻结 repo_path 直达解析与执行、压过环境路径）。

## 重构备注
和 `push.guard_push`、`scopes` 一样，这是一个纯权限原语 —— 保持它无依赖。任何新的
"MCP 可达能力"都必须表达为对 `READ_ONLY_KINDS` 的修改，**而不是这里的一个特例**。
