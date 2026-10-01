---
title: "common-rails 源码接口与集成边界 07"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# common-rails 源码接口与集成边界 07

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/tool_permission_context.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4150f4534106148d98e5b14c3338f95e285212379bab8bebb3ea7d6e81936f5a -->
**`jiuwenswarm/agents/harness/common/rails/permissions/tool_permission_context.py`**

- 源码对模块职责的说明：Tool permission channel context.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import contextvars`。
- 模块级配置或常量名称：`PUBLIC_HTTPS_FETCH_CONTEXT_ATTR`, `TOOL_PERMISSION_CHANNEL_ID`, `TOOL_PERMISSION_REQUEST_ID`, `SKILLS_REBUILD_SILENT`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/tool_permission_context.py#L1-L40)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/trusted_search_urls.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0b30c17fa49fe5aaa9bbdca540733fddf52b31706a53c3f16a7e91f36ab1e704 -->
**`jiuwenswarm/agents/harness/common/rails/permissions/trusted_search_urls.py`**

- 源码对模块职责的说明：Session-owned trusted search URL ledger and Host producer callback.。
- `SessionTrustedSearchUrls` 定义类型边界；方法入口：`__init__`, `bind_session`, `record_batch`, `contains`, `sources`, `dispose`。
- 调用入口 `bind_trusted_search_producer(ledger, key, tool_name, max_results)`；声明返回 `None`。
- 调用入口 `clear_trusted_search_producer()`；声明返回 `None`。
- 调用入口 `complete_trusted_search_producer(tool_name, success, urls)`；声明返回 `tuple[int, int]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from collections import OrderedDict`；`from collections.abc import Iterable`；`from contextvars import ContextVar`。
- 模块级配置或常量名称：`MAX_TRUSTED_SEARCH_URLS_PER_SESSION`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/trusted_search_urls.py#L1-L236)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/url_safety.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6861591e5d25162fa152cd13bcc2e7b4e73ea20132b3a9549aa726bed4445d70 -->
**`jiuwenswarm/agents/harness/common/rails/permissions/url_safety.py`**

- 源码对模块职责的说明：Shared URL review helpers for read-only network and browser actions.。
- `AbsoluteUriFacts` 定义类型边界。
- `NetworkScopeFacts` 定义类型边界。
- 调用入口 `inspect_network_scope(subject)`；声明返回 `NetworkScopeFacts`。
- 调用入口 `inspect_absolute_uris(value, workspace_root)`；声明返回 `tuple[AbsoluteUriFacts, ...]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import re`；`from collections.abc import Mapping, Sequence`；`from dataclasses import dataclass, field`。
- 模块级配置或常量名称：`URL_PATTERN`, `DOMAIN_PATTERN`, `TRAILING_URL_PUNCTUATION`, `ABSOLUTE_URI_PATTERN`, `UPLOAD_KEYS`, `SAFE_URL_SCHEMES`, `INTERNAL_HOST_SUFFIXES`, `METADATA_HOSTS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/url_safety.py#L1-L541)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/project_memory/files.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a32c3fc504a38782735ef23d8d8c9f8c15b4cf386303a4b18f839ffdb751c3e2 -->
**`jiuwenswarm/agents/harness/common/rails/project_memory/files.py`**

- 源码对模块职责的说明：Project memory file discovery + merge.。
- `LoadedMemoryFile` 定义类型边界。
- `GitWorktreeInfo` 定义类型边界。
- 调用入口 `clear_project_memory_cache(workspace)`；声明返回 `None`。
- 调用入口 `find_project_root(cwd)`；声明返回 `Optional[Path]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import functools`；`import glob as _glob`；`import os`。
- 模块级配置或常量名称：`PROJECT_ROOT_MARKERS`, `PROJECT_MEMORY_FILES`, `LOCAL_MEMORY_FILES`, `PROJECT_MEMORY_GLOBS`, `USER_MEMORY_FILES`, `USER_MEMORY_GLOBS`, `MANAGED_MEMORY_FILES`, `MANAGED_MEMORY_GLOBS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/project_memory/files.py#L1-L962)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/project_memory/section.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c6706ea86ce5d7b4fbc9d07d81b1fb183063e7a9adb112686db9e49ca11369eb -->
**`jiuwenswarm/agents/harness/common/rails/project_memory/section.py`**

- 源码对模块职责的说明：PromptSection factory for project memory.。
- 调用入口 `build_project_memory_section(content, language, priority)`；声明返回 `Optional[PromptSection]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Optional`；`from openjiuwen.harness.prompts import PromptSection`；`from jiuwenswarm.agents.harness.common.prompt.priority_registry import Syst`。
- 模块级配置或常量名称：`SECTION_NAME`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/project_memory/section.py#L1-L58)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/project_memory_rail.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3a0b15e11d51b3eb85af0beeeca01f43a2515e0451b97fbdf9985d7dfc716963 -->
**`jiuwenswarm/agents/harness/common/rails/project_memory_rail.py`**

- 源码对模块职责的说明：ProjectMemoryRail -- jiuwenswarm product-side rail.。
- `ProjectMemoryRail` 继承 `DeepAgentRail`；方法入口：`__init__`, `init`, `uninit`, `set_language`, `set_workspace_path`, `get_language`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import os`；`from typing import TYPE_CHECKING`；`from openjiuwen.core.single_agent.rail.base import AgentCallbackContext`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/project_memory_rail.py#L1-L227)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/response_prompt_rail.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=53a1e957b488b4d95c861a86620de8b618b059ed5dae65f95a827405abdd65e4 -->
**`jiuwenswarm/agents/harness/common/rails/response_prompt_rail.py`**

