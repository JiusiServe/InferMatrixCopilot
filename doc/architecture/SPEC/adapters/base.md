# adapters/base.py —— 规范

<!-- verified-against: 2026-08-25 -->

`LOC ~423 · 边缘（仓库知识） · refactor-status: ok`

## 职责
`RepoAdapter`（住在边缘的仓库知识）、adapter 注册表，以及确定性的 Phase-0 引导。
`RepoAdapter` 是一个仓库**两个信任层**的**容器**（DESIGN §V2.3.0）：它的 `.manifest`
是 **Tier 1**（`manifest.yaml`，人工门禁的配置），而
`.profile_dir`/`.skills_dir`/`.debug_memory_db` 是 **Tier 2**（agent 建立、证据门禁的
知识）。2026-07-11 由 "plugin" 更名而来（`RepoPlugin`→`RepoAdapter`、
`plugin.yaml`→`manifest.yaml`）—— "plugin" 会错误地暗示这是可执行的扩展代码
（见 DESIGN 的命名说明）。

## 公开契约
`expand_path(value, extra?)`、`AdapterError` 与其子类 `AdapterNotFound`；
`RepoAdapter`（属性 `status`、`repo_path`、`protected_branches`、`modules`、
`high_risk_modules`、`capabilities`、`skills_dir`、`debug_memory_db`、
`profile_dir`、`briefing()`；方法 `module_for_path`）；`load_adapter`、
`update_manifest`、`AdapterRegistry(resolve/all)`；`fingerprint_repo`、
`draft_adapter`。

## 不变量
- **D2**：`update_manifest` **拒绝** agent 对 `push`/`repo`/`upstream`/`rebase` 的写入。
- `expand_path` 先展开进程 env，再用 `extra`（典型是 `Settings.expansion_env()`，
  即 `.env` 里 pydantic 吃进 Settings 而未 export 的键）做**回退**；进程 env 永远
  获胜且**绝不被修改**；仍未解析的变量 → 返回 ""（fail-closed，能力缺口路径）。
- **未知 adapter 名抛 `AdapterNotFound`**（子类）；把"不存在"当兼容路径的调用方
  只能捕获这个子类 —— 已知 adapter 的畸形 manifest 必须仍是硬失败。
- `capabilities` 由 manifest 推导（repo.path/language.*/ci.provider/upstream.*/
  modules）+ 显式的 `capabilities:` —— 与 playbook 的 `requires:` 匹配。
- `high_risk_modules` = 标了 `risk: high` 的模块（喂给 patch-review，**A5**）。
- `fingerprint_repo` 是确定性的，**绝不修改目标仓库**；`draft_adapter` 停在
  `status: draft`（人工门）。
- `briefing()` 渲染 profile 的 briefing 切片（无 profile 时为空）。
- manifest 可以声明**知识路由键**（例如 `knowledge.review_checklist`），把一篇精选页
  注入评审；知识 linter 会校验它们。**这正是仓库知识到达引擎、而不让任何仓库字面量
  进入 `src/` 的方式。**
- skills / debug memory / profile 的解析顺序是**仓库优先、共享池其次**；
  写入**始终**落在当前仓库的命名空间里。

## 边界 —— 不属于这里
不含任务逻辑、不含 LLM、不含 profile store 内部机制（委托给 `profiles/store`）。

## 依赖（允许）
`profiles/store`（在 `briefing()` 内部）、`pyyaml`；stdlib。

## 测试
`test_adapters.py`、`test_capabilities.py`。

## 重构备注
两个关注点在这里共存得很干净：`RepoAdapter`（访问器）+ 注册表 + 引导。
如果引导继续长大（更丰富的指纹），可考虑 `adapters/bootstrap.py`。
**把 `capabilities` 推导保持为 planner 信任的唯一来源** —— 不要在 `cli.resolve` 里
复制一份能力逻辑（它目前只为 REPO_PATHS **补上** repo.path，这是可以接受的）。
