# ci/providers.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~118 · 边缘（CI） · refactor-status: ok`

## 职责
供 pr-debug 使用的、由 profile 选定的 CI 日志适配器。

## 公开契约
`provider_for(adapter, settings, gh_runner?) -> (provider|None, gap_reason)`；
`BuildkiteLogs.enrich`、`GithubActionsLogs.enrich`。

## 不变量
- provider 由 `profile.ci.provider` 选定，**绝不硬编码**。
- `enrich` 是**逐 check** 尽力而为的 —— 某次 API 出错只会让那个 check 退回按名字分组，
  **绝不崩溃**。
- 缺 provider/token → `(None, reason)`；调用方 step 记一条 `capability_gap`
  并降级为按名字分组（**E2**）。

## 边界 —— 不属于这里
只抓日志 —— 不含分组/调试逻辑；不做签名归一化。

## 依赖（允许）
stdlib 的 `urllib`/`json`/`re`；`gh_runner` 可调用对象是**注入**进来的
（不直接 import `._common.gh`，从而让这个包与引擎无关）。

## 扩展点
新的 CI 系统 → 一个带 `enrich` 的 `*Logs` 类 + `provider_for` 里的一个分支。

## 测试
`test_ci_and_repo_map.py`。

## 重构备注
干净的适配器模式。保持 `enrich(failures) -> count` 契约稳定，好让 `pr.py` 保持无感。
`gh_runner` 注入是**刻意的** —— 不要在这里 import `engine.steps._common`
（那会反转依赖方向，**§ARCH.4.1**）。
