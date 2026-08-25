# InferMatrixCopilot

**Playbook 驱动的仓库维护 copilot**：用一条自然语言命令审查 PR、rebase 分支、
调试 CI、回答 issue，并维护一套随上游发版持续更新的仓库知识。vLLM-Omni 是
第一个目标仓库（adapter zero），但核心与仓库解耦——新仓库通过
`adapters/<repo>/` 与 `knowledge/` 接入，不需要改 `src/`（仓库中立由护栏
测试强制，已知遗留泄漏被清单封顶且只能变少）。

一个仓库，两种形态，共享同一套知识与治理：

| | **Direct（默认）** | **Strict / CLI** |
|---|---|---|
| 谁读代码 | 你当前 Coding Agent（Codex / Claude Code / Cursor）自己的模型 | InferMatrixCopilot 配置的模型 |
| 入口 | `/imreview` `/imdesign` `/imcifix` `/imupdate` | `infermatrix-copilot -p "…"` |
| 服务端跑模型 | 否（零模型、零状态，同步返回知识路由与审查门禁） | 是（隔离子进程跑完整工作流） |
| 需要模型 Key | 否 | 是（或订阅制 harness 后端） |

安全模型贯穿两种形态：**默认一切 dry-run**（`ALLOW_PUSH=0` /
`ALLOW_POST=0`），权限由任务类型推导、自然语言永远无法扩权，force push 只有
`--force-with-lease`，保护分支无论如何不会被推送。

## 安装

**Direct（在 Coding Agent 里用，最常用）：**

```bash
git clone git@github.com:JiusiServe/InferMatrixCopilot.git
cd InferMatrixCopilot

./install-mcp.sh --repo-path /path/to/vllm-omni    # macOS / Linux
install.cmd --repo-path D:\path\to\vllm-omni       # Windows（双击也可以）
```

安装器识别本机的 Codex / Claude Code / Cursor，注册 MCP 与四个 Skill，并创建
`~/.infermatrix-copilot/.env`。装完**重启 Agent**：Codex 用 `$imreview`，
Claude Code / Cursor 用 `/imreview`。Direct 不需要模型密钥。对话中 Agent
没有主动调用时，直接说：

```text
Use InferMatrixCopilot in Direct mode to review this PR.
```

**Strict / CLI（独立运行）：**

```bash
bash install.sh               # venv + editable 安装 + ./infermatrix-copilot 包装器
./infermatrix-copilot doctor  # 预检：每个 ✗ 都打印确切的修复命令
```

Strict 需要在 `.env` 里填一种模型 Key（`ANTHROPIC_API_KEY` 或
`OPENAI_API_KEY`，各自支持可选 `*_BASE_URL`）和 `REPO_PATHS`。完整配置、
常用 flag 与排查见 [`QUICKSTART.md`](QUICKSTART.md)。

## 快速上手 1 · 审查（review）

Direct——在你的 Agent 里：

```text
$imreview https://github.com/vllm-project/vllm-omni/pull/5172   # Codex
/imreview                                # Claude Code / Cursor：当前 PR 或本地改动
或者直接说：帮我审核一下这个 pr 5172，用知识库
```

过程：固定 PR 快照并先报告 head / CI / mergeability →
`review(mode="direct")` 返回至多 3 条精确知识路由 + 审查门禁 → Agent 并行读
源码、跑验证 → 完成门 `validate_direct_review` → 单条带文件行号的结论。
默认只在当前对话输出，**不发布 GitHub 评论**。

Strict——完整后台工作流（多 lens ensemble 评审，跑在 pin 到 PR head 的
PR-time checkout 上）：

```bash
./infermatrix-copilot -p "review pr 5172"
./infermatrix-copilot -p "review pr 5172" --plan-only        # 只看计划不执行
./infermatrix-copilot -p "review pr 5172" --performance      # 用高能力模型档
```

产物落在 `~/.infermatrix-copilot/runs/run-*/RUN_REPORT.md`。发布到 GitHub 是
双闸：请求显式带 post 意图**且** `ALLOW_POST=1`，缺一不可。在 MCP 宿主里也
可以跑 Strict：说 "Use InferMatrixCopilot in Strict mode to review …"，拿到
`run_id` 后用 `get_review_status` / `get_review_result` 轮询。

## 快速上手 2 · rebase

把单个 PR rebase 到最新 base（fork-aware checkout → rebase → 逐模块验证 →
patch review 门 → with-lease push）：

```bash
./infermatrix-copilot -p "rebase pr 5134"
./infermatrix-copilot -p "rebase pr 5134, then review it"   # 复合命令自动排队
```

冲突先交给受治理的 agent 解决，解不开就 abort 并升级（`ESCALATION.md`，
退出码 3），绝不留下半成品树。push 同样双闸：PushPolicy 允许**且**
`ALLOW_PUSH=1`，否则是一次 dry-run，准确显示"本来会做什么"；force 只有
`--force-with-lease`，且只针对 PR 的 head 分支。

全仓库 rebase（夜跑）：

```bash
./infermatrix-copilot --playbook repo-rebase --yes
```

`repo-rebase` playbook 是 **locked** 状态：委托给已验证的外部 5 阶段编排器，
copilot 负责监控、进度事件与失败升级，永不改编。`repo-rebase-native` 是并排
验证中的原生分解候选，对 planner 不可见，只能 `--playbook` 点名运行。

## 快速上手 3 · 更新知识库

