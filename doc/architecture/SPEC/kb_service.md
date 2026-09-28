# kb_service/ —— 规范

<!-- verified-against: 2026-09-28 -->

`知识服务核心：仓库配置、账本、outbox、CLI · refactor-status: new`

## 职责
- `config`：解析 adapter `knowledge_lifecycle`（未知键、非法模式/触发器、缺失审计插件、
  知识目录与 adapter 不一致、私有上游配 `auto_merge`、`auto_merge` 无校准集均抛
  `LifecycleConfigError`）；`load_registry` 返回按仓库名的注册表，`general` 由服务配置。
- `ledger`：单个 SQLite，所有表按 `repo` 分区；心跳租约保证单实例；模式变化即代际 +1；
  `bump_generation` 使该仓库（或 `*`）之前签发的 outbox 项全部失效，可同时暂停。
- `outbox`：服务端签发 outbox 项、控制记录与暂停清单，读取发布器签名的回执；
  发布器端 `check_item`（签名、控制记录新鲜度、过期、代际、暂停、私有上游；
  只有 auto_merge 仓库才有非停止类写动作，shadow 与 disabled 一律不发布；
  `pause`/`close` 总可执行）；
  `verify_holds` 供 kb-gate 使用（过期即失败）。
- `cli`：`infermatrix-copilot kb keygen|status|pause|resume|control`。

## 不变量
- 模块不出现任何仓库名；仓库差异只来自 adapter 配置。
- bot 主机无 GitHub 写凭据：服务只写签名的 outbox 项。
- `knowledge_lifecycle` 属于 adapter 的高风险段，agent 写入被拒。

## 依赖（允许）
stdlib + PyYAML + `cryptography`（`kb` extra）+ `.adapters` + `.knowledge_service.signing`。

## 测试
`test_kb_service_core.py`。
