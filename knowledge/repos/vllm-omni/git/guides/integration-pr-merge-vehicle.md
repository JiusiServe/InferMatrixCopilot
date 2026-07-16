# Integration PR / Merge Vehicle Gate

来源：Greyfield Next V1 收尾中，先开 #35-#40 窄 PR，再开 #41 integration PR，过程中出现 draft/ready 状态漂移、PR body/docs stale、CodeRabbit success 被误读、过量状态机修复、sub-agent review 后置等问题。最终 #41 合入可接受，但过程违反框架规则：经验先写进了个人 Codex memory，而不是本仓框架。

## 0. 适用场景

出现任一情况时必须读本页：

- 同一目标被拆成多个 PR、stacked PR 或历史切片 PR。
- 准备创建 / ready / merge 一个 integration PR、release-candidate PR 或 evidence PR。
- PR body / docs 同时描述多个 issue、多个 head、多个 harness 证据。
- 有 superseded PR、draft PR、retarget、stacked base、merge-order 决策。

## 1. 先选唯一 Merge Vehicle

多 PR 工作流开跑前先回答：

```text
Primary merge vehicle: <PR number / branch>
Historical or review-only PRs: <PR list>
Merge path not chosen: <why not>
Integration-only fixes: <must not lose if using narrow path>
```

硬规则：

- 一组相关 PR 只能有一个主 merge path。
- 选择 integration PR 后，窄 PR 只能作为历史切片或 review reference；不能继续并行当主线。
- 选择窄 PR 顺序合入后，integration PR 必须保持 audit-only，且列出必须 cherry-pick / rebuild 的 integration-only fixes。
- stacked PR 的 base 不是目标分支时，禁止直接当最终落地 PR merge；要么 retarget/rebase，要么走 integration PR。

## 2. Ready 前状态审计

把 draft PR 转 ready 之前，先跑状态审计：

```text
PR body stale wording: draft / WIP / should stay draft / skipped because draft
Docs stale wording: draft evidence / draft integration PR / release claim
Bot comments: review actually ran? rate limited? skipped?
Open PR graph: which PRs will be superseded?
CI meaning: what did each check actually execute?
```

禁止：

- ready PR body 仍写 “draft PR / should stay draft”。
- 把 bot/check 的 `success` 当成 review 已完成，未读实际评论。
- 用 “draft evidence” 表达证据边界；改写成 `PR-local evidence` / `unmerged evidence` / `release-candidate evidence`。

## 3. PR Body 是当前合同

Integration PR body 必须描述当前事实：

- 当前 head 或合入策略。
- 当前验证命令和哪些是当前 head 后跑的。
- 哪些证据没跑，为什么没跑。
- 哪些不能 claim，例如 release complete / real provider complete。
- 若选择 integration PR 为主合入路径，明确窄 PR 合后要关闭或已 superseded。

避免易漂移词：

- 少写 `draft`，除非当前 GitHub 状态真是 draft。
- 少写 “will rerun / expected to run”，run 完后立刻改成实际结果。
- 不把旧 head 证据写成当前 head 证据。

## 4. 新增修复准入

每个新补丁先分类：

| 类别 | 是否进当前 PR | 标准 |
| --- | --- | --- |
| Blocker | 必须进 | 不修会坏用户路径、CI、合入或验收证据 |
| Review finding | 通常进 | 明确 P1/P2，改动小且验证明确 |
| Evidence/doc consistency | 进 | PR 状态、body、docs、check 口径与当前事实不一致 |
| State-machine polish | 默认不进 | 只是内部状态更整齐，不影响用户完成任务 |
| Nice-to-have | 不进 | 可独立 PR，不阻塞当前目标 |

边缘状态动手前必须问：

```text
这会不会让用户失败、误解、卡住？
是否有验收缺口或 P1/P2 finding？
不修它，当前 merge vehicle 是否仍能成立？
```

任一答案不成立，就先不修。

## 5. Sub-agent 前置

Integration PR ready / merge 前至少做三类只读 review：

- Code review：找行为 bug、race、harness 假阳性 / 假阴性。
- Merge-readiness review：判断该合哪个 PR、按什么顺序合、哪些 PR superseded。
- Evidence/docs review：查 PR body、docs、manifest、CI 口径是否过 claim 或 stale。

规则：

- sub-agent 只读，不改 PR body/comment、commit、push、merge。
- 不把 sub-agent `OK` 当证据；主 agent 必须复核其 source、diff、CI 和 PR 状态。
- merge-readiness review 应在 ready/merge 前做，不要等状态已经改完才补救。

## 6. 合入前决策格式

合入前给用户或自己写最短决策：

```text
Decision: merge now / merge after X / do not merge yet
Vehicle: #<PR>
Why this vehicle: <stacked base / integration-only fixes / CI / evidence>
Blockers: none / list
Not release claim because: <missing real env / post-merge rerun / target branch evidence>
After merge: <close superseded PRs / rerun commands>
```

没有这个决策，不 merge。

## 7. 合入后动作

Integration PR merge 后立刻：

1. Comment on superseded narrow PRs: `Superseded by #<integration PR>, merged into <target branch>.`
2. Close superseded PRs.
3. Check open PR list is empty or only expected PRs remain.
4. Run post-merge checkpoint on target branch before release claim.

最低 post-merge checkpoint 按项目实际脚本选择；不能用 PR-head green 替代 target branch green。

## 8. Real-env Evidence 边界

缺真实 env 的 provider / LLM / TTS / GPU harness 可以不阻塞 merge，但必须阻塞 release claim。

PR body 和 docs 必须写清：

- fake/local harness 覆盖了什么；
- real-env harness 未跑的 env 名称；
- 何时才能 claim release complete。

## 9. 反例信号

看到这些信号，立即停下来重做 merge-vehicle audit：

- “这个 PR 先 draft，现在 ready，但 body 还说 draft。”
- “CodeRabbit success，但评论说 rate limit / skipped。”
- “窄 PR 和 integration PR 都准备合。”
- “合入前又顺手修一个状态机一致性。”
- “sub-agent 是 merge 前最后一分钟才开的。”
- “合完了但没关闭 superseded PR。”
- “PR head 绿，所以说 main/release 也完成。”
