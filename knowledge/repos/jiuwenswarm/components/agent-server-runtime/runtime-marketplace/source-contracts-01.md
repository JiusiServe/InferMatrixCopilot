---
title: "runtime-marketplace 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# runtime-marketplace 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/server/runtime/marketplace/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=af26d7fc2f9ffd2f2e605ce001989c13283f50bb9a7a27cd3049e243c1619244 -->
**`jiuwenswarm/server/runtime/marketplace/__init__.py`**

- 源码对模块职责的说明：Shared clients and state for remote Jiuwen marketplaces.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.server.runtime.marketplace.hub_client import HubClient`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/marketplace/__init__.py#L1-L7)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/marketplace/asset_mcp_publish_converter.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=36217696bea640f420ead87881f7b10802e2fd652eca7077d3cf3b01b7cf62e9 -->
**`jiuwenswarm/server/runtime/marketplace/asset_mcp_publish_converter.py`**

- 源码对模块职责的说明：Turn an authorized custom configuration into a portable, credential-free source.。
- `CustomMcpSource` 定义类型边界。
- 调用入口 `convert_mcp_config(config, identity, metadata, output_dir)`；声明返回 `Path`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass`；`import ipaddress`；`import json`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/marketplace/asset_mcp_publish_converter.py#L1-L218)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/marketplace/asset_package_builder.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=98d88a7dc327a078cf959dcd3028a0fbf029aa39183acd9c785071cb109be51f -->
**`jiuwenswarm/server/runtime/marketplace/asset_package_builder.py`**

- 源码对模块职责的说明：Bounded, deterministic publishing snapshots; never mutate installed assets.。
- `PackageBuildError` 继承 `ValueError`；方法入口：`__init__`。
- `PackageLimits` 定义类型边界。
- `PreparedPackage` 定义类型边界。
- 调用入口 `collect_publish_files(root, limits, exclude_paths)`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from dataclasses import dataclass`；`from contextlib import ExitStack, contextmanager`；`import hashlib`；`import os`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/marketplace/asset_package_builder.py#L1-L372)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/marketplace/asset_publish_adapters.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fd46a8c3aa04ca620fe589420f9906c47e54d64d2fe759dfd392ec0b2b5b4e93 -->
**`jiuwenswarm/server/runtime/marketplace/asset_publish_adapters.py`**

- 源码对模块职责的说明：Offline validation and normalization of private publish snapshots.。
- `PublishValidationError` 继承 `ValueError`；方法入口：`__init__`。
- 调用入口 `normalize_and_validate(snapshot, identity, metadata)`；声明返回 `dict[str, object]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import re`；`from pathlib import Path, PureWindowsPath`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/marketplace/asset_publish_adapters.py#L1-L513)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/marketplace/asset_publish_api.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=02ccc431adfff04729f1957a65907c291627cd7d2678c0bc9d2cb8c71779b574 -->
**`jiuwenswarm/server/runtime/marketplace/asset_publish_api.py`**

- 源码对模块职责的说明：Web publishing boundary: server-resolved resources and credential-bound history.。
- `PublishAPIError` 继承 `ValueError`；方法入口：`__init__`。
- 调用入口 `resolve_local_asset(kind, local_id)`。
- `AssetPublishAPI` 定义类型边界；方法入口：`__init__`, `scope`, `start`, `close`, `call`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import hashlib`；`import hmac`；`import json`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/marketplace/asset_publish_api.py#L1-L346)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/marketplace/asset_publish_models.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b8b6f7fa4dbde6281d982084ddb11c32d4f1b229675bbdc0b29d50c3ce20f2d0 -->
**`jiuwenswarm/server/runtime/marketplace/asset_publish_models.py`**

- `PublishProtocolError` 继承 `ValueError`。
- `PublishIdentity` 定义类型边界。
- `PublishResult` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass`；`import re`；`from typing import Literal`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/marketplace/asset_publish_models.py#L1-L58)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/marketplace/asset_publish_service.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ec4847b07f7be8266fe326429f89d20c200180168d7307c3997e3428149156f4 -->
**`jiuwenswarm/server/runtime/marketplace/asset_publish_service.py`**

- 源码对模块职责的说明：Internal orchestration for one workspace's publishing operations.。
- `AssetPublishService` 定义类型边界；方法入口：`__init__`, `start`, `cleanup`, `prepare`, `commit`, `status`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`from collections.abc import Callable`；`from dataclasses import replace`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/marketplace/asset_publish_service.py#L1-L398)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/marketplace/asset_publish_store.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dd183ac3687cf67dffae49d1f0fd2c6909cff68482b0f9f032f9984999a966ed -->
**`jiuwenswarm/server/runtime/marketplace/asset_publish_store.py`**

- 源码对模块职责的说明：Durable publish drafts and single-attempt tasks. Credentials never enter this API.。
- `PublishStoreError` 继承 `RuntimeError`；方法入口：`__init__`。
- `PublishStore` 定义类型边界；方法入口：`__init__`, `save_draft`, `get_draft`, `commit_draft`, `operation_request`, `start`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from contextlib import contextmanager`；`import json`；`import math`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/marketplace/asset_publish_store.py#L1-L526)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/marketplace/hub_asset_installer.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bd47d2b763c64a46ef6b4b722da1045ef95e7b615f07d6769f5cc337f825abe4 -->
**`jiuwenswarm/server/runtime/marketplace/hub_asset_installer.py`**

