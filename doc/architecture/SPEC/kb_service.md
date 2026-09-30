# kb_service/ —— 规范

<!-- verified-against: 2026-09-30 -->

`知识服务核心：仓库配置、账本、outbox、CLI · refactor-status: new`

## 职责
- `config`：解析 adapter `knowledge_lifecycle`（未知键、非法模式/触发器、缺失审计插件、
  知识目录与 adapter 不一致、私有上游配 `auto_merge`、`auto_merge` 无校准集均抛
  `LifecycleConfigError`）；`load_registry` 返回按仓库名的注册表，`general` 由服务配置。
- `ledger`：单个 SQLite，所有表按 `repo` 分区；心跳租约保证单实例；模式变化即代际 +1；
  `bump_generation` 使该仓库（或 `*`）之前签发的 outbox 项全部失效，可同时暂停。
- `outbox`：服务端签发 outbox 项与控制记录，读取发布器签名的回执；
  发布器端 `check_item`（签名、控制记录新鲜度、过期、代际、暂停、私有上游；
  只有 auto_merge 仓库才有非停止类写动作，shadow 与 disabled 一律不发布；
  `close`/`open_revert_pr` 总可执行）。
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
- `merge`：publisher 回执推进状态（pr_requested → pr_open → merge_requested → merged，v8 见下文）；
  对 PR 的精确 head 签发判定（清单、逐块、一致性），随 `merge` 项交给发布器，每仓库同时至多 1 个；head 变化 → human；
  关闭未合并 → closed；合并后记录退役以便下个发版 purge。
- `activate`：每个 main SHA 生成不可变快照（`snapshots/<sha>/knowledge` + MANIFEST），
  加载校验、树级检查、各仓库 `_routes.yaml` 可加载后原子切换 `active`；支持回滚；保留最近 10 个及当前激活。
- `sweep`：发版触发（首次只记录基线）/ 兜底周期；T1 结构报告（唯一自动修复是补索引链接）；
  T2/T3 按规则页让生成器对照发版 diff 逐条给出 keep/edit/replace/retire；purge；全局熔断强制 human。
- `scheduler`（`kb serve`）：终身持有租约；每 tick 重签控制记录、处理回执、按仓库
  advance/intake/sweep（仓库间隔离）、main 变化即激活；24 小时内 2 个知识 PR 被人关闭 → 暂停该仓库。
- CLI：`kb serve [--once]`、`kb activate`、`kb rollback --to SHA`；`kb pause`/`kb resume` 只改代际与暂停状态。
- 每个变更集记录其待回执的 outbox 项（`pending_item`）：未过期时不重复签发；回执只作用于与之匹配的项和
  对应的前置状态，迟到的重复项回执不改变状态。
- 回滚后写入 `rollback_pin`：调度器不会重新激活被回滚的那个 main，只有更新的 main 才会激活。
- 巡检按页记录进度（`sweep_progress`）：页面评估失败与“保持”区分，失败页在下次重试，3 次后交给人；
  所有页面落定后基线才推进；兜底巡检只做 T1 与 purge。
- 熔断暂停与状态变化在同一加锁事务中发布控制记录。


## 2026-09-28 发布器
`publisher` 在 GPU 盒上以仓库负责人的 gh 登录运行（`kb publish`），是知识 PR 唯一的 GitHub 写入方。
- 每轮：经 SSH（或本地目录）读取签名控制记录，过期即整轮不动；对每个 outbox 项执行 `check_item`（签名、
  过期、代际、暂停、控制记录与**发布器自己的适配器配置**同时为 `auto_merge`），执行后先在本地记录结果，
  再写回发布器密钥签名的 `kb-ack`（字段：item_id、kind、changeset_id、ok、pr、head_sha、branch、error）。
- 幂等：已执行的项只重发 ack（服务收取 ack 后删除该项）；完成记录原子写入，损坏的记录移到 `.corrupt` 并等人处理，
  绝不猜测是否已执行；`open_pr` 只复用 head 恰为重建提交的已打开 PR（companion 还须是 draft）；
  提交由签名内容在 `base_sha` 上用临时索引重建，日期取自该项，重试得到同一 SHA；分支已存在且内容不同则拒绝，
  绝不覆盖。路径必须是受治理的知识页面（`knowledge/{repos/<r>,general}/**.md|yaml`，无 `..`）。
