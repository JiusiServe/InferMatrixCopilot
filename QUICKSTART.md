# 快速上手 —— InferMatrixCopilot

面向 vLLM-Omni 的 playbook 驱动仓库维护 copilot。一个自然语言入口即可审 PR、
调 CI、rebase 分支、回答/分流 issue、建立仓库 profile —— 并带一套硬安全模型：
**默认一切 dry-run**，且自然语言永远无法扩大权限。

本页讲的是**独立 CLI**。如果你想在 Codex / Claude Code / Cursor **里面**用
copilot，那是 Direct 模式，见 [`doc/guide/hosts/`](doc/guide/hosts/README.md)。

第一次接触代码？[`doc/GUIDE.md`](doc/GUIDE.md) 是唯一总览；
[`doc/architecture/CODE_TOUR.md`](doc/architecture/CODE_TOUR.md) 按数据流走一遍代码，
[`doc/architecture/DESIGN.md`](doc/architecture/DESIGN.md) 讲为什么这么设计。

---

## 1. 安装（一条命令）

```bash
bash install.sh
```

创建或复用 venv、以 editable 方式安装包、从模板生成 `.env`（**永不覆盖**已有的）、
写出仓库内的 `./infermatrix-copilot` 包装器（不改 PATH），最后跑一次 `doctor`。
`bash install.sh --uninstall` 只删除它自己创建的东西（永不动 `.env`）。

> 如果工作区 venv 里已经装好了，`./infermatrix-copilot` 直接可用 —— 除非你改过
> `.env`，否则跳到第 3 步。

## 2. 配置 `.env`（已被 git 忽略 —— **绝对不要提交**）

能跑起来的最小集：

```bash
ANTHROPIC_API_KEY=sk-...            # 或一个 DeepSeek 的 /anthropic key
ANTHROPIC_BASE_URL=                 # 使用兼容端点时填写
AGENT_MODEL=claude-sonnet-5         # 默认推理模型
REPO_PATHS={"vllm-omni": "/path/to/vllm-omni"}  # JSON 映射：仓库名 -> 路径
DEFAULT_REPO=vllm-omni
```

在你**确实想要**对外写入之前，两个写闸保持关闭：

```bash
ALLOW_PUSH=0     # 1 = 允许 git push（仍然只有 --force-with-lease，永不推 main）
ALLOW_POST=0     # 1 = 允许发布 PR 评论 / issue 回复
```

可选项：`REVIEWER_MODEL`、`INTENT_MODEL`、双路径两档后端
（`ECO_MODEL`/`PERFORMANCE_MODEL`，各自可带自己的 `*_BASE_URL`+`*_API_KEY` ——
三个要么都填要么都不填；未配置 performance 档时，performance 请求会**当场失败**
而不是悄悄跑 eco 模型）、`NOTIFY_EMAIL`+`RESEND_API_KEY`/SMTP（升级邮件）、
`LLM_MIXTURE`（MoA）。全部开关见 `.env.template`。

每次响应实际服务的模型都会与请求核对（fail-closed —— 那些悄悄替换模型的端点，
例如在 DeepSeek 的 `/anthropic` 上返回 Claude 名字，会被抓出来而不是被误标）。
`doctor` 免费检查档位/主机的合理性；`doctor --probe` 每档发一次 1-token 调用并
打印 `requested → served`。

## 3. 预检

```bash
./infermatrix-copilot doctor          # 每个 ✗ 都会打印确切的修复命令
```

检查项：包是否装好、`ANTHROPIC_API_KEY` 是否设置（只打印名字，**永不打印值**）、
`gh` 是否安装**且已认证**（`gh auth login` 一次即可）、`REPO_PATHS` 是否存在、
`.env` 能否解析、MoA 配置（如果设了）是否合法。

---

## 4. 最初几条命令

你不需要背任务 kind 或触发短语 —— 平实的中文/英文会自己路由；完整的 GitHub URL
会路由到正确的仓库和工作流。

```bash
# 审一个 PR（只读；产出评审意见，不发布）
./infermatrix-copilot -p "review pr 5134"
./infermatrix-copilot -p "do a full-depth review of pr 5134"
./infermatrix-copilot -p "review https://github.com/vllm-project/vllm-omni/pull/5134"

# 调 PR 上失败的 CI（report only = 只读分诊）
./infermatrix-copilot -p "debug pr 5134, report only"

# 回答 / 分流 issue
./infermatrix-copilot -p "answer issue 4842, do not post"
./infermatrix-copilot -p "triage recent open issues"

# 把 PR rebase 到它的 base 上
./infermatrix-copilot -p "rebase pr 5134"

# 复合请求 -> 有序队列，目标自动延续
./infermatrix-copilot -p "rebase pr 5134, then review it"
```

常用 flag：

| Flag | 作用 |
|---|---|
| `--yes` | 跳过 `[y/N]` 确认（headless / 脚本） |
| `--plan-only` | 只解析并打印计划，不执行任何步骤 |
| `--performance` | 本次 run 使用高能力模型档（默认 eco） |
| `--resume` | 从上一次 run 的首个未完成 step 重新进入 |
| `--playbook <name>` | 运行指定 playbook（含 candidate） |
| `--report-only` | 配合 `--playbook`：只读变体 |
| `--task-param k=v` | 配合 `--playbook`：传参（可重复） |
| `--no-chat` | 用朴素命令 REPL 代替对话模式 |

在 `-p --yes` 模式下，含糊的请求会带着**澄清问题以非零码退出**，而不是猜测执行
—— 这对评测 harness 和 CI 是安全的。

