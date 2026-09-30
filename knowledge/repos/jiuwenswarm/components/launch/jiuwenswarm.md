---
title: "jiuwenswarm 顶层包：启动入口、多实例与运行时补丁"
created: 2026-09-30
updated: 2026-09-30
type: architecture
tags: [jiuwenswarm]
sources: []
---

# jiuwenswarm 顶层包：启动入口、多实例与运行时补丁

负责 JiuwenSwarm 的进程启动和初始化：一条命令拉起 AgentServer 与 Gateway、管理多实例（--dotenv/--name）、本地 debug 构建启动、初始化用户数据目录，并在 import 链最前面解析 dotenv。这里还放着 OpenAI/Anthropic 各家方言和 SSE 网关的运行时补丁，以及 `acp/`、`cli/` 下为迁走模块保留的兼容别名。

**入口**

- `jiuwenswarm/start_services.py` — `jiuwenswarm-start` 主入口：按模式启动前后端服务，处理 --list/--status/--stop/--restart/--name 多实例命令、端口检查和端口回退
- `jiuwenswarm/app.py` — 先后启动 `server.app_agentserver` 和 `gateway.app_gateway` 两个进程，支持 --dotenv 多实例隔离
- `jiuwenswarm/debug_launcher.py` — `jiuwenswarm-start debug`：npm install/build 前端、按 config.yaml 里启用的外部 CLI agent 执行 uv sync，再在后台启动服务并写入带时间戳的日志；也负责停止后台服务
- `jiuwenswarm/init_workspace.py` — `jiuwenswarm-init`：询问语言偏好，把 config.yaml、.env 模板、agent 模板和多语言文件复制到用户数据根目录；支持 -f 强制重建和 --name 命名实例
- `jiuwenswarm/channels/acp/app_acp.py` — ACP 频道的命令行入口：用 argparse 解析参数，run_acp 负责运行，结果以 JSON 写到 stdout
- `jiuwenswarm/acp/cli.py` — 外部 ACP agent（stdio）的 CLI 冒烟测试，与 acp_chat 工具共用同一份配置
- `jiuwenswarm/cli/main.py` — 历史远程 CLI 模块路径的兼容入口

**关键文件**

- `jiuwenswarm/dotenv_early.py` — 扫描 sys.argv 里的 --dotenv/--name，设置 JIUWENSWARM_DATA_DIR；必须在导入其他 jiuwenswarm 模块之前调用
- `jiuwenswarm/llm_provider_compat_patch.py` — 运行时补丁：修正 ModelArts 等 provider 在 Anthropic 参数和 OpenAI tool_choice 上的方言差异
- `jiuwenswarm/llm_sse_patch.py` — 给 OpenAIModelClient._parse_response 打补丁：非流式 invoke() 收到只含 SSE 文本的响应时，先组装成 ChatCompletion 再交给原逻辑解析
- `jiuwenswarm/acp/stdio_client.py` — ACP stdio 客户端的 re-export，实现已移到 `jiuwenswarm.common.acp`；console script `jiuwenswarm-acp-chat` 仍引用这个路径
- `jiuwenswarm/acp/subprocess_env.py` — ACP 子进程环境构造的 re-export，按 docstring 计划在阶段 3 随 `acp/` 目录一起删除
- `jiuwenswarm/cli/chat.py` — `channels.cli.chat` 的兼容别名；同目录下的 _terminal/events/gateway_client/render 也是同类别名

**相关文档**

- `docs/zh/Quickstart.md` — 改动涉及启动命令、初始化流程或默认启动模式时读
- `README_CN.md` — 核对 jiuwenswarm-start / jiuwenswarm-init 等命令的对外说明是否与改动一致时读
- `docs/zh/ACP插件使用.md` — 改动涉及 acp/cli.py、channels/acp/app_acp.py 或 ACP 兼容路径时读
- `docs/zh/FAQ.md` — 改动影响端口、多实例或启动报错等常见问题的表现时读
- `TESTING.md` — 给启动器或补丁补测试时参考；里面有过期路径，应以 tests/ 下现有用例为准

**路由**

- `jiuwenswarm/acp/`
- `jiuwenswarm/app.py`
- `jiuwenswarm/channels/acp/`
- `jiuwenswarm/cli/`
- `jiuwenswarm/debug_launcher.py`
- `jiuwenswarm/dotenv_early.py`
- `jiuwenswarm/init_workspace.py`
- `jiuwenswarm/llm_provider_compat_patch.py`
- `jiuwenswarm/llm_sse_patch.py`
- `jiuwenswarm/start_services.py`
