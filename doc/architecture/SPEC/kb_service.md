# kb_service/ —— 规范

<!-- verified-against: 2026-09-29 -->

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


## 2026-09-28 发布器
`publisher` 在 GPU 盒上以仓库负责人的 gh 登录运行（`kb publish`），是知识 PR 唯一的 GitHub 写入方。
- 每轮：经 SSH（或本地目录）读取签名控制记录，过期即整轮不动；对每个 outbox 项执行 `check_item`（签名、
  过期、代际、暂停、控制记录与**发布器自己的适配器配置**同时为 `auto_merge`），执行后先在本地记录结果，
  再写回发布器密钥签名的 `kb-ack`（字段：item_id、kind、changeset_id、ok、pr、head_sha、branch、error）。
- 幂等：已执行的项只重发 ack（服务收取 ack 后删除该项）；完成记录原子写入，损坏的记录移到 `.corrupt` 并等人处理，
  绝不猜测是否已执行；`open_pr` 只复用 head 恰为重建提交的已打开 PR（companion 还须是 draft）；
  提交由签名内容在 `base_sha` 上用临时索引重建，日期取自该项，重试得到同一 SHA；分支已存在且内容不同则拒绝，
  绝不覆盖。路径必须是受治理的知识页面（`knowledge/{repos/<r>,general}/**.md|yaml`，无 `..`）。
- 恢复：`post_verdict` 只在未暂停、当前代际下签发，发布它时先移除 `kb:hold` 标签并确认已移除，再发布评论，使评论触发的预检不再因暂停标签失败。
  失败的 `pause`/`close` 不回执，留在 outbox 中每轮重试直到成功；格式错误的控制记录或项目记入 trace 并跳过。
  SSH 读取或回执失败只记入 trace，不终止进程；完成记录保留，下一轮重发回执而不重复动作。
- 动作：`open_pr`/`open_companion_pr`（始终 draft）、`post_verdict` 与 `enqueue`/`update_branch`（先核对 PR
  仍打开且 head 未变；`enqueue` 先把 draft 转为 ready，再 `gh pr merge --auto --match-head-commit`）、
  `pause`（程序 P：出队 → 关闭自动合并 → 转 draft，确认已是 draft，再加 `kb:hold`）、`close`。
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
`merge.advance` 记录每次签发判定的时间（`verdict_issued_at`）与入队时间（`queued_at`），并处理不再能通过门禁的判定：
- 判定签发超过 48 小时（有效期 72 小时）：`verdict_posted` 直接回到 `pr_open` 重签；`queued` 以及入队 2 小时仍未合并的
  PR **不按计时释放队列名额**，而是先下发 `pause`（出队 + 转 draft），其回执把它送回 `pr_open`，再重签并重新入队。
- 尚未过期的 `enqueue` 项未回执时不重签（其回执决定：进入 `queued` 后走上面的出队路径）。
- PR 阶段 `kb-gate` 失败（只看签发当前判定之后发布的状态），按描述（验证器的第一个问题）分类：暂停清单/不可达/
  验证器错误、我们自己暂停留下的 `kb:hold` 等瞬时问题 → 等待；判定过期或
  缺失 → 重签；上下文改变、一致性页面变化、无法干净合并、清单不符 → **重建**：只有持有租约的调度器执行，在当前 main
  上重新应用同样的操作并重新过质量门，暂存为 `rebuild` 变更集（证据带 `rebuild of <旧 id>` 标记，与暂存原子写入，
  中断后再次执行会找到它而不会重复暂存）。只有重建**通过**质量门才取代旧 PR：旧变更集进入 `superseding`，`close` 项
  过期即重发，直到观测到 PR 已关闭才记为 `superseded`（不计入被人工推翻的熔断）；重建未通过、操作无法再应用或没有
  可重放的操作 → `rebuild_failed` 并转人工，旧 PR 保持打开。其他失败（变更本身有问题）→ `gate_failed` 并转人工一次。

## 2026-09-28 外部知识 PR（来源④）与 human-approved 判定
`external.poll_external`（调度器按 intake 间隔、全局未暂停时调用，需持有租约）处理知识仓库中**非服务创建**、非 draft、
触碰 `knowledge/` 的打开 PR，每个 head 在每条路径（auto / human）上只评一次（auto 路径转人工的 head 在维护者审批后
无需新推送即可按 human 路径重新评判）：
- `kb:human-approved` 且知识维护者（main 上 `.github/kb-gate/` 的 CODEOWNERS）对**当前 head** 的审批仍有效（同一人的
  后续审阅覆盖之前的）→ 只在受治理页面上跑 L1（审批替代白名单与 L2，不替代其余 L1）→ 签发 `human-approved` 判定，
  绑定这些审阅。
