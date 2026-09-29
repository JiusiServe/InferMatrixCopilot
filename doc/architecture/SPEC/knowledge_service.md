# knowledge_service/ — provider curation components

<!-- verified-against: 2026-09-29 -->

The provider owns knowledge curation beneath the public SDK v1 facade.
`KnowledgeCurator` composes four domain components over one explicit work
checkout: `CatalogMixin` discovers contained owner rule pages and their
capacity; `PromptMixin` validates and bounds evidence and fences it as data;
`ProposalMixin` validates source/page/rule identity and binds accepted
proposals to page digests; `ApplyMixin` performs locked append-only writes,
fixed validators and byte-exact rollback. `common` contains shared syntax,
bounds, hashes, errors and lock capability.

No component imports a CLI/MCP transport or ReviewBot, calls a model, clones,
pushes, or publishes. The host owns evidence collection, model calls, retries,
local commits and proposal export. The public `sdk.v1.knowledge` module only
re-exports the curator and validator error. Existing proposal IDs, errors,
wire projections, validator order and rollback behavior are compatibility
contracts across the move.

Knowledge Ops API 2.0 sits beside the v1 curator and does not change it:
`lifecycle` parses rule pages (byte-exact) and their `kb:rule` footers,
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
outbox item, control record, publisher ack) never verifies for another. It
needs only `cryptography`.

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
