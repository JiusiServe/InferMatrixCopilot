# 后端（Backends）—— 谁跑在 copilot 里面

> **你要找的可能是另一篇。** 这里讲的是 **Strict 模式**下 copilot **拿去用**的
> 模型。如果你想知道怎么在 Codex / Claude Code / Cursor **里面**使用 copilot，
> 那是**宿主端**，看 [`hosts/`](hosts/README.md)。
>
> | 名字 | 作为**宿主**（copilot 跑在它里面） | 作为**后端**（它被 copilot 拉起） |
> |---|---|---|
> | Claude Code | ✅ `/imreview` → [`hosts/claude-code.md`](hosts/claude-code.md) | ✅ `STRICT_BACKEND=claude-code` |
> | Codex | ✅ `$imreview` → [`hosts/codex.md`](hosts/codex.md) | ✅ `STRICT_BACKEND=codex` |
> | Cursor | ✅ `/imreview` → [`hosts/cursor.md`](hosts/cursor.md) | ✅ `STRICT_BACKEND=cursor` |
> | DeepSeek（dsh） | ✗ | ✅ `STRICT_BACKEND=deepseek` |
> | api（Anthropic/OpenAI 兼容） | ✗ | ✅ 默认 |
>
> 一句话判据：**宿主提供模型给你用；后端是 copilot 拿去用的模型。**
> 宿主端不需要 API Key，后端端要么要 Key、要么要订阅登录。

---

## 1. 为什么会有"后端"这个概念

Strict 模式跑完整执行主脊，每一次模型调用原本都走 `llm.py::LLM`——一个需要
`ANTHROPIC_API_KEY` 或 `OPENAI_API_KEY` 的原始 completions 客户端。只有编码
Agent 订阅（Claude Pro/Max、ChatGPT、Cursor）而没有裸 API Key 的用户，根本
跑不了 Strict。

但 Claude Code、Codex CLI、cursor-agent 在订阅认证下**不暴露 completions
接口**——它们是**自带工具循环的 agent harness**。所以接入点不可能是
`LLM.create()`（无状态的 `system+messages+tools → tool_use` 往返），只能上移
一层：**委托一整个 agent step**。

于是有了两种 provider kind：

| kind | 是什么 | 谁拥有工具循环 | 接入点 |
|---|---|---|---|
| `api` | 原始 Anthropic/OpenAI 兼容端点 | **我们的** `agent_loop` | `LLM.create()` |
| `harness` | 订阅制（或 SDK 制）厂商 agent | **厂商的** | `run_session()`——一整个 step |

两者住在同一张注册表 `providers/registry.py` 里，走同一条解析路径、同一套
trace 词汇。**用 `api` 时行为逐字节不变**（平价棘轮）。

## 2. 五个后端

| id | kind | 凭据 | 能力 | 验证程度 |
|---|---|---|---|---|
| `api` | api | `.env` 里的 Key | 完整——我们自己的工具循环 | 基线路径 |
| `cursor` | harness | 订阅（`cursor-agent` CLI） | `mcp_tools` `usage_reporting` | 已实测 |
| `claude-code` | harness | 订阅（`claude` CLI） | `mcp_tools` `builtin_tools_off` `max_turns` `system_prompt` `usage_reporting` `cost_reporting` | 订阅认证下实测 |
| `codex` | harness | 订阅（`codex` CLI） | `mcp_tools` `sandbox_read_only` `usage_reporting` | **仅离线测试**（开发机无 ChatGPT 登录，readiness 会报出登录缺口） |
| `deepseek`（dsh） | harness | **API Key** | `sandbox_read_only` `system_prompt` `api_keyed`——**注意没有 `mcp_tools`**，见下 | 最新加入 |

`claude-code` 的能力集最全；`codex` 与 `deepseek` 靠 OS 级只读沙箱而不是关闭
内置工具；`cursor` 两者都做不到，因此额外配了事后审计（见 §5）。

**`deepseek` 是个例外，有两处打破常规，都要记住**：

1. **它是 harness，却需要 API Key。** 通过 Python SDK 驱动（PATH 上没有二进制，
   运行时随 wheel 发布），凭据是 `DEEPSEEK_HARNESS_API_KEY`（缺省回退
   `ANTHROPIC_API_KEY`）。注册表用 `api_keyed` 标出这个不对称，供那些默认
   "harness ⇒ 凭据在厂商那边"的调用方判断。
