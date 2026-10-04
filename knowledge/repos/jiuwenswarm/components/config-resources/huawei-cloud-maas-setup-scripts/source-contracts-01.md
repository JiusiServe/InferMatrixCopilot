---
title: "huawei-cloud-maas-setup-scripts 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# huawei-cloud-maas-setup-scripts 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c6c0d8c3dc1fa822d6108c748fe58d7d5c3948ae011d6ebe69ff1a951217ce84 -->
**`jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py`**

- 源码对模块职责的说明：自动完成华为云 MaaS 委托授权（V2 折中方案）。。
- 调用入口 `auto_authorize(cdp_url, timeout_s)`；声明返回 `dict`。
- 调用入口 `main(argv)`；声明返回 `int`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import logging`；`import sys`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_authorize.py#L1-L234)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d32fef2258903e829116987deebf83dd7bba2269ea8f18f880db3f48a961d970 -->
**`jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py`**

- 源码对模块职责的说明：自动创建华为云 MaaS API Key 并捕获完整 Key（V2 折中方案）。。
- 调用入口 `auto_create_apikey(cdp_url, tag, description, timeout_s)`；声明返回 `dict`。
- 调用入口 `main(argv)`；声明返回 `int`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import logging`；`import re`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_create_apikey.py#L1-L410)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_open_model.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=423aaf7b799471baa3f9db9c209ff568ed329f0108f4396b5e026ccec0d05d74 -->
**`jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_open_model.py`**

- 源码对模块职责的说明：自动开通华为云 MaaS 预置服务（文本生成）模型。。
- 调用入口 `auto_open_models(cdp_url, models, type_filter, timeout_s)`；声明返回 `dict`。
- 调用入口 `main(argv)`；声明返回 `int`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import json`；`import logging`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/auto_open_model.py#L1-L816)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f07a03ae2d50200e95536bf380e6048eecbb2987d24273fd5830838cefb0e222 -->
**`jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py`**

- 源码对模块职责的说明：检测华为云账号状态（实名认证 + 引导弹窗关闭）。。
- 调用入口 `check_account(cdp_url, timeout_s)`；声明返回 `dict`。
- 调用入口 `main(argv)`；声明返回 `int`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import logging`；`import sys`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/check_account.py#L1-L132)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/config_writer.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=34f8aa0df294759e7a0c3ea0f4c32fff61af4bb96158964ba1143cc3bdd9d091 -->
**`jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/config_writer.py`**

- 源码对模块职责的说明：华为云 MaaS 模型配置写入脚本。。
- 调用入口 `safe_update_env(updates, env_path)`；声明返回 `Path`。
- 调用入口 `add_models(api_base, api_key, models, provider)`；声明返回 `dict[str, Any]`。
- 调用入口 `main(argv)`；声明返回 `int`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import json`；`import logging`。
- 模块级配置或常量名称：`ENV_PREFIX`, `DEFAULT_PROVIDER`, `DEFAULT_TIMEOUT`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/config_writer.py#L1-L358)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/ensure_browser.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d84365ebb25532adfadc3fc80f9e42b3f600fcd5a4d7a2624a7e67b7127b6edb -->
**`jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/ensure_browser.py`**

- 源码对模块职责的说明：确保 Chromium 系浏览器在 CDP 端口可用。。
- 调用入口 `ensure_browser(timeout_s)`；声明返回 `dict[str, Any]`。
- 调用入口 `main(argv)`；声明返回 `int`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import json`；`import logging`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/ensure_browser.py#L1-L321)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/cdp_client.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b928dc49b3d90a0bcd62f595166c86e40f2bf27799a338dcb84706be4a20e2ee -->
**`jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/cdp_client.py`**

- 源码对模块职责的说明：CDP 连接与浏览器状态工具。。
- 调用入口 `emit(step, message)`；声明返回 `None`。
- 调用入口 `emit_progress(current, total, message)`；声明返回 `None`。
- 调用入口 `output_json(payload)`；声明返回 `None`。
- 调用入口 `load_browser_profile()`；声明返回 `dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import logging`；`import os`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/cdp_client.py#L1-L228)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/flow_state.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8b4042a376ca2c0c62d988deda0dd4508e5167a104f05adfe4bccd88b5341e46 -->
**`jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/flow_state.py`**

- 源码对模块职责的说明：统一的成功/失败 JSON 生成函数，供所有脚本复用。。
- 调用入口 `make_failure(stage, message, **extra)`；声明返回 `dict[str, Any]`。
- 调用入口 `make_success(stage, **extra)`；声明返回 `dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/flow_state.py#L1-L24)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/huawei_selectors.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3871ffe4f3b39133199068e755469908663493e70bc615348faec8baaecd2b86 -->
**`jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/huawei_selectors.py`**

- 源码对模块职责的说明：华为云 MaaS 控制台页面选择器集中维护。。
- `SelectorSet` 定义类型边界；方法入口：`first_visible`, `wait_first`。
- 调用入口 `click_first_visible(page, selector_set, timeout_ms)`；声明返回 `bool`。
- 调用入口 `click_wait_first(page, selector_set, timeout_ms)`；声明返回 `bool`。
- 调用入口 `extract_api_key_from_dialog(page)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import time`；`from dataclasses import dataclass, field`。
- 模块级配置或常量名称：`MAAS_HOMEPAGE_URL`, `MAAS_APIKEY_URL`, `MAAS_DEPLOYMENT_URL`, `HUAWEI_COST_CENTER_URL`, `HUAWEI_REALNAME_AUTH_URL`, `MAAS_DEPLOYMENT_ROWS`, `MAAS_DEPLOYMENT_ROW_NAME`, `MAAS_DEPLOYMENT_ROW_STATUS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/lib/huawei_selectors.py#L1-L605)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/navigate.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e8780253e3bf318bde60ae3de0d4e30ba894bbb270b7ec12f9d57e9062f6f3e1 -->
**`jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/navigate.py`**

- 源码对模块职责的说明：通用 URL 跳转脚本（V2 折中方案核心脚本）。。
- 调用入口 `navigate(url, cdp_url, wait_until, timeout_ms)`；声明返回 `dict`。
- 调用入口 `main(argv)`；声明返回 `int`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import json`；`import logging`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/navigate.py#L1-L124)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/validate_config.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=64d7aa1ee38291d70d555bee1079c9daad18d1bdc3abff8f77b631ebfcad5cb2 -->
**`jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/validate_config.py`**

- 源码对模块职责的说明：验证 jiuwenswarm 中的华为云 MaaS 配置是否有效。。
- 调用入口 `check_config_exists()`；声明返回 `tuple[bool, dict[str, str]]`。
- 调用入口 `test_connectivity(api_base, api_key, model_name)`；声明返回 `tuple[bool, str]`。
- 调用入口 `main()`；声明返回 `int`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import json`；`import logging`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/huawei-cloud-maas-setup/scripts/validate_config.py#L1-L152)。
<!-- /kb:file -->
