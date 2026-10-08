# knowledge_service/ — provider curation components

<!-- verified-against: 2026-10-08 -->

Pinned source identities and depth markers accept full SHA-1 or SHA-256 Git
commits. Evidence bodies, stored hashes and native approval semantics remain
unchanged; accepting a wider object identity never renews an old approval.

`PinnedObserver` reuses successful Git tree and blob reads by full commit SHA
and path within one observer. Concurrent readers share its lock and cache;
mutable references are resolved on each call before choosing a cache key, and
returned top-level sets cannot mutate cached values. A fresh observer reads
again, read failures are never cached, and live PR metadata is always fetched.
This avoids repeated Git subprocesses during checkpoint evidence replay while
preserving the same source text and evidence hashes.

The provider owns knowledge curation beneath the public SDK v1 facade.
`KnowledgeCurator` delegates to four function modules over one explicit work
checkout: `catalog` discovers contained owner rule pages and their
capacity; `prompt` validates and bounds evidence and fences it as data;
`proposals` validates source/page/rule identity and binds accepted
proposals to page digests; `apply` performs locked append-only writes,
fixed validators and byte-exact rollback. `common` contains shared syntax,
bounds, hashes, errors and lock capability.

Workspace, limits and locks are explicit function inputs, not inherited shared
attributes. The public curator signatures, proposal identities and byte-exact
results remain unchanged. Successful SDK application is a local candidate,
not an independent semantic admission or publication. See
[knowledge lifecycle layers](../knowledge-lifecycle.md).

No component imports a CLI/MCP transport or ReviewBot, calls a model, clones,
pushes, or publishes. The host owns evidence collection, model calls, retries,
local commits and proposal export. The public `sdk.v1.knowledge` module only
re-exports the curator and validator error. Existing proposal IDs, errors,
wire projections, validator order and rollback behavior are compatibility
contracts across the move.

Knowledge Ops API 2.0 sits beside the v1 curator and does not change it:
`lifecycle` parses rule pages (byte-exact) and their `kb:rule` footers,
and owns the shared depth format, intact-prose reader and safe source-path
syntax used by retrieval and init/audit; upstream proof verification stays in
`kb_service.knowledge_depth`.
`ops.apply_operations` applies typed add / edit_same_meaning / replace / retire
/ purge changes with their mechanical consequences, and `l1` is the
deterministic half of the quality gate (`check_tree`, `check_changeset`). The
three modules need only the standard library and PyYAML and import nothing else
from the package.

`release_audit` loads a repository's release-audit plugin from its adapter
directory and runs it with a baseline generated for the audited SHA pair:
knowledge-document issues are enforced, adapter-baseline maintenance is
reported as reconciliation.

`signing` provides Ed25519 envelopes whose signature covers a purpose tag plus
the canonical JSON payload, so a signature made for one purpose (gate verdict,
outbox item, control record, publisher ack, reconciliation plan, supervised
reconciliation receipt) never verifies for another. Plans use
`kb-reconciliation-plan`; only revalidated receipts use the distinct
`kb-reviewed-reconciliation` purpose, and neither can be replayed as an
automatic gate verdict or publisher action. It
needs only `cryptography`.

`containment` implements the opt-in consumer protocol independently of knowledge
snapshots and physical releases: signed fresh policies, durable monotonic
high-water state, private provider issuance and usage receipts, availability
checks and a shared installation/publication fence. Invalid signatures, stale
policy, replay or unavailable issued knowledge fail closed. It does not create
authority decisions or model judgements. Signing also separates containment,
authenticated transport, maintenance resolution, human case, calibration, drill
and short-lived merge authorization purposes. See
[containment.md](knowledge_service/containment.md).

## 2026-09-28 verdict
`verdict` defines the signed gate verdict (`kb-gate-verdict/1`): identity
(repository, PR, exact head, nonce, 72-hour issue window), the complete patch
manifest compared by pre/post git blob IDs independent of any base SHA, the
passing per-block judgements, the consistency judgement with the page hashes it
saw, upstream fact attestations and the decision source (always `auto` since
v8). `check_binding` rejects replay on another PR, head or window. Standard
library only.

