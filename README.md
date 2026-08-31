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

## 配置 .env

`install.sh` / `install-mcp.sh` 会从 [`.env.template`](.env.template) 生成
`.env`（CLI 用仓库根的 `.env`，Direct/MCP 宿主用
`~/.infermatrix-copilot/.env`）。`.env` 已被 git 忽略——**绝不提交**，token
和机器本地的绝对路径只放这里。

最小可用配置分三层：Direct 只需要仓库映射；Strict/CLI 加模型；rebase 的
远端 CI 再加 token：

```bash
# 模型（Strict/CLI）：Anthropic 或 OpenAI 二选一；*_BASE_URL 可选代理
ANTHROPIC_API_KEY=sk-...
AGENT_MODEL=claude-sonnet-5
STRICT_BACKEND=api            # 或 cursor / claude-code / codex（订阅制 CLI）

# 仓库映射：名字 -> 本地 checkout
REPO_PATHS={"vllm-omni": "/data/me/vllm-omni"}
DEFAULT_REPO=vllm-omni
REPO_FULL_NAMES={"vllm-omni": "vllm-project/vllm-omni"}   # GitHub URL 路由

# adapter manifest 的路径变量（vllm-omni）：上游 checkout 与目标 venv
VLLM_OMNI_REPO=/data/me/vllm-omni
VLLM_UPSTREAM_REPO=/data/me/vllm
VLLM_OMNI_VENV=/data/me/vllm-omni-venv

# 安全闸：默认全关；打开是显式动作
ALLOW_PUSH=0                  # push 双闸的环境端（另一半是 push 闸裁决）
ALLOW_POST=0                  # 发 PR / issue 评论

# rebase 远端 CI（rebase_mode=remote_ci / full 才需要）
GITHUB_TOKEN=ghp_...          # push 走 header 认证
BUILDKITE_API_TOKEN=bkua_...  # 需要 write_builds scope
REBASE_CI_TIMEOUT_SEC=18000   # CI 监控预算（缺省 10800 = 3h）
```

改完跑 `./infermatrix-copilot doctor`——每个 ✗ 都打印确切修复命令；
`doctor --probe` 再做 1-token 真连线校验（唯一的付费检查）。完整变量清单
（模型分档、订阅后端、邮件通知等）见 [`.env.template`](.env.template)。

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

全仓库 rebase：引擎是 `repo-rebase-v3` —— rebase_engine 全量合并后的原生
playbook（wheel pin、按模块分波验证、本地测试环、push 闸、远端 CI 监控全部
在内，无外部编排器）。2026-08-25 起为 **locked**（L0 原样复用，planner 直接
召回）；旧的委托版 `repo-rebase` v2 与 `repo-rebase-native-v1` 已删除。

```bash
# 只读评估：不动工作树，产出 RUN_REPORT
./infermatrix-copilot --repo vllm-omni --yes --playbook repo-rebase-v3 \
    --task-param rebase_mode=report_only
```

真实示例——把 vllm-omni 追到 vLLM **v0.28.0**（adapter manifest 已设
`upstream.target_branch: releases/v0.28.0`；管线在上游 checkout 解析该分支
tip，即 tag `v0.28.0` = `2cf0a691`，并校验预编译 wheel 可用）：

```bash
# 端到端：从上次对齐的 1af5a386c 追到 releases/v0.28.0 tip —— wheel pin →
# 模块波次 → 本地测试环 → push dev/vllm-align → 自建 Buildkite 构建并监控
./infermatrix-copilot --repo vllm-omni --yes --playbook repo-rebase-v3 \
    --task-param rebase_mode=full \
    --task-param last_rebase_commit=1af5a386cd43695b23a1f7a63b0646bbf043fc9c

# 树已推送、只需要 CI 验证指定 commit 时：remote_ci + 精确 sha
./infermatrix-copilot --repo vllm-omni --yes --playbook repo-rebase-v3 \
    --task-param rebase_mode=remote_ci \
    --task-param upstream_commit=2cf0a6915ce544dc493a0990f2ea38d81601128a
```

**目标从哪里来**

