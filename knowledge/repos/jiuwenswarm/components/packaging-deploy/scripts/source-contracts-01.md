---
title: "scripts 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# scripts 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=scripts/build-electron-exe.ps1 pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=137082fcd017d9094eb102ad518104475acb4fab5756f8f0a17ec0e184caa32f -->
**`scripts/build-electron-exe.ps1`**

- 脚本执行边界：`uv sync --extra dev --extra claude --extra codex`；`npm install`；`npm run build`；`npm install`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/build-electron-exe.ps1#L1-L398)。
<!-- /kb:file -->

<!-- kb:file path=scripts/build-exe.ps1 pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c9d746cd802d2378d2445c6b54148f65ea5e9a0580ec05a1001ab0e63f84452c -->
**`scripts/build-exe.ps1`**

- 脚本执行边界：`uv sync --extra dev`；`npm install`；`npm run build`；`uv run pyinstaller scripts\jiuwenswarm.spec --noconfirm`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/build-exe.ps1#L1-L187)。
<!-- /kb:file -->

<!-- kb:file path=scripts/build-harmony-hap.sh pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d1dc4b6c8227532861038166a3e314d2004de7b8b12cae557d2210e60046abe3 -->
**`scripts/build-harmony-hap.sh`**

- 源码声明的类型、组件或调用边界：`fs`, `srcFile`, `destFile`, `content`, `obj`, `obj`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`const fs = require('fs');`。
- 脚本执行边界：`npm install 2&gt;&1 // {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/build-harmony-hap.sh#L1-L563)。
<!-- /kb:file -->

<!-- kb:file path=scripts/build-harmony.sh pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ae9016f85dd4e455794202aec616e54f28f1dabbf06a1f81404339e2259d0525 -->
**`scripts/build-harmony.sh`**

- 源码声明的类型、组件或调用边界：`d`；这是词法声明索引，不把局部变量当成对外导出 API。
- 脚本执行边界：`npm install`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/build-harmony.sh#L1-L218)。
<!-- /kb:file -->

<!-- kb:file path=scripts/build-macos.sh pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d14f28be96feddce5f19fc00cb54a87b7247c2826f1aae822e70f9d7a109bab6 -->
**`scripts/build-macos.sh`**

- 脚本执行边界：`uv sync --extra dev`；`npm install`；`npm run build`；`uv run pyinstaller scripts/jiuwenswarm.spec --noconfirm`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/build-macos.sh#L1-L237)。
<!-- /kb:file -->

<!-- kb:file path=scripts/build-runtimes.psm1 pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cbc9b61b43a81e6449d6fa6f4221292f54c8825dc68a1bd22830e7c82c5f2835 -->
**`scripts/build-runtimes.psm1`**

- 源码声明的类型、组件或调用边界：`Test`, `Get`, `Get`, `Download`, `Resolve`, `Use`, `Copy`, `Resolve`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/build-runtimes.psm1#L1-L228)。
<!-- /kb:file -->

<!-- kb:file path=scripts/build.ps1 pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d96cea85ad98bd5e38de1db3f613f8889681f97a039f7f14388e46f851b1220f -->
**`scripts/build.ps1`**

- 脚本执行边界：`npm install`；`npm run build`；`python -m pip install --upgrade build wheel 2&gt;$null`；`python -m build --wheel --no-isolation`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/build.ps1#L1-L75)。
<!-- /kb:file -->

<!-- kb:file path=scripts/build.sh pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fb042a11715ba48da3989985b0040c4e28a7efc2489bffdbd3c0ec0d0761b390 -->
**`scripts/build.sh`**

- 脚本执行边界：`uv run --no-project --python 3.11 python "$PROJECT_ROOT/scripts/build_config.py" --sync`；`uv sync --all-extras \`；`npm install`；`npm run build`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/build.sh#L1-L83)。
<!-- /kb:file -->

<!-- kb:file path=scripts/build_config.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=267abe170167431a7fa18d0adb64f5cfcebef6515cf3e87fb5a8bfb462277494 -->
**`scripts/build_config.py`**

- 源码对模块职责的说明：Read and derive the build identity from the root ''pyproject.toml''.。
- `ProductNames` 定义类型边界。
- `BuildConfigError` 继承 `ValueError`。
- `BuildConfig` 定义类型边界；方法入口：`app_full_name`, `app_bundle_name`, `executable_name_windows`, `dist_dir_name`, `dmg_filename`, `setup_base_name`。
- 调用入口 `load_build_config(project_root)`；声明返回 `BuildConfig`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import json`；`import logging`。
- 模块级配置或常量名称：`PROJECT_ROOT`, `RUNTIME_CONFIG_PATH`, `PRODUCT_NAMES`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/build_config.py#L1-L303)。
<!-- /kb:file -->

<!-- kb:file path=scripts/build_python_packages.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9b1919138415536727e324258ac0717304c906d57ea2edc355058115983a039b -->
**`scripts/build_python_packages.py`**

