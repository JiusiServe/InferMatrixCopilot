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

## 2026-09-28 intake 与质量门
- `models`：生成与评审模型按 (provider, model, effort) 钉死（默认 `claude-code:claude-opus-5-5`
  与 `codex:gpt-6-sol:medium`，评审必须与生成不同家族）；不可用/超时/无法解析 → `ModelUnavailable`，
  调用方保持排队，绝不降级；每次调用经 recorder 记录输入、输出、用量。
- `sources`：知识仓库克隆的只读读取（`knowledge_files`、`external_texts`）、只读 GitHub 客户端
  （合并 PR、PR 证据有界摘录、release/tag）、本机 Copilot 运行经验收件目录。
- `intake`：每个事件由生成器起草类型化操作（只允许 add/edit_same_meaning/replace/retire），
  `apply_operations` 必须接受，最多两轮带精确错误的修复；多事件合并为一个变更集。
- `gate`：L1 → 逐块 L2（每类块只问适用维度）→ 按 owner 目录的一致性检查；
  外部引用、protected、熔断（按仓库计算）、任何不确定 → human；L1 失败不调用模型。
- `runtime`：collect → intake → gate → publish；shadow 只记录；变更集文件存 `changesets/<id>.json`。
- `calibration`：按仓库的校准集评分（坏样例须全部拦下、好样例误拒 ≤ 20%）。
- `runner`：经标准 executor 运行 `kb-*` playbook。CLI 新增 `kb run`、`kb calibrate`。
