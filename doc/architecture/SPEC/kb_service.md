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

## 2026-09-28 合并流程、激活、巡检与调度
- `merge`：publisher 回执推进状态（pr_requested → pr_open → verdict_posted → queued → merged）；
  对 PR 的精确 head 签发 kb-gate 判定（清单、逐块、一致性）并经 outbox `post_verdict` 发布；
  PR 阶段 `kb-gate` 成功后才发 `enqueue`，每仓库同时至多 1 个排队；head 变化 → human；
  关闭未合并 → closed；合并后记录退役以便下个发版 purge。`pause_open_prs` 发出出队 + 转 draft 项。
- `activate`：每个 main SHA 生成不可变快照（`snapshots/<sha>/knowledge` + MANIFEST），
  加载校验、树级检查、各仓库 `_routes.yaml` 可加载后原子切换 `active`；支持回滚；保留最近 10 个及当前激活。
- `sweep`：发版触发（首次只记录基线）/ 兜底周期；T1 结构报告（唯一自动修复是补索引链接）；
  T2/T3 按规则页让生成器对照发版 diff 逐条给出 keep/edit/replace/retire；purge；全局熔断强制 human。
- `scheduler`（`kb serve`）：终身持有租约；每 tick 重签控制记录与暂停清单、处理回执、按仓库
  advance/intake/sweep（仓库间隔离）、main 变化即激活；24 小时内 2 个知识 PR 被人关闭 → 暂停该仓库并出队。
- CLI：`kb serve [--once]`、`kb activate`、`kb rollback --to SHA`；`kb pause` 同时为已开 PR 发暂停项。
- 每个变更集记录其待回执的 outbox 项（`pending_item`）：未过期时不重复签发；回执只作用于与之匹配的项和
  对应的前置状态，迟到的重复项回执不改变状态。
- 回滚后写入 `rollback_pin`：调度器不会重新激活被回滚的那个 main，只有更新的 main 才会激活。
- 巡检按页记录进度（`sweep_progress`）：页面评估失败与“保持”区分，失败页在下次重试，3 次后交给人；
  所有页面落定后基线才推进；兜底巡检只做 T1 与 purge。
- 熔断暂停与状态变化在同一加锁事务中发布控制记录与暂停清单。

