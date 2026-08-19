# push.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~46 · 安全原语（推送授权） · refactor-status: ok`

## 职责
唯一的推送授权 choke point，以及它的 policy/decision 类型。

> 历史：它曾是 `targets/base.py`，那是一个从未成为真正抽象的"Target 层"设计的残留
> （它的任务定义职责由 `TaskSpec` + `Playbook` 承担）。死掉的 target dataclass 已被
> 移除（精简 K1），模块也改名为它**实际**是的东西 —— 推送授权。**不存在 Target 层。**

## 公开契约
`PushPolicy`、`PushDecision`、`guard_push(policy, protected_branches)`。

## 不变量（**C4**）
- 只有在策略允许**且**分支不受保护时，推送才会发生。
- force 只有 with-lease；受保护分支**永不被推送**（无论是否 force），与策略无关。
- **唯一**的推送授权点 —— `ci.push` 和原生 phase-4 都在这里汇合。

## 边界 —— 不属于这里
不执行 git（那是 step 的事）；不含仓库知识；不做 dry-run 判断（那是 step 读
`ALLOW_PUSH` 的事）。

## 依赖（允许）
仅 stdlib。它是一个叶子安全原语（和 `scopes.py` 一样）。

## 测试
`test_push_and_steps.py`。

## 重构备注
安全攸关且纯粹 —— 保持它无依赖、无副作用。**每一条推送路径都必须经过
`guard_push`**；一个自己重新实现这些检查的新推送点就是缺陷。它和 `scopes.py` 是天然
的兄弟（两者都是纯权限原语）；如果将来引入 `safety/` 包，它们应该住在一起。
