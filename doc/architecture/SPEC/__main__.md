# __main__.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~12 · 模块入口点 · refactor-status: trivial`

## 职责
`python -m infermatrix_copilot` —— MCP server 用来拉起一次已预约 run 的入口。

## 不变量（**C3**、**E1**）
- server 以 `sys.executable -m infermatrix_copilot --execute-reserved <run_id>`
  拉起子进程，即**用当前解释器**，因此子进程继承 server 被安装进去的那套环境。
- 子进程必须是**独立进程**而不是线程：它的 stdout 落到该 run 的 `console.log`
  （server 自己的 stdout 只走 JSON-RPC），并且进程级全局 tracer / `last_run_dir`
  **由此天然按 run 隔离**。

## 边界 —— 不属于这里
**没有逻辑。** 它委托给 `cli.main`，并且必须一直这么薄。

## 依赖（允许）
`.cli`。

## 测试
由 `test_mcp.py` 覆盖（它会拉起一个真实子进程）。

## 重构备注
在这里加任何东西，都会**先于 `cli.main` 的那些门**执行。
