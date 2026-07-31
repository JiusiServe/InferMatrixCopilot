# InferMatrixCopilot

让 Codex、Claude Code、Cursor 等 Coding Agent 按 **vLLM-Omni 的项目知识**
审查代码，并在上游版本变化后更新这套知识。

它主要解决两个问题：

- `/imreview`：审查 PR 或本地改动时，让 Agent 知道相关模型、组件和维护者规则，
  不只做一遍通用代码检查。
- `/imupdate`：vLLM-Omni 发版或目录变化后，对比新旧版本，更新
  InferMatrixCopilot 中容易过期的模型清单、registry、deploy、路径路由和 source pin。

默认使用 **Direct 模式**：代码仍由你当前 Agent 的模型读取和判断；
InferMatrixCopilot 提供知识入口和审查门禁，不运行第二个模型，不自动发布 GitHub
评论，也不推送代码。

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

安装器会识别本机的 Codex、Claude Code 和 Cursor，并安装 MCP、`imreview` 和
`imupdate` Skill。未识别到已知 Agent 时，会生成标准
`infermatrix-copilot.mcp.json` 供其他 MCP 客户端导入。

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

## 审查代码：`/imreview`

```text
/imreview https://github.com/vllm-project/vllm-omni/pull/5172
/imreview
```

- 传 PR URL：读取该 PR 的当前 head、diff、CI 和 mergeability。
- 不传参数：审查当前 PR；没有 PR 时审查当前本地改动。
- 默认只在当前对话输出带文件和行号的审查意见，不发布到 GitHub。

工作过程：

```text
你发起 /imreview
  → Agent 固定 PR 快照并在当前对话报告 head、CI 和 mergeability
  → Agent 把 title、body 和 changed files 传给 review(..., mode="direct")
  → MCP 返回至多 3 个相关知识入口及精简 quick map
  → Agent 并行读取代码、执行相关验证
  → Agent 输出带文件和行号的审查结论
```

Agent 会先确认 PR 版本和 CI 状态，再继续读代码。审查结果只显示在当前对话，
不会自动发到 GitHub。

## 更新知识：`/imupdate`

上游仓库会不断增加模型、调整 registry、移动文件或修改 deploy。`/imupdate`
用于把这些**结构事实**同步到 InferMatrixCopilot，避免以后按旧路径和旧清单审查。
它更新的是 InferMatrixCopilot 知识，不会修改传入的 vLLM-Omni 仓库。

```text
# 本地 checkout：baseline 对比当前 HEAD
/imupdate D:\path\to\vllm-omni

# 仓库名或别名
/imupdate vllm-omni
/imupdate vllmomni

# URL；可选指定目标 tag 或 SHA
/imupdate https://github.com/vllm-project/vllm-omni v0.26.0rc1
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

`/imupdate` 不会根据一次 diff 自动编造 owner 规则，也不会自动 commit、push 或开 PR。
详细的审计项和底层命令见
[`doc/VLLM_OMNI_RELEASE_MAINTENANCE.md`](doc/VLLM_OMNI_RELEASE_MAINTENANCE.md)。

## Skill 命令和 MCP 接口不是一回事

平时直接用 `/imreview` 和 `/imupdate` 即可，下面的接口由 Agent 调用：

- `review(target, repo="vllm-omni", mode="direct", post=false,
  review_depth="", title="", body="", changed_files=[], repo_path="")`：
  Direct 根据 PR 描述返回至多 3 个精确知识路由和审查门禁；Strict 返回
  `run_id`。`repo_path` 可临时指定 Strict 使用的本地 checkout。
- `validate_direct_review(subtraction_signal, subtraction?,
  minimality_proof?, final_comment_count=1)`：Direct 最终输出前的完成检查。
  普通小修改传 `subtraction_signal="none"`；存在新增或扩张结构时传
  `"triggered"`，并提供减法项或最小性证明。
- `get_review_status(run_id)`：查看 Strict 后台任务的步骤和进度。
- `get_review_result(run_id, offset=0)`：轮询 Strict 结果；报告较长时按
  `next_offset` 继续读取。
- `update_knowledge(repo="vllm-omni")`：只返回知识贡献入口
  `knowledge/CONTRIBUTING.md`。它不是 `/imupdate` 的发版审计器。
- `doc_search(query, repo="vllm-omni", limit=20)`：搜索模型或组件知识。
- `doc_read(path, repo="vllm-omni", offset=0)`：读取搜索到的知识页面。

## Direct 和 Strict 是同一个 MCP

`/imreview` 默认使用 Direct；需要完整后台工作流时，可以明确要求 Strict。
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

Autonomous workflow 不是 `/imreview` 的第三种模式，而是同一工作流引擎的独立
CLI/MCP 入口。默认安装器不会注册它；只有需要独立执行 issue、CI、rebase 等任务时
才需要阅读
[`docs/autonomous-workflow.md`](docs/autonomous-workflow.md)。

## 维护者文档

- [安装和通用 MCP 配置](doc/MCP.md)
- [vLLM-Omni 发版漂移审计](doc/VLLM_OMNI_RELEASE_MAINTENANCE.md)
- [知识库贡献规范](knowledge/CONTRIBUTING.md)
- [知识维护示例](docs/knowledge-maintainer.zh-CN.md)
- [项目设计与实现](doc/)
- [评测说明](eval/README.md)
