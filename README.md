# InferMatrixCopilot

让 Codex、Claude Code、Cursor 等 Coding Agent 按**目标仓库的项目知识**
审查和维护代码，而不只是做一遍通用检查。上游发版或目录变化后，还能更新
这套知识，避免 Agent 继续按旧路径和旧清单工作。

它提供四个常用 Skill：

- `imreview`：审查 PR 或本地改动时，找到相关模型、组件和维护者规则，让审查
  不只停留在通用检查。
- `imdesign`：写代码前理清问题、方案、接口边界和验证计划。
- `imcifix`：从 GitHub issue 出发，在本地复现、最小修复并针对性验证。
- `imupdate`：上游变化后更新模型清单、registry、deploy、路径路由和
  source pin，避免继续按旧知识工作。

copilot 本身与具体仓库无关：每个仓库的知识住在自己的 adapter
（`adapters/<repo>/`）和知识切片（`knowledge/repos/<repo>/`）里，playbook
按能力匹配任意仓库，接入新仓库不需要改核心代码（见「其它能力」的新仓库
接入）。vLLM-Omni 是第一个接入的仓库（adapter zero），也是本文全部示例；
afd-plugin 已按同样方式作为第二个仓库接入。

先选使用方式：

| | **Direct（默认）** | **Strict / CLI** |
|---|---|---|
| 谁读代码 | 当前 Coding Agent 自己的模型 | InferMatrixCopilot 配置的模型 |
| 入口 | `$imreview` 等宿主 Skill | `infermatrix-copilot -p "…"` |
| 模型凭据 | 不需要 API Key | 模型 API Key，或订阅制 harness 后端 |
| GitHub 写入 | 结果留在当前对话，不发布 | 默认关闭，相关请求和安全闸均允许后才执行 |

Direct 是最常用的默认方式：InferMatrixCopilot 只提供知识路由和审查门禁，
不启动第二个模型。Strict 则在隔离子进程中运行完整工作流，可审查 PR、调试 CI、
rebase 分支和处理 issue。两种方式共享同一套知识和安全规则；对外 push 与发布
评论默认关闭。

## 安装

**Direct（在 Coding Agent 里使用）：**

```bash
git clone git@github.com:JiusiServe/InferMatrixCopilot.git
cd InferMatrixCopilot

# macOS / Linux
./install-mcp.sh
./install-mcp.sh --repo-path /path/to/vllm-omni

# Windows
install.cmd
install.cmd --repo-path D:\path\to\vllm-omni
```

Windows 也可以直接双击 `install.cmd`。`--repo-path` 可选，用于同时写入 Strict
使用的本地 checkout。安装器会识别本机的 Codex、Claude Code 和 Cursor，注册
MCP 与四个 Skill，并创建 `~/.infermatrix-copilot/.env`。

安装后重启 Agent。Codex 使用 `$imreview`，Claude Code 和 Cursor 使用
`/imreview`；Direct 不需要 API Key。若 Agent 没有主动调用，直接说：

```text
Use InferMatrixCopilot in Direct mode to review this PR.
```

**Strict / CLI（独立运行）：**

```bash
# 创建 venv、editable 安装和 ./infermatrix-copilot 包装器
bash install.sh
./infermatrix-copilot doctor  # 预检：每个 ✗ 都打印确切的修复命令
```

`install.sh` 会在仓库根从模板生成 `.env`（已被 git 忽略，永不覆盖已有的）；
Strict 还要在其中配置 `REPO_PATHS`。使用 API 后端时，填写
`ANTHROPIC_API_KEY` 或 `OPENAI_API_KEY`，各自支持可选的 `*_BASE_URL`；
也可以改用订阅制 harness 后端。API 配置、常用 flag 与排查见
[`QUICKSTART.md`](QUICKSTART.md)，订阅后端配置见
[后端指南](doc/guide/backends.md)。

## 快速上手 1 · 审查

Direct——在你的 Agent 里：

