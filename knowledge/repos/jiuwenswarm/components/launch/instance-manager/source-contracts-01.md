---
title: "instance-manager 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# instance-manager 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/instance_manager/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bc5dae7e753bf107f063bf4b77aaf96d44ff4f44d50943dfdc208e2f1a9de409 -->
**`jiuwenswarm/instance_manager/__init__.py`**

- 源码对模块职责的说明：Instance manager for multi-instance isolation.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from jiuwenswarm.instance_manager.config import InstanceConfig, InstanceSta`；`from jiuwenswarm.instance_manager.config import is_valid_instance_name, val`；`from jiuwenswarm.instance_manager.config import calculate_instance_ports, c`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/instance_manager/__init__.py#L1-L156)。
<!-- /kb:file -->
