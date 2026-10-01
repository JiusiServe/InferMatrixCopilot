---
title: "runtime-skill 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# runtime-skill 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/server/runtime/skill/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5851908df887df85f9065fe4bb52cbd1549ce440745d0fbcb170304c80c34325 -->
**`jiuwenswarm/server/runtime/skill/__init__.py`**

- 源码对模块职责的说明：Skill 运行时模块 — 对外暴露公共工具函数.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.server.runtime.skill.skilldev import filter_visible_skill_`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/__init__.py#L1-L29)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/skill/archive_store.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d8581113ea5abe2eb734f3663fee06f7700212d2126270119d5b309d832d9dad -->
**`jiuwenswarm/server/runtime/skill/archive_store.py`**

- 源码对模块职责的说明：Skill 本地产品版本仓储（''.archive/versions''）.。
- `SkillArchiveError` 继承 `Exception`；方法入口：`__init__`。
- 调用入口 `empty_versions_index()`；声明返回 `dict[str, Any]`。
- 调用入口 `archive_root(skill_dir)`；声明返回 `Path`。
- 调用入口 `versions_index_path(skill_dir)`；声明返回 `Path`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import logging`；`from pathlib import Path, PurePosixPath`。
- 模块级配置或常量名称：`ARCHIVE_DIRNAME`, `VERSIONS_DIRNAME`, `INDEX_FILENAME`, `CONTENT_DIRNAME`, `SCHEMA_VERSION`, `ERROR_VERSION_NOT_FOUND`, `ERROR_VERSION_CONTENT_INVALID`, `ERROR_INDEX_CORRUPT`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/archive_store.py#L1-L376)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/skill/skill_content_images.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=85282995d9f08e45d7a6c8cf8372030ecb58615e6ebc3b9cd9f3960c1d881a43 -->
**`jiuwenswarm/server/runtime/skill/skill_content_images.py`**

- 源码对模块职责的说明：Skill 正文 Markdown 本地图片改写与受控预览解析.。
- 调用入口 `is_allowed_skill_content_image(path, mime_type)`；声明返回 `bool`。
- 调用入口 `build_skill_content_image_url(token, session_id)`；声明返回 `str`。
- 调用入口 `resolve_skill_content_root(name, version, skills_dir)`；声明返回 `Path`。
- 调用入口 `resolve_skill_content_image_file(name, version, relative_path, skills_dir)`；声明返回 `tuple[Path, str]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import mimetypes`；`import re`。
- 模块级配置或常量名称：`ALLOWED_SKILL_CONTENT_IMAGE_MIMES`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skill_content_images.py#L1-L294)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/skill/skill_files.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8d3960e49abdd5f85800ba1a296220366f9fceea5fa27d59d631f3ab521852bf -->
**`jiuwenswarm/server/runtime/skill/skill_files.py`**

- 源码对模块职责的说明：Skill 工作副本文件预览（skills.files.*）.。
- `SkillFilesError` 继承 `Exception`；方法入口：`__init__`。
- 调用入口 `guess_mime_type(path)`；声明返回 `str`。
- 调用入口 `list_skill_workspace_files(skill_root)`；声明返回 `list[dict[str, Any]]`。
- 调用入口 `resolve_skill_relative_file(skill_root, relative_path)`；声明返回 `tuple[Path, str]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import mimetypes`；`from pathlib import Path, PurePosixPath`；`from typing import Any`。
- 模块级配置或常量名称：`ERROR_UNSAFE_PATH`, `ERROR_NOT_FOUND`, `ERROR_FILE_TOO_LARGE`, `DEFAULT_TEXT_PREVIEW_MAX_BYTES`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skill_files.py#L1-L234)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/skill/skill_type.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f69f186610b11e7ec57471faab1f1ba2b260435697e1db9cba72814331badf12 -->
**`jiuwenswarm/server/runtime/skill/skill_type.py`**

- 源码对模块职责的说明：根据 Skill frontmatter / 资源识别 skill_type.。
- 调用入口 `detect_skill_type(skill_dir)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import re`；`from pathlib import Path`；`import yaml`。
- 模块级配置或常量名称：`SKILL_TYPE_SKILL`, `SKILL_TYPE_SKILLPACK`, `SKILL_TYPE_SWARM`, `SKILL_TYPE_MULTIMODAL`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skill_type.py#L1-L122)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/skill/skilldev/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ab4815196ae89c83d206284c9bf1c47f0e96aff9448e25a9de5877053edff3d5 -->
**`jiuwenswarm/server/runtime/skill/skilldev/__init__.py`**