- 调用入口 `run(cmd, cwd, env)`；声明返回 `None`。
- 调用入口 `remove_path(path)`；声明返回 `None`。
- 调用入口 `clean_root()`；声明返回 `None`。
- 调用入口 `clean_sidecar()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import logging`；`import os`。
- 模块级配置或常量名称：`ROOT`, `SIDECAR_ROOT`, `SIDE_CAR_DIST`, `JIUWENBOX_ROOT`, `JIUWENBOX_DIST`, `TUI_ROOT`, `TUI_TARGETS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/build_python_packages.py#L1-L231)。
<!-- /kb:file -->

<!-- kb:file path=scripts/build_tui.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=48d6d2f0fb758e2979024dfe8de9ad730fc55d5457a2e1de83fe3a4a0fdf4b75 -->
**`scripts/build_tui.py`**

- 调用入口 `current_platform_key()`；声明返回 `str`。
- 调用入口 `output_binary_name(platform_key)`；声明返回 `str`。
- 调用入口 `resolve_requested_targets(raw)`；声明返回 `list[str]`。
- 调用入口 `build_target(platform_key)`；声明返回 `Path`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import logging`；`import os`。
- 模块级配置或常量名称：`ROOT`, `TUI_ENTRY`, `OUTPUT_ROOT`, `TARGETS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/build_tui.py#L1-L135)。
<!-- /kb:file -->

<!-- kb:file path=scripts/harmony_entry.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=29913f4c8815f5818893d9612518a810bb020c6021e8c4bcd6b38ab1409960e5 -->
**`scripts/harmony_entry.py`**

- 源码对模块职责的说明：HarmonyOS entry point for JiuwenSwarm services.。
- 调用入口 `check_tcp_port(host, port)`；声明返回 `bool`。
- 调用入口 `wait_for_tcp_port(host, port, timeout, interval, service_name)`；声明返回 `bool`。
- 调用入口 `find_free_port(start_port)`；声明返回 `int`。
- 调用入口 `start_service(module_path, args, service_name)`；声明返回 `subprocess.Popen`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import os`；`import sys`；`import signal`。
- 模块级配置或常量名称：`DEFAULT_AGENTSERVER_PORT`, `DEFAULT_GATEWAY_PORT`, `DEFAULT_FRONTEND_PORT`, `PORT_CHECK_TIMEOUT`, `PORT_CHECK_INTERVAL`, `SERVICE_MONITOR_INTERVAL`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/harmony_entry.py#L1-L365)。
<!-- /kb:file -->

<!-- kb:file path=scripts/installer-electron.iss pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c7afe85a4b6b190bd8801f9bd92574481bae67a8a4ea3004d7ad3fe665896506 -->
**`scripts/installer-electron.iss`**

- 源码声明的类型、组件或调用边界：`InitializeSetup`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/installer-electron.iss#L1-L295)。
<!-- /kb:file -->

<!-- kb:file path=scripts/installer.iss pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0f835487aa06e6138903da084273d866a6061b22de7cea806eb09f2cd21c2e27 -->
**`scripts/installer.iss`**

- 源码声明的类型、组件或调用边界：`HasDescriptionStemInTree`, `HasNestedDescriptionReplacement`, `GetWebView2RuntimeVersion`, `StripQuotes`, `TryRegUninstaller`, `TryFallbackUninstaller`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/installer.iss#L1-L570)。
<!-- /kb:file -->

<!-- kb:file path=scripts/jiuwenswarm.iss pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=024009e10df7f10467f77faf10f1965656e66aa76e11e8603828f80c32657c83 -->
**`scripts/jiuwenswarm.iss`**

- 源码声明的类型、组件或调用边界：`UserWorkspaceDir`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/jiuwenswarm.iss#L1-L62)。
<!-- /kb:file -->

<!-- kb:file path=scripts/jiuwenswarm.spec pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3354f65936e295ceb788798585e7940556e80284901b7c8d5a7e2d02a34de11d -->
**`scripts/jiuwenswarm.spec`**

- 集成边界的导入/加载声明：`import glob`；`import os`；`import runpy`；`import shutil`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/jiuwenswarm.spec#L1-L557)。
<!-- /kb:file -->

<!-- kb:file path=scripts/jiuwenswarm_exe_entry.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=22a0a334157406ebdc44bfea8b4b104773b9376beecfbd704502a20f42b87fd0 -->
**`scripts/jiuwenswarm_exe_entry.py`**

- 源码对模块职责的说明：PyInstaller 打包入口：根据参数分发到主应用或子命令。。
- 调用入口 `main()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import os`；`import sys`；`import ctypes`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/jiuwenswarm_exe_entry.py#L1-L658)。
<!-- /kb:file -->

<!-- kb:file path=scripts/openjiuwen_team_mcp_exe_entry.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d28f63e42dfd65af8a350540079d4255259b120812ced52b891289207fb5d555 -->
**`scripts/openjiuwen_team_mcp_exe_entry.py`**

- 源码对模块职责的说明：PyInstaller entry point for the bundled OpenJiuWen team MCP server.。
- 调用入口 `main()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import atexit`；`import os`；`import sys`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/openjiuwen_team_mcp_exe_entry.py#L1-L82)。
<!-- /kb:file -->

<!-- kb:file path=scripts/reset_trajectory_data.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6ca68f108de74bb07ddc752af413d8e12a90e433f4a0a778ddaf389b20fedc99 -->
**`scripts/reset_trajectory_data.py`**

- 源码对模块职责的说明：Delete trajectory data written under the previous trajectory contract.。
- 调用入口 `main(argv)`；声明返回 `int`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import glob`；`import shutil`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/scripts/reset_trajectory_data.py#L1-L118)。
<!-- /kb:file -->