上游发版或目录变化后，用 `imupdate` 把**结构事实**（模型清单、registry、
deploy、路径路由、source pin）同步进知识库——只改 InferMatrixCopilot 的
知识，不动目标仓库：

```text
$imupdate vllm-omni                              # Codex：仓库名或别名
/imupdate /path/to/vllm-omni                     # Claude Code / Cursor：本地 checkout
$imupdate https://github.com/vllm-project/vllm-omni v0.26.0rc1   # URL + 目标 tag/SHA
或者直接说：帮我更新一下 vllmomni 仓库最新到知识库
```

流程：从 `release_baseline.yaml` 的 `audited_sha` 对比目标版本 → 只读机器
审计（Git 对象、registry、pipeline、deploy、路径路由、source pin）→ Agent
只更新审计报告能证明的结构事实 → enforce、知识检查与相关测试验收。它不会
根据一次 diff 自动编造 owner 规则，也不自动 commit、push 或开 PR。审计项
明细见 [`doc/contributing/release-maintenance.md`](doc/contributing/release-maintenance.md)。

手工贡献知识（新增规则页、调整路由）遵循
[`doc/knowledge/CONTRIBUTING.md`](doc/knowledge/CONTRIBUTING.md)，整批改完
跑两个校验器：

```bash
python knowledge/tools/check_knowledge_tree.py
python knowledge/tools/check_wiki_lint.py
```

另外两条知识通道由 run 自动积累、人工晋升：仓库 profile
（`-p "profile the repo"` 建立，fact 必须引证据）与 skills / debug memory
（agent 只能提案 candidate，人类晋升）。

## 其它能力

- `imdesign` —— 写代码前的协同设计包（问题 / 方案 / 接口变化 / 验证计划），
  不自动改代码。
- `imcifix` —— 从 GitHub issue 出发：本地复现 → 最小修复 → 针对性验证；
  默认不 commit、不 push、不发评论。
- CI 调试与 issue：`-p "debug pr 5134, report only"`、
  `-p "answer issue 4842, do not post"`、`-p "triage recent open issues"`。
- 新仓库接入：`-p "profile the repo"` 建立 draft profile，零 `src/` 改动。

## MCP 接口（由 Agent 调用，平时用 Skill 命令即可）

- `review(target, repo="vllm-omni", mode="direct", post=false,
  review_depth="", title="", body="", changed_files=[], repo_path="")`：
  Direct 返回至多 3 条精确知识路由和审查门禁；Strict 返回 `run_id`。
  `repo_path` 可临时指定 Strict 使用的本地 checkout。
- `validate_direct_review(subtraction_signal, subtraction?,
  minimality_proof?, final_comment_count=1, evidence_head_sha)`：Direct 最终
  输出前的完成门。`evidence_head_sha` 必须是本次审查固定的 head 提交；普通
  小修改传 `subtraction_signal="none"`，存在新增或扩张结构时传
  `"triggered"` 并提供减法项或最小性证明。
- `get_review_status(run_id)` / `get_review_result(run_id, offset=0)`：
  查看 Strict 后台任务进度、轮询结果（长报告按 `next_offset` 续读）。
- `update_knowledge(repo="vllm-omni")`：只返回知识贡献入口
  `doc/knowledge/CONTRIBUTING.md`，**不是** `imupdate` 的发版审计器。
- `doc_search(query, repo="vllm-omni", limit=20)` /
  `doc_read(path, repo="vllm-omni", offset=0)`：搜索并阅读模型/组件知识页。

## 安全默认值一览

| 行为 | 默认 | 打开它需要 |
|---|---|---|
| git push | dry-run | `ALLOW_PUSH=1` 且 PushPolicy 允许 且 非保护分支 |
| 发 PR 评论 / issue 回复 | 关 | `ALLOW_POST=1` 且 请求显式带 post 意图 |
| force push | 仅 `--force-with-lease` | 无法放宽 |
| 未知仓库 | 生成 DRAFT adapter 后停下 | 人工审核后激活 |
| 高风险 manifest 段（`repo`/`upstream`/`push`） | agent 写入被拒 | 只能人工改 |

## 更多文档

**[`doc/README.md`](doc/README.md) 是文档地图**——一行一条，按你要做的事挑一篇：

| 你要做什么 | 看这篇 |
|---|---|
| CLI 完整上手（配置、命令、排查） | [`QUICKSTART.md`](QUICKSTART.md) |
| 完整了解它是什么、能做什么 | [指南](doc/GUIDE.md)（概览 / 功能 / 使用 / 开发 / playbook / step / tool / 性能） |
| 在 Codex / Claude Code / Cursor 里装上用 | [宿主端](doc/guide/hosts/README.md) |
| 安装细节，或接入其他 MCP 客户端 | [MCP 安装](doc/guide/mcp.md) |
| 让 Strict 跑在订阅或别的模型上 | [后端](doc/guide/backends.md) |
| 独立执行 issue / CI / rebase 任务 | [autonomous workflow](doc/guide/autonomous-workflow.md) |
| 维护这个仓库本身 | [开发者入口](DEVELOPMENT.md) |

> **宿主 ≠ 后端**：`claude-code` / `codex` / `cursor` 这三个名字两边都出现，
> 方向相反。宿主提供模型给你用（Direct），后端是 copilot 拿去用的模型
> （Strict）。

其余：[发版漂移审计](doc/contributing/release-maintenance.md) ·
[知识库贡献规范](doc/knowledge/CONTRIBUTING.md) ·
[知识维护示例](doc/knowledge/maintainer-walkthrough.md) ·
[评测结论](doc/evaluation/README.md)
