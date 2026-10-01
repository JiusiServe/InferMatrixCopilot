---
title: "jiuwenbox-src 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# jiuwenbox-src 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenbox/src/jiuwenbox/bundled_configs.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9680248b238b8ae50193f3fa1c9b6addd36ba24dc8685fa4bcd92cd41166901b -->
**`jiuwenbox/src/jiuwenbox/bundled_configs.py`**

- 源码对模块职责的说明：Bundled policy YAML files shipped inside the jiuwenbox package.。
- 调用入口 `configs_dir()`；声明返回 `Path`。
- 调用入口 `default_policy_path()`；声明返回 `Path`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from pathlib import Path`；`import jiuwenbox`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/bundled_configs.py#L1-L20)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/cli/jiuwenbox.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=92c1b01c74f12843b193ec498bd8fa64e3e0cdc04265bbd8a7ef761884509649 -->
**`jiuwenbox/src/jiuwenbox/cli/jiuwenbox.py`**

- 源码对模块职责的说明：jiuwenbox HTTP API 命令行客户端 (单文件实现).。
- 调用入口 `cmd_health(args, client)`；声明返回 `Any`。
- 调用入口 `cmd_sandbox_create(args, client)`；声明返回 `Any`。
- 调用入口 `cmd_sandbox_ls(args, client)`；声明返回 `Any`。
- 调用入口 `cmd_sandbox_get(args, client)`；声明返回 `Any`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import json`；`import logging`。
- 模块级配置或常量名称：`EXIT_OK`, `EXIT_API_ERROR`, `EXIT_CONNECT_ERROR`, `EXIT_LOCAL_ERROR`, `EXIT_INTERRUPT`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/cli/jiuwenbox.py#L1-L1513)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/logging_config.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dd61e3b36d0c06f6d1785405f4de74e48caf6df5a389cfa1879177ecc327b192 -->
**`jiuwenbox/src/jiuwenbox/logging_config.py`**

- 源码对模块职责的说明：Shared logging configuration for jiuwenbox.。
- 调用入口 `patch_uvicorn_logging()`；声明返回 `None`。
- 调用入口 `configure_logging(level)`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`。
- 模块级配置或常量名称：`LOG_FORMAT`, `LOG_DATE_FORMAT`, `UVICORN_LOGGER_NAMES`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/logging_config.py#L1-L43)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/models/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b847f7188b548fdcc9de1a565b4405ffd957f5fd7663626b56eab39535cc9689 -->
**`jiuwenbox/src/jiuwenbox/models/__init__.py`**

- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenbox.models.sandbox import BackgroundExecRequest, BackgroundExecR`；`from jiuwenbox.models.policy import ArchitectureSyscallPolicy, BindMount, D`；`from jiuwenbox.models.common import AuditEvent, AuditEventType, HealthRespo`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/models/__init__.py#L1-L67)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/models/common.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8fabae393eb510f19f79894501a2216d263e71468e07d319e871dc09e6d9b606 -->
**`jiuwenbox/src/jiuwenbox/models/common.py`**

- 源码对模块职责的说明：Common data models shared across components.。
- `AuditEventType` 继承 `str, enum.Enum`。
- `AuditEvent` 继承 `BaseModel`。
- `HealthResponse` 继承 `BaseModel`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import enum`；`from datetime import datetime`；`from pydantic import BaseModel, Field`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/models/common.py#L1-L44)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/models/policy.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=456f8d88ce099de00affaa3c3bcbc17707430340b870c9528eee9c88bcc6363b -->
**`jiuwenbox/src/jiuwenbox/models/policy.py`**

- 源码对模块职责的说明：Security policy data models (static only).。
- `BindMount` 继承 `BaseModel`；方法入口：`reject_wildcard_host_path`, `expand_paths`。
- `BindRootEntries` 继承 `BaseModel`；方法入口：`expand_paths`。
- `DeviceMount` 继承 `BaseModel`；方法入口：`expand_paths`。
- `DirectoryMount` 继承 `BaseModel`；方法入口：`expand_path`, `permissions_must_be_octal`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import enum`；`import os`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/models/policy.py#L1-L802)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/models/sandbox.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=db14d4284a01665c64d6c31d75d83f0958fde682247409f2400a0f87bbf0acd3 -->
**`jiuwenbox/src/jiuwenbox/models/sandbox.py`**