- 恢复：失败的 `close`/`open_issue`/`post_findings` 不回执，留在 outbox 中每轮重试直到成功；格式错误的控制记录或项目记入 trace 并跳过。
  SSH 读取或回执失败只记入 trace，不终止进程；完成记录保留，下一轮重发回执而不重复动作。
- 动作：`open_pr`、`open_companion_pr`（始终 draft）、`merge`（v8，见下文）、`post_findings`、`open_revert_pr`、
  `open_issue`、`close`。
- 双重门控：无 `ALLOW_POST=1` 只记录将要执行的动作；推送分支还需 `ALLOW_PUSH=1`。无法验证或不可执行的项
  既不执行也不回执。每轮与每个决定都写入 `traces/publisher.jsonl`。
- 测试：`test_kb_publisher.py`（端到端 open_pr → ack → pr_open、dry-run、崩溃后不重复执行、伪造/未配置/过期、
  越界路径、verdict/入队/暂停/关闭、暂停期间仍执行暂停、SSH 引号与回执、ack 字段）。

## 2026-09-28 留痕、回放与数据集
- 运行时持有 `TraceStore(state_dir/traces)`：`ModelGateway` 的每次调用（含失败）写为 `model_call`；
  `gate_and_stage` 先分配变更集 ID，判定期间绑定 `changeset_id`/`rule_ids`，暂存后写 `decision`；
  `merge.advance` 写 `outcome`（merged / closed_unmerged / head_changed），退役写 `rule_retired`。
  intake、sweep、calibration 分别绑定 playbook `kb-intake`/`kb-sweep`/`kb-calibrate`。留痕失败从不中断服务。
- `replay`：用记录中的原始 system/prompt 询问替代模型，比较决定性字段（`dimensions` 或 `verdict`），写
  `replay` 记录；替代模型的调用本身也记为 playbook `kb-replay`。只调用模型，不触及 GitHub、outbox 或账本。
- `export_dataset`：按角色导出（输入、高成本模型输出、变更集判定、事后结果、规则后续结果）；丢弃校准与回放
  调用、失败调用（截断、空、无法解析或不符 schema 的回复都记为失败），以及 prompt 中任意位置出现校准用例证据
  引用（如 `PR #8107`，按边界匹配）或标题的调用。生成器调用发生在变更集之前：每次起草有唯一 `draft_key`（intake 为事件、
  巡检为发版 + 页面，均带随机后缀），只有被采纳的那次尝试（`draft_key#attempt`）列入之后 `decision` 记录的
  `draft_keys`，被拒绝的尝试与失败的重试不继承判定。记录的每个字符串（含键、model、usage）都经过脱敏。
- CLI：`kb traces`、`kb replay --record ID --model P:M[:E]`、`kb export --out FILE`。

## 2026-09-28 过期判定：重签、重建或转人工
（v8 改写）发布器本地门禁拒绝 `merge` 时按理由分类（见“v8：发布器本地门禁与合并”）：瞬时问题 → 回到 `pr_open` 重签；
上下文改变、一致性页面变化、无法干净合并、清单不符 → **重建**：只有持有租约的调度器执行，在当前 main
上重新应用同样的操作并重新过质量门，暂存为 `rebuild` 变更集（证据带 `rebuild of <旧 id>` 标记，与暂存原子写入，
中断后再次执行会找到它而不会重复暂存）。只有重建**通过**质量门才取代旧 PR：旧变更集进入 `superseding`，`close` 项
过期即重发，直到观测到 PR 已关闭才记为 `superseded`（不计入被人工推翻的熔断）；重建未通过、操作无法再应用或没有
可重放的操作 → `rebuild_failed` 并转人工，旧 PR 保持打开。变更本身的问题见“v8：精炼—复检”。
## 2026-09-28 外部知识 PR（来源④）
（v8 改写：没有 human-approved 路径，每日复检见下文）`external.poll_external`（调度器、全局未暂停时调用，需持有租约）
处理知识仓库中**非服务创建**、非 draft、触碰 `knowledge/` 的打开 PR，每个 head 只评一次：
- 全部路径须为受治理页面 → 以**当前 main 加上 PR 改动**完整过质量门（L1、L2、一致性）→ 通过则签发 `auto` 判定。
  PR 的前像必须等于 main（否则合并落地的改动与签名不同），不等则请作者 rebase。
  与服务自己的 PR 一样，`auto` 判定要求当前通过的评审校准；否则记为 `calibration_required`，校准恢复后才重新评判
  （期间不重复调用付费评审）。
