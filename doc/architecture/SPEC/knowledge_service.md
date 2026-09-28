# knowledge_service/ — provider curation components

<!-- verified-against: 2026-09-28 -->

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
from the package, so the kb-gate verifier bundle can vendor them.

`release_audit` loads a repository's release-audit plugin from its adapter
directory and runs it with a baseline generated for the audited SHA pair:
knowledge-document issues are enforced, adapter-baseline maintenance is
reported as reconciliation.

`signing` provides Ed25519 envelopes whose signature covers a purpose tag plus
the canonical JSON payload, so a signature made for one purpose (gate verdict,
outbox item, control record, hold list, publisher ack) never verifies for
another. It needs only `cryptography` and is vendored by the kb-gate verifier.

## 2026-09-28 verdict
`verdict` defines the signed kb-gate verdict (`kb-gate-verdict/1`): identity
(repository, PR, exact head, nonce, 72-hour issue window), the complete patch
manifest compared by pre/post git blob IDs independent of any base SHA, the
passing per-block judgements, the consistency judgement with the page hashes it
saw, upstream fact attestations and the decision source (`auto` or
`human-approved` with its reviews). `check_binding` rejects replay on another
PR, head or window. Standard library only; vendored by kb-gate.

## 2026-09-28 T1 索引修复
L1 的索引检查允许为目录中已存在但未列入索引的页面补链接（巡检 T1 修复），新页面仍必须被链接。

## 2026-09-28 kb-gate 验证器
`gate_verifier` 是仓库端必需检查 `kb-gate`。`tools/build_kb_gate_bundle.py` 把它和
`l1`、`lifecycle`、`ops`、`signing`、`verdict` 原样复制到 `.github/kb-gate/`（附
`requirements.lock` 按哈希固定依赖，`MANIFEST.sha256` 为包内文件哈希），工作流只从该目录运行。
- PR 阶段（`pull_request_target`/带判定标记的 `issue_comment`/手动）：用 git 对象读取 PR（从不检出
  或执行），在 `merge-tree` 结果上跑 L1，把 `kb-gate` 状态发布到**已验证的**那个 head。
- merge group 阶段：`main..head` 的 first-parent 链每段必须是双亲合并提交；第二父按 open PR 的
  head 唯一反查；每个触碰 `knowledge/` 的段以其第一父为有效 base 独立验证，最后在整棵落地树上跑 L1。
- 知识变更通过条件：签名有效且绑定本仓库/PR/head、在签发有效期内；清单与实际变更（与 base 无关）
  相等；`auto` 要求块表与 L1 分块完全一致且全部 pass、一致性判定覆盖相同 owner 目录且页面哈希与落地树
  相同、`context_base_sha..有效 base` 未改动上下文集合；`human-approved` 要求绑定的审阅仍为
  APPROVED、针对当前 head、由 `.github/kb-gate/` 的 CODEOWNERS（知识维护者）之一给出，且标签仍在。
  另需无 `kb:hold`、签名暂停清单新鲜（≤10 分钟）且未命中；清单缺失/伪造/过期一律失败。
  `human-approved` 豁免自动合并白名单（`knowledge/tools`、`skills`、脚本、混合 PR），页面生命周期 L1 只作用于
  受治理页面，其余 L1 不豁免；
  本变更退役/删除的规则 ID 在落地树中不得被引用（排在后面的 PR 或 main 可能新增了引用）。
  暂停清单按范围匹配：`repos/<r>/` 对应仓库名 `<r>`，`general/` 对应 `general`。
- 不变量：失败即关闭——缺公钥、缺 `holds_url`、无法归属的 merge group、带上游事实证明的判定都失败；
  未触碰 `knowledge/` 的变更不读取任何判定或暂停清单，总是通过。git < 2.38 时 PR 阶段用临时索引做
  只接受单侧改动的三方合并（更严格，不更宽松）。
- 测试：`test_kb_gate_verifier.py`（重放/过期/伪造、清单漏项、块表不全、混合路径与可执行位、暂停清单、
  上下文失效、状态发布、人工审批撤销、merge group 逐段与前序同目录 PR、验证包新鲜与自包含、独立运行）。
