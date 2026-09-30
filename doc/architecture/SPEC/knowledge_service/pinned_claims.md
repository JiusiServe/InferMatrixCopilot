# knowledge_service/pinned_claims.py —— 规范

<!-- verified-against: 2026-09-30 -->

`LOC ~200 · 在钉住的上游 SHA 上核验规则声明与代码证据（kb init §9.1） · refactor-status: new`

## 职责
- `PinnedObserver(repo_dir, repository, pin, pull=)`：在本地 git 仓库（bare 或非 bare）上实现
  `facts.Observer`，`head()` 固定返回钉住的 SHA；`top_level` / `path_exists` / `file_text` 读 git
  对象，`pull(n)` 默认走 `gh api repos/{repo}/pulls/{n}`（可注入；任何查询失败——没有 `gh`、网络错误、非对象回答——都归一为 `FactsError`，原有的 `FactsError` 原样抛出）。另加协议之外的
  `is_ancestor(sha)`：`sha` 是钉点或其祖先（非 40 位 SHA、镜像中不存在的对象、非 commit 对象为 False；候选对象损坏（`cat-file --batch-check` 同样输出 missing 但 stderr 报解包错误），或 git 读不到钉点历史（`merge-base` 此时也以 1 退出、只在 stderr 报 `Could not read`）时抛 `FactsError`，不把读失败当成"合入在钉点之后"）。钉点必须是 40 位
  且在仓库中存在的提交，否则构造即抛 `FactsError`。
- `check_rules(rule_texts, observer)`：对每条（活跃）规则用 `facts.claims_in` 抽取声明，按
  `facts.observe` 在钉点观测；每条声明必须成立，`^[PR #N]` 还必须已合并进钉点历史
  （`is_ancestor(merge_commit_sha)`）。返回以规则 ID 开头的问题列表。
- `Evidence(path, start, end, sha256)`、`evidence_for(observer, path, start, end)`、
  `check_evidence(entries, observer)`：把钉点上某文件的行区间（1 起、闭区间）绑定到内容哈希，
  并能复核：文件存在、区间在文件内、哈希一致。

## 公开契约
哈希口径：`str.splitlines()` 切行（`\n`、`\r\n`、缺末尾换行视为相同），取 `start..end` 行以
`\n` 连接再补一个 `\n`，UTF-8 编码后 SHA-256。`Evidence.to_dict()/from_dict()` 用于 init 记录。

## 不变量
- 与服务端 `facts.attest` 的声明抽取完全一致（同一 `claims_in`），只是观测点从上游 head 换成钉点。
- 不修改 `facts.Observer` 协议，不影响服务与发布器。
- 上游不可读（git 失败、未知提交、PR 查询失败）抛 `FactsError`，不当作"声明不成立"。

## 边界 —— 不属于这里
不写任何文件、不调用模型、不决定 init 各阶段如何处理问题（阻断或进清单由调用方决定）。

## 依赖（允许）
标准库 + `facts`；外部命令仅 `git` 与（默认 `pull`）`gh`。

## 测试
`test_kb_pinned_claims.py`（临时 git 仓库：钉点前后文件、符号、PR 合并先后与未合并、证据区间与
哈希、换行风格无关、非法钉点）。
