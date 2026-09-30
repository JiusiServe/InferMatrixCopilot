# ut_coverage.py —— 规范

<!-- verified-against: 2026-09-29 -->

`LOC ~290 · 新增公开函数的单测覆盖候选（#164） · refactor-status: ok`

## 职责
两段式检查的**确定性一半**：从 PR diff 找出新增的公开函数/方法，再看 diff 中的
测试文件、以及（有 checkout 时）被评审树的测试文件是否按名字引用它们。没有任何
测试引用的名字只是**候选**，从不直接判定为“缺测试”——由评审者（Strict lens 或
Direct agent）逐个判断：经调用方被间接覆盖、trivial，还是真缺口。

## 公开契约
`UTCoverageRules`（`from_manifest(manifest)`：读 adapter 的 `ut_coverage:`
段——`source_roots`、`test_globs`、`exclude`、`enabled`；非 Python 仓库或
`enabled: false` 返回 `None`）；`PublicDef`；`CoverageReport`；
`new_public_defs(diff, rules)`；`analyze(diff, rules, repo=None)`；
`render(report)`（Strict evidence 文本，无候选时为空）；
`cap_gap_comments(comments, report)`；`REVIEWER_INSTRUCTIONS`；
`MAX_CANDIDATES=15`；`MAX_COMMENTS=3`。

## 不变量
- **只提名，不裁决**：模块不产生评论；评论只来自评审者对候选的判断。
- 新增 = diff 中 `+def` 且同一**限定名**（`类.方法` 或模块函数名）没有在 diff
  任何位置被删除（移动、改签名不算新 API）；另一个类的同名方法不受影响。跳过：`_` 开头与 dunder 名、嵌套函数、`@overload`/
  `@abstractmethod` 桩、测试文件、`exclude` 命中的文件；私有类的方法跳过。
- 方法判定只看同一 hunk 内可见的 `class`（上下文或新增行）或 hunk 头；看不到
  父作用域的缩进 def 按模块函数处理。
- 树内搜索用 `git grep -l -w -F`，只计入 `test_globs` 命中的文件，逐名限时；
  失败按“无引用”处理（只会多提名，交给评审者判断）。
- 发布上限在评审之后确定性执行，且只作用于评审者**显式分类**为
  `kind: untested_api` 的评论：最多保留 3 条，其余的名字进 summary 一行，不丢失。
  同一函数上的其他发现（不论锚点、严重度）从不被截断；`kind` 是内部字段，
  发布前一律移除。
- 仓库中立：仓库差异全部来自 adapter 的 `ut_coverage:` 段。

## 边界 —— 不属于这里
评审 prompt 与评论发布（`engine/steps/review/`）；Direct 策略包
（`direct_routing.py`）；运行任何测试或覆盖率工具。

## 依赖（允许）
标准库（`re`、`subprocess`、`fnmatch`、`dataclasses`）。

## 测试
`test/test_ut_coverage.py`。