- 其余情况（跨多个仓库、受治理页面以外的路径——要求作者拆分、质量门未通过）不合并，理由写入发现评论。
- 判定清单直接取自 git（`merge-base..head` 的完整原始 diff）；`context_base_sha` 为评判时的 main。
- 暂存为 `external` 变更集后走普通合并流程。作者推送新 head → `head_changed`（不转人工）；上下文失效 → `stale_context`；
  两者都在下次复检时重新评判。外部 PR 没有操作列表，L1 发现的退役/删除规则写入 `retirements`/`purges`，合并后同样进入
  退役账本（之后的发版巡检据此 purge）。作者关闭自己的 PR 不计入熔断。只触碰非受治理知识路径的 PR 归入 `general`（若其接收
  人工 PR），否则归入第一个接收人工 PR 的仓库。
## 2026-09-28 每日合并审计
`audit.audit_main`（调度器每 24 小时）沿 main 的 first-parent 历史从上次审计的提交向后检查：每个相对第一父改动了
`knowledge/` 的提交，都必须是账本已记录合并的变更集。证明只看结构、从不信提交信息：提交 SHA 为某变更集的 merge SHA，或它是双亲
合并、第二父正是某个已合并变更集记录的 head，且它对知识的改动恰好就是该 head 的改动（改动的每个
知识路径都在该 PR 的改动内且内容与 head 相同；夹带额外改动的合并同样被发现）。否则（admin bypass、直接推送、账本漏记）对其涉及的仓库暂停自动合并（改动在仓库范围之外 → 全局暂停）、
并转人工；不在 `auto_merge` 的仓库只写 `unrecorded_merge` trace。首次运行只记录基线；晚于
2 小时宽限期的提交留到下次，避免与调度器记录合并赛跑。暂停逻辑与熔断共用 `Scheduler._pause`。

## 2026-09-29 巡检汇总 issue
每次巡检完成（`complete`）后，`report.publish_summary` 把汇总（T1 发现、修复的索引、保留/失败的页面、变更集及其状态、
各类操作数、待人工处理数、模型调用次数/token/耗时）写入 `<state_dir>/reports/sweep-<repo>-<tag>.md`；仅当仓库为
`auto_merge` 且上游公开时，另通过新的 outbox 项 `open_issue`（7 天有效）在知识仓库发布一个 issue。发布器按标题复用已有
issue（同一报告只开一个），标签不存在时不带标签重试，绝不丢报告。

## 2026-09-29 留痕离机归档
`archive.make_archive`（调度器每 7 天）把 `<state_dir>/traces` 中尚未归档的内容（不含可重建的 `index.db`）打包为
`archive/traces-<序号>-<时间>.tar.gz`（序号在前且单调递增，名称顺序即恢复顺序，不受时钟回拨影响；从不复用或覆盖）。已归档内容以 `archive/archived.json`（路径 → 内容
哈希）显式记录而非依赖时间戳：blob 不可变只归档一次，增长的记录文件再次归档，归档期间才落盘的 blob 进入下一个归档，并写 `.sha256` 清单（首行为包的哈希，其后每个成员一行；清单最后写入，
标志归档完整）。发布器（GPU 盒，经已有的 SSH 通道）每轮拉取本地没有的归档，只有哈希校验通过才保存到
`$KB_PUBLISHER_STATE/archive/`，否则记入 trace 并拒绝。恢复：按名称顺序解开到空目录后运行 `TraceStore.rebuild_index`。