```text
# Codex：审查指定 PR
$imreview https://github.com/vllm-project/vllm-omni/pull/5172

# Claude Code / Cursor：审查当前 PR 或本地改动
/imreview

或者直接说：帮我审核一下这个 PR 5172，用知识库
```

Agent 会先固定 PR 快照并报告 head、CI 和 mergeability，再取得至多 3 条相关
知识路由和审查门禁，读取源码、运行验证，最后在当前对话输出一条带文件和行号的
审查结论。Direct 不发布 GitHub 评论。

Strict——运行完整 CLI 工作流：

```bash
./infermatrix-copilot -p "review pr 5172"
./infermatrix-copilot -p "review pr 5172" --plan-only        # 只看计划不执行
./infermatrix-copilot -p "review pr 5172" --performance      # 用高能力模型档
```

Strict 在固定到 PR head 的 checkout 上运行，并按改动规模和风险选择审查深度。报告写入
`~/.infermatrix-copilot/runs/run-*/RUN_REPORT.md`。也可以在 MCP 宿主中说
“Use InferMatrixCopilot in Strict mode to review …”；拿到 `run_id` 后，用
`get_review_status` 和 `get_review_result` 轮询。

## 快速上手 2 · rebase

把单个 PR rebase 到最新 base。工作流会识别 fork，检出 PR 分支，完成 rebase、
逐模块验证和 patch review；推送另经安全闸：

```bash
./infermatrix-copilot -p "rebase pr 5134"
./infermatrix-copilot -p "rebase pr 5134, then review it"   # 复合命令自动排队
```

冲突先交给受治理的 Agent 解决；解不开就 abort 并升级，写出
`ESCALATION.md`，以退出码 3 结束。push 需要 PushPolicy 允许并且
`ALLOW_PUSH=1`；否则只显示“本来会做什么”。force 只使用
`--force-with-lease`，且只针对 PR 的 head 分支。

全仓库 rebase（夜跑）：

```bash
./infermatrix-copilot --playbook repo-rebase --yes
```

`repo-rebase` 是 **locked** playbook：它委托给已验证的 5 阶段编排器，必须
原样复用，永不改编或重新生成。`repo-rebase-native` 是与它并排验证的原生分解
候选，对 planner 不可见，只能用 `--playbook` 点名运行。

## 快速上手 3 · 更新知识库

上游发版或目录变化后，用 `imupdate` 把**结构事实**（模型清单、registry、
deploy、路径路由、source pin）同步进知识库——只改 InferMatrixCopilot 的
知识，不动目标仓库：

```text
# Codex：仓库名或别名
$imupdate vllm-omni

# Claude Code / Cursor：本地 checkout
/imupdate /path/to/vllm-omni

# URL + 目标 tag/SHA
$imupdate https://github.com/vllm-project/vllm-omni v0.26.0rc1

或者直接说：帮我更新一下 vllmomni 仓库最新到知识库
```

流程：从 `release_baseline.yaml` 的 `audited_sha` 对比目标版本，执行只读机器
审计（Git 对象、registry、pipeline、deploy、路径路由、source pin）；Agent
只更新审计报告能证明的结构事实，再以 `enforce` 模式审计、知识检查和相关测试
验收。它不会根据一次 diff 自动编造 owner 规则，也不自动 commit、push 或开 PR。
审计项明细见[发版维护](doc/contributing/release-maintenance.md)。

手工贡献知识（新增规则页、调整路由）遵循
[`doc/knowledge/CONTRIBUTING.md`](doc/knowledge/CONTRIBUTING.md)，整批改完
跑两个校验器：

```bash
python knowledge/tools/check_knowledge_tree.py
python knowledge/tools/check_wiki_lint.py
```

## 其它能力

- `imdesign`：写代码前生成协同设计包（问题、方案、接口变化和验证计划），
  不自动改代码。
- `imcifix`：从 GitHub issue 出发，在本地复现、最小修复并针对性验证；
  默认不 commit、不 push、不发评论。
