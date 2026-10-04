---
title: "gateway-health-check 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# gateway-health-check 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/gateway/health_check/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d17008a7d181257e42baa4143c720e80a7e9f45503dda732e0bda9adcc034b5f -->
**`jiuwenswarm/gateway/health_check/__init__.py`**

- 源码对模块职责的说明：HealthCheck 模块，负责原 Heartbeat 的服务探活能力。。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.gateway.health_check.health_check import HEALTH_CHECK_CHAN`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/health_check/__init__.py#L1-L28)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/health_check/health_check.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cf293788b8ce259a04e861e475c6593c2eab676299f43c600f63d1ae6fb1f857 -->
**`jiuwenswarm/gateway/health_check/health_check.py`**

- 源码对模块职责的说明：HealthCheck(旧 Heartbeat 探活)— Gateway 内周期性向 AgentServer 发送探活请求.。
- 调用入口 `normalize_active_hours(active_hours)`；声明返回 `dict[str, str] / None`。
- `HealthCheckConfig` 定义类型边界。
- `IHealthCheck` 继承 `ABC`；方法入口：`start`, `stop`, `is_running`。
- `GatewayHealthCheckService` 继承 `IHealthCheck`；方法入口：`__init__`, `start`, `stop`, `is_running`, `last_tick_ok`, `last_tick_at`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`import secrets`。
- 模块级配置或常量名称：`HEALTH_CHECK_CHANNEL_ID`, `HEALTH_CHECK_OK`, `HEALTH_CHECK_PROMPT`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/health_check/health_check.py#L1-L368)。
<!-- /kb:file -->
