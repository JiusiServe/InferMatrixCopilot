---
title: "jiuwenswarm/common/：公共基础模块"
created: 2026-09-30
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources:
  - openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/config.py
  - openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/model_selection.py
  - openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/model_catalog.py
  - openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/model_config_validation.py
  - openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/permission_tools.py
  - openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/mcp_config.py
  - openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/test_model_selection_migration.py
  - openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/test_config.py
  - openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/common/test_model_config_validation.py
  - openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/common/test_config_concurrent_models.py
---

# jiuwenswarm/common/：公共基础模块

Gateway 和 AgentServer 共用的基础层，负责 config.yaml 的读写与迁移、模型目录、模型选择与校验、运行模式解析、工作区路径，以及南北向客户端契约等共享逻辑。进程监管、启动诊断、自动升级、后台清理和异步状态转储等进程级工具也放在这里。

**从这里读起**

- `jiuwenswarm/common/config.py` — get_config / update_config：读取 config.yaml 并展开环境变量，加锁后原子写回，同时提供各特性开关的读取函数
- `jiuwenswarm/common/mode_matrix.py` — resolve_request_mode：把 Web 的 agent/team/agent.plan 和 work_mode 组合成 canonical mode，并据此路由到 Deep 或 Code Adapter
- `jiuwenswarm/common/model_catalog.py` — ModelCatalog：只读目录，统一提供默认模型、AgentOS 模型和模型组
- `jiuwenswarm/common/client/agent_client.py` — AgentServerClient 抽象：与 AgentServer 通信的南北向契约，Gateway 仓另有一份副本
- `jiuwenswarm/common/process_supervision.py` — supervise：监管 AgentServer 和 Gateway 子进程，判断哪些退出需要重启
- `jiuwenswarm/common/startup_diagnostics.py` — doctor_main：只依赖标准库的 --doctor 启动诊断，用于排查打包桌面版启动失败
- `jiuwenswarm/common/updater.py` — UpdaterService：负责版本检查、安装包下载和升级执行
- `jiuwenswarm/common/cleanup.py` — start_background_cleanup：按保留期定期清理旧会话数据和 file_ops 日志

**关键文件**

- `jiuwenswarm/common/model_selection.py` — ModelSelection 和 Resolved* 等 DTO，描述稳定的模型选择与模型组选择
- `jiuwenswarm/common/model_config_validation.py` — 校验模型目录和模型组 patch，并探测模型连通性
- `jiuwenswarm/common/kv_cache_affinity_config.py` — KV cache 亲和配置和 provider 规则的权威定义
- `jiuwenswarm/common/mcp_config.py` — 把 config.yaml 的 MCP 条目转成运行时配置，也负责预检、探活和预热
- `jiuwenswarm/common/hooks_config.py` — 定义 config.yaml 中 hooks 段的 schema 和事件匹配逻辑
- `jiuwenswarm/common/projectless_workspace.py` — 为无项目请求在 Documents/JiuwenSwarm 下分配按日期划分的任务目录，并登记会话
- `jiuwenswarm/common/team_artifacts.py` — 确定 Team 成员工作目录和共享交付目录的根路径
- `jiuwenswarm/common/cron_team_completion.py` — Gateway 和 AgentServer 共用的 cron 团队轮次结束判定
- `jiuwenswarm/common/chat_final.py` — chat.final 的 final_mode 字段（patch_segment / replace_turn / append），决定前端如何落地最终回复
- `jiuwenswarm/common/client/agent_http_bridge.py` — 解析受认证 HTTP bridge 的基址并执行大文件上传，大文件因此不走 E2A 帧
- `jiuwenswarm/common/security/ws_origin.py` — 共享的 WebSocket Origin 校验
- `jiuwenswarm/common/_build_config.py` — 由 scripts/build_config.py --sync 生成，不要手改

**相关文档**

- `docs/zh/E2A-protocol.md` — 改 client/ 下的南北向契约或上传通道时，对照 E2A 线协议
- `docs/zh/MCP配置.md` — 改 mcp_config.py 里 MCP 条目的解析或凭据处理时读
- `docs/zh/AgentTeam.md` — 改 team 模式解析、team_artifacts.py 或 cron_team_completion.py 时读
- `docs/zh/Harness.md` — 改 cron_team_completion.py 里 harness 轮次结束条件时读
- `TESTING.md` — 给本模块补测试时参考；其中有过期路径，要先核对 tests/ 下已有的用例

## 配置读取与环境变量解析

