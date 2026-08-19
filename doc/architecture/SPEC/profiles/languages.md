# profiles/languages.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~50 · 边缘（共享数据） · refactor-status: ok`

## 职责
按语言规则的**唯一归处**（精简 K2），此前曾一式三份。

## 公开契约
`suffixes(language) -> tuple[str, ...]`；`symbol_re(language) -> Pattern | None`；
`sweep_re(language) -> (Pattern, Pattern) | None`。

## 功能
朴素数据映射（`_SUFFIXES`、`_SYMBOL_RE`、`_SWEEP_RE`）+ 极小的访问器。

## 不变量
- 未知语言返回空/None，因此每个消费者都**诚实降级**（只做文件级 sweep / 空的模块扫描 /
  "use grep"）。
- 纯数据 —— 无 I/O、无状态。

## 边界 —— 不属于这里
不含扫描/渲染逻辑 —— 规则由消费者施加（`review._sweep_targets`、
`establish.scan_modules`、`repo_map`）。

## 依赖（允许）
仅 stdlib 的 `re`。**必须保持为叶子**（`_ARCHITECTURE.md` §4）—— 不得 import
engine/profiles 的机器。

## 测试
经三个消费者各自的测试覆盖
（`test_ci_and_repo_map.py`、`test_profile_steps.py`）。

## 重构备注
新增一种语言 = 在三张映射里各加一行。保持它是**朴素数据**；不要让它长成语言检测引擎
（检测留在 `fingerprint_repo`）。这是 K2 的去重目标 —— **不要**把规则再内联回某个
消费者。
