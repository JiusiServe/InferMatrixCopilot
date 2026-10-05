---
title: "scripts/ — 打包与构建脚本"
created: 2026-10-05
updated: 2026-10-05
type: architecture
tags: [jiuwenswarm]
sources: []
---

# scripts/ — 打包与构建脚本

该模块集中了 JiuwenSwarm 各平台的打包构建脚本（Windows/macOS Electron 与 exe、鸿蒙 HAP、wheel 包、TUI 二进制）、PyInstaller 打包入口与配置，以及冻结产物的离线校验脚本。构建标识（应用名、版本、产物文件名）统一由 build_config.py 从根 pyproject.toml 派生并同步到各打包文件。

**构建入口**

- `scripts/build_config.py` — 构建标识的唯一事实来源：从 pyproject.toml 读取并派生各平台产物名，检测/写回各打包文件中的版本漂移
- `scripts/build-electron-exe.ps1` — Windows Electron 安装包入口（依赖 → 前端 → PyInstaller → Inno Setup）
- `scripts/build-electron-exe.sh` — macOS Electron 打包入口，与 Windows 版流程对应
- `scripts/build-exe.ps1` — Windows 纯 Python exe 打包入口（uv sync → npm build → PyInstaller → Inno Setup）
- `scripts/build-macos.sh` — macOS .app/.dmg 打包入口，按机器是否配置签名身份自动决定是否签名/公证
- `scripts/build.sh` — 通用打包入口：编译 web 前端并构建含前端 dist 的 wheel 包（Windows 对应 build.ps1）
- `scripts/build-harmony.sh` — 鸿蒙 .hap 打包入口（前端构建 → HNP/rawfile → hvigorw）
- `scripts/build_python_packages.py` — 构建 root/sidecar/jiuwenbox wheel 与 TUI 二进制的统一驱动
- `scripts/jiuwenswarm_exe_entry.py` — PyInstaller 打包后的主入口：分发主应用与子命令（含 Windows 单实例锁、捆绑二进制转发）
- `scripts/harmony_entry.py` — 鸿蒙端服务编排入口：启动 AgentServer、Gateway、Web 前端并输出 HARMONY_READY 信号

**关键文件**

- `scripts/jiuwenswarm.spec` — PyInstaller 打包配置，列出后端冻结所需的隐藏导入与资源
- `scripts/build-runtimes.sh` — Node 运行时解析与绑定的共享实现（macOS 两条打包链路的单一来源），build-runtimes.psm1 是其 PowerShell 对应
- `scripts/jiuwenswarm.iss` — Inno Setup 安装包定义（另有 installer.iss / installer-electron.iss）
- `scripts/build_tui.py` — 跨平台构建 TUI 二进制，含 macOS 签名修正
- `scripts/update_playwright_mcp_runtime.py` — 生成可复现、免 npm 的 Playwright MCP 运行时归档并提交仓库
- `scripts/verify_playwright_mcp_bundle.py` — 冻结产物校验：Node 与 Playwright MCP CLI（同类还有 verify_a2ui_bundle / verify_gitcode_cli_bundle / verify_rsi_bundle / verify_playwr
- `scripts/reset_trajectory_data.py` — 清理旧轨迹契约（schema v2/4/2 之前）遗留的工作区数据
- `scripts/openjiuwen_team_mcp_exe_entry.py` — 捆绑的 OpenJiuWen team MCP server 的 PyInstaller 入口
- `scripts/run_gateway_acp.sh` — ACP 模式下启动 Gateway 的 shell 包装（Windows 对应 run_gateway_acp.cmd）
- `scripts/build-harmony-hap.sh` — 不用 DevEco Studio、纯 CLI 的 HAP 五阶段手动构建脚本

**相关文档**

- `docs/README.md` — 需要各平台构建或部署的完整说明时先查这里
- `docs/zh/HarmonyOS_Dev_Workflow_Test_Guide.md` — 改动 build-harmony*.sh 或 harmony_entry.py 时读
- `TESTING.md` — 打包契约测试（如 test_desktop_electron_contract.py）相关改动时读

**构建链路**

- `scripts/build-electron-exe.ps1`
- `scripts/build-electron-exe.sh`
- `scripts/build-exe.bat`
- `scripts/build-exe.ps1`
- `scripts/build-harmony-hap.sh`
- `scripts/build-harmony.sh`
- `scripts/build-macos.sh`
- `scripts/build-runtimes.psm1`
- `scripts/build-runtimes.sh`
- `scripts/build.ps1`
- `scripts/build.sh`
- `scripts/build_config.py`
- `scripts/build_python_packages.py`
- `scripts/build_tui.py`
- `scripts/harmony_entry.py`
- `scripts/installer-electron.iss`
- `scripts/installer.iss`
- `scripts/jiuwenswarm.iss`
- `scripts/jiuwenswarm.spec`
- `scripts/jiuwenswarm_exe_entry.py`
- `scripts/openjiuwen_team_mcp_exe_entry.py`
- `scripts/reset_trajectory_data.py`
- `scripts/update_playwright_mcp_runtime.py`
- `scripts/verify_a2ui_bundle.py`
- `scripts/verify_gitcode_cli_bundle.py`
- `scripts/verify_playwright_mcp_bundle.py`
- `scripts/verify_playwright_mcp_offline.py`
- `scripts/verify_rsi_bundle.py`