## 2026-09-29 配套 PR（外部引用）
质量门唯一的问题是"知识目录外引用了本次退役/替换/删除的规则"时（非巡检暂存、非强制人工），`companion.stage_companion`
自动起草配套变更：被替换规则的 ID 改为新 ID；引用已退役规则的列表项/表格行删除，其余提及去掉 ID；只改配套白名单
（`skills/`、`plugins/`、`adapters/`、`doc/`、`playbooks/`）。配套 PR 经 `open_companion_pr` 以 draft 创建并打 `kb:companion`
标签，进入人工队列；发布器拒绝在其上执行 `merge`（ready 与合并只能由人完成），且拒绝白名单外路径
（`knowledge/`、`.github/`、`src/`、`tools/`）。知识变更集处于 `companion_pending`（规则保持 active）；配套 PR 合并后，调度器
在当前 main 上重建它（外部引用已清零 → 正常过门与发布）；配套 PR 被关闭则知识变更转人工，且不计入熔断。

## 2026-09-29 巡检中的发版审计与基线配套 PR
配置了 `release.auditor` 的仓库，调度器在每次巡检前以 generated-baseline 模式运行审计插件（上游 SHA 对未变的回退巡检
跳过）：知识文档问题按页面转为巡检生成器的提示；审计失败每次巡检只转人工一次，巡检照常进行（无提示）。reconciliation
（提交的适配器基线落后于审计的上游）不阻塞巡检，而是起草一个配套 PR：插件以 `baseline_file`（相对适配器目录）指明基线
文件，只替换其中的 `upstream:` 与 `inventories:` 块（其余内容与注释保留），经 `open_companion_pr` 以 draft 发布并转人工；
每次巡检最多一个。巡检汇总列出 reconciliation 数量。

## 2026-09-29 快照保留与运行钉住
`activate.prune` 保留最新 10 个快照与当前激活快照之外，还保留被**未结束**运行钉住的快照（运行目录中的
`knowledge.json` 指向该快照且 `run_status` 非终态）。运行目录位置取 `KB_RUN_ROOTS`（`os.pathsep` 分隔，可列多个服务）、
否则运行服务实际生效的 `run_root`（环境变量或其支持的 `.env` 文件）。切换激活快照时记录旧快照的停用时间；
停用不足 1 小时的快照不删除——在切换前刚解析到它的预留会在此窗口内写下钉住记录（运行服务在其他进程中，无法共享
激活锁，因此以宽限期协调）。测试通过自动 fixture 把 `KB_RUN_ROOTS` 指向空目录，从不读取真实运行目录。


## 2026-09-29 激活前的格式检查
`verify_snapshot` 在其他检查之前核对快照声明的知识格式：未声明或不在本 Copilot 支持的 `SUPPORTED_FORMATS` 中 →
`ActivationError`，`active` 保持不变（先升级 Copilot 再激活新格式的知识）。快照随顶层 Markdown 一起携带
`_format.yaml`。

## 2026-09-29 Copilot 运行经验（来源②）
`collect_events` 在 `intake.copilot_runs` 开启时，除 `inbox/lessons/` 外还读取 `pr_debug` 的已验证修复记录（v1/v2，
`engine/steps/pr/debug.py` 产出）：同机运行投放到 `KB_BUGFIX_DIR`（缺省 `<state_dir>/inbox/bugfix`，与运行侧
`KNOWLEDGE_INTAKE_DIR` 配为同一目录），异机运行发到邮箱 issue `KB_BUGFIX_MAILBOX`（`owner/repo#N`）。仓库按完整名
（不区分大小写）或别名精确匹配；歧义身份改名 `.quarantined` 隔离、从不改写；属于其他仓库的投放文件留待其处理。
邮箱是公开 issue，只接受 `KB_BUGFIX_AUTHORS` 列出的作者（未设置则不读邮箱），每个仓库各自维护评论游标。
事件 ID 与记录的 `event_id` 一致，重复投递幂等。

## 2026-09-29 v8：发布器本地门禁与合并
- 服务不发布判定评论、不等待 GitHub 状态检查、不入合并队列：`pr_open` 时签发绑定 PR/head 的判定，随
  `merge` 项交给发布器（每仓库同时至多一个 `merge_requested`）。回执：成功 → `merged`（合并 SHA、落地后复核结果）；
  落地后复核失败 → 暂停该仓库并转人工；拒绝 → 按理由分为重建（上下文/页面哈希变化、无法干净合并、清单不符 →
  `rebuild_needed`，由持有租约的调度器在当前 main 上重建）、瞬时（main 持续变化、控制记录变化、git/gh 问题 → 回到
  `pr_open` 重签）、变更本身的问题（→ `gate_failed`，转人工，从不按原样重试）。未回执的 `merge` 过期后回到 `pr_open`。
