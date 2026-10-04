---
title: "jiuwenbox-src 源码接口与集成边界 03"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# jiuwenbox-src 源码接口与集成边界 03

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenbox/src/jiuwenbox/supervisor/network.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=892c3fffcbd829f2b8ca675f3f506438ef878ebe238802c64f686eb35eb7adde -->
**`jiuwenbox/src/jiuwenbox/supervisor/network.py`**

- 源码对模块职责的说明：Network isolation via iptables rules inside an unshared network namespace.。
- `NetworkSetupError` 继承 `RuntimeError`。
- `ResolvedNetworkRules` 定义类型边界。
- 调用入口 `resolve_domains(domains)`；声明返回 `list[str]`。
- 调用入口 `normalize_ips(values)`；声明返回 `list[str]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import hashlib`；`import ipaddress`；`import logging`。
- 模块级配置或常量名称：`IP_BINARY`, `IPTABLES_BINARY`, `IP6TABLES_BINARY`, `IPTABLES_LEGACY_BINARY`, `IP6TABLES_LEGACY_BINARY`, `IPTABLES_NFT_BINARY`, `IP6TABLES_NFT_BINARY`, `NETNS_NAME_PREFIX`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/supervisor/network.py#L1-L974)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/supervisor/sandbox_daemon.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7b1594a30ef694a708a184e5b010d8d6b6edb188e4e5cf4bd0730b15c8afc841 -->
**`jiuwenbox/src/jiuwenbox/supervisor/sandbox_daemon.py`**

- 源码对模块职责的说明：Long-running in-sandbox daemon that handles ''exec'' requests.。
- `DaemonState` 定义类型边界；方法入口：`__init__`, `begin_request`, `end_request`, `wait_drain`。
- `FastPathStats` 定义类型边界；方法入口：`__init__`, `record_request`, `record_hit`, `record_fallback`, `record_cold_start`, `record_worker_restart`。
- `FastPathUnavailable` 继承 `RuntimeError`；方法入口：`__init__`。
- `FastPathExecUncertain` 继承 `RuntimeError`；方法入口：`__init__`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import contextlib`；`import datetime`；`import errno`。
- 模块级配置或常量名称：`SANDBOX_RESERVED_DIR`, `SANDBOX_DAEMON_SANDBOX_PATH`, `SANDBOX_LAUNCHER_PATH`, `SANDBOX_DAEMON_COMMAND`, `LISTENER_FD_ENV`, `REQUEST_TYPE_EXEC`, `REQUEST_TYPE_SHUTDOWN`, `REQUEST_TYPE_WRITE_FILE`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/supervisor/sandbox_daemon.py#L1-L2719)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/src/jiuwenbox/supervisor/seccomp.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2485cabccb228c3eaeeccffb112e9f2e6e51f7ce2da7dd30bb1e9e772f0888a2 -->
**`jiuwenbox/src/jiuwenbox/supervisor/seccomp.py`**

- 源码对模块职责的说明：Seccomp BPF filter generation for sandbox syscall restriction.。
- 调用入口 `build_seccomp_filter(policy)`；声明返回 `bytes`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import platform`；`import struct`。
- 模块级配置或常量名称：`BPF_LD`, `BPF_W`, `BPF_ABS`, `BPF_JMP`, `BPF_JEQ`, `BPF_K`, `BPF_RET`, `SECCOMP_RET_ALLOW`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/supervisor/seccomp.py#L1-L336)。
<!-- /kb:file -->