- 源码对模块职责的说明：Shared acquisition and commit flow for installable Hub asset packages.。
- `HubPackageExtractor` 继承 `Protocol`；方法入口：`download_and_extract`。
- `HubPackageInstallResult` 定义类型边界。
- 异步入口 `install_hub_asset_package(kind, asset_id, destination_root, state_store, package_name_validator, package_validator, conflict_validator, on_committed, on_rollback, hub_port, …)`；声明返回 `HubPackageInstallResult`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import json`；`import shutil`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/marketplace/hub_asset_installer.py#L1-L195)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/marketplace/hub_asset_port.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ffdbfae2fc6af496a0f7151fa76c4d695fb4a17f22359bd8350f793f203b18b8 -->
**`jiuwenswarm/server/runtime/marketplace/hub_asset_port.py`**

- 源码对模块职责的说明：Stable downstream-facing port for remote marketplace assets.。
- `HubSearchRequest` 定义类型边界。
- `HubAssetQuery` 定义类型边界。
- `HubDownloadRequest` 定义类型边界。
- `HubAssetSummary` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass`；`from typing import Literal, Protocol`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/marketplace/hub_asset_port.py#L1-L114)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/marketplace/hub_asset_type_adapter.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c82b8c1798f1634ff1f8a2ce71e39c19fbcd7a7593053ba6b684d8e301b6ccec -->
**`jiuwenswarm/server/runtime/marketplace/hub_asset_type_adapter.py`**

- 源码对模块职责的说明：Mapping between stable Jiuwenswarm kinds and evolving Hub type strings.。
- `HubAssetTypeContract` 定义类型边界；方法入口：`accepts`。
- `HubAssetTypeConflictError` 继承 `ValueError`。
- 调用入口 `resolve_hub_asset_kind(plugin_type, asset_type)`；声明返回 `HubAssetKind / None`。
- 调用入口 `get_hub_asset_type_contract(kind)`；声明返回 `HubAssetTypeContract`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass`；`from jiuwenswarm.server.runtime.marketplace.hub_asset_port import HubAssetK`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/marketplace/hub_asset_type_adapter.py#L1-L89)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/marketplace/hub_avatar_cache.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0d53c571743af19a03ca7c844a54df31ac941e72acdb8205f2eb90352f9076af -->
**`jiuwenswarm/server/runtime/marketplace/hub_avatar_cache.py`**

- 源码对模块职责的说明：Small public Hub thumbnails, never persisted as signed URLs or original files.。
- 调用入口 `thumbnail(body)`；声明返回 `str`。
- `HubAvatarCache` 定义类型边界；方法入口：`__init__`, `get`, `fill`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import base64`；`from collections import OrderedDict`。
- 模块级配置或常量名称：`MAX_INPUT_BYTES`, `MAX_EDGE`, `MAX_THUMBNAIL_BYTES`, `MAX_ENTRIES`, `TTL`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/marketplace/hub_avatar_cache.py#L1-L112)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/marketplace/hub_catalog_cache.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e9fd882ef0a6d29891db0e59a2786c31fcdafe9525f2d56e6bbcd6e2ccd31352 -->
**`jiuwenswarm/server/runtime/marketplace/hub_catalog_cache.py`**

- 源码对模块职责的说明：Bounded, public-card-only Hub catalog cache with nonblocking refresh.。
- 调用入口 `safe_metadata(value, depth)`。
- `CatalogCards` 继承 `list`；方法入口：`__init__`。
- `HubCatalogCache` 定义类型边界；方法入口：`__init__`, `read`, `close`。
- 调用入口 `catalog_memory_scope(base_url, credentials, context)`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import copy`；`import hashlib`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/marketplace/hub_catalog_cache.py#L1-L382)。
<!-- /kb:file -->
