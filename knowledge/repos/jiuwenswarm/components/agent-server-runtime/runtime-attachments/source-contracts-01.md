---
title: "runtime-attachments 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# runtime-attachments 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/server/runtime/attachments/document_attachments.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a205780744d56234994a4473a0987597e64cf0027f01a039640ddfefe485c628 -->
**`jiuwenswarm/server/runtime/attachments/document_attachments.py`**

- 源码对模块职责的说明：Helpers for normalizing browser document attachments.。
- 调用入口 `forbidden_formats()`；声明返回 `list[str]`。
- 调用入口 `is_forbidden_document(filename, suffix)`；声明返回 `bool`。
- 调用入口 `is_supported_document(filename)`；声明返回 `bool`。
- 调用入口 `persist_and_parse_documents(params, session_id)`；声明返回 `dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import base64`；`import binascii`；`import logging`。
- 模块级配置或常量名称：`FORBIDDEN_DOCUMENT_EXTENSIONS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/attachments/document_attachments.py#L1-L387)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/attachments/media_attachments.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0b199f28032a0a7ae9425c5afbda17709ae6402148ec2824c9844bc9ea115914 -->
**`jiuwenswarm/server/runtime/attachments/media_attachments.py`**

- 源码对模块职责的说明：Helpers for normalizing browser-uploaded media attachments.。
- 调用入口 `image_suffix_for_mime(mime_type)`；声明返回 `str / None`。
- 调用入口 `supported_image_suffixes()`；声明返回 `frozenset[str]`。
- 调用入口 `ensure_image_upload_filename(filename, canonical_suffix)`；声明返回 `str`。
- 调用入口 `discard_session_upload(session_id, raw_path)`；声明返回 `dict[str, bool]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import base64`；`import binascii`；`import os`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/attachments/media_attachments.py#L1-L200)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/attachments/upload_storage.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b22b4f2676fc63283f3a4282807c08877702da99e8dbeffb5467f2c7a5c91b99 -->
**`jiuwenswarm/server/runtime/attachments/upload_storage.py`**

- 源码对模块职责的说明：Shared naming rules for browser-uploaded attachments.。
- 调用入口 `safe_upload_filename(filename, fallback)`；声明返回 `str`。
- 调用入口 `safe_session_dirname(session_id)`；声明返回 `str`。
- 调用入口 `unique_upload_path(path)`；声明返回 `Path`。
- 调用入口 `atomic_write_unique(target, data)`；声明返回 `Path`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import os`；`import re`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/attachments/upload_storage.py#L1-L154)。
<!-- /kb:file -->
