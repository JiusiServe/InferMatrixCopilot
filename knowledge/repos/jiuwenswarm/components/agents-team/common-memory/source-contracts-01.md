---
title: "common-memory 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# common-memory 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/agents/harness/common/memory/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b543f21c6aba807dea427fbf333d325da6f295995cbfcd8bc1e11af0e4786177 -->
**`jiuwenswarm/agents/harness/common/memory/__init__.py`**

- 源码对模块职责的说明：Memory system for JiuWenSwarm.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from .types import MemorySearchResult, MemoryFileEntry, MemoryChunk, Memory`；`from .manager import MemoryIndexManager, get_memory_manager, clear_memory_m`；`from .config import MemorySettings, create_memory_settings, is_memory_enabl`；`from .embeddings import EmbeddingProvider, create_embedding_provider`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/__init__.py#L1-L78)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/memory/config.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e0125a4ac4aa76fc1b078e183d622d71283d70e1c5cc9d8329633b94b6d477bc -->
**`jiuwenswarm/agents/harness/common/memory/config.py`**

- 源码对模块职责的说明：Memory configuration for JiuWenSwarm.。
- 调用入口 `clear_config_cache()`；声明返回 `None`。
- 调用入口 `get_embed_config()`；声明返回 `Dict[str, str]`。
- `MemorySettings` 定义类型边界。
- 调用入口 `create_memory_settings(workspace_dir, **overrides)`；声明返回 `MemorySettings`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import logging`；`import os`；`import re`；`from typing import Any, Optional, Dict, List`。
- 模块级配置或常量名称：`DEFAULT_CONFIG_PATH`, `DEFAULT_WORKSPACE_DIR`, `EMBED_API_KEY`, `EMBED_BASE_URL`, `EMBED_MODEL`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/config.py#L1-L339)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/memory/dreaming/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=15c165eccfaf213bdc12227aa7b3e02f63b9c012c7e60c856c60703b593a7a62 -->
**`jiuwenswarm/agents/harness/common/memory/dreaming/__init__.py`**

- 源码对模块职责的说明：Public API of Dreaming Memory Integration Module。
- 调用入口 `get_dreaming_orchestrator(mode)`；声明返回 `DreamingOrchestrator / None`。
- 异步入口 `start_dreaming(sessions_dir, output_dir, mode, busy_checker)`；声明返回 `DreamingOrchestrator / None`。
- 异步入口 `stop_dreaming(mode)`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from typing import Callable`；`from openjiuwen.core.memory.dreaming import DreamingOrchestrator`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/dreaming/__init__.py#L1-L86)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/memory/dreaming/sweeper.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7d05da317d6cb215e9e4f78ca4b8e7d6c98b9be5dbed0fb2a27f49275b2bfbdd -->
**`jiuwenswarm/agents/harness/common/memory/dreaming/sweeper.py`**

- 源码对模块职责的说明：Dreaming Sweeper: Scan + Compression + LLM Extraction + Promotion (Unified Pipeline)。
- `DreamingConfig` 定义类型边界；方法入口：`load`。
- `Sweeper` 定义类型边界；方法入口：`__init__`, `init`, `run_sweep`, `scan_new_sessions`, `load_existing_summary`, `promote_agent`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import hashlib`；`import json`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/dreaming/sweeper.py#L1-L813)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/memory/embeddings.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0bc2b6cdaea6c344e1f105e9d74424bf3aaf7047d17b3472d95388ba7eb99123 -->
**`jiuwenswarm/agents/harness/common/memory/embeddings.py`**

- 源码对模块职责的说明：Embedding providers for memory system.。
- `EmbeddingProvider` 继承 `ABC`；方法入口：`embed_query`, `embed_documents`。
- `OpenAICompatibleEmbeddingProvider` 继承 `EmbeddingProvider`；方法入口：`__init__`, `embed_query`, `embed_documents`。
- `MockEmbeddingProvider` 继承 `EmbeddingProvider`；方法入口：`embed_query`, `embed_documents`。
- 异步入口 `create_embedding_provider(provider, model, fallback)`；声明返回 `EmbeddingProvider`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import logging`；`import os`；`from abc import ABC, abstractmethod`；`from typing import List, Optional`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/embeddings.py#L1-L175)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/memory/forbidden.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=74fa3bef932a637d1852ca407612b30a0a60874c5dc43afd56b9005b01688317 -->
**`jiuwenswarm/agents/harness/common/memory/forbidden.py`**

- 调用入口 `contains_forbidden_memory_content(text)`；声明返回 `bool`。
- 调用入口 `get_forbidden_memory_prompt(language)`；声明返回 `str`。
- 调用入口 `get_disabled_memory_filter_prompt(language)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import re`；`from typing import Any, Dict, Iterable`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/forbidden.py#L1-L221)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/memory/internal.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d7cabed55764e3ffb6651734aff02de54dcce4eec08cc0c5905beeba7c1e4697 -->
**`jiuwenswarm/agents/harness/common/memory/internal.py`**

- 源码对模块职责的说明：Internal utilities for memory system.。
- 调用入口 `estimate_tokens(text)`；声明返回 `int`。
- 调用入口 `ensure_dir(path)`；声明返回 `None`。
- 调用入口 `list_memory_files(workspace_dir, extra_paths)`；声明返回 `List[str]`。
- 异步入口 `build_file_entry(abs_path, workspace_dir)`；声明返回 `Dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import os`；`import re`；`import hashlib`；`import math`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/internal.py#L1-L215)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/memory/types.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1fcef17f4f55fce01e210b3e14613fc97b0077a7500a2975b5ba8dc86434075c -->
**`jiuwenswarm/agents/harness/common/memory/types.py`**

- 源码对模块职责的说明：Memory system type definitions.。
- `MemorySearchResult` 定义类型边界。
- `MemoryProviderStatus` 定义类型边界。
- `MemorySyncProgressUpdate` 定义类型边界。
- `FileEntry` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from typing import Optional, Literal`；`from dataclasses import dataclass`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/types.py#L1-L79)。
<!-- /kb:file -->