- 源码对模块职责的说明：Inject the response/message-format section before each model call.。
- `ResponsePromptRail` 继承 `DeepAgentRail`；方法入口：`__init__`, `init`, `uninit`, `set_channel`, `before_invoke`, `before_model_call`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from collections.abc import Mapping`；`from openjiuwen.core.single_agent.rail.base import AgentCallbackContext`。
- 模块级配置或常量名称：`A2UI_BROWSER_WORKFLOW_CONTEXT_KEY`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/response_prompt_rail.py#L1-L243)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/runtime_prompt_rail.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=27e94869ea10fb9bfae3419fb9748473c306cbd20228799ea266f05bb131b0af -->
**`jiuwenswarm/agents/harness/common/rails/runtime_prompt_rail.py`**

- 源码对模块职责的说明：RuntimePromptRail — Assemble stable and dynamic runtime prompt state.。
- `RuntimePromptRail` 继承 `DeepAgentRail`；方法入口：`__init__`, `init`, `uninit`, `set_language`, `set_channel`, `set_trusted_dirs`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import os`；`import shutil`；`import sys`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/runtime_prompt_rail.py#L1-L795)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/skill_retrieval_prompt_rail.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2fdab07abeaa35d19a1f441ebb12cb04847498d0f9f3906180e68fe2e6b703f4 -->
**`jiuwenswarm/agents/harness/common/rails/skill_retrieval_prompt_rail.py`**

- 源码对模块职责的说明：Prompt boundary for Symphony-managed runtime Skill discovery.。
- `SkillRetrievalPromptRail` 继承 `DeepAgentRail`；方法入口：`__init__`, `init`, `uninit`, `before_invoke`, `before_model_call`, `after_model_call`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from typing import Any`；`from openjiuwen.core.single_agent.rail.base import AgentCallbackContext`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/skill_retrieval_prompt_rail.py#L1-L581)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/stream_event_rail.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ab9b201825ad0f80241c7dc7fc4a8b075896e3bd8f00a8590f3ea37254f41bcc -->
**`jiuwenswarm/agents/harness/common/rails/stream_event_rail.py`**

- 源码对模块职责的说明：JiuSwarmStreamEventRail — Stream event emission, pause checks, context fix.。
- `JiuSwarmStreamEventRail` 继承 `DeepAgentRail`；方法入口：`__init__`, `callback_priority`, `init`, `pause`, `resume`, `abort`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import copy`；`import json`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/stream_event_rail.py#L1-L1840)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/symphony/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0f6b0c6fb9e6d2ebea644f79fae92fdad38e38ce058cb3d791bb85a01da9564f -->
**`jiuwenswarm/agents/harness/common/rails/symphony/__init__.py`**

- 源码对模块职责的说明：Symphony-specific agent rails and stream lifecycle helpers.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.agents.harness.common.rails.symphony.orchestration_rail im`；`from jiuwenswarm.agents.harness.common.rails.symphony.tool_stream_events im`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/symphony/__init__.py#L1-L10)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/symphony/orchestration_rail.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5f784c3dd4a16f253398c56abfd31b7c786b4defc062b489157bc4849a9a2a2c -->
**`jiuwenswarm/agents/harness/common/rails/symphony/orchestration_rail.py`**

- 源码对模块职责的说明：Prompt and candidate lifecycle rail for Symphony orchestration.。
- `SymphonyOrchestrationRail` 继承 `DeepAgentRail`；方法入口：`__init__`, `init`, `uninit`, `before_invoke`, `after_invoke`, `before_model_call`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import re`；`import threading`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/symphony/orchestration_rail.py#L1-L1140)。
<!-- /kb:file -->
