---
title: "code-rails 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# code-rails 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/heartbeat/store.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=36e26f0012d8f8ee734e4b79bd32d6a2b75e08bc4dcc7d2f774611138552a791 -->
**`jiuwenswarm/agents/harness/code/rails/heartbeat/store.py`**

- 源码对模块职责的说明：HeartbeatJobStore — 读写 heartbeat_jobs.json.。
- `HeartbeatStoreDataError` 继承 `ValueError`。
- `HeartbeatJobStore` 定义类型边界；方法入口：`__init__`, `path`, `list_jobs`, `get_job`, `claim_run`, `replace_claimed_run`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import json`；`import logging`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/heartbeat/store.py#L1-L1203)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/heartbeat/tools.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a3a147c9dbea26513d4d5a9ceff6d08293cf1371658ce9e7c0f6afe696cba88e -->
**`jiuwenswarm/agents/harness/code/rails/heartbeat/tools.py`**

- `HeartbeatJobService` 继承 `Protocol`；方法入口：`handle_operation`。
- `HeartbeatRuntimeBridge` 定义类型边界；方法入口：`__init__`, `set_service`, `build_tools`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any, Protocol`；`from openjiuwen.core.foundation.tool import LocalFunction, Tool, ToolCard`；`from jiuwenswarm.agents.harness.code.rails.heartbeat.models import DEFAULT_`。
- 模块级配置或常量名称：`HEARTBEAT_TOOL_NAMES`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/heartbeat/tools.py#L1-L312)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/heartbeat_rail.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d5e0c0b19bc6d2644bada98db37fdf8baa90287e48fa9d05910e3c5153d9be56 -->
**`jiuwenswarm/agents/harness/code/rails/heartbeat_rail.py`**

- 源码对模块职责的说明：Agent Heartbeat Rail shared by single-agent and Team profiles.。
- `HeartbeatRail` 继承 `DeepAgentRail`；方法入口：`__init__`, `init`, `uninit`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from typing import Any`；`from openjiuwen.harness.rails.base import DeepAgentRail`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/heartbeat_rail.py#L1-L60)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/sdd/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=13798996ceaeeebf821af6100dc8375e2024105f9d100b9eff7595db187d9617 -->
**`jiuwenswarm/agents/harness/code/rails/sdd/__init__.py`**

- 源码对模块职责的说明：SDD-family state-machine rails — shared base + independent rails.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from jiuwenswarm.agents.harness.code.rails.sdd.common.rail_state_machine im`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/__init__.py#L1-L24)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/sdd/common/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=36208b064ce2a558059f34438d472ee2fd786fdd38c9b0736e63926a7de88689 -->
**`jiuwenswarm/agents/harness/code/rails/sdd/common/__init__.py`**

- 源码对模块职责的说明：Shared infrastructure for SDD-family rails.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from jiuwenswarm.agents.harness.code.rails.sdd.common.rail_state_machine im`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/common/__init__.py#L1-L15)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a3da380c0cec0cf71edffb09beb6fa3397926c0c6617b2fad9dede649755d48a -->
**`jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py`**

- 源码对模块职责的说明：RailStateMachineBase — shared base for state-machine-driven rails.。
- `RailStateMachineBase` 继承 `DeepAgentRail`；方法入口：`__init__`, `init`, `uninit`, `before_model_call`, `after_tool_call`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from pathlib import Path`；`from typing import Any, Optional`；`from openjiuwen.core.foundation.tool import LocalFunction, ToolCard`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/common/rail_state_machine.py#L1-L680)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/sdd/design_rail/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a7b7ca97053499538f727f82562ec58d2ff6c8d0bf08f1af9b9c601e496b2fa7 -->
**`jiuwenswarm/agents/harness/code/rails/sdd/design_rail/__init__.py`**

