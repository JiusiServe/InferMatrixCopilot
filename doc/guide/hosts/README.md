# 宿主（Hosts）—— copilot 跑在谁里面

**宿主**是你日常使用的编码 Agent。装好之后，copilot 以 MCP + Skill 的形式住在
它里面，用**它自己的模型**读代码做判断——这就是 **Direct 模式**，不需要任何
API Key，服务端不跑模型。

| 宿主 | 调用形式 | 安装页 |
|---|---|---|
| Claude Code | `/imreview` | [`claude-code.md`](claude-code.md) |
| Codex | `$imreview`（**不是** `/imreview`） | [`codex.md`](codex.md) |
| Cursor | `/imreview` | [`cursor.md`](cursor.md) |
| 其他 MCP 客户端 | 手动导入 `infermatrix-copilot.mcp.json` | 见下方 §3 |

---

## 1. 你要找的可能是另一篇

`claude-code`、`codex`、`cursor` 这三个名字**在本项目里出现两次，方向相反**：

| | **宿主**（本目录） | **后端**（[`../backends.md`](../backends.md)） |
|---|---|---|
| 谁调用谁 | copilot 跑在宿主里面 | copilot 把厂商 CLI 拉起来 |
| 谁的模型在读代码 | **宿主的** | copilot 配置的 |
| 模式 | Direct | Strict |
| 需要 API Key | **不需要** | 要 Key 或订阅登录 |
| 配置项 | 安装器自动写入 | `STRICT_BACKEND=<id>` |

判据一句话：**宿主提供模型给你用；后端是 copilot 拿去用的模型。**

举个具体例子——同一个 `codex` 二进制：

- **作为宿主**：你在 Codex 里敲 `$imreview`，Codex 用它当前选中的模型审代码，
  copilot 只负责返回知识路由和治理契约。
- **作为后端**：你在 CLI 里跑 Strict，copilot **反过来**把 `codex exec` 作为
  子进程拉起，让它执行一个 agent step。

## 2. 一次装完所有识别到的宿主

```bash
git clone git@github.com:JiusiServe/InferMatrixCopilot.git
cd InferMatrixCopilot

./install-mcp.sh                                # macOS / Linux
./install-mcp.sh --repo-path /path/to/vllm-omni

install.cmd                                     # Windows（双击也可以）
install.cmd --repo-path D:\path\to\vllm-omni
```

安装器**自动识别本机的 Codex、Claude Code 和 Cursor**，为识别到的每一个注册
MCP 与四个 Skill（`imreview` / `imdesign` / `imcifix` / `imupdate`），并创建
`~/.infermatrix-copilot/.env`。

**装完必须重启宿主。**

`--repo-path` 只影响 Strict（它需要一个本地 vLLM-Omni checkout）；纯 Direct
使用可以不传。

## 3. 没被识别到的宿主

安装器会生成一份标准的 `infermatrix-copilot.mcp.json`，任何兼容 MCP 的客户端
都可以导入。现成的配置模板在
[`integrations/config-templates/`](../../../integrations/config-templates/)：

- `codex/config.toml` —— Codex 的 `[mcp_servers.infermatrix_copilot]` 段
- `cursor/mcp.json` —— Cursor 的 MCP 配置

接口清单见 [`../mcp.md`](../mcp.md)。

## 4. 确认装好了

在宿主的 MCP 页面里应该能看到 `infermatrix-copilot` 已连接。Codex 还可以：

```powershell
codex mcp list
```

宿主没有主动调用它时，直接说出来即可：

```text
Use InferMatrixCopilot in Direct mode to review this PR.
```

## 5. Direct 一次审查会发生什么

```text
你发起 imreview
  → 固定 PR 快照，60 秒内先报 head SHA / CI / mergeability
  → 调 review(mode="direct")，传 title / body / changed_files
  → 拿到 ≤3 条知识路由（内嵌 quick_map，3.5k 封顶）
     + execution_budget（硬顶）+ checklist
  → 宿主自己的模型并行读源码、跑验证
  → validate_direct_review 完成门（机械的结构检查）
  → 输出单条合并结论
```

结论**只出现在当前对话**，不会自动发到 GitHub。Direct 发布需要显式要求，且服务端
配置 `ALLOW_POST=1`；Strict 则一律不发布——一个 PR 只能有一个发布者，所以读结构化
结果自己发，或走 CLI 做人工发布。

想要完整后台工作流时明说 Strict——那会用到后端，见
[`../backends.md`](../backends.md)。
