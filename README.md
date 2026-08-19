# InferMatrixCopilot

让 Codex、Claude Code、Cursor 等 Coding Agent 按 **vLLM-Omni 的项目知识**
审查代码，并在上游版本变化后更新这套知识。

它主要解决两个问题：

- `imreview`：审查 PR 或本地改动时，让 Agent 知道相关模型、组件和维护者规则，
  不只做一遍通用代码检查。
- `imdesign`：写代码前先围绕 issue、PR 或粗略需求做协同设计，产出方案、边界和验证计划。
- `imcifix`：从 GitHub issue 出发，让 Agent 在本地复现、修复并验证补丁。
- `imupdate`：vLLM-Omni 发版或目录变化后，对比新旧版本，更新
  InferMatrixCopilot 中容易过期的模型清单、registry、deploy、路径路由和 source pin。

默认使用 **Direct 模式**：代码仍由你当前 Agent 的模型读取和判断；
InferMatrixCopilot 提供知识入口和审查门禁，不运行第二个模型，不自动发布 GitHub
评论，也不推送代码。

开发或维护 InferMatrixCopilot 本身，请直接看
[开发者入口](DEVELOPMENT.md)。

## 安装

私有仓库过渡期：

```text
git clone git@github.com:JiusiServe/InferMatrixCopilot.git
cd InferMatrixCopilot

# Windows：双击也可以
install.cmd

# 同时配置 Strict 使用的本地 vLLM-Omni checkout
install.cmd --repo-path D:\path\to\vllm-omni

# macOS / Linux
./install-mcp.sh
./install-mcp.sh --repo-path /path/to/vllm-omni
```

安装器会识别本机的 Codex、Claude Code 和 Cursor，并安装 MCP、`imreview`、
`imdesign`、`imcifix` 和 `imupdate` Skill。未识别到已知 Agent 时，会生成标准
`infermatrix-copilot.mcp.json` 供其他 MCP 客户端导入。

Codex 重启后用 `$imreview` / `$imdesign` / `$imcifix` / `$imupdate`，也可以先运行 `/skills` 查找；
`/imreview` 不是 Codex 的 Slash Command。Claude Code 和 Cursor 仍使用
`/imreview` / `/imdesign` / `/imcifix` / `/imupdate`。

安装器还会创建 `~/.infermatrix-copilot/.env`。Direct 不需要模型密钥；使用
Strict 时，任选一种填写：

```text
# Anthropic
ANTHROPIC_API_KEY=...
ANTHROPIC_BASE_URL=        # 可选，代理或兼容网关地址

# 或 OpenAI
OPENAI_API_KEY=...
OPENAI_BASE_URL=           # 可选，代理或兼容网关地址
```

只填一种 Key 时会自动选择后端。两种都填时，用
`LLM_PROVIDER=anthropic` 或 `LLM_PROVIDER=openai` 指定。安装时没有传
`--repo-path` 的，还要填写 `REPO_PATHS`。然后重启 Agent。

## 确认安装成功

在 Agent 的 MCP 页面确认 `infermatrix-copilot` 已连接。Codex 也可以运行：

```powershell
codex mcp list
```

看到 `infermatrix-copilot` 后即可使用。如果对话中 Agent 没有调用它，直接说：

```text
Use InferMatrixCopilot in Direct mode to review this PR.
```

## 审查代码：`imreview`

```text
# Codex
$imreview https://github.com/vllm-project/vllm-omni/pull/5172
$imreview

# Claude Code / Cursor
/imreview https://github.com/vllm-project/vllm-omni/pull/5172
或者说
“帮我审核一下这个pr xxxx，用知识库”
```

- 传 PR URL：读取该 PR 的当前 head、diff、CI 和 mergeability。
- 不传参数：审查当前 PR；没有 PR 时审查当前本地改动。
- 默认只在当前对话输出带文件和行号的审查意见，不发布到 GitHub。

