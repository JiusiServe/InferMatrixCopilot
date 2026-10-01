---
title: "jiuwenbox-src 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# jiuwenbox-src 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenbox/src/jiuwenbox/server/routes/mcp.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=db828636a79028f998b815c8606850a23c8d7b70aa2d490c0727dc89107d7887 -->
**`jiuwenbox/src/jiuwenbox/server/routes/mcp.py`**

- 源码对模块职责的说明：MCP route: expose JiuwenBox sandbox capabilities via remote MCP.。
- `SandboxRunCommandParams` 继承 `BaseModel`。
- 异步入口 `sandbox_run_command(params)`；声明返回 `dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import os`；`import time`。
- 模块级配置或常量名称：`ENV_MCP_ALLOWED_HOSTS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/server/routes/mcp.py#L1-L176)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/server/routes/policy.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=eff711665507076ea3c14abc35707415ba531866b8a061c3fb3cdd5d011f5df6 -->
**`jiuwenbox/src/jiuwenbox/server/routes/policy.py`**

- 源码对模块职责的说明：Policy API routes.。
- 异步入口 `get_policy(sandbox_id)`。
- `UpdatePolicyRequest` 继承 `BaseModel`。
- `UpdatePolicySkippedItem` 继承 `BaseModel`。
- `UpdatePolicyFailedItem` 继承 `BaseModel`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from typing import Any`；`from fastapi import APIRouter, HTTPException`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/server/routes/policy.py#L1-L180)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/server/routes/proxy.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1dc50ac0bb165704b5a61944fb0f36fbc93fd18369fae6f035500422399737ba -->
**`jiuwenbox/src/jiuwenbox/server/routes/proxy.py`**

- 源码对模块职责的说明：Inference privacy proxy API routes.。
- `RouteRequest` 继承 `BaseModel`。
- 异步入口 `create_proxy(route)`。
- 异步入口 `list_proxies()`。
- 异步入口 `get_proxy(proxy_name)`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from fastapi import APIRouter, HTTPException, Query`；`from fastapi.responses import PlainTextResponse`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/server/routes/proxy.py#L1-L209)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/server/routes/sandbox.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c59c84a9d19958ae79a7052c347d83e19e9a0db2ea14aef56309a87456dbc8da -->
**`jiuwenbox/src/jiuwenbox/server/routes/sandbox.py`**

- 源码对模块职责的说明：Sandbox API routes.。
- `CreateSandboxRequest` 继承 `BaseModel`。
- `ExecRequest` 继承 `BaseModel`。
- `ListFilesQuery` 继承 `BaseModel`。
- 异步入口 `create_sandbox(request)`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from typing import Annotated, Any`；`from fastapi import APIRouter, File, Query, UploadFile`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/server/routes/sandbox.py#L1-L259)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/server/runtime/base.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5b10a6f40b54e003f1b2359ac387ce82fa099e146ef748615aaa7845ca7ddb8b -->
**`jiuwenbox/src/jiuwenbox/server/runtime/base.py`**

- 源码对模块职责的说明：Abstract base class for sandbox runtime adapters.。
- `RuntimeExecRequest` 定义类型边界。
- `RuntimeBackgroundExecRequest` 定义类型边界。
- `RuntimeFileOpResult` 定义类型边界。
- `RuntimeAdapter` 继承 `abc.ABC`；方法入口：`create`, `stop`, `is_running`, `exec`, `exec_background`, `get_background_job`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import abc`；`from dataclasses import dataclass`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/server/runtime/base.py#L1-L186)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/server/runtime/process.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1231840a2bca358a014e0e90d3a19d3dc3ae277810a3ae1508d3305a5845db3f -->
**`jiuwenbox/src/jiuwenbox/server/runtime/process.py`**

- 源码对模块职责的说明：Process-based runtime adapter (bare-metal mode).。
- `BackgroundJob` 定义类型边界。
- `BackgroundJobNotFoundError` 继承 `Exception`。
- 调用入口 `enable_child_subreaper()`；声明返回 `bool`。
- `ProcessRuntime` 继承 `RuntimeAdapter`；方法入口：`__init__`, `register_zombie_reaper`, `unregister_zombie_reaper`, `get_sandbox_ip_address`, `create`, `stop`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import base64`；`import dataclasses`。
- 模块级配置或常量名称：`SERVER_PROTECT_PORTS_ENV`, `LISTEN_URI_ENV`, `DEFAULT_SERVER_PROTECT_PORTS`, `LANDLOCK_LAUNCHER_SOURCE`, `SANDBOX_DAEMON_SOURCE`, `PYTHON_EXECUTABLE`, `FASTPATH_ENV`, `FASTPATH_MAX_SANDBOXES_ENV`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/server/runtime/process.py#L1-L3356)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/server/sandbox_manager.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4c27e23f641ad9b6b7d888ebfe28b098f3dadc4e41c0f1f4f5c009144a0aee51 -->
**`jiuwenbox/src/jiuwenbox/server/sandbox_manager.py`**