2. **它用不了我们的工具桥**——这是实测结论不是选择。它捆绑的运行时编译进了 122
   个插件，`@deepseek-ai/dsh-mcp-client` 不在其中，所以 dsh 的 lens 跑在 harness
   自带的 `bash` + `str_replace_editor` 上，我们的 scoped 工具（含考古工具组）
   **作为具名工具不可达**。bash 能覆盖其中大部分（它们本就是薄薄的 git 包装），
   但那些调用**落在我们的审计轨迹之外**，因此每个拿到桥 spec 却无法履约的会话都会
   记一条 `capability_gap`。

   > **由此而来的一条硬规矩：跑在原生 bash 上的 arm，绝不能被标成"tools
   > bridged"。** 本轮战役已经测到过三个 arm 与其标签不符。

## 3. 怎么选

**默认用 `api`。** 它是唯一行为完全确定、成本可测、且所有评测结论都建立其上的
后端。选别的只有三个理由：

1. **你只有订阅，没有裸 Key** —— 用 `cursor` / `claude-code` / `codex`。
2. **你要按 pass 混搭模型** —— 见 §4 的 `REVIEW_LENS_BACKENDS`。
3. **你在做后端对比实验** —— 先读 §6 的实测结果，别重复已有结论。

反过来，有一条**不该**选 harness 的理由值得写下来：harness 会话
**不向 span 记账暴露 token**（每一项都记 `tok_out=0`），所以它们的成本优势是
**假定的，不是测出来的**。metrics 会把来源记成 `subscription`，绝不编造 USD。

## 4. 怎么配

```bash
# ~/.infermatrix-copilot/.env
STRICT_BACKEND=api            # api | cursor | claude-code | codex | deepseek
# STRICT_BACKEND_MODEL=       # harness 内部的模型 id（可选，见下）
# STRICT_BACKEND_CONCURRENCY=2  # 并发 harness 会话数
# STRICT_BACKEND_CLI=         # 二进制路径覆盖（否则走 PATH 查找）
# STRICT_BACKEND_TIMEOUT_S=1800 # 单会话墙钟上限
```

**`STRICT_BACKEND_MODEL` 留空时谁来定模型。** 三个订阅制 CLI
（`cursor`/`claude-code`/`codex`）自己挑模型，留空即可。**`deepseek`（dsh）没有内建
缺省**——空模型会让每一轮以 `has no provider/model` 失败，所以它在 provider 注册表里
声明了 `default_model: deepseek-v4-pro`，由 `Settings.tier_target` 解析。因此留空时
run 报告的模型与实际服务的模型仍然是同一个（不会出现 target 记 `""`、dsh 实跑
`deepseek-v4-pro` 这种贴错标签）。想换模型就显式填这一项。

**显式选择，硬报错。** 未知 id 在 `Settings` 校验阶段就被拒（会列出合法取值）；
Strict 启动前 `strict_readiness` 先查缺项，**绝不启动一个注定失败的后台任务**。
没有自动探测，没有静默回退——这与 `TierNotConfiguredError` 是同一套哲学。

**按 pass 路由**（把测出来的模型互补性变成一条 arm）：

```bash
REVIEW_LENS_BACKENDS=adversary=claude-code:...,round2=claude-code:...
```

把某个评审 pass 映射到 `provider:model`，让那个 seat 跑在别的后端上。改之前先读
[`eval/dataset/results/model_comparison.md`](../../eval/dataset/results/model_comparison.md)。

## 5. 换后端不会绕过权限闸

这是接入 harness 时最要紧的一条：**厂商 agent 自带工具循环，但它拿到的工具是
我们给的**。

- **工具经 MCP tool bridge 回流**（`tool_bridge.py`）：harness 会话拿到的是
  copilot 自己的 scoped 工具，每一次调用仍然经过 `tools.dispatch`，
  `ToolScope` / `PathScope` 检查与 trace 记录一个不少。桥比进程内循环还**多两条
  收紧**：读取也受容纳根约束（`ToolScope` 本身只管写；harness 是持有不可信 diff
  的低信任调用方，这是防 `.env` 外泄的那道），且工具事件写独立的
  `bridge_trace.jsonl`，不与父进程的 `run_trace.jsonl` 交错。
  桥提供内置工具 + `doc_search`/`doc_read` + 按需 `repo_map` + 考古工具组；
  **skill/memory 检索刻意不开放**——那两个能提知识 candidate，跨进程写入口没有开。
  **例外：`deepseek` 用不了这座桥**（见 §2），它的调用落在审计轨迹之外。
- **能关内置工具的就关**（`builtin_tools_off`，claude-code）；
  **关不掉的用 OS 级只读沙箱**（`sandbox_read_only`，codex / deepseek）。