- 落地后复核：回执中的 `passed`/`failed` 为终态（`failed` 暂停该仓库并转人工），即使 GitHub 先显示已合并、回执后到也照常处理；
  `unknown`（发布器无法运行，或崩溃后恢复的合并）由服务 `verify_merged` 在自己的克隆上重跑，无法运行则下一轮重试。
- `local_gate`：发布器在自己安装的 Copilot 版本上，对 `main` tip 与 PR head 的合并树运行 `gate_verifier.verify_change`
  （直接传入已验签的判定），另要求每个路径都在该项所属仓库的知识目录内、判定来源为 `auto`，并检查合并树
  无新增树级问题；`post_merge_problems` 在 GitHub 实际生成的合并提交上重跑。
- 发布器 `merge`：整轮持有跨进程 `flock`（第二个实例直接退出）；验签与绑定 → PR 打开且目标为 `main`、head 一致 →
  取 main 与 PR head 跑本地门禁 → main 变化则重来（至多 3 次）→ 重读控制记录（暂停/代际变化即放弃）→ 写合并意图 →
  `gh pr merge --merge --match-head-commit` → 读取合并提交并做落地后复核。合并之后的任何异常都不会变成失败回执；
  每轮开始先恢复有意图无完成记录的项（已合并则补发回执，未合并则丢弃意图、下一轮重试）。
  `gh pr merge` 报错时无法确定是否已合并：保留意图、不写记录也不回执，由下一轮恢复向 GitHub 确认。draft PR
  从不被转为 ready 或合并（瞬时拒绝，作者转回 ready 后再合并）。
  只有 GitHub 显示 `MERGED` 才算合并：若 `main` 要求合并队列或开启了自动合并，`gh pr merge` 只会入队——此时关闭自动合并并
  拒绝（转人工，要求 `main` 允许发布器直接合并）；只有经 GraphQL 确认既不在合并队列中（必要时 `dequeuePullRequest`）也没有自动合并，才记为拒绝，否则保留意图，由恢复流程继续取消或接收
  后来发生的合并。存在未结的合并意图时该项跳过，直到恢复流程从 GitHub 得到结果。
- external 的状态集合由 `merge.IN_FLIGHT` 派生，合并中的外部 PR 不会被重复评审。

## 2026-09-29 v8：精炼—复检
`refine`：质量门拒绝的服务自身变更（`intake`/`rebuild`/`refine` 类，暂存时 `failed` 且判定为 `fail`，或发布器本地门禁因变更本身
拒绝 → `refine_needed`）从不合并。调度器（持有租约、仓库未暂停）把全部拒绝理由（本地门禁问题、L1 问题、L2 各维度理由、
一致性冲突、判定理由）连同原操作交给生成器，在当前 main 上生成精炼后的变更集（kind `refine`，`refine_round`、`refine_history`），
整体重跑 L1 + L2 + 一致性；通过则发布，原变更记为 `refined`（有 PR 则 `superseding` 并关闭旧 PR）。至多 `MAX_REFINES = 2`
轮；仍失败 → `refine_exhausted`，人工队列一条，附每一轮理由，之后不再调用生成器。精炼按证据标记恢复（任意状态，含 `companion_pending`），崩溃后不会重复暂存；生成器拿到全部原始证据；重建沿用精炼轮次，
上限不会因上下文变化而重置；精炼一次处理整个变更集，操作数上限为 6 × 事件数（且不少于原操作数）。
服务自己的 PR 在任何状态下（`Ledger.changesets_for_pr`）都不会被当作他人的 PR 重新评审。
外部 PR 被本地门禁拒绝仍为 `gate_failed` 转人工（他人 PR 的处理见后续）；仓库设置导致的拒绝（`main` 必须允许发布器直接合并）
也转人工，精炼无法修复。

