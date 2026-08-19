# Provider registry —— Strict 的五种后端

> **一览**
> | | |
> |---|---|
> | **状态** | ✅ 已实现。`api` / `cursor` / `claude-code` / `deepseek` 已实测；`codex` 仅离线测试（开发机无 ChatGPT 登录，readiness 会报出登录缺口） |
> | **做什么** | 让只有编码 Agent 订阅、没有裸 API Key 的用户也能跑 Strict；顺带把原有 api 路径收编进同一张注册表 |
> | **怎么开关** | `STRICT_BACKEND=api\|cursor\|claude-code\|codex\|deepseek`（另有 `STRICT_BACKEND_MODEL` / `_CONCURRENCY` / `_CLI` / `_TIMEOUT_S`） |
> | **怎么用** | 面向使用者的说明在 [`../guide/backends.md`](../guide/backends.md) |
> | **实测** | 后端对比见 [`eval/dataset/results/model_comparison.md`](../../eval/dataset/results/model_comparison.md)；结论摘要在 [`../GUIDE.md §8`](../GUIDE.md#8-性能对比) |
> | **硬边界** | 用 `api` 时行为**逐字节不变**（平价棘轮）；harness 会话的工具一律经 `tools.dispatch`；子进程环境是白名单 |
>
> 以下是原始决策记录（RFC），保留它是因为其中的取舍——为什么接入点必须是
> `run_session()` 而不是 `LLM.create()`、为什么工具治理分预防/侦测两级——
> 至今仍在约束这块代码。

---

## 原始 RFC

- 状态：已接受（2026-08-14 的 grilling 会话）；M1（注册表、api 平价、工具桥、
  cursor transport）已在 PR #81 合入并实网冒烟；M2 claude-code 与 M3 codex 已在本分支
  实现 —— claude-code 已在订阅认证下实网冒烟，codex **仅离线测试**
  （开发机没有 ChatGPT 登录；readiness 会报出这个登录缺口）。
  工具桥另外提供按需的 `repo_map`；skill/memory 检索工具**仍然仅限进程内**
  （跨进程的 candidate 写入**刻意未开放**）。
- 归属：LLM/后端层（`llm.py`、`config.py`）、agent 运行时
  （`engine/agent_runtime/runner.py`）、新增的 `src/infermatrix_copilot/providers/`
- 研究过的先行工作：Hermes Agent 的 `api_mode` transport
  （hermes-agent.nousresearch.com/docs/developer-guide/adding-providers）·
  opencode 的 provider 注册表（opencode.ai/v2/docs/providers）

## 动机

Strict 模式跑完整执行主脊，而每一次模型调用都经过 `llm.py::LLM` ——
一个需要 `ANTHROPIC_API_KEY` 或 `OPENAI_API_KEY` 的原始 Anthropic/OpenAI 兼容
completions 客户端。**只有编码 agent 订阅**（Claude Code Pro/Max、Codex CLI 用的
ChatGPT 套餐、Cursor）作为模型访问方式的用户，**根本跑不了 Strict**。

Claude Code、Codex CLI 和 cursor-agent 在订阅认证下**不暴露原始 completions API**
—— 它们是**自带工具循环的 agent harness**。所以接入点不可能是 `LLM.create()`
（无状态的 `system+messages+tools → tool_use` 往返）；它必须上移一层，
落在**委托一整个 agent step** 的位置。

Hermes 用一个 `api_mode` transport 抽象解决了相邻的问题（规范化的内部消息形状；
逐模式的请求构建、响应归一化、用量抽取适配器；一条标准化的运行期解析记录）。
本代码库其实已经走了一半：Anthropic 的 block 协议就是我们的规范形状，
`_openai_messages()` 就是一个 transport 适配器，`Settings.tier_target()` →
`ResolvedTarget` 就是运行期解析。本 RFC 把这些**形式化成一张 provider 注册表**，
并加上 Hermes 只在它的跨进程 Codex 路径上才需要的那条轴：
**transport kind**（`api` vs `harness`）。

## 决策（与维护者锁定，2026-08-14）

1. **目的：产品覆盖面。** 让没有裸 API key 的用户能在订阅认证下跑 Strict。
   保真度按 harness **尽力而为**，并**逐 run 标注**。评测/战役表格不受影响 ——
   一个 harness 后端测量的是**循环 + 模型**，**绝不**被并入生成器消融表
   （长期规则：生成器臂骑我们的流水线，**只换模型**）。
2. **显式选择，硬报错。** 由一个 `.env` 键选定后端。对于**没有选定后端**的 Strict run，
   服务端会在**前面**带着确切缺失项报错（与 `TierNotConfiguredError` /
   `strict_readiness` 同一套哲学）。**没有自动探测，没有静默回退。**
3. **工具经桥回流，预防优先。** harness 会话经 MCP 拿到 copilot 自己的工具，
   每次调用都过 `tools.dispatch`（ToolScope/PathScope 这个 choke point 被保住）。
   harness 支持时**关闭厂商内置工具**；cursor-agent 另外配上产品化的运行后审计
   （纵深防御），并把**控制类别**披露在 RUN_REPORT 里。
4. **统一注册表。** 既有的 API 路径成为同一张表下的 provider `api` ——
   **一条解析路径、一套 trace 词汇**。平价棘轮：用 provider `api` 时行为**逐字节一致**，
   而既有测试套件就是那道门。
5. **分期：cursor-agent 先行**，然后 Claude Code，然后 Codex。

## 设计

### 术语

- **provider id** —— 注册表的键，也是选择配置的取值：
  `api`、`cursor`、`claude-code`、`codex`。
- **kind** —— `api`（无状态 completions；实现 `complete`）或
  `harness`（自带工具循环；实现 `run_session` + 一次性的 `complete`）。
- **api_mode** —— `api` provider **内部**的线上协议：
  `anthropic_messages` | `chat_completions`。这**恰好**就是今天的
  `Settings.resolved_llm_provider`；既有代码里的 "provider" 一词
  （`llm_provider`、`ResolvedTarget.provider`）**继续**指 API 厂商协议，
  原样映射到 api_mode。

### 包布局

```
src/infermatrix_copilot/providers/
  __init__.py     再导出；register_builtin_providers()
  base.py         ProviderSpec + Transport 协议 + 会话数据类
  api.py          provider "api"：包住既有的 LLM 类（两种 api_mode）。
                  包装，不是重写 —— LLM 内部、tier_target、served-model
                  守卫、tracing 全部不变。
  cursor.py       M1 harness transport（cursor-agent CLI）
  claude_code.py  M2 harness transport（claude -p）
  codex.py        M3 harness transport（codex exec）
  audit.py        运行后会话审计（从 eval/dataset/run_cursor_arm.py 产品化）
  registry.py     PROVIDER_REGISTRY + resolve_provider(settings)
src/infermatrix_copilot/tool_bridge.py
                  暴露该 run scoped 工具的 stdio MCP server
                  （入口：python -m infermatrix_copilot.tool_bridge）
```

### base.py —— 那些契约

```python
@dataclass(frozen=True)
class ProviderSpec:
    id: str                      # "api" | "cursor" | "claude-code" | "codex"
    kind: Literal["api", "harness"]
    display: str
    cli_names: tuple[str, ...] = ()      # 要探测的二进制（harness）
    capabilities: frozenset[str] = frozenset()
    # 能力标志: "mcp_tools", "builtin_tools_off", "max_turns",
    # "system_prompt", "usage_reporting", "cost_reporting"

class Transport(Protocol):
    # api kind + harness 的无工具调用；签名镜像 LLM.create
    def complete(self, *, system, messages, tools=None, model=None,
                 max_tokens=None, on_text=None, role="") -> Reply: ...
    # 仅 harness kind：一整个 agent step
    def run_session(self, req: AgentSessionRequest) -> AgentOutcome: ...
```

`run_session` 返回既有的 `agent_loop.AgentOutcome`（text、iterations、
tool_calls、truncated、refusals、token 用量、tools_used），
于是 runner 分叉**之后**的一切 —— `_coerce_output`、`agent_output` trace 事件、
`_to_step_result` —— **原封不动**。harness 无从得知的字段（iterations）尽力而为；
`tools_used` 来自桥的 trace。

### 解析 —— 一个地方，做了扩展

`ResolvedTarget`（config.py）新增两个带默认值的字段，使**每一处既有构造点仍然有效**：

```python
provider_id: str = "api"
kind: Literal["api", "harness"] = "api"
```

`Settings.tier_target()` 仍然是**唯一**把 模型×端点×凭据 配对起来的地方；
当 `strict_backend` 选中一个 harness provider 时，它返回带该 provider id/kind 和 harness
模型（`STRICT_BACKEND_MODEL` 或该 provider 默认值）的目标 ——
**base_url/api_key 为空**（订阅认证住在 harness CLI 里，**绝不在我们的配置里**）。
`LLM.for_target()` **只**对 `kind == "api"` 的目标被咨询。

选择范围：**Strict run 必须有 `STRICT_BACKEND`** —— 在
`CopilotMCP.strict_readiness()` 里检查（与当前的 `shared_api_key` 检查并列，
后者变成 `api` provider 的就绪项），并在子进程的
`--execute-strict-reserved` 启动时**再检查一次**。CLI 路径（`run_task`）把空值当作
`api` —— 对维护者**没有破坏性变更** —— 将来可能长出一个 `--backend` flag。

### runner 分叉 —— 唯一的接入点

在 `run_agent_step`（engine/agent_runtime/runner.py:170）里，当前这次调用

```python
outcome = await asyncio.to_thread(run_agent, step_llm, system=..., ...)
```

变成按解析出的目标 kind 做**二选一分叉**。`harness` 目标把桥 spec（见下）写进 run 目录，
并在**同一个 worker 线程**里调用 `provider.run_session(...)`。
分叉**之前**的一切（dispatch context、证据包、briefing、把 scope 绑到 PR-time worktree
根、`agent_dispatch` trace）和分叉**之后**的一切（`_coerce_output` 及其一轮修复与升级
抢救、`agent_output` trace、skill touch）都是**共享的** ——
**harness 骑的是完全相同的 v13 prompt 包和输出契约。**

无工具的角色（评审 planner 的灰区调用、ensemble reducer/merge、覆盖率提升、
`_coerce_output` 修复）经一个实现了 `LLM.create()` 签名的 `HarnessLLM` 适配器：
**传入非空 `tools` 时它抛错**，否则跑一次性 CLI 调用，并返回带 CLI JSON 用量的
归一化 `Reply`。它的 `available` 属性镜像 doctor 的 CLI 探测，
于是 `run_agent_step` 的 `ctx.llm.available` 门继续有效。对 cursor，
一次性 completion 在一个**空的临时 cwd** 里运行，好让原生工具**无物可读**。

MoA（`for_member`）在 v1 里**拒绝**把 harness provider 作为混合成员 ——
预约台账需要**逐请求定价**，而订阅制 CLI 给不出。

### 工具桥 —— 保住 choke point

`python -m infermatrix_copilot.tool_bridge --spec <run_dir>/bridge/<step>.json`
是一个 stdio MCP server（FastMCP，已在 `[mcp]` extra 里），
**恰好**暴露该 step 的 scope 所允许的那些工具。spec 文件序列化：

- 那个 `ToolScope`（frozen dataclass → JSON：name、allowed_tools、read_only、
  root、path_scope 模式）—— 可轻松往返；
- 仓库名 + repo_path（PR-time worktree）、run_dir；
- 要重建哪些额外工具族（knowledge/doc/repo_map）—— 它们在桥进程里由
  `Settings()` + adapter 重建，用的是**与 runner 相同的工厂**
  （`_knowledge_tools`、`_repo_map_tool`、`_repo_docs_tool`）。

每个 MCP 工具 handler 都是套在
`tools.dispatch(name, args, scope=scope, trace=bridge_trace, extra=extra)`
之上的**薄壳** —— 拒绝、越界记录、相对 worktree 根的路径解析、结果封顶，
**全部与进程内循环表现一致**。桥追加写 run 目录里的 `bridge_trace.jsonl`
（自己的文件：来自第二个进程的仅追加 jsonl **绝不能**与父进程的 `run_trace.jsonl`
交错）；会话结束后 runner 把摘要（tool_calls、tools_used、refusals）折进正常 trace 事件。

守卫测试（外泄用例）：经桥 `read_file` 读取
`~/.infermatrix-copilot/.env` —— 位于 scope 根之外 —— **被拒绝并记 trace**。

### 环境净化 —— 承重

harness 子进程拿到的是**构造出来的白名单环境**（PATH、HOME、TERM、LANG/LC_*、
按需的 PYTHON*，加上 provider 专属变量），**绝不是** `os.environ` 透传。
就在这台机器上的具体危险：

- 我们的 `.env` 把 `ANTHROPIC_BASE_URL` 指向一个 DeepSeek 兼容网关 ——
  一旦泄漏进 `claude`，订阅调用会被**路由到错误端点并计到错误账户上**；
- 环境里存在的 `ANTHROPIC_API_KEY`/`OPENAI_API_KEY` 会**悄悄**把这些 CLI
  从订阅认证切换成 API 计费；
- 当 Strict 的宿主**本身就是** Claude Code 时，`CLAUDECODE`/宿主标记会让嵌套的 CC 混乱。

Strict 子进程本身已经从 server worker 那里收到一份精选环境
（mcp_server.py:100–115）；**同一套纪律再向下延伸一层**。

### 守卫与记账

- **served-model 守卫**：harness CLI 在它们的 JSON 输出里报告实际使用的模型；
  经既有的 `llm.served` 事件记录，裁决逻辑不变
  （不匹配 → 按 `MODEL_MISMATCH_POLICY` 失败；缺失 → `unverified`，告警）。
- **用量/成本**：token 计数从 CLI JSON 解析（claude `-p --output-format json`
  含用量 + 成本；codex `--json` 发出 token 事件；cursor stream-json 含用量）。
  `metrics.py` 把成本来源记为 `subscription`，且**对 harness provider 不查
  `MODEL_PRICES`** —— **CATQ 的 C 项绝不能编造 USD。**
- **ensemble 错峰**（`ensemble_stagger_seconds`）对 harness 目标**禁用**：
  跨 CLI 会话**不存在**可预热的共享 prompt-cache 前缀。每个被委托的 pass 就是一次
  harness 会话，所以 32 轮深度 pass 内部的上下文缓存是 harness 自己的事。
- **并发**：`STRICT_BACKEND_CONCURRENCY`（默认 2）是并发会话上的信号量
  （深度 pass + 验证扇出）—— **订阅的速率窗口是真实存在的**；
  认证/限流错误浮现为 BLOCKED，**绝不重试到被封**。

### 配置 schema（.env）

```
STRICT_BACKEND=                # Strict 必需：api | cursor | claude-code | codex
STRICT_BACKEND_MODEL=          # harness 内部的模型 id（可选）
STRICT_BACKEND_CONCURRENCY=2   # 并发 harness 会话数
STRICT_BACKEND_CLI=            # 二进制路径覆盖（否则走 PATH 查找）
STRICT_BACKEND_TIMEOUT_S=1800  # 单会话墙钟上限
```

安装器和 `.env.template` 写入 `STRICT_BACKEND=api`，于是既有环境随文件刷新即可迁移；
缺失时 `strict_readiness` 会点名**确切的修复行**。`doctor` 增加逐 provider 检查：
二进制是否找到 + 版本、认证状态、桥自检（拉起、列工具、一次受 scope 的读取）；
`doctor --probe` 经选定 provider 做一次**廉价往返**。

### Cursor transport（M1 细节）

- 调用：`cursor-agent --print --output-format stream-json --force`，
  prompt 走 stdin，`--model` 来自配置，MCP 配置文件指向工具桥，
  cwd = PR-time worktree。
- 解析、会话记账和边界 prompt 行**复用 Composer 评测臂已经学到的东西**
  （`eval/dataset/run_cursor_arm.py`）—— 包括那次冒烟 run 读了
  `~/.claude/skills/` 的事故。
- **要先做 spike 的未决问题**：在配置了 MCP 工具时，cursor-agent 能否关闭它的内置工具。
  能 → 预防型；不能 → 桥是**附加的**，而 `providers/audit.py` 就是执行层：
  每次文件访问都做 realpath 归一化的 worktree 边界、写入禁令、讨论访问正则；
  裁决 + 标志进 trace 并渲染进 RUN_REPORT
  （"backend: cursor —— 原生工具可能可用，审计：干净/N 个标志"）。
- 没有 `--max-turns` 的对应物 → 墙钟超时 + 既有的预算纪律 prompt 行
  （把最后几轮留给契约）。

### Claude Code（M2）与 Codex（M3）

- `claude -p --output-format json --mcp-config <bridge> --allowedTools
  <仅桥工具> --max-turns <预算> --model <m>`；**最守规矩的 harness 公民**
  （内置工具可完全关闭、原生 max-turns、支持 system prompt、输出含用量 + 成本）。
- `codex exec --json --sandbox read-only` + 配置里的 MCP server；
  **没有 system-prompt 通道**（契约前置到 prompt 里）；预算靠超时。

## 里程碑与验收

**M1 —— provider 层 + cursor-agent**

1. `providers/` + 注册表 + `ResolvedTarget` 扩展 + 包住 `LLM` 的 `api` provider。
   验收：**不改任何配置**的情况下既有全套测试绿；`STRICT_BACKEND=api` **逐字节一致**
   （平价棘轮）。
2. 工具桥 + 桥测试。验收：dispatch 平价（与进程内相同的拒绝/上限）、
   `.env` 外泄读取被拒并记 trace。
3. cursor transport + 审计 + doctor 检查 + readiness 接线。验收：假 CLI 离线测试绿；
   在一个小 PR 上做一次实网 Strict 冒烟，RUN_REPORT 里带后端标签、用量和审计裁决；
   Strict 启动时未设 `STRICT_BACKEND` 会给出**确切的修复行**报错。

**M2 —— claude-code** · **M3 —— codex**：同样的验收形状（离线假 CLI 测试 + 各一次实网
冒烟）；M2 另外要证明在净化环境下**嵌套 CC**（Strict 宿主 = Claude Code）能工作。

## 测试计划（离线优先，本仓库纪律）

- `test_providers.py` —— 注册表解析；Strict 与 CLI 在空选择下的行为差异；
  `HarnessLLM` 在带工具时抛错；MoA 成员拒绝；档位交互
  （`tier_target` 返回 harness 目标）。
- `test_tool_bridge.py` —— spec 往返；经桥的 scope 强制；桥 trace 内容。
- `test_provider_cursor.py` —— 用发出预置 stream-json 的 fixture 脚本：
  最终文本抽取、用量解析、超时 → truncated 结果、审计标志浮现。
- doctor：逐 provider 的检查渲染 + 修复行。
- 棘轮不受影响：`test_repo_neutral_core`、`test_llm_providers.py`、
  `test_tier_split.py`、`test_thin_mcp_server.py`、`test_mcp.py`。
- 实现之后，在 `doc/architecture/SPEC/` 下为 `providers/` 和 `tool_bridge.py`
  新增 SPEC 页（本仓库规矩：**逐文件约束住在那里**）。

## 风险与未决问题

1. cursor-agent 能否限制内置工具**未知** → M1 做 spike；治理兜底**已经定好**
   （审计作为执行层）。
2. 在没有 system-prompt 通道时的契约遵从度（cursor/codex）——
   由既有的修复 + 升级抢救路径吸收；**先在冒烟里观察，再决定是否信任**。
3. harness 的内部推理对我们的 trace 是**不可见的**；只有经桥的工具调用被审计。
   **逐 run 声明 —— 绝不把它呈现为全保真的 Strict tracing。**
4. 订阅 ToS/速率限制：并发封顶，限流错误**大声 BLOCK**。
   用户通过显式选择后端，来自行决定把哪个账户暴露出去。
5. harness 内部的模型命名（composer id、codex 模型 slug）——
   `doctor --probe` 报告 CLI **实际服务**的是什么；served-model 守卫逐次调用记录它。