- **两者都做不到的（cursor-agent）额外上事后审计**（`providers/audit.py`）：
  检查文件读取是否越出会话的容纳根（PR-time worktree + run 目录），只读 scope
  下是否出现了 write/edit 调用。这是**侦测型而非预防型**的兜底，
  结论会写进 RUN_REPORT——**公开声明，绝不静默**。
  （这套检查是从 Composer 评测臂产品化过来的，它当初真的抓到过一次越界读
  `~/.claude/skills/...`。）
- **子进程环境是白名单**（`providers/base.py::sanitized_env`）：只保留
  `PATH` `HOME` `TERM` `COLORTERM` `LANG` `USER` `LOGNAME` `SHELL` `TMPDIR`
  以及 `LC_*` / `XDG_*`。厂商 CLI 必须保住自己的订阅认证（存在 HOME 状态里），
  但**绝不能继承我们的模型端点变量**——这类机器上的 `ANTHROPIC_BASE_URL`
  往往指向某个网关，继承过去会**悄悄把厂商 CLI 的流量改道**。API Key、
  gh token、`CLAUDECODE` 这类宿主标记也一并丢弃。

## 6. 实测特点（2026-08-17）

> 数据以 [`eval/dataset/results/model_comparison.md`](../../eval/dataset/results/model_comparison.md)
> 为准，它比这张表更新得勤。方法论与完整结论见
> [`GUIDE.md §8`](../GUIDE.md#8-性能对比)。

同一批 10 个 train item 上的后端冠军是 **api/DeepSeek 核心，不是 Composer**：

| 配置 | Δrecall [95% CI] | Δprecision [95% CI] |
|---|---|---|
| v17ds train（api/DeepSeek） | **+.024 [−.030, +.077]** | **+.016 [−.061, +.093]** |
| v17cb train（Composer 2.5 / cursor） | −.052 [−.165, +.061] | −.097 [−.215, +.021] |

val 一度把 Composer 排前面，那是 n=5、区间 ±.22 的小样本幻觉；train 的 item
方差紧四倍（sd .075 vs .158）。**每个 CI 都跨零**——结论是"测量精度内打平"，
不是"更优"。

速度与成本：harness 后端快 2–4 倍（Composer 350–680s vs api 1000–2900s 每项）
且吃订阅，但如 §3 所述，**成本优势未经测量**。

一条安全提醒：**grok 家族（4.5 / 4.6，Composer 从未出现）会在评审会话中主动
搜索并读取 copilot 自己的 `imreview` 方法论 skill**。相关评测臂已作废并进污染
台账。跑 cursor 系评测前，三份 skill 副本必须移出 `$HOME` 并在事后恢复。

## 7. 排查

```bash
infermatrix-copilot doctor          # 逐项 ✓/✗，失败即给出唯一修复命令
infermatrix-copilot doctor --probe  # 每档模型 1-token 实探（唯一付费检查）
```

| 症状 | 原因与修法 |
|---|---|
| `unknown STRICT_BACKEND 'x'` | 配置校验拒绝了未知 id；合法取值已在报错里列出 |
| `... backend selected but no CLI found` | 厂商 CLI 不在 PATH；装上，或设 `STRICT_BACKEND_CLI=/path/to/cli` |
| readiness 报登录缺口 | 该 harness 的订阅未登录（`codex` 在开发机上就是这个状态）；用厂商 CLI 自己的登录命令 |
| `deepseek` 报缺凭据 | 设 `DEEPSEEK_HARNESS_API_KEY`（或 `ANTHROPIC_API_KEY`） |
| Strict 直接返回缺项而没起任务 | 这是**设计行为**：`strict_readiness` 不会启动注定失败的后台任务 |

各后端的判定逻辑在 `providers/<id>.py::auth_gap()`——它只做一次廉价的状态调用，
拿不准就返回 `None` 让运行期大声失败，而不是猜。

## 8. 加一个新后端

1. 在 `providers/registry.py::PROVIDERS` 加一条 `ProviderSpec`（id / kind /
   display / cli_names / capabilities）。
2. 实现 `HarnessTransport` 子类：`run_session()`（一整个 agent step）+
   `complete()`（一次性无工具调用，供 `HarnessLLM`），可选 `auth_gap()`。
3. 在 `transport_for_id()` 里接上。未实现的后端登记进 `_UNSHIPPED`，
   这样 readiness/doctor 会报"尚未发布"而不是运行到一半失败。
4. 测试：`test_providers.py` + 对应的 `test_provider_<id>.py`。

设计决策记录在 [`../features/provider-registry.md`](../features/provider-registry.md)。