工作过程：

```text
你发起 imreview
  → Agent 固定 PR 快照并在当前对话报告 head、CI 和 mergeability
  → Agent 把 title、body 和 changed files 传给 review(..., mode="direct")
  → MCP 返回至多 3 个相关知识入口及精简 quick map
  → Agent 并行读取代码、执行相关验证
  → Agent 输出带文件和行号的审查结论
```

Agent 会先确认 PR 版本和 CI 状态，再继续读代码。审查结果只显示在当前对话，
不会自动发到 GitHub。

## 协同设计：`imdesign`

```text
# Codex
$imdesign https://github.com/JiusiServe/InferMatrixCopilot/issues/46
$imdesign 支持 co-design skill，并提供便捷入口

# Claude Code / Cursor
/imdesign <goal-or-issue-or-pr>
```

`imdesign` 会先读取 issue、PR 或本地相关代码，只产出协同设计包：问题、现状、
方案、接口或配置变化、实施步骤、验证计划和风险。它不自动改代码；确认方案后再让
Agent 继续实现。

## 修复 Issue：`imcifix`

```text
# Codex
$imcifix https://github.com/vllm-project/vllm-omni/issues/5023
$imcifix issue 5023

# Claude Code / Cursor
/imcifix <issue-or-url>
```

`imcifix` 会读取 issue、检查当前 checkout、尽量复现或缩小问题，然后在本地做最小修复
并跑针对性验证。它默认不 commit、不 push、不开 PR、不发评论；需要发布时要明确说。

## 更新知识：`imupdate`

上游仓库会不断增加模型、调整 registry、移动文件或修改 deploy。`imupdate`
用于把这些**结构事实**同步到 InferMatrixCopilot，避免以后按旧路径和旧清单审查。
它更新的是 InferMatrixCopilot 知识，不会修改传入的 vLLM-Omni 仓库。

```text
# Codex：本地 checkout，baseline 对比当前 HEAD
$imupdate D:\path\to\vllm-omni

# 仓库名或别名
$imupdate vllm-omni
$imupdate vllmomni

或者直接说

帮我更新一下 vllmomni仓库最新到知识库

# URL；可选指定目标 tag 或 SHA
$imupdate https://github.com/vllm-project/vllm-omni v0.26.0rc1
```

它接受本地 Git 路径、仓库名、别名或 URL，第二个参数可选填目标 tag 或 SHA。

本地路径的流程：

```text
release_baseline.yaml 的 audited_sha
  → 对比目标仓库 HEAD（或指定 tag/SHA）
  → 只读审计 Git 对象、registry、pipeline、deploy、路径路由和 source pin
  → Agent 只更新报告能够证明的结构事实
  → enforce、知识检查和相关测试确认更新完整
```

仓库名、别名或 URL 的流程：

```text
解析权威仓库和目标版本
  → 优先使用已配置或当前工作区中的 checkout
  → 否则尽量建立临时 checkout，运行同一套机器审计
  → 无法运行机器审计时，只做有来源的模型分析，并明确标记验证不完整
```

`imupdate` 不会根据一次 diff 自动编造 owner 规则，也不会自动 commit、push 或开 PR。
详细的审计项和底层命令见
[`doc/contributing/release-maintenance.md`](doc/contributing/release-maintenance.md)。

## Skill 命令和 MCP 接口不是一回事

平时直接用 `imreview`、`imcifix` 和 `imupdate` 即可，下面的接口由 Agent 调用：

- `review(target, repo="vllm-omni", mode="direct", post=false,
  review_depth="", title="", body="", changed_files=[], repo_path="")`：
  Direct 根据 PR 描述返回至多 3 个精确知识路由和审查门禁；Strict 返回
  `run_id`。`repo_path` 可临时指定 Strict 使用的本地 checkout。
