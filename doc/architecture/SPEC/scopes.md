# scopes.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~94 · 引擎（权限） · refactor-status: ok`

## 职责
路径级的工具权限 —— dispatcher 强制执行的那套权限词汇。

## 功能
`ToolScope.check`（工具是否允许？写路径是否允许？）；`PathScope.check_write`
（可写硬墙 + primary 归属文件）；scope 工厂函数。

## 公开契约
`ToolScope(name, allowed_tools, path_scope?, read_only)`；`PathScope(writable,
primary)`；`Decision`；`read_only_scope`、`pre_plan_scope`、`post_plan_scope`；
工具集常量（READ/WRITE/EXEC）。

## 不变量
- **三种结果**：允许 / 拒绝（工具不在集合内、写到 `writable` 之外、或处于只读
  scope）/ 越界（在 `writable` 内但在 `primary` 之外 —— **允许并记录**）。
- `writable` 是一堵硬墙；`primary` 定义该模块归属的文件。

## 边界 —— 不属于这里
只做权限判定 —— 不执行、不记 trace（由 dispatcher 记）。

## 依赖（允许）
仅 stdlib。

## 扩展点
新的 scope 形状 → 加一个工厂函数；保持三结果的 `Decision` 契约。

## 测试
`test_scopes_tools.py`。

## 重构备注
干净、无依赖、安全攸关。保持它是纯的（无副作用），这样它才一直是可轻松测试的。
`engine/step.py` 会 import 它 —— **不要**加反向 import。

## 影子边界（元改进引擎 P0，设计 §8.2）
- `ToolScope` 新增四个默认关闭的字段：`read_roots`（设置后每个读/exec 路径先 `realpath` 再要求位于某个根之下，
  `..` 与符号链接因此无法逃逸）、`deny_prefixes`（如 `--shared` 克隆的 `.git/`）、`strict_extras`（step 提供的
  extra 工具必须在 `allowed_tools` 内，`internal_write` 的 extra 一律拒绝）、`executables`（影子 PATH 白名单，
  由影子环境强制，这里只做自描述）。`check_read(path)` 是读围栏的裁决。
- `shadow_scope(shadow_dir, tools=…, extra_read_roots=…, executables=…)`：内建读工具 + 声明的影子工具、只读、
  读根 = 影子 checkout + 只读的知识/适配器根、拒绝 `.git/`、严格 extra。
- 未设置这些字段时行为与之前逐字节相同（`test_improve_p0b.py` 的"普通 scope 行为不变"断言）。