## 5. 对话模式（默认，不加 `-p`）

```bash
./infermatrix-copilot
```

Claude-Code 风格的对话：问仓库的事、问过往 run，也可以直接通过工具执行工作 ——
走的是与 flag CLI **完全相同**的 TaskSpec、planner 和 `[y/N]` 确认门（对话模式
永远无法扩大权限）。内置命令：`/status`、`/logs [n]`、`/playbooks`、`/resume`、
`/quit`。仓库读取被囚禁在已配置的仓库内；`.env*` 一律拒绝。

---

## 6. 安全模型（发布或推送之前请先读这一节）

对外生效的动作是**双闸**，两者必须同时成立：

- **发 PR 评论 / issue 回复** → 请求必须带明确的 `post` 意图
  （例如 `"review pr 5134 and post it"`）**并且** `ALLOW_POST=1`。
- **git push** → 推送策略允许**并且** `ALLOW_PUSH=1`。force 只有
  `--force-with-lease`；**`main` 永远不会被推送**，无论策略怎么写。

任何一个条件不满足，都是一次 **dry run**，它会准确显示"本来会做什么"。
Adapter zero（`adapters/vllm_omni/manifest.yaml`）声明了 `push.allowed: false`
—— vLLM-Omni 的改动一律走 PR，绝不直接推送。被阻塞的 run 会写出
`ESCALATION.md` 并以退出码 3 结束（通知，绝不猜测）。

## 7. 产物在哪

```
~/.infermatrix-copilot/runs/run-<ts>-<uuid6>/
  RUN_REPORT.md      交付物（评审 / 回答 / 调试摘要）
  DIAGNOSTICS.md     逐 step 诊断
  run_trace.jsonl    仅追加的事实日志
  progress.json      step 检查点（--resume 读的就是它）
  metrics.json       CATQ run 指标
  ESCALATION.md      仅在被阻塞时出现
~/.infermatrix-copilot/worktrees/<repo>-pr<n>/   评审用的 PR-time checkout
~/.infermatrix-copilot/sessions/                  对话记录
```

## 8. Playbook

```bash
./infermatrix-copilot -p "…"                          # 由 planner 挑选已审核的 playbook
./infermatrix-copilot --playbook pr-review --plan-only # 按名字点名运行
```

已注册：`pr-review`、`pr-debug`、`pr-rebase`、`issue-assist`、`issue-triage`、
`repo-rebase`（**locked** —— 委托给已验证的 5 阶段夜跑编排器）、
`repo-rebase-native`（candidate）、`repo-profile`、`profile-consolidate`
（candidate；Stage-4 维护）。candidate 对 planner **不可见**，只能用
`--playbook` 显式运行。

## 9. 接入一个新仓库（profile）

```bash
./infermatrix-copilot -p "profile the repo" --yes     # 指纹 -> draft profile
./infermatrix-copilot --playbook profile-consolidate --yes   # Stage-4 去重/刷新
```

仓库知识住在边缘的 `adapters/<repo>/`（人工门禁的 `manifest.yaml` + agent 建立、
证据门禁的 `profile/`）—— **永远不在 `src/` 里**。`PROFILE_BRIEFING_ENABLED=0`
用于跑 {无 profile} 的评测对照臂。

## 10. 进阶：MCP 服务端（Claude Code / Codex / Cursor）

```bash
pip install -e '.[mcp]'      # 可选 extra，不进基础安装
```

暴露只读工具 —— `start_review` / `start_issue_answer` / `start_issue_triage`
（返回 `run_id`）、`get_status` / `get_result`（轮询）、`list_playbooks`、
`doc_read` / `doc_search`。评审要跑 5–12 分钟，所以接口是"先启动再轮询"。
只有只读 kind 可达，且 `post` 在**服务端边界和 run 子进程两处**都被强制关闭。
配置方法见 [`doc/guide/mcp.md`](doc/guide/mcp.md)。

---

## 排查

- **"capability gap … run repo_profile"** —— 任务需要 profile 尚未提供的仓库知识；
  先执行第 9 步建立 profile。
- **`-p --yes` 下抛出澄清问题** —— 请求含糊，按设计以非零码退出。补上 PR/issue
  编号，或补上 `post` / `report only` 意图。
- **评审/回答看起来被阻塞但有内容** —— 打开 `RUN_REPORT.md`；即使某个 step 升级，
  实质性草稿也会被抢救并交付。
- **`doctor` 里任何一条红色** —— 那条消息**本身就是修复方法**。最常见的是 `gh`
  认证：`gh auth login`。

深入阅读 —— 从文档地图 [`doc/README.md`](doc/README.md) 开始：

- [`doc/GUIDE.md`](doc/GUIDE.md) —— 唯一总览（功能、使用、开发、playbook、step、
  tool、实测性能）
- [`doc/guide/backends.md`](doc/guide/backends.md) —— 怎么选和配 Strict 后端
- [`doc/architecture/CODE_TOUR.md`](doc/architecture/CODE_TOUR.md) —— 按数据流讲代码 ·
  [`doc/architecture/DESIGN.md`](doc/architecture/DESIGN.md) —— 为什么
- [`doc/architecture/SPEC/`](doc/architecture/SPEC/README.md) —— 逐文件契约：
  改一个文件之前先读它对应的那页

注意 `IMPLEMENTATION_STATUS.md` 已移到
[`doc/archive/`](doc/archive/IMPLEMENTATION_STATUS.md) 并冻结 —— 它描述的是 7 月的
构建，不是现状。现状以 `doc/GUIDE.md` 为准。