## 2026-09-28 T1 索引修复
L1 的索引检查允许为目录中已存在但未列入索引的页面补链接（巡检 T1 修复），新页面仍必须被链接。

## 2026-09-30 kb init 的 L1 bootstrap 模式
`l1.check_changeset(..., bootstrap=)` 只供 `kb init`（`kb_service/init_stages.py`）：允许在新目录新建
`_index.md`、修改共享的 `repos/_index.md`；`l1.check_index_links(base, head)` 检查 init 改动的索引链接。
细节见 [l1](knowledge_service/l1.md)。服务门禁与发布器从不传 `bootstrap`。

## 2026-09-28 知识验证器（v8：发布器本地门禁）
`gate_verifier.verify_change(ctx, pr=, head_sha=, pre=, post=, final=, effective_base=, verdict=)` 是发布器本地门禁
（`kb_service.local_gate`）在合并前与合并后运行的检查；v7 的仓库端 `kb-gate` 工作流、`.github/kb-gate/` 验证包、
merge group 逐段验证、暂停清单与 `human-approved` 审批核对已于 2026-09-29 删除。用 git 对象读取 PR（从不检出或执行）。
- 知识变更通过条件：PR 打开且 head 未变；来源为 `auto`；清单与实际变更（与 base 无关）相等；
  L1 在 PR 自身改动与将要落地的树上都通过；块表与 L1 分块完全一致且全部 pass、一致性判定覆盖相同 owner 目录且页面哈希与落地树
  相同、`context_base_sha..有效 base` 未改动上下文集合；本变更退役/删除的规则 ID 在落地树中不得被引用
  （main 可能新增了引用）；知识目录外仍引用退役规则则需配套 PR。
- 不变量：失败即关闭——带上游事实证明的判定失败（服务目前不签发事实）；未触碰 `knowledge/` 的变更总是通过。
  判定的签名与绑定由调用方（`local_gate.check_verdict`）验证。
- 测试：`test_kb_local_gate_verifier.py`（重放/过期/伪造/非 auto 来源、清单漏项、块表不全、混合路径与可执行位、
  跨仓库、上下文失效、落地树中的悬空引用）。
## 2026-09-29 verify_change 供本地门禁调用
`verify_change` 只接受调用方已验签与绑定的判定（`verdict=`），不再从 PR 评论查找判定，也不读暂停清单；
暂停由签名控制记录表达。

## 2026-09-29 上游事实（facts）
`facts` 从变更涉及的规则中抽取可解析的上游声明：`^[PR #N]` 引用（PR 已合并）、反引号中首段为上游仓库顶层条目的路径
（文件或目录存在）与 `path::Symbol`（文件中以 def/class/赋值定义了每个点分量）；首段不是顶层条目的片段路径、`..` 与
`...` 段不算声明。`active` 规则的声明必须成立；退役规则的声明只按观测记录，但退役证据中的 PR 必须已合并。
`attest(claims, observer)` 在上游当前 head 上观测，返回 `upstream={repository, sha}`、事实列表与问题；超过 200 条声明拒绝。
`recheck(upstream, facts, observer)` 由发布器调用：仓库一致、SHA 为 40 位、每条事实重新观测后逐字段相等，
签名了不成立的必需事实或格式错误均为问题；上游不可读（未知 SHA、网络、API 错误）抛 `FactsError`，由调用方重试。
仅标准库。`gate_verifier.verify_change` 不再拒绝带事实的判定（由发布器的 `recheck` 复核）。

## 2026-09-30 钉点声明（pinned_claims）
`pinned_claims` 供 `kb init` 使用：`PinnedObserver` 在本地克隆上以固定钉点实现 `facts.Observer`（另有
`is_ancestor`），`check_rules` 在钉点上观测规则声明且要求引用的 PR 已合并进钉点历史，`Evidence` /
`check_evidence` 把行区间绑定到内容哈希。服务与发布器的 `facts` 路径不变。详见
[pinned_claims.md](knowledge_service/pinned_claims.md)。