- Strict 还可调试 CI 和处理 issue：`-p "debug pr 5134, report only"`、
  `-p "answer issue 4842, do not post"`、`-p "triage recent open issues"`。
- 新仓库接入：`-p "profile the repo"` 建立 DRAFT profile；接入内容放在
  `adapters/<repo>/` 和 `knowledge/repos/<repo>/`，不需要修改 `src/`。

## MCP 接口

平时使用 Skill 命令即可；以下接口由 Agent 调用。`repo` 参数默认 adapter
zero（`vllm-omni`），可传任何已接入仓库的短名、别名或 owner/name：

- `review(target, repo="vllm-omni", mode="direct", post=false,
  review_depth="", title="", body="", changed_files=[], repo_path="")`：
  Direct 返回至多 3 条精确知识路由和审查门禁；Strict 返回 `run_id`。
  `repo_path` 可临时指定 Strict 使用的本地 checkout。
- `validate_direct_review(subtraction_signal, subtraction?,
  minimality_proof?, final_comment_count=1, evidence_head_sha)`：Direct 最终
  输出前的完成门。`subtraction_signal="none"` 时不得附带减法证据；传
  `"triggered"` 时必须提供减法项或最小性证明。最终评论必须恰好一条，
  `evidence_head_sha` 必须是本次审查固定的 head 提交。
- `get_review_status(run_id)`：查看 Strict 后台任务的步骤和进度。
- `get_review_result(run_id, offset=0)`：轮询 Strict 结果；长报告按
  `next_offset` 继续读取。
- `update_knowledge(repo="vllm-omni")`：只返回知识贡献入口
  `doc/knowledge/CONTRIBUTING.md`，**不是** `imupdate` 的发版审计器。
- `doc_search(query, repo="vllm-omni", limit=20)`：搜索模型或组件知识。
- `doc_read(path, repo="vllm-omni", offset=0)`：读取搜索到的知识页。

## 安全默认值一览

| 行为 | 默认 | 打开它需要 |
|---|---|---|
| git push | dry-run | `ALLOW_PUSH=1` 且 PushPolicy 允许 且 非保护分支 |
| 发 PR 评论 / issue 回复 | 关 | `ALLOW_POST=1` 且 请求显式带 post 意图 |
| force push | 仅 `--force-with-lease` | 无法放宽 |
| 脏工作树 | 拒绝启动 | 先清理 |
| 未知仓库 | 生成 DRAFT adapter 后停下 | 人工审核后激活 |
| 高风险 manifest 段（`repo`/`upstream`/`push`） | Agent 写入被拒 | 只能人工改 |

## 更多文档

**[`doc/README.md`](doc/README.md) 是文档地图**——按你要做的事挑一篇：

| 你要做什么 | 看这篇 |
|---|---|
| CLI 完整上手（配置、命令、排查） | [`QUICKSTART.md`](QUICKSTART.md) |
| 完整了解它是什么、能做什么 | [指南](doc/GUIDE.md) |
| 在 Codex / Claude Code / Cursor 里装上用 | [宿主端](doc/guide/hosts/README.md) |
| 安装细节，或接入其他 MCP 客户端 | [MCP 安装](doc/guide/mcp.md) |
| 让 Strict 跑在订阅或别的模型上 | [后端](doc/guide/backends.md) |
| 独立执行 issue / CI / rebase 任务 | [独立工作流](doc/guide/autonomous-workflow.md) |
| 维护这个仓库本身 | [开发者入口](DEVELOPMENT.md) |

> **宿主 ≠ 后端**：`claude-code` / `codex` / `cursor` 这三个名字两边都出现，
> 方向相反。宿主提供模型给你用（Direct），后端是 copilot 拿去用的模型
> （Strict）。

其余：[发版漂移审计](doc/contributing/release-maintenance.md) ·
[知识库贡献规范](doc/knowledge/CONTRIBUTING.md) ·
[知识维护示例](doc/knowledge/maintainer-walkthrough.md) ·
[评测结论](doc/evaluation/README.md)
