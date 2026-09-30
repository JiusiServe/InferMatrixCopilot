# providers/zcode.py —— 规范

<!-- verified-against: 2026-10-01 -->

`LOC ~400 · harness transport（Z.AI / GLM 订阅） · refactor-status: ok`

## 职责
在 Z.AI OAuth 订阅认证下，通过 `zcode` CLI 跑完**一整个** agent step。

## 功能
headless `zcode --prompt=... --output-format stream-json --mode plan --cwd <临时目录>
--disallowed-tools=<非读工具>`；工具桥写进临时目录的 `.zcode/config.json`；从事件流解析
`result.response`、`result.usage`、`session.updated.modelId` 和 `tool.updated`（`kind:
scheduled`）。prompt 超过 100,000 字节时写成文件并 `--attach`（zcode 没有 stdin 通道，
argv 单参数上限 128KiB）。

## 公开契约
`ZCodeTransport`（`auth_gap`、`run_session`、`complete`）、`spec = PROVIDERS["zcode"]`。

## 不变量（**C1**、**C2**）
- **会话 cwd 永远是自有临时目录，不是 PR worktree。** zcode 从 cwd 加载 `.env`，并从 cwd
  往上到 git 根发现 `zcode.json` / `.zcode/config.json`，项目配置里的 stdio MCP server 会被
  直接连接。PR checkout 不能成为 cwd；仓库按绝对路径读取。
- **非读工具靠剥离，不靠信任。** `--mode plan` 下仍有 node REPL MCP、子 agent（能拿到
  shell）、workflow、联网抓取；`_DISALLOWED` 把它们全部去掉（实测 28 → 11 个工具，全是读）。
  每次会话事后对照 `_READ_TOOLS` + 工具桥前缀审计，越界记为 `audit:` refusal——zcode 新版本
  加了而拒绝列表漏掉的工具会被**侦测到，不会静默**。保留下来的原生读工具
  （`Read`/`Grep`/`Glob`，读超长 prompt 附件要用）还要做容纳审计：路径（含绝对 glob 的根）
  落在 checkout、run 目录、会话临时目录之外即违规（复用 `audit.contained_in`；glob 的字面前缀
  按搜索目录解析，`../../etc/*` 这类穿越也会被抓到）。这是侦测型；预防型的读取走工具桥。
- **`complete()` 连原生读工具也去掉**（输入可能是不可信文本）；只有 prompt 超长、必须靠
  `Read` 读附件时才保留 `Read`，且任何读到临时目录之外的调用都让这次调用失败。
- **失败的运行不能读成空评审。** 非零退出或流里没有 `result` 事件（未超时时）直接抛
  `RuntimeError`，带上 zcode 自己的 stderr。
- **模型按次钉死，再断言。** zcode 没有 `--model`；一个会话取其个人 provider 配置里的
  `defaultModelSelection`，且仅当该条目**可选**（0.16.9 的 `resolveInitialModelSelection` 要求
  `options.reasoningLevel` 存在，否则静默回退到目录里第一个模型——这就是过去手写条目"不起作用"的原因），
  并按**区分大小写**的相等匹配模型 id（`glm-5.3-flash` 选不中，同样回退）。传输层因此在会话临时目录写一份
  **最小**个人配置：空的 provider/model 规则集 + `defaultModelSelection`（provider id 取 `zcode_provider_id`，
  缺省读宿主条目的 id，再缺省为 Z.AI 个人 coding plan；模型 id 经 `canonical_model_id` 按目录拼写规范化——
  宿主 `runtime/provider/**/zcode-builtin.json` 里的 id 加 0.16.9 的内置清单，未知 id 原样写入；
  `options.reasoningLevel` = `zcode_reasoning_level`，low/high/max，缺省 max），用
  `ZCODE_PERSONAL_PROVIDER_CONFIG_FILE` 指给子进程。**宿主文件除 provider id 外一概不读入**：会话目录是
  zcode 会话的读根，宿主 provider 规则可能带 API key，不能落在里面；宿主文件从不改写。请求的模型
  （`req.model` / `STRICT_BACKEND_MODEL`）仍与流里的 `modelId` 不区分大小写比对，不一致时按
  `MODEL_MISMATCH_POLICY` 处理（缺省 `fail`）；未请求模型时不写配置，服务宿主缺省。注册表仍不声明 `default_model`。
- `auth_gap()` 只检查 `~/.zcode/v2/credentials.json` 是否存在（zcode 没有登录状态命令）；
  存在不代表 token 仍有效，过期会在第一次运行时大声失败。子进程保留 `ZCODE_DATA_BASE_DIR`，
  保证检查的目录与运行登录用的是同一个。

## 边界 —— 不属于这里
不改 zcode 的全局配置（`~/.zcode/v2/provider_config.json` 属于宿主）；不编造用量或模型。

## 依赖（允许）
stdlib + `.base` + `..agent_loop.AgentOutcome` + `..llm` 的类型与 `ModelMismatchError`。

## 测试
`test_provider_zcode.py`（离线，事件形状取自 zcode 0.16.9 实跑）；2026-09-30 用真实 zcode 做过
一次端到端冒烟（工具桥 `read_file` 被调用，`bridge_trace.jsonl` 有记录）。

`complete()` 接受并忽略 `max_budget_usd`；`stops_at_spend` 为 False（CLI 无花费阈值，`ModelGateway` 请求阈值时在派发前拒绝）。
