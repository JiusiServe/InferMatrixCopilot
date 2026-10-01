---
title: "runtime-marketplace 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# runtime-marketplace 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/server/runtime/marketplace/hub_install_state.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=53dec380cc9eb40c5ed0a749b93d7d91aab7733b86cbaaaf0eb0a5edff5bec8f -->
**`jiuwenswarm/server/runtime/marketplace/hub_install_state.py`**

- 源码对模块职责的说明：Persistent provenance for marketplace packages prepared from Hub.。
- `HubInstallRecord` 定义类型边界；方法入口：`from_dict`。
- `HubInstallStateStore` 定义类型边界；方法入口：`__init__`, `get`, `all`, `get_by_package_id`, `upsert`, `remove`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import tempfile`；`from dataclasses import asdict, dataclass`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/marketplace/hub_install_state.py#L1-L125)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/marketplace/hub_models.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=20670fa583d82855394202b4063ae2ade235f1464aa1855058e90e299c5a7c52 -->
**`jiuwenswarm/server/runtime/marketplace/hub_models.py`**

- 源码对模块职责的说明：Normalized Team Skills Hub response models.。
- `HubPayloadError` 继承 `ValueError`。
- `HubCatalogItem` 定义类型边界；方法入口：`from_payload`。
- `HubVersionDetail` 定义类型边界；方法入口：`from_payload`。
- `HubArtifact` 定义类型边界；方法入口：`from_payload`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/marketplace/hub_models.py#L1-L177)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/marketplace/hub_package_downloader.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e577922119088e43ec8afaf51a28446b96ea77d6aa35d34e5efe444b4969f8e6 -->
**`jiuwenswarm/server/runtime/marketplace/hub_package_downloader.py`**

- 源码对模块职责的说明：Verified and bounded artifact download/extraction shared by Hub consumers.。
- `HubDownloadArtifact` 继承 `Protocol`。
- `HubDownloadError` 继承 `RuntimeError`。
- `HubPackageDownloader` 定义类型边界；方法入口：`__init__`, `assert_download_url_allowed`, `validated_members`, `extract_zip`, `download_and_extract`, `download_bytes`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import hashlib`；`import io`；`import os`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/marketplace/hub_package_downloader.py#L1-L222)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/marketplace/hub_publish_client.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7111656d7461182f52cf8f241b652b10ba55235a02fa4ae009141576b9ee087e -->
**`jiuwenswarm/server/runtime/marketplace/hub_publish_client.py`**

- 源码对模块职责的说明：User-scoped, single-attempt streaming uploads to the configured Hub.。
- `PublishAuth` 定义类型边界。
- `PublishRequest` 定义类型边界。
- `PublishUploadError` 继承 `RuntimeError`；方法入口：`__init__`。
- `HubPublishClient` 定义类型边界；方法入口：`__init__`, `publish`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`from dataclasses import dataclass, field`；`import hashlib`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/marketplace/hub_publish_client.py#L1-L351)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/marketplace/hub_publish_port.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=eec1a72a1522c221019eb6d32cf26b40dd14421880619dadddb686dd1de513dd -->
**`jiuwenswarm/server/runtime/marketplace/hub_publish_port.py`**

- 调用入口 `parse_publish_result(data, expected, expected_visibility)`；声明返回 `PublishResult`。
- `HubPublishPort` 继承 `Protocol`；方法入口：`publish`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from collections.abc import Mapping`；`from typing import TYPE_CHECKING, Literal, Protocol, cast`；`from jiuwenswarm.server.runtime.marketplace.hub_asset_type_adapter import g`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/marketplace/hub_publish_port.py#L1-L109)。
<!-- /kb:file -->
