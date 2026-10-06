# 知识服务 —— Copilot 全权负责知识库

> **一览**
> | | |
> |---|---|
> | **状态** | 🚧 分阶段落地。已合并：Direct 路由多仓库化与按请求知识视图（#203）、Knowledge Ops API 2.0 与 L1（#204）、generated-baseline 发版审计（#205）、服务核心（#206）、intake 与质量门（#207）；本 PR 加入合并流程、快照激活、发版巡检与调度器；本页随后续 PR 更新 |
> | **做什么** | 知识的创建、维护、退役、删除与发版巡检全部在 Copilot；每次变更经质量门，通过后由发布器在本地门禁复核合并结果再合并；ReviewBot 只读消费 |
> | **怎么开关** | 每个仓库在 `adapters/<repo>/manifest.yaml` 的 `knowledge_lifecycle`（人工审阅的高风险段）中设置 `enabled` 与 `mode: shadow\|auto_merge` |
> | **设计** | 经 GPT-6 sol 评审批准的设计文档（知识库管理重构设计，多仓库，v8） |
> | **硬边界** | bot 主机不持有任何 GitHub 写凭据；所有 GitHub 写动作由 GPU 盒上的发布器以 owner 账号执行，且只执行服务签名、未过期、代际有效的 outbox 项；私有上游仓库只能 shadow，不产生任何公开产物 |

## 组成

| 部分 | 位置 | 职责 |
|---|---|---|
| 仓库配置与注册表 | `kb_service/config.py` | 解析每个 adapter 的 `knowledge_lifecycle`；`general/` 由服务配置 |
| 账本 | `kb_service/ledger.py` | 单个 SQLite（`$KB_STATE_DIR/kb.db`），所有表按 `repo` 分区；单实例租约；代际号 |
| 签名 | `knowledge_service/signing.py` | Ed25519 信封，按用途（判定、outbox、控制记录、回执）隔离签名 |
| outbox | `kb_service/outbox.py` | 服务写签名项与控制记录；发布器执行前用 `check_item` 复核 |
| CLI | `infermatrix-copilot kb …` | `keygen`、`status`、`pause`、`resume`、`control` |

## 代际与暂停

任何暂停、熔断、回滚或切回 `shadow` 都会使该仓库（或全局 `*`）代际 +1，并立即重签
控制记录。发布器只执行代际与当前一致、未过期（`merge` 30 分钟，其余 24 小时）且控制记录签发
不超过 10 分钟的项；`close` 与 `open_revert_pr` 总是可执行。
只有 `auto_merge` 仓库会产生非停止类写动作：`shadow` 只记录“将要做什么”，不开 PR、
不发评论；模式变化本身也会使代际 +1。
发布器是知识 PR 唯一的合并方，所以暂停只需停止下发 `merge`，并在合并前复读控制记录：
不需要出队、转 draft、暂停标签或 GitHub 端的暂停清单。

## 运维

```bash
infermatrix-copilot kb keygen --out /etc/infermatrix-kb/service.pem   # 公钥交给发布器（KB_SERVICE_PUBKEY）
export KB_SIGNING_KEY=/etc/infermatrix-kb/service.pem KB_STATE_DIR=/var/lib/infermatrix-kb
infermatrix-copilot kb status
infermatrix-copilot kb pause --repo vllm-omni --reason "rollback drill"
infermatrix-copilot kb resume --repo vllm-omni
```

依赖：`pip install "infermatrix-copilot[kb]"`（cryptography）。

## Intake 与质量门

```bash
infermatrix-copilot kb run --playbook kb-intake --repo vllm-omni   # 一次 intake（shadow 下只记录）
infermatrix-copilot kb calibrate --repo vllm-omni                  # 评审模型校准；不达标不得切 auto_merge
```

模型：`KB_GENERATOR`（默认 `claude-code:claude-opus-5-5`）、`KB_JUDGE`（默认
`codex:gpt-6-sol:medium`）。生成器可显式配置一个备用模型：

```bash
export KB_GENERATOR_FALLBACK=zcode:GLM-5.3
```

主生成器缺少 CLI、未登录、调用失败、超时或回复无法解析时，同一次请求尝试备用生成器一次；
两者都不可用则事件继续排队。评审模型不切换，备用生成器也必须与评审来自不同家族。
每次尝试记录实际 provider/model，备用调用还记录 `fallback_from`；变更集注明实际生成器。
未设置此变量时只调用主模型。schema 错误仍由原有修复流程处理；带花费阈值的调用不切换，
因为预算只为主模型预留且 Zcode 无法执行阈值。
调用记录位于 `$KB_STATE_DIR/traces/records/`。