- 源码对模块职责的说明：Sandbox data models.。
- `InvalidSandboxIdError` 继承 `Exception`。
- `InvalidJobIdError` 继承 `Exception`。
- 调用入口 `generate_sandbox_id()`；声明返回 `str`。
- 调用入口 `validate_custom_sandbox_id(value)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import enum`；`import re`；`import uuid`。
- 模块级配置或常量名称：`SANDBOX_ID_MIN_LEN`, `SANDBOX_ID_MAX_LEN`, `CUSTOM_SANDBOX_ID_RE`, `SANDBOX_ID_FORMAT_MESSAGE`, `JOB_ID_MIN_LEN`, `JOB_ID_MAX_LEN`, `CUSTOM_JOB_ID_RE`, `JOB_ID_FORMAT_MESSAGE`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/models/sandbox.py#L1-L166)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/proxy/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9d7a26e6a3d989fed22ff7891ab1011186560d3f5c3243e15bdfcc3f1f5ede76 -->
**`jiuwenbox/src/jiuwenbox/proxy/__init__.py`**

- 源码对模块职责的说明：Inference privacy proxy package.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenbox.proxy.inference_privacy_proxy import InferencePrivacyProxy, `；`from jiuwenbox.proxy.inference_privacy_proxy_manager import InferencePrivac`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/proxy/__init__.py#L1-L24)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/server/audit_logger.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=84f371650a2c3c58dec23ab14cf44aa5fc4f6b07d562a646be5a98ce61acdbd2 -->
**`jiuwenbox/src/jiuwenbox/server/audit_logger.py`**

- 源码对模块职责的说明：Structured audit logging in JSONL format.。
- `AuditLogger` 定义类型边界；方法入口：`__init__`, `log_event`, `log_event_sync`, `log`, `flush`, `read_logs`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import logging`；`import threading`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/server/audit_logger.py#L1-L243)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/server/auth.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4d9ef574511d1432ee62d7e76d158bc9b38e965d7cdba0678c2050485674c219 -->
**`jiuwenbox/src/jiuwenbox/server/auth.py`**

- 源码对模块职责的说明：Opt-in Bearer token authentication for the jiuwenbox HTTP API.。
- 调用入口 `get_configured_token()`；声明返回 `str / None`。
- 调用入口 `extract_bearer_token(authorization)`；声明返回 `str / None`。
- 调用入口 `token_is_valid(provided, expected)`；声明返回 `bool`。
- `BearerTokenAuthMiddleware` 继承 `BaseHTTPMiddleware`；方法入口：`dispatch`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import hmac`；`import os`；`from starlette.middleware.base import BaseHTTPMiddleware`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/server/auth.py#L1-L59)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/server/launcher.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2387df2e820cc71b65658469d6a8d62cfee8678ca4a447962d9f286fa1cfb2f0 -->
**`jiuwenbox/src/jiuwenbox/server/launcher.py`**

- 源码对模块职责的说明：jiuwenbox server 启动器 (HTTP / UDS 二选一).。
- `ListenURIError` 继承 `ValueError`。
- 调用入口 `parse_listen(uri)`；声明返回 `ListenSpec`。
- 调用入口 `main(argv)`；声明返回 `int`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import logging`；`import os`。
- 模块级配置或常量名称：`ENV_LISTEN`, `ENV_UDS_PATH`, `ENV_UDS_MODE`, `ENV_SAVE_LOGS_DIR`, `DEFAULT_LISTEN`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/server/launcher.py#L1-L300)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/server/policy_engine.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=47bd49ea9a2021e1687728923927c20e2a7e512d664cc2c4cf954a1ab35e94e1 -->
**`jiuwenbox/src/jiuwenbox/server/policy_engine.py`**

- 源码对模块职责的说明：Policy Engine - validates and resolves static security policies.。
- `PolicyValidationError` 继承 `Exception`；方法入口：`__init__`。
- `PolicyEngine` 定义类型边界；方法入口：`__init__`, `validate_policy`, `resolve_policy`, `merge_policy`, `write_sandbox_policy`, `load_policy_from_file`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from collections.abc import Mapping`；`from pathlib import Path, PurePosixPath`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/server/policy_engine.py#L1-L311)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/server/policy_reader.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8a9496022582db5c21a774ffa321a485ec8a6cca3487d35f28113d3c910a6381 -->
**`jiuwenbox/src/jiuwenbox/server/policy_reader.py`**

- 源码对模块职责的说明：Policy file reader for loading security policies from YAML files.。
- `PolicyReader` 定义类型边界；方法入口：`__init__`, `load_policy`, `load_policy_from_file`, `is_proxy_only`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import os`；`from pathlib import Path`。
- 模块级配置或常量名称：`JIUWENBOX_POLICY_PATH_ENV`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/server/policy_reader.py#L1-L121)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/server/proxy_manager.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=de6e09970f72e820939d812d9d98f38ddb1ebf80e4710fa8427ad97a15299a67 -->
**`jiuwenbox/src/jiuwenbox/server/proxy_manager.py`**

- 源码对模块职责的说明：Proxy lifecycle manager.。
- `ProxyManager` 定义类型边界；方法入口：`__init__`, `load_policy`, `start`, `stop`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from pathlib import Path`；`from jiuwenbox.logging_config import configure_logging`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/server/proxy_manager.py#L1-L67)。
<!-- /kb:file -->