## 2026-09-29 v8：他人的知识 PR 每日复检与发现评论
`poll_external` 按 PR 限频：每个 PR 每天至多检查一次，检查完成即在账本记下（`external_checked:<PR>`），重启或中途失败都不会
当天重复检查已完成的 PR（`force=True` 用于测试与手动）。当天对每个打开的
他人知识 PR：当前 head 已通过并在合并流程中的不再评审；未通过（`failed`/`human`/`gate_failed`/上下文失效/head 变化等）的每天重新评审，
作者推送多少次都只在下一次每日检查时评审。每次评审（含本地门禁拒绝）都签发 `post_findings`：发布器在该 PR 上只维护一条带
`<!-- kb-findings:v1 -->` 标记、由自己账号发出的评论，已有则编辑、没有才创建，从不编辑他人伪造的同标记评论。未通过的外部 PR 不进
人工队列（作者负责修改），也从不合并；影子模式与私有上游不发布评论；跨多个仓库的 PR 经其中一个
公开且为 `auto_merge` 的仓库发布评论（只要其中有私有上游就不发布）。`post_findings` 失败时不回执，每轮重试直至成功；每条发现评论以签发时间为修订号，
发布器记住每个 PR 已发布的最新修订，较旧的项不会覆盖较新的评论；服务在账本（全局 `findings:<PR>`，每个 PR 一条，与其涉及的仓库
范围无关）记下最新一条直至发布器确认送达，过期仍未送达的以相同内容与原修订号重新签发（与 PR 当前状态无关），因此旧发现永远
不会覆盖新的；发布器的修订记录原子写入，损坏时视为无记录。

## 2026-09-29 v8：来历检查与撤回
`audit`（原每日审计）改为每个调度 tick 运行，沿 main 的第一父链检查每个触碰 `knowledge/` 的提交：可信（账本记录的合并 SHA，或只携带
已记录 head 知识变化的双亲合并）、待回执（合并项仍在等待回执的 head，下一 tick 再看）、已处置（精确撤回已合并）、未知。
- 未知提交：暂停其涉及的仓库（触及仓库范围之外则全部暂停），记录 `unknown:<sha>`，告警，并把其内容作为新候选事件（`unrecorded`）
  送回 intake；对受治理路径生成撤回 PR（恢复为第一父内容，由发布器构建、永不自动合并；`open_revert_pr` 属于总可执行项）。
  路径之后又被修改（会冲突）或涉及非受治理路径时不生成撤回、转人工。无租约时记为 `revert_pending`，由下一次持有租约的检查补发。
- 撤回 PR 由人合并：只有 PR 合并的正是发布器构建的撤回提交、且合并提交在受治理路径上的变化恰为撤回路径并恢复到前像，才记录
  `disposed:<sha>` 处置配对；不精确的撤回合并本身也是未知提交。关闭撤回 PR 则保持未处置并告警。
- 存在未处置的未知提交时不激活任何快照（G5 例外）；可信列表（合并 SHA 与处置配对）写入签名控制记录的 `provenance`，发布器合并前
  核对自当前激活快照以来 main 上每个受治理知识提交都可信（或是其自己的合并），否则不合并（瞬时，服务随即暂停并撤回）。
- 精确性按树条目（模式 + 内容）比较；手工撤回同样被识别：与某提交共享知识路径的未处置未知提交（传递闭包，先前的部分撤回也是其中之一）
  构成一组；若该提交只改动这组涉及的路径，且之后这组触及的每条知识路径（不限受治理路径）都恢复到最早一个提交之前的树条目
  （按祖先关系排序），则整组被处置。未知记录保存完整路径列表与全部知识路径的前像，冲突检查覆盖所有路径。已处置的未知提交只在其处置撤回属于被检查的历史时
  才可信（main 回退到撤回之前会使其重新成为未知）；只要涉及的任一仓库范围为私有上游，就不开公开撤回 PR、不生成候选事件，只转人工。结算撤回前先拉取，避免把新合并的撤回误判为未知。
- 激活本身（`activate()`，含 `kb activate`）核对从当前激活快照到目标 SHA 的每个知识提交都可信（首次激活除外），否则
  `ActivationError`；调度器在激活前做同样的检查并只记录 `activation_blocked`。入 intake 的候选事件带上该提交的 diff。
- 尚未实现：`kb accept-unknown`（接受未知提交内容而不撤回），目前通过合并精确撤回（服务开出的或手工的）解除。