- 源码对模块职责的说明：Sandbox lifecycle manager.。
- `SandboxExecRequest` 定义类型边界。
- `SandboxBackgroundExecRequest` 定义类型边界。
- `SandboxListRequest` 定义类型边界。
- `SandboxNotFoundError` 继承 `Exception`；方法入口：`__init__`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import base64`；`import binascii`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/server/sandbox_manager.py#L1-L1626)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/server/workspace.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=463269a533d2ef154b96d5fcabc92dbef761ff18238b86e692cbe098c8a5bf2c -->
**`jiuwenbox/src/jiuwenbox/server/workspace.py`**

- 源码对模块职责的说明：Server-managed workspace paths.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import os`；`import pwd`；`from pathlib import Path`。
- 模块级配置或常量名称：`JIUWENBOX_HOME`, `SANDBOX_WORKSPACE`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/server/workspace.py#L1-L20)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/supervisor/bwrap.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e2205c347b50718df093f729a422beab040c7ed5914a5819942628ae59b7989f -->
**`jiuwenbox/src/jiuwenbox/supervisor/bwrap.py`**

- 源码对模块职责的说明：Bubblewrap (bwrap) sandbox wrapper.。
- `BwrapConfig` 定义类型边界；方法入口：`from_policy`, `add_dir_mount`, `to_args`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import fnmatch`；`import logging`；`import posixpath`。
- 模块级配置或常量名称：`BWRAP_BINARY`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/supervisor/bwrap.py#L1-L503)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/supervisor/cgroup.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0d4f2346608a1500400486b9658ceba5d7ad4048fb5ec62d53e5d2476062e565 -->
**`jiuwenbox/src/jiuwenbox/supervisor/cgroup.py`**

- 源码对模块职责的说明：Per-sandbox cgroup resource limits.。
- `CgroupSetupError` 继承 `RuntimeError`。
- `CgroupBackend` 继承 `str, enum.Enum`。
- `CgroupHandle` 定义类型边界。
- 调用入口 `detect_backend()`；声明返回 `CgroupBackend / None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import enum`；`import logging`；`import os`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/supervisor/cgroup.py#L1-L528)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/supervisor/daemon_ipc.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f09ec000d2799683ece2d6216a4b80c0c0ce306b87e5d16ab3c4119129a1e712 -->
**`jiuwenbox/src/jiuwenbox/supervisor/daemon_ipc.py`**

- 源码对模块职责的说明：IPC protocol shared between box-server and the in-sandbox daemon.。
- 调用入口 `recv_exact(sock, n)`；声明返回 `bytes`。
- 调用入口 `send_frame(sock, payload)`；声明返回 `None`。
- 调用入口 `recv_frame(sock, max_size)`；声明返回 `bytes`。
- 调用入口 `encode_request(request_type, payload)`；声明返回 `bytes`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import socket`；`import struct`；`from typing import Any`。
- 模块级配置或常量名称：`SANDBOX_RESERVED_DIR`, `SANDBOX_DAEMON_SANDBOX_PATH`, `SANDBOX_CONTROL_SOCKET_NAME`, `SANDBOX_LAUNCHER_PATH`, `LISTENER_FD_ENV`, `SANDBOX_DAEMON_COMMAND`, `REQUEST_TYPE_EXEC`, `REQUEST_TYPE_SHUTDOWN`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/supervisor/daemon_ipc.py#L1-L125)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/supervisor/landlock.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a84a8b6a14310e4667dd739ea40f13ae07aa71bcbd93e1326afacb6c90064f86 -->
**`jiuwenbox/src/jiuwenbox/supervisor/landlock.py`**

- 源码对模块职责的说明：Landlock policy helpers shared by the supervisor and launcher.。
- 调用入口 `detect_landlock_abi()`；声明返回 `int`。
- 调用入口 `encode_landlock_payload(policy)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import base64`；`import ctypes`；`import json`。
- 模块级配置或常量名称：`LANDLOCK_CREATE_RULESET`, `LANDLOCK_ADD_RULE`, `LANDLOCK_RESTRICT_SELF`, `LANDLOCK_RULE_PATH_BENEATH`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/supervisor/landlock.py#L1-L94)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/supervisor/landlock_launcher.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=db3710e7899d9fbc24b6d0a56dc5a809cdd25fd4f6f19c30f19cad209ffdfb5d -->
**`jiuwenbox/src/jiuwenbox/supervisor/landlock_launcher.py`**

- 源码对模块职责的说明：In-sandbox Landlock launcher.。
- `LandlockRulesetAttr` 继承 `ctypes.Structure`。
- `LandlockPathBeneathAttr` 继承 `ctypes.Structure`。
- `LandlockHardRequirementError` 继承 `Exception`。
- 调用入口 `apply_landlock(payload)`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import base64`；`import ctypes`；`import json`。
- 模块级配置或常量名称：`LANDLOCK_CREATE_RULESET`, `LANDLOCK_ADD_RULE`, `LANDLOCK_RESTRICT_SELF`, `LANDLOCK_RULE_PATH_BENEATH`, `PR_SET_NO_NEW_PRIVS`, `READ_FILE`, `READ_DIR`, `EXECUTE`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/supervisor/landlock_launcher.py#L1-L296)。
<!-- /kb:file -->
