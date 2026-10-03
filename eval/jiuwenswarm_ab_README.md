# JiuwenSwarm 文档与知识库 A/B 评估复现

本评估比较原项目作者资料（A）与当前 JiuwenSwarm 知识库（B）为 GLM‑5.3 PR 评审提供的上下文。脚本、精简报告在 `eval/`；源码检出、原始文档、提示词、模型回复和完整调用日志保存在仓库外。

本次结果：[中文对比报告](knowledge-depth/jiuwenswarm-original-docs-comparison-cn-20261003.md)、[紧凑 JSON](knowledge-depth/jiuwenswarm-original-docs-comparison-cn-20261003.json)。72 次终态、55 次有效评审、12 次独立评分；报告保留失败及条件统计的限制。

## 固定输入与统计边界

- 知识源码 SHA：`f0a69728c96b5961d993449f1a901cbd2f4dac5b`。
- B 为已合并 [PR #290](https://github.com/JiusiServe/InferMatrixCopilot/pull/290) 的知识内容：552/553 项认可（207 严格、345 轻量），生产文件结构覆盖 2043/2199。认可率不等于 PR 缺陷判断准确率。
- A 为同一源码 SHA 的 488 篇作者 Markdown，包含 `.doc_project_maintainer`、`docs/` 及嵌套开发、测试、发布文档。包装只添加路径与来源元数据，保留原文；映射评审的结论不会注入 A。
- 已归档快照摘要：A `f228db8ed02d00a8a5be13edf3f8a785810cebdbd35e19a65c068476e3c313e5`；B `f98af18e075181bdd60c1342b03bedc83ee9577ab4201d60ac8ddf78b3a16ab5`。每篇文档另有内容 SHA。
- 12 个 PR 的不可变 head 在 [准备脚本](jiuwenswarm_ab_prepare.py) 的 `HEADS` 中。主样本为 #7641、#7642、#7645、#7647、#7649、#7650、#7651、#7675（8 PR、48 次）；#7639、#7654、#7655、#7656 是旧分叉（4 PR、24 次），单列为探索结果。

主样本直接基于知识 SHA 且 head 提交晚于它；旧分叉的 head 更早，最新知识可能包含分叉后的相关实现。不能仅用 PR 创建时间消除这种时效性影响，也不能将 72 次重复当作 72 个独立 PR。

## 准备与冻结

从仓库根运行，使用安装了本项目依赖的 Python、已认证订阅的 Zcode 与 Codex CLI。评估拒绝 API/fallback；实际账单没有报告时保持未知。以下路径示例用于**新建**外部复现目录；已有归档只读使用，改变输入或脚本后另建目录。

```bash
export PYTHONPATH=src:.
AB_PYTHON=/tmp/kb-owner-knowledge-venv/bin/python
AB_SOURCE=/absolute/path/to/pinned-jiuwenswarm
AB_STATE=/absolute/path/outside/repository/jiuwenswarm-docs-ab-reproduction
AB_KB=/absolute/path/outside/repository/knowledge-pr290
AB_STUDY="$AB_STATE/evaluation-v2"
AB_PIN=f0a69728c96b5961d993449f1a901cbd2f4dac5b

git fetch origin refs/pull/290/head
git worktree add --detach "$AB_KB" 58279d334cd827adb631891a760bb14efe376420

"$AB_PYTHON" eval/jiuwenswarm_docs_compare.py \
  --root "$AB_KB" --source "$AB_SOURCE" --state "$AB_STATE" \
  --pin "$AB_PIN" --map-native --workers 4

"$AB_PYTHON" eval/jiuwenswarm_ab_prepare.py \
  --run-root "$AB_STATE" --source "$AB_SOURCE" --knowledge-checkout "$AB_KB"

"$AB_PYTHON" eval/jiuwenswarm_ab_prepare.py \
  --run-root "$AB_STUDY" --derive-pr-bases-from "$AB_STATE/campaign.json"
```

[文档脚本](jiuwenswarm_docs_compare.py)要求源码干净且精确位于固定 SHA，生成 `mapping/inventory.json`、A/B 快照及原文映射。当前知识目录需与归档 B 版本一致；完整脚本、CLI、快照及源码摘要由后续 identity 绑定。

评估脚本从包含本次改动的 checkout 执行，B 库存从独立 PR290 checkout 读取。JiuwenSwarm 源码需要足够 Git 历史来计算旧分叉的 merge-base；浅克隆应先补全历史，不能用固定 target 冒充 fork 点。

`--derive-pr-bases-from` 是本次评估的规范步骤：对每个冻结 head 计算 `git merge-base <固定 target> <head>`，生成 **merge-base→head** diff，保留 target/base/head 三者。GitHub 的 `pull.base.sha` 是目标分支 tip，不能直接当作所有 PR 的 diff 起点。该步骤从原准备记录派生新目录，保留旧实验输入与错误设置的历史记录。

原文映射每功能一次独立 Codex 评审，共 79 次；每包最多 8 篇文档、24,000 字符原文及 16,000 字符定位源码。只有 15/79 包完整包含其候选正文，故 361 支持、18 冲突、174 未知是**有界证据映射**，未知不能解释为全库缺失。原文支持与源码一致性分别统计，不能直接与当前认可率相减。

已归档 79 次映射使用当时的默认 Codex transport：精确提示词、回复和用量记录存在，完整 CLI 原生事件流存在缺口。后续脚本改用 `ArchivedCodexTransport`，不能据此声称旧记录已有完整事件流。历史引用校验的修正仅重放归档回复；`--normalize-map-only` 不调用模型，保留初始结果与逐维未知，不重抽样。

## 独立基准、评审与盲评

先通过 Codex 封闭只读 MCP 预检，然后冻结源码缺陷基准；再启动 GLM。完成预检后冻结执行代码，处理中不修改已绑定的脚本、CLI 或快照。

```bash
"$AB_PYTHON" eval/jiuwenswarm_ab_judge.py preflight \
  --campaign "$AB_STUDY/campaign.json" --preflight-tag initial

"$AB_PYTHON" eval/jiuwenswarm_ab_judge.py truth \
  --campaign "$AB_STUDY/campaign.json" --workers 4

"$AB_PYTHON" eval/jiuwenswarm_pr_review_ab.py preflight \
  --campaign "$AB_STUDY/campaign.json"

"$AB_PYTHON" eval/jiuwenswarm_pr_review_ab.py run \
  --campaign "$AB_STUDY/campaign.json" --workers 13 \
  --truth-manifest "$AB_STUDY/private-codex/truth-manifest.json"

"$AB_PYTHON" eval/jiuwenswarm_pr_review_ab.py collect \
  --campaign "$AB_STUDY/campaign.json"

"$AB_PYTHON" eval/jiuwenswarm_ab_judge.py score \
  --campaign "$AB_STUDY/campaign.json" --workers 4 \
  --reviews-manifest "$AB_STUDY/reviews-manifest.json"

# 最终更新上游观测，并定稿 final-validation.json、ci-code-checks.json 等补充输入。
"$AB_PYTHON" - "$AB_STATE" <<'PY'
import sys
from pathlib import Path
from eval.jiuwenswarm_ab_report import refresh_upstream
refresh_upstream(Path(sys.argv[1]))
PY

"$AB_PYTHON" eval/jiuwenswarm_ab_archive.py \
  --state "$AB_STATE" --output "$AB_STATE/raw-trace-index.json"

"$AB_PYTHON" eval/jiuwenswarm_ab_report.py \
  --state "$AB_STATE" --study "$AB_STUDY" --output-dir "$AB_STATE/report"
```

[Codex 基准与盲评](jiuwenswarm_ab_judge.py)仅通过 `read_task/source_read/source_grep` 读取固定 base/head 代码，关闭 shell、网络及继承 MCP。基准阶段不读取 A/B 文档、GLM 回复或 GitHub 讨论。`truth-manifest.json` 冻结全部 12 个样本及失败记录，GLM 的 `run` 必须绑定该文件；它不向 GLM 暴露基准。

[GLM 评审器](jiuwenswarm_pr_review_ab.py)使用 Zcode GLM‑5.3、相同提示词与检索算法，初始最多两页、累计 6,000 字符知识预算；后续文档搜索/读取共享余量。每次评审最多 60 次源码调用，每次结果最多 24,000 字符，超时 1,800 秒；源码工具禁止读取文档以绕过知识预算。13 workers 共享启动间隔与限流冷却，交错 A/B 顺序，运行 12×2×3=72 次；两组原生 bootstrap 预检另外记录，不计入 72 次。

盲评随机标签隐藏知识组及重复序号，逐条给出 TP、FP、unknown 或非缺陷建议。真实但未在冻结基准中的缺陷单列，不回填基准；unknown 不算 FP。三重复先在 PR/组内平均，再做 PR 层面的宏平均；主样本与旧分叉分开报告。基准是独立自动评审确认的部分缺陷集，召回率不能声称覆盖全部真实缺陷。源码只读，不执行上游测试。

started/completed/failed 检查点及身份摘要约束恢复；Codex 基准与评分失败不重抽样，GLM 的无效回复与中断不重抽样。GLM 仅对 transport_failed 最多补一次外层原生 CLI 尝试，保留两次日志及累计源码、文档预算；Zcode 原生请求内部的 429 退避另计，不称作重新抽样评审；恢复时不会重新派发已存在的未完成 attempt。`collect` 保留失败分母，`score` 要求全部 72 个槽位均有终态记录。报告分开列原生耗时、排队、检索及端到端耗时，并保留未报告的用量、费用和不可计算指标。

## 外部归档与离线检查

本次完整归档的逻辑名称为 `.kb-jiuwenswarm-docs-ab-20261003/`，规范 PR 评审目录为其 `evaluation-v2/`。`mapping/` 保存原文包、逐功能回复、校验派生结果、运行脚本副本与调用记录；`snapshots/` 保存知识快照；`evaluation-v2/items/` 保存实际注入文本、工具读取、模型回复及 Zcode 原生 stdout/stderr/JSONL 事件；`evaluation-v2/private-codex/` 保存冻结基准、匿名评分、原生记录及盲标签映射。旧根目录实验和基础设施失败记录留作溯源，不能混入 v2 指标。

[报告脚本](jiuwenswarm_ab_report.py)可对已有归档离线重建精简中文 `.md/.json`，输入摘要随报告保存。`extraction-timing.json`、`upstream-freshness.json`、`final-validation.json` 是独立补充输入；缺失时保持未知。知识提取耗时由 [提取时间脚本](jiuwenswarm_extraction_timing.py)的 `--archive/--output` 汇总，与本次 PR 评审耗时分别统计。

[归档索引脚本](jiuwenswarm_ab_archive.py)只在 72 个评审槽位与 12 个盲评记录均为终态后生成 `raw-trace-index.json`。索引按路径排序，仅保存相对路径、字节数与 SHA256；覆盖映射、文档快照及 v2 原生记录，排除运行缓存、临时锁、派生汇总和索引自身。索引与完整原始材料都留在 Git 外，不内联认证信息或模型原文。

`baseline-pr290.json`、`ci-code-checks.json`、提取时间、上游观测与最终验证属于交付补充输入，可在交付前更新。顺序须为**最终刷新与验证 → 生成索引 → 生成报告**；索引之后不再运行 `--refresh-upstream`。任何已索引补充文件的修改，都需要重新生成索引并重建报告，避免报告绑定过期摘要。

```bash
"$AB_PYTHON" -m pytest -q \
  test/test_jiuwenswarm_docs_compare.py test/test_jiuwenswarm_ab_prepare.py \
  test/test_jiuwenswarm_pr_review_ab.py test/test_jiuwenswarm_ab_judge.py \
  test/test_jiuwenswarm_ab_diagnostics.py test/test_jiuwenswarm_ab_archive.py \
  test/test_jiuwenswarm_ab_report.py
```

上述测试不调用模型；覆盖固定输入、真实 merge-base、工具隔离、预算、引用校验、恢复与计数。完整原生日志保存在外部归档，提交到 Git 的报告使用精简指标和摘要。

## 协议修复后复测

原始 72 次结果及其失败保持不变。复测通过 [准备工具](jiuwenswarm_ab_retest.py)核对已发布报告的哈希绑定、12 个 PR 的固定源码、文档快照及模型预算，再创建独立外部目录。复用原来评审前冻结的 Codex 问题清单，包含 #7656 的未知状态；只重绑定实验元数据，问题正文、数量和原始记录另存哈希，不重新抽样问题基准。

```bash
AB_PREVIOUS=/absolute/path/outside/repository/jiuwenswarm-docs-ab-original/evaluation-v2
AB_RETEST=/absolute/path/outside/repository/jiuwenswarm-docs-ab-retest
AB_STUDY="$AB_RETEST/evaluation-v2"

"$AB_PYTHON" eval/jiuwenswarm_ab_retest.py prepare \
  --previous-study "$AB_PREVIOUS" --run-root "$AB_STUDY"

"$AB_PYTHON" eval/jiuwenswarm_ab_judge.py preflight \
  --campaign "$AB_STUDY/campaign.json" --preflight-tag protocol-fix

"$AB_PYTHON" eval/jiuwenswarm_pr_review_ab.py preflight \
  --campaign "$AB_STUDY/campaign.json"

"$AB_PYTHON" eval/jiuwenswarm_pr_review_ab.py run \
  --campaign "$AB_STUDY/campaign.json" --workers 13 \
  --truth-manifest "$AB_STUDY/private-codex/truth-manifest.json"

"$AB_PYTHON" eval/jiuwenswarm_pr_review_ab.py collect \
  --campaign "$AB_STUDY/campaign.json"

"$AB_PYTHON" eval/jiuwenswarm_ab_judge.py score \
  --campaign "$AB_STUDY/campaign.json" --workers 4

"$AB_PYTHON" eval/jiuwenswarm_ab_retest_report.py \
  --previous-study "$AB_PREVIOUS" --study "$AB_STUDY" \
  --output-dir "$AB_RETEST/report"
```

此次修复统一评估提示词与严格输出校验：所有评审条目都有字符串锚点，无法提供精确锚点时为空字符串；重复候选合并在 findings 中。目录检索允许安全的 `.` 根目录别名与一个尾部 `/`，文件读取和路径边界保持严格。提示词工具使用连续游标，完整读完后才开放源码与文档工具。原生预检实际分页读取大型 PR 的上下文和完整 diff，验证修复后的目录写法及规范空评审格式。

预检不计入正式 72 次；预检失败则停止正式派发。代码和输入冻结后不修改协议；无效内容和格式不补采样、不事后晋升。新报告同时列前后完成率、有效评审的条件精确率、有限基准召回和速度，记录提示词协议变化与服务排期差异，不能将前后差额单独归因于知识库。