## 2026-09-29 v8：移除 v7 的 GitHub 端机制
- 删除：`.github/workflows/kb-gate.yml`、`.github/kb-gate/` 验证包与 `tools/build_kb_gate_bundle.py`、`.github/CODEOWNERS`、
  暂停清单（`publish_holds`/`verify_holds`/`holds_server`/`kb holds-server`、签名用途 `kb-holds`）、`human-approved` 路径
  （维护者审批、`kb:human-approved`、`approval_withdrawn`）、outbox 项 `post_verdict`/`enqueue`/`pause`/`update_branch` 及其
  发布器动作、暂停确认（`pause_open_prs`/`pause_unconfirmed`/`resume_paused_prs`、`kb status` 的 `pause_unconfirmed`）、
  状态 `verdict_posted`/`queued`/`paused`（v7 从未在生产启用自动合并，没有需要迁移的记录）。
- 暂停只由代际与暂停状态表达：服务不再签发 `merge`，发布器在执行前与合并前两次拒绝旧代际或暂停仓库的项；
  暂停期间仍跟踪 PR 的合并、关闭与撤回，恢复后下一轮为同一 head 重签判定。
- 判定只有 `auto` 来源（`verdict.SOURCES`），不再带 `review_ids`/`reviewers`。
- 测试：`test_kb_local_gate_verifier.py`（取代 `test_kb_gate_verifier.py`；本地门禁上的重放/过期/伪造/非 auto 来源、清单与块表、
  混合路径与可执行位、跨仓库、上下文失效、落地树中的悬空引用）；`test_kb_publisher.py`（暂停不触碰 PR、恢复后重签合并、
  draft 不合并、`close` 重试）；`test_kb_external.py`（受治理页面以外的路径从不合并）。

## 2026-09-29 v8：上游事实证明与发布器复核
- 服务：`run_gate(facts=observer)` 在 L1 之后、L2 之前对变更涉及的规则调用 `facts.attest`（观测者为
  `upstream_facts.MirrorObserver`：服务自己的上游裸镜像 `<state_dir>/upstream/<repo>.git`（与发版巡检共用）+ 只读
  GitHub reader）。必需声明不成立 → `fail`（理由 `upstream fact: …`，不调用付费评审，进入精炼）；上游不可读 → `human`。
  事实与钉住的 `upstream` 写入 `decision`，`sign_verdict` 签入判定。没有上游（`general`）或不发布的仓库不做证明。
  `KbRuntime.upstream_facts(lifecycle)` 提供观测者（`from_env` 装配；测试默认不证明）。
- 发布器：`merge` 在本地门禁通过后、最后一次读控制记录前调用 `facts.recheck`，数据来源独立：发布器自己的镜像
  `<publisher_state>/upstream/<repo>.git` 与 `gh api repos/<upstream>/pulls/<n>`；上游来自**发布器自己的**适配器配置
  （`upstreams`，只含启用且发布的仓库）。任何不一致、未配置公开上游或上游不可读 → 本轮不合并（`not merging: upstream facts: …`）。
- 服务收到这类拒绝：回到 `pr_open` 下一轮重签，记录 `facts_failing_since`；连续 24 小时仍失败 → `gate_failed` 并转人工。
  其他任何回执结束这段连续失败。
- 测试：`test_kb_upstream_facts.py`（声明抽取、符号定义、证明与复核的一致/不一致/不可达/伪造、真实 git 镜像、
  门禁在 L2 前失败、发布器一致时合并、不一致或不可达时不合并并在 24 小时后转人工、未配置上游不合并）。

## 2026-09-29 v8：`kb accept-unknown`
第二种处置未知提交的方式（与精确 revert 并列，design §8.3）：
- `kb accept-unknown SHA`（至少 7 位、唯一前缀）只校验并记录请求（`accept_request:<sha>`，已处置或不是未知提交 → 退出码 2）；
  `kb serve` 持有租约，在下一个 tick 由 `accept.accept_pending` 判定。
- 判定：该提交自身的改动（第一父 → 提交）作为 `accept` 变更集走**完整**门禁（L1、L2、一致性、上游事实），要求当前通过的
  评审校准；只能是单个启用且公开的仓库范围、全部为受治理页面、非根提交。服务的 revert PR 仍在创建中（`pr_requested`）
  时等到下一 tick。