| 目标 | 来源 | 说明 |
| --- | --- | --- |
| 目标仓库 | `--repo <名字>`（缺省 `DEFAULT_REPO`） | 名字经 `.env` 的 `REPO_PATHS`（JSON）映射到本地 checkout；仓库必须有 `adapters/<repo>/` 适配器 |
| 上游分支 | 适配器 manifest 的 `upstream.target_branch`（如 `releases/v0.28.0`） | 管线在上游 checkout 上解析该分支 tip 作为 rebase 目标，并校验预编译 wheel 可用 |
| 上游 checkout / 目标 venv | manifest 声明的路径变量，经 `.env` 展开（vllm-omni：`VLLM_UPSTREAM_REPO`、`VLLM_OMNI_VENV`） | full 模式要求两者就绪 |

**task 参数**（`--task-param k=v`，可重复）

| 参数 | 适用模式 | 说明 |
| --- | --- | --- |
| `rebase_mode` | 必填 | `report_only`（只读）/ `local_ci`（本地测试环，不 push）/ `remote_ci`（push + 远端 CI 监控）/ `full`（端到端） |
| `last_rebase_commit` | full | 上次对齐到的 upstream sha（基线；run state 已有记录时可省略） |
| `upstream_commit` | remote_ci 必填 | 要推送并监控的目标 upstream sha |
| `force_upstream_commit` | full | 跳过分支 tip 解析，强制指定目标 sha |
| `main_ci_idx` | remote_ci / full | 多条 CI 流水线时选主流水线（缺省 0） |
| `halt_on_module_failure` | full | 模块失败即停（缺省 false：wave 门只清空 wave 2） |
| `halt_on_phase3_failures` | full | 本地测试环失败即停（缺省 false） |
| `push_with_failures` | remote_ci / full | 允许带失败推送（缺省 false） |
| `strict_push_gate` | remote_ci / full | 更严的 push 闸（缺省 false） |

**环境闸（`.env`）**：push 受双闸 —— push 闸裁决**且** `ALLOW_PUSH=1`；push
认证走 `GITHUB_TOKEN`，远端 CI 需要 `BUILDKITE_API_TOKEN`；CI 监控预算
`REBASE_CI_TIMEOUT_SEC`（缺省 3h）。远端 CI 优先领养同 commit 的 schedule
构建；对 schedule-only 流水线，按 adapter 声明
（`rebase.ci.ignore_branch_filters`）直接创建构建。

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

自动知识回流也遵循同一条边界：本仓库发布的
`infermatrix_copilot.sdk.v1.KnowledgeCurator` 是 catalog、受信 prompt、proposal
shape/ID/page/source 校验、append-only apply 与两道 validator rollback 的唯一实现；
ReviewBot 只把 evidence 和 model JSON 接到该 API，并继续拥有 dedicated clone、
ledger/retry、Git commit、fork push、PR 与 schedule。SDK 不 clone、不调 model、
不发布，也不会写 wheel 内的 knowledge 副本。

## 快速上手 4 · CI 修复（imcifix）

从 GitHub issue 出发：本地复现、最小修复、针对性验证；默认不 commit、
不 push、不发评论：

```text
# Codex：issue 号或 URL
$imcifix https://github.com/vllm-project/vllm-omni/issues/5100

# Claude Code / Cursor
/imcifix 5100

或者直接说：帮我修一下 issue 5100，先本地复现
```

Agent 会解析 issue（标题、正文、标签、评论一律按不可信证据处理），先报告
issue 号、分支、脏树状态和初始假设，再用最小命令复现，做最小修复并针对性
验证。只有明确要求发布时才建 `fix/<issue>-<slug>` 分支，只加增量提交，
永不 force-push。

Strict 对应的 CI / issue 工作流：

```bash
./infermatrix-copilot -p "debug pr 5134, report only"     # CI 失败诊断
./infermatrix-copilot -p "answer issue 4842, do not post" # 起草 issue 回复
./infermatrix-copilot -p "triage recent open issues"      # 批量分诊
```

## 其它能力

- `imdesign`：写代码前生成协同设计包（问题、方案、接口变化和验证计划），
  不自动改代码。例：`/imdesign 给 scheduler 加抢占开关，先理清接口边界`，
  Codex 用 `$imdesign …`。
- 新仓库接入：`./infermatrix-copilot -p "profile the repo"` 建立 DRAFT
  profile；接入内容放在 `adapters/<repo>/` 和 `knowledge/repos/<repo>/`，
  不需要修改 `src/`。

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
