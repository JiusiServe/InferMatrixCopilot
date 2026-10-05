---
title: "scripts/ — 打包构建与冻结产物校验"
created: 2026-10-05
updated: 2026-10-05
type: architecture
tags: [jiuwenswarm]
sources: []
---

# scripts/ — 打包构建与冻结产物校验

该模块承载 JiuwenSwarm 的跨平台打包链路（Windows/macOS/Electron/HarmonyOS 的 wheel、exe、dmg、hap 安装包）以及 PyInstaller 冻结入口和冻结产物的校验脚本。构建身份（应用名、版本、平台标识）统一由 build_config.py 从根 pyproject.toml 派生，各平台 wrapper 与 Inno Setup 脚本共享这一单一来源。

**从哪里启动打包**

- `scripts/build-exe.ps1` — Windows exe 打包 wrapper：uv sync → 前端构建 → PyInstaller → Inno Setup 安装包
- `scripts/build-electron-exe.ps1` — Windows Electron 桌面端打包（组装 Electron shell + 前端 + 后端 exe，产出 setup 安装包）
- `scripts/build-electron-exe.sh` — macOS Electron 桌面端打包，产出 DMG
- `scripts/build-macos.sh` — macOS .app + .dmg 打包，签名/公证按机器身份自动决定
- `scripts/build-harmony.sh` — 鸿蒙应用打包：npm build → HNP 嵌入前端 → hvigorw 构建 .hap
- `scripts/build.sh` — 通用打包入口：编译 web 前端后构建 wheel（另有 build.ps1 / build-exe.bat 对应 Windows 路径）
- `scripts/jiuwenswarm_exe_entry.py` — PyInstaller 冻结入口：按参数分发主应用或子命令，含 Windows 单实例互斥
- `scripts/harmony_entry.py` — HarmonyOS 服务编排入口：启动 AgentServer/Gateway/Web 前端子进程并等待端口就绪

**构建配置与共享模块**

- `scripts/build_config.py` — 从根 pyproject.toml 读取并派生构建身份（ProductNames/BuildConfig），是各平台打包脚本名字与版本的权威来源
- `scripts/jiuwenswarm.spec` — PyInstaller 打包配置，Windows/macOS 桌面冻结共用的 spec
- `scripts/build-runtimes.sh` — Node 运行时解析与绑定的共享 bash 模块（build-macos.sh 与 build-electron-exe.sh source 它）
- `scripts/build-runtimes.psm1` — node/uv 运行时解析与绑定的 PowerShell 模块（build-exe.ps1 与 build-electron-exe.ps1 共享）
- `scripts/installer.iss` — Inno Setup 安装脚本，由 build-exe.ps1 传入构建配置调用
- `scripts/installer-electron.iss` — Electron 版 Inno Setup 脚本，应用名/版本由 build-electron-exe.ps1 注入
- `scripts/build_python_packages.py` — 构建 Python wheel 包（可含前端 dist），build.sh 底层调用
- `scripts/build_tui.py` — TUI 二进制构建（跨平台目标解析、输出名、macOS 签名修正）
- `scripts/update_playwright_mcp_runtime.py` — 生成可复现、免 npm 的 Playwright MCP 运行时归档并提交仓库
- `scripts/verify_playwright_mcp_bundle.py` — 冻结产物校验之一：Node 与 Playwright MCP CLI（同类还有 verify_a2ui/gitcode_cli/rsi_bundle）
- `scripts/openjiuwen_team_mcp_exe_entry.py` — 随包发布的 OpenJiuWen team MCP 服务器的 PyInstaller 入口
- `scripts/run_gateway_acp.sh` — 开发/运行辅助：以仓库根为 PYTHONPATH 启动 ACP 连接模块（.cmd 为 Windows 版）

**相关文档**

- `README_CN.md` — 安装与整体产品入口，了解打包产物的使用背景
- `docs/zh/HarmonyOS_Dev_Workflow_Test_Guide.md` — 涉及鸿蒙打包（build-harmony.sh / build-harmony-hap.sh / harmony_entry.py）时先读
- `TESTING.md` — 打包契约测试（如 tests/unit_tests/test_desktop_electron_contract.py）与验证脚本的测试约定
- `docs/zh/AutoHarness.md` — 理解 verify_rsi_bundle.py 校验的 RSI native Harness baseline

**Routes**

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
