# profiles/repo_map.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~138 · profile（按需结构） · refactor-status: ok`

## 职责
按需、按目标排序、有预算上限的符号索引（设计 §V2.0.2：结构是**被拉取的，永不被推送**）。

## 公开契约
`RepoMap(repo, language, cache_dir?)`，带 `supported`、`index()`、
`render(query, budget_chars)`；以及 `build_index`。

## 不变量
- 按语言的正则符号索引；按 HEAD 做磁盘缓存（一个 HEAD 一份缓存；漂移时重建）。
- `render` 按查询排序 + 预算封顶；零分尾部被丢弃。
- 语言不支持时返回诚实的 "use grep" 字符串（agent 运行时会记一条 `capability_gap`）。

## 边界 —— 不属于这里
**永远不注入 prompt** —— 只以 `repo_map` 工具的形式浮现
（接线在 `agent_runtime._repo_map_tool`）。

## 依赖（允许）
stdlib 的 `re`/`json`/`subprocess`。

## 测试
`test_ci_and_repo_map.py`。

## 重构备注
基于正则（不依赖 tree-sitter）—— 这是**刻意的**简单性/可移植性取舍。如果精度成为问题，
可以让 tree-sitter 后端接在同一个 `RepoMap.render` 契约后面。保持"按需拉取"的姿态 ——
**不要**新增把这张图注入 prompt 的代码路径。

## 精简 —— **K2**（共享语言规则）
`_SYMBOL_RES` + `_SUFFIXES` 是按语言规则集的第三份副本（另两份见
`review._sweep_targets`、`profiles/establish`）。改为消费共享的
`profiles/languages.py`（K2）。必须保留：未知语言时 `supported` 为 false + 诚实的
"use grep"。
