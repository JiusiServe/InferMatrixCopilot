---
title: "common-tools 源码接口与集成边界 05"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# common-tools 源码接口与集成边界 05

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8ce32147feefe3ae74291a01acb4b0b4b9d8062ded76780711cb8339f4701b9c -->
**`jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py`**

- 源码对模块职责的说明：Utilities for xiaoyi handset tools.。
- `ToolInputError` 继承 `Exception`；方法入口：`__init__`。
- 异步入口 `execute_device_command(intent_name, command, timeout)`；声明返回 `Dict[str, Any]`。
- 调用入口 `raise_if_device_error(outputs, what_failed)`；声明返回 `None`。
- 调用入口 `validate_required_params(params, required)`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import json`；`from typing import Any, Dict, Optional`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L1-L289)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fd1b9f79349fca53708ebdec83b22747fa624e2588d17b4d9f5e96f381549c8c -->
**`jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py`**

- 源码对模块职责的说明：Collection tools - 小艺收藏工具.。
- 异步入口 `query_collection(query_all, query)`；声明返回 `Dict[str, Any]`。
- 异步入口 `delete_collection(item_ids)`；声明返回 `Dict[str, Any]`。
- 异步入口 `add_collection(data_type, content, uri, source_app_bundle_name, title)`；声明返回 `Dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`from typing import Any, Dict, List, Optional, Union`；`from openjiuwen.core.foundation.tool import tool`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/xiaoyi_collection_tool.py#L1-L390)。
<!-- /kb:file -->