- 源码对模块职责的说明：SkillDev — Skill 开发模式模块.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.server.runtime.skill.skilldev.state_utils import filter_vi`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skilldev/__init__.py#L1-L46)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/skill/skilldev/context.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=40731bc2d2ffb05bdc6cef85aa3249eb5f7fa002d7081abc968aa942b23b4091 -->
**`jiuwenswarm/server/runtime/skill/skilldev/context.py`**

- 源码对模块职责的说明：SkillDevContext — 每个阶段的执行上下文.。
- `SkillDevContext` 定义类型边界；方法入口：`__init__`, `emit`, `create_stage_agent`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skilldev/context.py#L1-L114)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/skill/skilldev/deps.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=20f0c5ec9f282a82c1f0d0d14e8924fbfec73945fd872a780fbfd132db3c3614 -->
**`jiuwenswarm/server/runtime/skill/skilldev/deps.py`**

- 源码对模块职责的说明：SkillDevDeps — SkillDevService 的最小外部依赖定义.。
- `SkillDevDeps` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass`；`from typing import Callable`；`from jiuwenswarm.server.runtime.skill.skilldev.store import StateStore`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skilldev/deps.py#L1-L37)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/skill/skilldev/pipeline.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=afc899a612fcd4c4cea7fb7d8771050b49f3fa8fc850cebef2c62da54e3201a0 -->
**`jiuwenswarm/server/runtime/skill/skilldev/pipeline.py`**

- 源码对模块职责的说明：SkillDevPipeline — 确定性状态机编排器.。
- `SkillDevPipeline` 定义类型边界；方法入口：`__init__`, `run`, `resume`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`from typing import AsyncIterator`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skilldev/pipeline.py#L1-L194)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/skill/skilldev/schema.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c0ecc2c11acbbc5ee54b6424484bcf83449e6e6b661227d7c213e4540970ceed -->
**`jiuwenswarm/server/runtime/skill/skilldev/schema.py`**

- 源码对模块职责的说明：SkillDev 模块的核心数据模型.。
- `SkillDevStage` 继承 `str, Enum`。
- `SkillDevTaskMode` 继承 `str, Enum`。
- `SkillDevEventType` 继承 `str, Enum`。
- `SkillDevEvent` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import time`；`from dataclasses import dataclass, field`；`from enum import Enum`。
- 模块级配置或常量名称：`SUSPENSION_POINTS`, `ALLOWED_FRONTMATTER_KEYS`, `SKILL_NAME_MAX_LEN`, `SKILL_DESC_MAX_LEN`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skilldev/schema.py#L1-L669)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/skill/skilldev/service.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=72b4f74b0128c9073dd3cf58d9449bb908cb3326353ee1f15a4b618d9bdacd02 -->
**`jiuwenswarm/server/runtime/skill/skilldev/service.py`**

- 源码对模块职责的说明：SkillDevService — 无状态请求处理器.。
- `SkillDevService` 定义类型边界；方法入口：`__init__`, `handle`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import base64`；`import logging`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skilldev/service.py#L1-L360)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/skill/skilldev/stages/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fdbffc1e68cdc6c61d800183e8619c4ea1d365ddb137ec1ac4bf9e36a649e9f0 -->
**`jiuwenswarm/server/runtime/skill/skilldev/stages/__init__.py`**

- 源码对模块职责的说明：SkillDev Pipeline 各阶段处理器.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.server.runtime.skill.skilldev.stages.base import StageHand`；`from jiuwenswarm.server.runtime.skill.skilldev.stages.init_stage import Ini`；`from jiuwenswarm.server.runtime.skill.skilldev.stages.plan_stage import Pla`；`from jiuwenswarm.server.runtime.skill.skilldev.stages.generate_stage import`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skilldev/stages/__init__.py#L1-L34)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/skill/skilldev/stages/base.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7a0538ddf15f3901faa597c76243a999bdfa14c9443219ecf3a32779112b0ea2 -->
**`jiuwenswarm/server/runtime/skill/skilldev/stages/base.py`**

- 源码对模块职责的说明：StageHandler 基类和 StageResult.。
- `StageResult` 定义类型边界。
- `StageHandler` 继承 `ABC`；方法入口：`execute`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from abc import ABC, abstractmethod`；`from dataclasses import dataclass`；`from jiuwenswarm.server.runtime.skill.skilldev.schema import SkillDevStage`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skilldev/stages/base.py#L1-L40)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/skill/skilldev/stages/desc_optimize_stage.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4339e82cbed7670e9f72fb8b0430049e53420731f19abe06699e2afb2e11f76a -->
**`jiuwenswarm/server/runtime/skill/skilldev/stages/desc_optimize_stage.py`**

- 源码对模块职责的说明：DESC_OPTIMIZE 阶段处理器.。
- `DescOptimizeStageHandler` 继承 `StageHandler`；方法入口：`execute`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import logging`；`import random`。
- 模块级配置或常量名称：`MAX_ITERATIONS`, `HOLDOUT_RATIO`, `TRIGGER_QUERY_GEN_PROMPT`, `IMPROVE_DESC_PROMPT`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/skill/skilldev/stages/desc_optimize_stage.py#L1-L394)。
<!-- /kb:file -->