- 只有 `pass` 才处置：`disposed:<sha> = <sha>`（提交在历史中即被信任）、记录 `state=accepted`、丢弃该提交的 `unrecorded`
  intake 候选、已打开的 revert PR 转 `superseding` 并下发 `close`。暂停不自动解除：由人 `kb resume`。
  其余结果（门禁未过、无校准、范围或路径不合格）不处置，转人工并写入请求记录。
- 可恢复：通过后先把记录写为 `accepting`，清理（按 `ledger.event_by_external_id` 直接定位候选事件、revert 转 `superseding`）
  完成后才写 `disposed:` 与 `accepted`；中途崩溃由下一 tick 完成清理且不再次调用评审。
- 与外部 PR 一样，L1 发现该提交退役/删除的规则写入 `accept` 变更集的 `retirements`/`purges`，清理时经 `record_retirements`
  （幂等 upsert）记入退役账本，下个发版的巡检据此 purge。
- `kb status` 新增 `unknown_commits`：未处置的未知提交及其接受请求的状态。
- 测试：`test_kb_accept_unknown.py`。

## 2026-09-29 一致性冲突只算本次改动的
一致性评审看整个 owner 目录，但只有**涉及本次改动的规则**（新增、编辑、退役、被替代的规则 ID）的冲突才使变更失败；
两条都未被改动的规则之间的冲突已经在 main 上，记入该目录的 `preexisting`，不计入变更（精炼也无法修复它，否则该目录
的任何变更都会被永久挡住并白白消耗精炼轮次）。没有写出规则 ID 的冲突仍算本次改动的（失败即关闭）。评审提示中带
`changed_rule_ids`。校准不传 `changed`，保持整目录严格判定。首个线上运行即遇到此情况：configuration 目录中 CONF-1a..4a 在
两页重复、DIFF-2s/2t、SERV-4o/4r5 在 main 上已冲突，导致两批 intake 全部 `refine_exhausted`。

## 2026-09-29 L2 按规则取证据
`evidence.for_rule(rule_text, evidence, observer)`：L2 评审每条规则时只给它引用的 PR（`^[PR #N]`；一个都不在批次里则
全部给），并把这些上游合并 PR 的 8 KB 摘录换成合并提交的完整逐文件 diff（服务自己的上游镜像，`MirrorObserver.file_diff`）：
规则提到的文件在前，每文件 24 KB、每条规则 48 KB，截断处注明；超出预算的文件列在 `diffs_omitted`。镜像读不到或没有
diff 时保留原摘录（证据不会因此变得更"好过"）。只扩展带 `merged_at` 的上游 PR 证据；Copilot 运行经验与外部 PR 证据不变。
`merged_pr` 事件的证据新增 `merge_commit_sha`（旧事件经 `pull()` 查询）。`run_gate(evidence_for=...)` 由 `gate_and_stage`
与事实证明共用同一个观测者（一次镜像同步）。首个线上运行中"所给 diff 在…之前截断"是 L2 判 unsure/fail 的主要原因，
而整批 10 个 PR 的证据（约 105 KB）对每条规则都重复发送；按规则取证据后约 11 KB + 所引 PR 的完整 diff。

## 2026-09-30 adapter 生命周期开关检查（kb init）
`lifecycle_flip.check_lifecycle_flip(base_yaml, head_yaml, allowed=)`：两版 manifest 解析后删去允许的键路径，
其余必须完全相等（比较解析值，注释与格式可保留）；`FLIP_KEYS` = `knowledge_lifecycle.enabled/mode`，
`CALIBRATION_KEYS` = `knowledge_lifecycle.calibration_set`。`check_flip_to_shadow` 另要求 head 为
`enabled: true` 且 `mode` 为 shadow（缺省即 shadow）。知识 L1 的白名单只含 `knowledge/`，adapter 这一处改动由它单独校验；
调用方还需在 head adapter 上跑 `config.parse_lifecycle`。测试：`test_kb_lifecycle_flip.py`。

## 2026-09-30 模型回复解析
`models.parse_json_object` 取裸 JSON 对象或最后一个 ```json 围栏块，用 `json.loads(strict=False)`：字符串里的原始控制字符（多行值里的换行、制表符，例如图示）按数据接受，不再把结构正确的回答判为 `ModelUnavailable`。测试：`test_kb_intake_gate.py`。