`KB_JUDGE` 可把评审切到其他后端（如 `zcode:GLM-5.3`，与 GPT-6 Sol 并列的受支持后端）。
zcode 评审的 `:effort` 后缀无效——推理档位由全局 `ZCODE_REASONING_LEVEL`（默认 `max`）决定；
zcode 无花费阈值能力，评审超时或不可解析按既有 fail-closed 语义记 `human`，绝不自动合并。
同一后端既起草又评审（GLM 生成 + GLM 评审）时，必须显式设置 `KB_JUDGE_FAMILY_WAIVER=1`：
每次启动记录警告，且该评审标签的校准记录必须重跑（`kb calibrate`），否则 auto_merge 保持
`calibration_required`。评审侧的可进化面在 `kb_service/judge_tuning.py`（提示词、rubric 措辞、
聚合策略、上下文预算）；`gate.py` 是受保护文件，只经人审 PR 变更。

运行经验（来源②）：`pr_debug` 的已验证修复记录经 `KB_BUGFIX_DIR`（同机，与运行侧 `KNOWLEDGE_INTAKE_DIR`
配为同一目录）与 `KB_BUGFIX_MAILBOX`（异机，`owner/repo#N`，只接受 `KB_BUGFIX_AUTHORS` 列出的作者）进入 intake。

## 调度、合并、激活与巡检

```bash
infermatrix-copilot kb serve                 # 常驻调度器（systemd），持有单写入租约
infermatrix-copilot kb activate              # 立即激活知识仓库 main 的快照
infermatrix-copilot kb rollback --to <sha>   # 回指到较早的快照（下一请求生效）
```

合并流程（v8）：`open_pr` 回执 → 为该 PR 的精确 head 签发判定，随 `merge` 项交给 GPU 盒发布器 → 发布器在
`main` 与 PR head 的合并树上运行本地门禁，通过才 `gh pr merge`（每仓库同时至多 1 个）→ 合并后激活新快照。
本地门禁拒绝的变更从不合并：上下文变化则在当前 main 上重建；服务自己的变更被质量门或本地门禁拒绝时，由生成器按
理由精炼后整体复检，至多 2 轮，仍失败则留在人工队列（不合并）。他人的知识 PR 每天检查一次：结果写在该 PR 上唯一一条
“知识质量门”评论里（原地更新），未通过则不合并，作者修改后次日复检。
有人绕过门禁直接合并/推送知识变更时，服务立即暂停该仓库、停止激活新快照、告警，并开出撤回 PR（不自动合并）；
合并精确的撤回 PR 并 `kb resume` 后恢复，被撤回的内容会作为新候选重新过门禁；也可以用 `kb accept-unknown <sha>` 让该提交本身完整通过门禁后保留它（通过才算处置，仍需 `kb resume`）。发版巡检在上游新 release 后运行
T1/T2/T3 与 purge，每个规则页一个变更集，全部经过质量门。

初始化、增加 owner 目录、修改顶层入口或校验器时，负责人合并的 PR 可能包含普通自动规则门禁不接受的路径。
`kb reconcile-reviewed` 是这种已合并历史的显式操作员接收流程：以服务密钥签名，先生成可检查的计划，再重新核验后写入不可变回执。
要求当前 main 的完整 SHA、当前 active 的连续 first-parent 历史、每个知识提交对应的唯一真实已合并 PR、
允许的负责人 merger 与认证操作员，以及精确 PR head 上指定的当前成功检查。保留实际 review 状态，不虚构 APPROVED。
在固定目标树上必须通过两个知识校验器与真实快照加载、格式、哈希和路由检查；缺失、失败或进行中的检查均拒绝。

```bash
infermatrix-copilot kb reconcile-reviewed --plan reconciliation.json \
  --target <full-main-sha> --allow-merger <owner-login> --require-check suite \
  --reason 'Owner-authorized recovery of merged initialization and administration'
# 检查计划中的提交、PR、操作员、检查和校验哈希后，再明确执行：
infermatrix-copilot kb reconcile-reviewed --apply reconciliation.json
infermatrix-copilot kb status
infermatrix-copilot kb resume --all
infermatrix-copilot kb activate
```

