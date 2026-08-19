# tools.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~228 · 引擎（能力 + choke point） · refactor-status: ok`

## 职责
原子能力，以及**唯一那个强制 scope 的 dispatch choke point**。

## 功能
定义内置工具（read_file、write_file、edit_file、list_dir、grep、run_shell）；
`dispatch` 对每次调用做 scope 检查、执行并记 trace。

## 公开契约
`ToolDef`；`TOOLS`；`tool_definitions_for(scope, extra?)`；
`dispatch(name, args, *, scope?, trace?, extra?) -> {ok, result|error, out_of_scope}`。

## 不变量（**C3**）
- 每次内置调用都做 scope 检查；被拒 → **返回错误值**（绝不抛异常）。
- 越界的写**会执行**但发出 `out_of_scope_edit`；整文件写 `.py` 发出 `full_file_write`。
- **错误是观测结果，不是崩溃。**
- 额外（由 step 提供的）工具绕过内置 allowlist，但**仍然被记 trace**。
- **`read_file` 是窗口化的（48k 字符，用 `offset` 翻页），不是整文件读。**
  整文件读会吹爆会话历史、成倍增加未缓存 token，并把会话推出可靠缓存长度 ——
  这是**实测出来的成本，不是谨慎**。
- **`grep` 默认按字面量匹配**（要正则得传 `regex:true`），所以搜 `items[0]` 不需要转义。
  一个默认正则的工具，会对**最常见的查询形状**静默给出错误答案。
- 同一个 `dispatch` 通过 `tool_bridge.py` 服务 harness 后端，
  所以**在这里改强制逻辑，等于对所有后端同时改**。

## 边界 —— 不属于这里
只回答"能做什么" —— 工具表达**能力**，不表达工程语义（那是 step，**A3**）。
不含任务/仓库逻辑。

## 依赖（允许）
`run_trace`、`scopes`；stdlib。

## 扩展点
新内置工具 → 在 `TOOLS` 里加一个 `ToolDef`（会写就声明 `write_path_arg`）。
step 专属工具作为 `extra` 传入，**不加在这里**。

## 测试
`test_scopes_tools.py`。

## 重构备注
dispatch choke point 是一条**硬安全不变量** —— 每条路径（内置和 extra）都必须保持
被记 trace 且被 scope 检查。**不要新增绕过 `dispatch` 的"快路径"。** 当前体量没问题。