- 否则全部路径须为受治理页面 → 以**当前 main 加上 PR 改动**完整过质量门（L1、L2、一致性）→ 通过则签发 `auto` 判定。
  PR 的前像必须等于 main（否则队列落地的改动与签名不同），不等则请作者 rebase。
  与服务自己的 PR 一样，`auto` 判定要求当前通过的评审校准；否则记为 `calibration_required`，校准恢复后才重新评判
  （期间不重复调用付费评审）。维护者审批读取全部分页的审阅，后续页上的撤回同样生效。
- 其余情况（跨多个仓库、白名单外路径未经审批、L1 失败、质量门未通过）转人工，每个 head 一次。
- 判定清单直接取自 git（`merge-base..head` 的完整原始 diff），覆盖白名单外路径；`context_base_sha` 为评判时的 main。
- 暂存为 `external` 变更集后走普通合并流程。作者推送新 head → `head_changed`（不转人工）；上下文失效 → `stale_context`；
  两者都在下次轮询时重新评判。签发后维护者撤回审批（最新审阅不再批准该 head）→ 转人工并下发 `pause`（出队 + draft）；
  在 pause 回执成功前保持原状态（继续占用队列名额），回执后才记为 `approval_withdrawn`，剩余审批不会让同一 head 重新暂存。外部 PR 没有操作列表，L1 发现的退役/删除规则写入 `retirements`/`purges`，合并后同样进入
  退役账本（之后的发版巡检据此 purge）。作者关闭自己的 PR 不计入熔断。只触碰非受治理知识路径的 PR 归入 `general`（若其接收
  人工 PR），否则归入第一个接收人工 PR 的仓库。

## 2026-09-28 每日合并审计
`audit.audit_main`（调度器每 24 小时）沿 main 的 first-parent 历史从上次审计的提交向后检查：每个相对第一父改动了
`knowledge/` 的提交，都必须是账本已记录合并的变更集。证明只看结构、从不信提交信息：提交 SHA 为某变更集的 merge SHA，或它是双亲
合并、第二父正是某个已合并变更集记录的 head（合并队列落地的形态），且它对知识的改动恰好就是该 head 的改动（改动的每个
知识路径都在该 PR 的改动内且内容与 head 相同；夹带额外改动的合并同样被发现）。否则（admin bypass、直接推送、账本漏记）对其涉及的仓库暂停自动合并（改动在仓库范围之外 → 全局暂停）、
出队其打开的知识 PR 并转人工；不在 `auto_merge` 的仓库只写 `unrecorded_merge` trace。首次运行只记录基线；晚于
2 小时宽限期的提交留到下次，避免与调度器记录合并赛跑。暂停逻辑与熔断共用 `Scheduler._pause`。

## 2026-09-29 暂停清单端点
`holds_server`（`kb holds-server`）只以 `GET/HEAD /holds.json` 提供 `<state_dir>/public/holds.json`（`Cache-Control: no-store`），
其余路径一律 404，不列目录、不跟随路径、不接受写入；清单尚不存在时返回 503（门禁视为不可达并失败关闭）。默认只绑定
`127.0.0.1`，由 bot 主机的反向代理加 TLS 后对外，URL 写入 `.github/kb-gate/config.json` 的 `holds_url`。

## 2026-09-29 暂停以观测确认
`pause_open_prs` 记录每个暂停请求的时间与原因。回执只代表发布器的说法：状态 `paused` 的变更集只有在 GitHub 显示该 PR
为 draft 时才记为已确认（draft 不能在合并队列中，也不能再次入队）；否则重发 `pause`。请求 5 分钟后仍未回执或未确认 →
转人工一次，附出队与 `gh pr ready <n> --undo` 命令。`kb status` 报告每个仓库 `pause_unconfirmed` 数量，熔断/回滚在其归零
前不算完成；`kb resume` 清除这些记录。

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
标签，进入人工队列；发布器拒绝在其上执行 `post_verdict`/`enqueue`（ready 与合并只能由人完成），且拒绝白名单外路径
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