- `validate_direct_review(subtraction_signal, subtraction?,
  minimality_proof?, final_comment_count=1, evidence_head_sha)`：Direct 最终
  输出前的完成检查。`evidence_head_sha` 必须是本次审查固定的 head 提交，
  证明引用的源码和验证结果都读取自该版本而非本地工作区的其他分支。
  普通小修改传 `subtraction_signal="none"`；存在新增或扩张结构时传
  `"triggered"`，并提供减法项或最小性证明。
- `get_review_status(run_id)`：查看 Strict 后台任务的步骤和进度。
- `get_review_result(run_id, offset=0)`：轮询 Strict 结果；报告较长时按
  `next_offset` 继续读取。
- `update_knowledge(repo="vllm-omni")`：只返回知识贡献入口
  `doc/knowledge/CONTRIBUTING.md`。它不是 `imupdate` 的发版审计器。
- `doc_search(query, repo="vllm-omni", limit=20)`：搜索模型或组件知识。
- `doc_read(path, repo="vllm-omni", offset=0)`：读取搜索到的知识页面。

## Direct 和 Strict 是同一个 MCP

`imreview` 默认使用 Direct；需要完整后台工作流时，可以明确要求 Strict。
两者都通过同一个 `infermatrix-copilot-mcp` 的 `review` 接口调用，不需要再安装一个
Strict MCP。

```text
Use InferMatrixCopilot in Strict mode to review
https://github.com/vllm-project/vllm-omni/pull/5172.
```

Strict 会返回 `run_id`，Agent 再用 `get_review_status` 查看进度，并用
`get_review_result` 取得最终报告。它默认也不会发布评论；发布仍需用户明确要求、
调用传入 `post=true`，并且服务端配置 `ALLOW_POST=1`。

发布包已经包含 Strict 所需的 playbook、adapter 和 skill，不需要另外下载源码版。
安装器会创建统一配置文件 `~/.infermatrix-copilot/.env`，并可通过 `--repo-path`
写入目标 checkout。模型密钥不会被安装器猜测或复制；使用 Strict 前填写
`ANTHROPIC_API_KEY` 或 `OPENAI_API_KEY` 即可。Anthropic 和 OpenAI 都支持各自的
可选 `*_BASE_URL`。配置不完整时，`review` 会直接返回缺少的项目，不会启动一个
注定失败的后台任务。

## 独立执行器

Autonomous workflow 不是 `imreview` 的第三种模式，而是同一工作流引擎的独立
CLI/MCP 入口。默认安装器不会注册它；只有需要独立执行 issue、CI、rebase 等任务时
才需要阅读
[`doc/guide/autonomous-workflow.md`](doc/guide/autonomous-workflow.md)。

## 更多文档

**[`doc/README.md`](doc/README.md) 是文档地图**——一行一条，按你要做的事挑一篇。
下面只列最常用的四条路：

| 你要做什么 | 看这篇 |
|---|---|
| 完整了解它是什么、能做什么 | [指南](doc/GUIDE.md)（概览 / 功能 / 使用 / 开发 / playbook / step / tool / 性能） |
| 在 Codex / Claude Code / Cursor 里装上用 | [宿主端](doc/guide/hosts/README.md) |
| 让 Strict 跑在订阅或别的模型上 | [后端](doc/guide/backends.md) |
| 维护这个仓库本身 | [开发者入口](DEVELOPMENT.md) |

> **宿主 ≠ 后端**：`claude-code` / `codex` / `cursor` 这三个名字两边都出现，
> 方向相反。宿主提供模型给你用（Direct），后端是 copilot 拿去用的模型（Strict）。

其余：[MCP 接口](doc/guide/mcp.md) ·
[发版漂移审计](doc/contributing/release-maintenance.md) ·
[知识库贡献规范](doc/knowledge/CONTRIBUTING.md) ·
[知识维护示例](doc/knowledge/maintainer-walkthrough.md) ·
[评测结论](doc/evaluation/README.md)
