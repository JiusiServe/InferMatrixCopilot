# 在 Cursor 里使用 InferMatrixCopilot

> **宿主端页面。** 这里讲 copilot 跑在 Cursor **里面**（Direct 模式，用 Cursor
> 自己的模型）。如果你要的是让 copilot **反过来**把 `cursor-agent` 拉起来执行
> Strict 的 agent step，那是**后端**，看 [`../backends.md`](../backends.md)。
> 对照表见 [`README.md`](README.md)。

默认的 MCP 是一个**知识提供方**：Cursor 用它当前选中的模型审代码，这条路径
**不需要 API Key，也不需要配置模型**。

## 安装

```bash
git clone git@github.com:JiusiServe/InferMatrixCopilot.git
cd InferMatrixCopilot

./install-mcp.sh                                # macOS / Linux
./install-mcp.sh --repo-path /path/to/vllm-omni
install.cmd                                     # Windows
```

安装器自动识别 Cursor 并注册 MCP 与四个 Skill。**装完重启 Cursor。**

手动配置（安装器没识别到，或你要自己接管）时，模板在
[`integrations/config-templates/cursor/mcp.json`](../../../integrations/config-templates/cursor/mcp.json)。

## 用法

Cursor 用 slash 形式：

```text
/imreview https://github.com/vllm-project/vllm-omni/pull/5172
/imreview                       # 当前 PR；没有 PR 时审当前本地改动
/imdesign <目标 / issue / PR>
/imcifix <issue 或 URL>
/imupdate vllm-omni
```

`integrations/cursor/` 下另有 `imreview.md` / `imcifix.md` 两份提示词文件，
供直接粘贴或自定义命令使用。

## 一条 Cursor 特有的注意事项

这一条属于**后端**侧，但用 Cursor 的人最容易撞上，所以在这里也写一次：

**grok 家族模型（4.5 / 4.6）会在评审会话中主动搜索并读取 copilot 自己的
`imreview` 方法论 skill。** Composer 从未出现这个行为。如果你在用 cursor 后端
跑评测，三份 skill 副本必须先移出 `$HOME` 并在事后恢复，否则结果会被污染。

也因为 cursor-agent 无法完全关闭自己的内置工具，凡是走 cursor **后端**的会话
都会额外过一遍事后审计（`providers/audit.py`），审计结论写进 RUN_REPORT。
细节见 [`../backends.md` §5](../backends.md#5-换后端不会绕过权限闸)。

## 确认装好了

在 Cursor 的 MCP 设置里确认 `infermatrix-copilot` 已连接。Agent 没主动调用时
直接说：

```text
Use InferMatrixCopilot in Direct mode to review this PR.
```
