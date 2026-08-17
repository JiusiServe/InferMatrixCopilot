# 在 Claude Code 里使用 InferMatrixCopilot

> **宿主端页面。** 这里讲 copilot 跑在 Claude Code **里面**（Direct 模式，用
> Claude Code 自己的模型）。如果你要的是让 copilot **反过来**把 `claude` CLI
> 拉起来执行 Strict 的 agent step，那是**后端**，看
> [`../backends.md`](../backends.md)。对照表见 [`README.md`](README.md)。

默认的 MCP 是一个**知识提供方**：Claude Code 用它当前选中的模型审代码，所以
这条路径**不需要 API Key，也不需要配置模型**。

## 安装

```bash
git clone git@github.com:JiusiServe/InferMatrixCopilot.git
cd InferMatrixCopilot

./install-mcp.sh                                # macOS / Linux
./install-mcp.sh --repo-path /path/to/vllm-omni # 顺带配置 Strict 的本地 checkout
install.cmd                                     # Windows
```

安装器自动识别 Claude Code，注册 MCP 与四个 Skill，用的是与 Codex、Cursor
**同一份** MCP 描述符和 Skill。

**重启 Claude Code。**

## 用法

Claude Code 用 slash 形式（Codex 用 `$`）：

```text
/imreview https://github.com/vllm-project/vllm-omni/pull/5172
/imreview                       # 当前 PR；没有 PR 时审当前本地改动
/imdesign <目标 / issue / PR>
/imcifix https://github.com/vllm-project/vllm-omni/issues/5023
/imupdate vllm-omni
```

也可以直接用自然语言：

```text
帮我审核一下这个 PR xxxx，用知识库
Use InferMatrixCopilot in Direct mode to review this PR.
```

## 四个 Skill 的边界

| Skill | 做什么 | 不做什么 |
|---|---|---|
| `imreview` | 审 PR 或本地改动，输出带文件行号的结论 | 不自动发 GitHub |
| `imdesign` | 产出协同设计包（方案、边界、验证计划） | 不自动改代码 |
| `imcifix` | 本地复现 → 最小修复 → 针对性验证 | 不 commit / push / 开 PR / 发评论 |
| `imupdate` | 同步上游发版带来的结构事实 | 不修改目标仓库 |

`imcifix` 是**宿主 Agent 的本地补丁流程**——它不意味着 MCP 会去改你的仓库。

## 确认装好了

在 Claude Code 的 MCP 页面里确认 `infermatrix-copilot` 已连接。如果对话里
Agent 没有主动调用它，直接说：

```text
Use InferMatrixCopilot in Direct mode to review this PR.
```

## 想跑 Strict

明确说出来：

```text
Use InferMatrixCopilot in Strict mode to review
https://github.com/vllm-project/vllm-omni/pull/5172.
```

Strict 会返回 `run_id`，再用 `get_review_status` 看进度、`get_review_result`
取报告。它需要一个后端和一个本地 checkout——见
[`../backends.md`](../backends.md)。