需提供 `KB_GITHUB_READ_TOKEN` 以核验认证操作员（沿用负责人的现有只读 API 凭据）。计划本身不产生信任；
apply 重新核验所有证据，main 或 active 改变、证据变化时要求新计划。两个 pin 不变时重复 apply 返回同一回执。
回执在 `$KB_STATE_DIR/reconciliations/`，应随恢复备份保留；审计、激活和控制记录每次直接校验其签名与完整提交范围，
不缓存此类信任。新知识提交仍会阻塞激活；删除或破坏回执不能续签旧信任。
接收不写 `disposed:`，不解除暂停，不更改 shadow/auto_merge，也不替代自动候选的完整质量门。
已有异步接受、撤回或待 intake 候选的提交必须先处理完，不能由此流程绕过。

评审服务读取知识：将 `KNOWLEDGE_ROOT` 指向 `$KB_STATE_DIR/active`。


## 本地门禁（取代 v7 的仓库端 `kb-gate`）

仓库端没有知识门禁的工作流、验证包、CODEOWNERS、合并队列或 ruleset：发布器在合并前于
`merge-tree(main, head)` 上运行 `knowledge_service.gate_verifier.verify_change`（签名判定、清单一致、L1、
逐块与一致性判定、上下文未变），通过才合并，合并后再检查落地的提交。只接受 `auto` 判定，
没有 `human-approved` 路径：改动受治理页面以外路径的知识 PR 不会被自动合并，作者会在发现评论里被要求拆分。
绕过发布器直接合并或推送的知识变更由每轮审计发现、暂停并撤回（见上文）。
规则对上游的声明（引用的 PR 已合并、写全的上游路径与 `path::Symbol` 存在）在质量门中对钉住的上游 SHA 证明并签入判定；
发布器合并前用自己的上游镜像与 `gh api` 逐条复核，不一致或上游不可读则不合并，连续 24 小时失败转人工。

切换前的负责人步骤：`main` 必须允许发布器直接合并（不开合并队列、不开自动合并）；
按设计 §P3 的顺序关闭 v7 遗留的自动合并并卸载 v7 发布器。

## 发布器（GPU 盒）

发布器以仓库负责人现有的 `gh` 登录执行服务签名的 outbox 项，写回签名回执。凭据不离开 GPU 盒。

```bash
infermatrix-copilot kb keygen --out ~/.infermatrix-copilot/kb-publisher.pem   # 发布器密钥；公钥给服务的 KB_PUBLISHER_PUBKEY
export KB_SERVICE_PUBKEY=/path/to/service.pub          # 服务公钥（kb keygen 输出的一行）
export KB_PUBLISHER_KEY=~/.infermatrix-copilot/kb-publisher.pem
export KB_PUBLISHER_GIT_AUTHOR='Name <email>'         # 知识 PR 提交的作者
export KB_PUBLISHER_STATE=/data/<owner>/kb-publisher  # 必须在负责人目录下（gh 包装器按目录选择登录）
infermatrix-copilot kb publish --remote bot-host:/path/to/kb-state --once   # 只记录（dry-run）
ALLOW_POST=1 ALLOW_PUSH=1 infermatrix-copilot kb publish --remote bot-host:/path/to/kb-state   # 常驻
```

每轮还会拉取 bot 主机上每周生成的留痕归档（`$KB_STATE_DIR/archive/`），哈希校验通过后保存到
`$KB_PUBLISHER_STATE/archive/`，作为离机副本。

没有 `ALLOW_POST=1` 时只把将要执行的动作写入 `$KB_PUBLISHER_STATE/traces/publisher.jsonl`；推送分支还需要
`ALLOW_PUSH=1`。控制记录超过 10 分钟未更新（服务可能宕机）时整轮不执行任何动作。

## 留痕、回放与数据集（trace/1）

知识服务的每次模型调用（含失败）、每个质量门判定与每个事后结果都写入 `$KB_STATE_DIR/traces/`
（JSONL + 内容寻址 blob + SQLite 索引，写入前脱敏）。RB 通过 `sdk.v1.TraceStore` 使用同一 schema。

```bash
infermatrix-copilot kb traces --changeset <id>                      # 查询记录
infermatrix-copilot kb replay --record <id> --model codex:gpt-6-mini:low   # 用便宜模型重放一次调用
infermatrix-copilot kb export --out judge.jsonl                     # 导出数据集（自动剔除校准集相关调用）
```