- `get_config()` 的流水线固定为 `_read_with_retry` → `resolve_env_vars` → `_normalize_config`，env 解析和归一化在锁外执行以缩短锁持有时间。只有 YAML parse 结果进缓存：键是文件身份 `(mtime_ns, size)`，命中与写入都深拷贝，文件 mtime_ns 或 size 改变时会使缓存失效；不能检测保持两者不变的内容改写，而 `load_dotenv_runtime(override=True)` 后的新环境变量下一次读取立即生效，无需显式失效钩子（[config.py L171-L244](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/config.py#L171-L244)）。`_read_with_retry` 遇 `YAMLError` 默认最多尝试 3 次（最多重试 2 次）（间隔 0.05s 递增）以跨过另一进程写一半的文件；`get_config_raw()` 跳过 env 解析，专供局部读改写回（[L199-L234](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/config.py#L199-L234)、[L262-L264](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/config.py#L262-L264)）。
- `resolve_env_vars` 的 `${VAR:-default}` 按 bash 语义：unset 或空串都用默认值；无 `:-` 的 `${VAR}` 在 unset 时得到空串。变量名含 `api_key`/`token`（不区分大小写）且有值时先经 crypto provider 解密。`mcp.servers` 条目的 `headers`/`env`/`staticHeaders`/`static_headers` 子树原样保留 `${VAR}` 占位符——它们属于 CredentialStore，在构建 `McpServerConfig` 时才解析；提前塌缩成空串会让 httpx 报 `Illegal header value b'Bearer '`（[config.py L62-L125](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/config.py#L62-L125)；选择器 `TestResolveEnvVars::test_mcp_server_headers_env_placeholders_preserved`，[test_config.py L623-L712](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/test_config.py#L623-L712)）。
- `_normalize_config` 对 KV cache 亲和 fail-closed：开关已开但 `validate_affinity_invariant` 不通过时只在内存里关掉开关（保留用户文件供诊断），绝不激活不一致配置；同时把 JSON 字符串形式的 `custom_headers` 解析成 dict，并为 `channels.{web,feishu,xiaoyi}` 顶层缺省的 `send_file_allowed` 兜底 True（[config.py L128-L168](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/config.py#L128-L168)）。

## 模型目录、稳定选择与配置校验

该工作流的职责、顺序、错误边界与源码入口见[模型目录、稳定选择与配置校验](jiuwenswarm-common-model-catalog.md)。

## permissions 与 MCP 配置面

- `permissions.tools` 的值只允许小写 `allow|ask|deny` 或 legacy `{"*": level}`，写入前经 `_validate_tools_map` 规范化；rules 必须有非空 `tools`+`pattern`，`id` 缺省自动生成 `ui_rule_<uuid4hex12>`，可变键白名单为 `tools/pattern/severity/action/description/match_type`，`severity` 归一为大写 `LOW|MEDIUM|HIGH|CRITICAL`、`action` 归一为小写三级；重复 rule id 在 mutator 内抛 `ValueError`，整个写入中止（[config.py L1097-L1204](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/config.py#L1097-L1204)、[L1225-L1261](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/config.py#L1225-L1261)、[L1368-L1387](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/config.py#L1368-L1387)）。
- `permission_tools.py` 的别名表只有四条：`exec_command→mcp_exec_command`、`fetch_webpage→mcp_fetch_webpage`、`free_search→mcp_free_search`、`paid_search→mcp_paid_search`。`resolve_permission_tool_name` 对歧义别名图 fail-closed（conflict 时 `canonical_name` 置空，不猜）；`stricter_permission_level` 按 `allow(0)<ask(1)<deny(2)` 取更严一侧，未知输入按 ask 的等级参与比较，但函数仍可能返回原始未知字符串；调用方需先校验合法等级（[permission_tools.py L9-L95](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/permission_tools.py#L9-L95)）。
- 当前 MCP 合并两个事实源：`get_mcp_servers` 合并 config.yaml `mcp.servers`（command.mcp/TUI 手填）与 `mcp/state.json` 的 connected 记录（marketplace/custom），同名冲突 state.json 优先，stale marketplace 记录和 skill-only 记录跳过，state 读取失败只降级为 config.yaml 部分（[config.py L2546-L2590](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/config.py#L2546-L2590)）。`upsert_mcp_server` 按名字路由：已在 config.yaml 的原地更新，其余写 state.json；command.mcp 的 add/update 传 `state="connecting"`，探活通过后才翻成 `connected`（[L2703-L2730](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/config.py#L2703-L2730)）。
- `build_mcp_server_config` 要求非空 `name` 和五种 transport 之一，否则返回 None（跳过而非报错）；stdio 必须有 `command`（`args` 里的 `${VAR}` 要替换，因为子进程 argv 不会再做 shell 展开），HTTP 必须有 `url`。`${VAR}` 占位符仅在调用方提供 resolver 时解析（`CredentialStore(name) ∪ os.environ`，缺省保持字面量）；HTTP 的 `headers` 必须落到 `auth_headers`——openjiuwen 的 SseClient/StreamableHttpClient 读的是 `auth_headers` 而不是 `params.headers`，此适配层将认证 headers 放在 SDK 读取的 auth_headers，不能据此保证任意远端的错误表现（[mcp_config.py L47-L71](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mcp_config.py#L47-L71)、[L107-L195](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mcp_config.py#L107-L195)）。`extract_enabled_mcp_server_entries` 以合并后的 `get_mcp_servers()` 为权威来源（传入 config_base 的 `mcp.servers` 会漏掉 state.json 的动态 MCP），只保留 enabled（缺省 True）的条目；合并读取抛错时可回退到传入 config_base 的服务器列表（[L74-L104](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mcp_config.py#L74-L104)）。
- prewarm 是后台 fire-and-forget：并发上限 6、兜底 stall 超时 120s，不设激进超时（npx 首次安装要几十秒）。HTTP 探活 `preflight_mcp_server_reachable` 用裸 `httpx.AsyncClient` POST 一个与 mcp SDK initialize 完全一致的报文，绝不用 `client.connect()`（401/超时会泄漏 anyio ghost task）；401/403 判为 auth rejected，任何 ≥400 都拦截；每服务器 `timeout_s` 优先，否则调用方 timeout，否则 10s；非 HTTP transport 直接视为可达（[mcp_config.py L25-L33](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mcp_config.py#L25-L33)、[L226-L324](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mcp_config.py#L226-L324)）。

## 相关组件知识

- [common 审查规则](rules.md) — config.yaml 写事务与跨仓契约的硬约束（本页描述的是已实现行为，规则页是改动时的门禁）
- [配置面板 handler（config_panel）](jiuwenswarm-common-config-panel.md) — Web/TUI 侧调用本页这些持久化入口的 handler 层
- [../login-auth/jiuwenswarm-common-auth.md](../login-auth/jiuwenswarm-common-auth.md) — `get_available_models` 叠加的登录模型来源（auth/model_catalog），凭据按用户隔离
- [../agent-runtime/jiuwenswarm-runtime.md](../agent-runtime/jiuwenswarm-runtime.md) — 消费模型目录与权限配置的共享 Agent Runtime

**改动路由**

- `jiuwenswarm/common/_build_config.py`
- `jiuwenswarm/common/chat_final.py`
- `jiuwenswarm/common/cleanup.py`
- `jiuwenswarm/common/client/`
- `jiuwenswarm/common/coding_memory_paths.py`
- `jiuwenswarm/common/config.py`
- `jiuwenswarm/common/context_keys.py`
- `jiuwenswarm/common/context_window.py`
- `jiuwenswarm/common/cron_session.py`
- `jiuwenswarm/common/cron_team_completion.py`
- `jiuwenswarm/common/debug_dump.py`
- `jiuwenswarm/common/external_cli_catalog.py`
- `jiuwenswarm/common/external_cli_runtime.py`
- `jiuwenswarm/common/git_safe_directory.py`
- `jiuwenswarm/common/hooks_config.py`
- `jiuwenswarm/common/kv_cache_affinity_config.py`
- `jiuwenswarm/common/log_preview.py`
- `jiuwenswarm/common/mcp_config.py`
- `jiuwenswarm/common/media_capability_config.py`
- `jiuwenswarm/common/mode_matrix.py`
- `jiuwenswarm/common/model_catalog.py`
- `jiuwenswarm/common/model_config_validation.py`
- `jiuwenswarm/common/model_errors.py`
- `jiuwenswarm/common/model_migration.py`
- `jiuwenswarm/common/model_selection.py`
- `jiuwenswarm/common/model_vendor_registry.py`
- `jiuwenswarm/common/openrouter_attribution.py`
- `jiuwenswarm/common/permission_tools.py`
- `jiuwenswarm/common/playwright_mcp_runtime.py`
- `jiuwenswarm/common/process_supervision.py`
- `jiuwenswarm/common/projectless_workspace.py`
- `jiuwenswarm/common/protocol_ids.py`
- `jiuwenswarm/common/reasoning_config.py`
- `jiuwenswarm/common/reasoning_injector.py`
- `jiuwenswarm/common/runtime_log_filter.py`
- `jiuwenswarm/common/runtime_workspace.py`
- `jiuwenswarm/common/security/`
- `jiuwenswarm/common/session_message.py`
- `jiuwenswarm/common/stage_timer.py`
- `jiuwenswarm/common/startup_diagnostics.py`
- `jiuwenswarm/common/task_loop_config.py`
- `jiuwenswarm/common/team_artifacts.py`
- `jiuwenswarm/common/todo_snapshot.py`
- `jiuwenswarm/common/tool_display.py`
- `jiuwenswarm/common/tool_ownership.py`
- `jiuwenswarm/common/updater.py`
- `jiuwenswarm/common/updater_restart_helper.py`
- `jiuwenswarm/common/upgrade_executor.py`
- `jiuwenswarm/common/utils.py`
- `jiuwenswarm/common/version.py`
- `jiuwenswarm/common/version_source.py`
- `jiuwenswarm/common/work_mode.py`
- `jiuwenswarm/common/ws_diagnostics.py`
- `jiuwenswarm/common/ws_limits.py`

## 怎样验证

模型选择迁移、目录脱敏、write-only 字段保留、reasoning 档位和并发配置写入分别查本页 sources 中的聚焦单测。这里描述固定版本的静态源码行为，不能单独证明真实模型端点或 marketplace 的连通性。
