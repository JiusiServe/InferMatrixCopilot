---
title: "jiuwenswarm/common/：公共基础模块"
created: 2026-09-30
updated: 2026-09-30
type: architecture
tags: [jiuwenswarm]
sources: []
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