- 源码对模块职责的说明：DesignRail package — SDD (Spec-Driven Development) state machine for Code mode.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from jiuwenswarm.agents.harness.code.rails.sdd.design_rail.rail import Desi`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/design_rail/__init__.py#L1-L20)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/sdd/design_rail/config_loader.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=768c603c4b56b4dd5479b668f2a9969e15ee5ebf4bea0e517ac881d1c3e55336 -->
**`jiuwenswarm/agents/harness/code/rails/sdd/design_rail/config_loader.py`**

- 源码对模块职责的说明：config_loader — YAML load + one-shot validation for design_rail/config.yaml.。
- `ConfigLoadError` 继承 `Exception`。
- `ValidationResult` 定义类型边界。
- 调用入口 `load(path)`；声明返回 `dict`。
- 调用入口 `validate(cfg, rail_pkg_dir)`；声明返回 `ValidationResult`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass, field`；`from pathlib import Path`；`from typing import List, Optional`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/design_rail/config_loader.py#L1-L158)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=72d1310aa3bddcdd1a3f42e83eac10f6161dbd907b1f039f65b6fb7aee72198b -->
**`jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py`**

- 源码对模块职责的说明：DesignRail — SDD (Spec-Driven Development) state machine for Code mode.。
- `DesignRail` 继承 `RailStateMachineBase`；方法入口：`__init__`, `after_tool_call`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from pathlib import Path`；`from typing import Optional`；`import re`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/design_rail/rail.py#L1-L211)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/sdd/design_rail/skills/aet-req-analysis/scripts/assemble-checklist.mjs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8e253a6ca9fe6b94a772a8b8edf3522ea2d845392bc2711947151cf10fc5b5e2 -->
**`jiuwenswarm/agents/harness/code/rails/sdd/design_rail/skills/aet-req-analysis/scripts/assemble-checklist.mjs`**

- 源码声明的类型、组件或调用边界：`__dirname`, `skillTemplatesDir`, `projectAetDir`, `userAetDir`, `resolveFile`, `searchPaths`, `filePath`, `parseArgs`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { readFileSync, existsSync } from 'fs';`；`import { join, dirname } from 'path';`；`import { fileURLToPath } from 'url';`；`import { homedir } from 'os';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/design_rail/skills/aet-req-analysis/scripts/assemble-checklist.mjs#L1-L230)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/sdd/design_rail/skills/aet-req-analysis/scripts/assemble-template.mjs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9aadf8fb0a3fd8dc9a7da89c4e333967113233f6e5704a6fdad012f0129b16ed -->
**`jiuwenswarm/agents/harness/code/rails/sdd/design_rail/skills/aet-req-analysis/scripts/assemble-template.mjs`**

- 源码声明的类型、组件或调用边界：`__dirname`, `skillTemplatesDir`, `projectAetDir`, `userAetDir`, `resolveFile`, `searchPaths`, `filePath`, `getCurrentTime`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { readFileSync, existsSync } from 'fs';`；`import { join, dirname } from 'path';`；`import { fileURLToPath } from 'url';`；`import { homedir } from 'os';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/design_rail/skills/aet-req-analysis/scripts/assemble-template.mjs#L1-L392)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/sdd/design_rail/skills/aet-req-design/scripts/assemble-checklist.mjs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8e253a6ca9fe6b94a772a8b8edf3522ea2d845392bc2711947151cf10fc5b5e2 -->
**`jiuwenswarm/agents/harness/code/rails/sdd/design_rail/skills/aet-req-design/scripts/assemble-checklist.mjs`**

- 源码声明的类型、组件或调用边界：`__dirname`, `skillTemplatesDir`, `projectAetDir`, `userAetDir`, `resolveFile`, `searchPaths`, `filePath`, `parseArgs`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { readFileSync, existsSync } from 'fs';`；`import { join, dirname } from 'path';`；`import { fileURLToPath } from 'url';`；`import { homedir } from 'os';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/design_rail/skills/aet-req-design/scripts/assemble-checklist.mjs#L1-L230)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/sdd/design_rail/skills/aet-req-design/scripts/assemble-template.mjs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9aadf8fb0a3fd8dc9a7da89c4e333967113233f6e5704a6fdad012f0129b16ed -->
**`jiuwenswarm/agents/harness/code/rails/sdd/design_rail/skills/aet-req-design/scripts/assemble-template.mjs`**

- 源码声明的类型、组件或调用边界：`__dirname`, `skillTemplatesDir`, `projectAetDir`, `userAetDir`, `resolveFile`, `searchPaths`, `filePath`, `getCurrentTime`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { readFileSync, existsSync } from 'fs';`；`import { join, dirname } from 'path';`；`import { fileURLToPath } from 'url';`；`import { homedir } from 'os';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/sdd/design_rail/skills/aet-req-design/scripts/assemble-template.mjs#L1-L392)。
<!-- /kb:file -->
