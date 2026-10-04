---
title: "web-frontend 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# web-frontend 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/app_web.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f4f517082ca5d5c93d477892255b427ad5523921507c4359b3250d20fbce9358 -->
**`jiuwenswarm/channels/web/app_web.py`**

- 源码对模块职责的说明：Serve built frontend static files with optional reverse proxy.。
- 调用入口 `main()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import errno`；`import hmac`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/app_web.py#L1-L2386)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/directory_picker.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bd81940f9dc16788afffe973d3972b6d3b8a0389b880f3282fd1f8a77dc55e8b -->
**`jiuwenswarm/channels/web/directory_picker.py`**

- 源码对模块职责的说明：浏览器 / Web 通道使用的本机目录选择器（非 pywebview）。。
- 调用入口 `select_directory_native(initial_dir)`；声明返回 `str / None`。
- 调用入口 `select_file_native(initial_dir, title)`；声明返回 `str / None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import os`；`import shutil`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/directory_picker.py#L1-L520)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/file_picker.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=df19dca71a2da8b7153d36529730a4f623d5437638b14c5ee28fafe60cee0a25 -->
**`jiuwenswarm/channels/web/file_picker.py`**

- 源码对模块职责的说明：浏览器 / Web 通道使用的本机文件选择器（非 pywebview）。。
- 调用入口 `get_last_file_picker_dir()`；声明返回 `str / None`。
- 调用入口 `remember_file_picker_dir(path)`；声明返回 `None`。
- 调用入口 `resolve_file_picker_initial_dir(initial_dir)`；声明返回 `str`。
- 调用入口 `attachment_mime_type(filename)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import base64`；`import logging`；`import mimetypes`。
- 模块级配置或常量名称：`IMAGE_EXTENSIONS`, `MAX_IMAGE_BYTES`, `FORBIDDEN_DOCUMENT_EXTENSIONS`, `ATTACHMENT_DIALOG_EXTENSIONS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/file_picker.py#L1-L667)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/index.html pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=997594e044366df45da755e5838cc7539df6ddef26ae6eaf745b2206da19452b -->
**`jiuwenswarm/channels/web/frontend/index.html`**

- 源码声明的类型、组件或调用边界：`len`, `i`, `escaped`；这是词法声明索引，不把局部变量当成对外导出 API。
- 页面装配边界：body, link, script 标签；资源装载与宿主连接取决于对应属性和脚本实现。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/index.html#L1-L61)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/featureFlags.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ef19f4bf5adde06d59bc44686f5904582591dd37758526fd37447f681245d841 -->
**`jiuwenswarm/channels/web/frontend/src/featureFlags.ts`**

- 源码声明的类型、组件或调用边界：`FEATURE_APP_UPDATER_UI`, `FEATURE_PERSONAL_CONTEXT_UI`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/featureFlags.ts#L1-L11)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/main.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fc4973ebae883abda81832627a35a17e1b55fa8a98a778405f3d3f6f72a14224 -->
**`jiuwenswarm/channels/web/frontend/src/main.tsx`**

- 源码声明的类型、组件或调用边界：`flagA2UIIconFontAvailability`, `fonts`, `hasMaterialSymbols`, `handleA2UIAction`, `resolveOpenSourceSettingsRequest`, `runnerJobId`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import './i18n';`；`import ReactDOM from 'react-dom/client';`；`import { A2UIProvider } from '@a2ui/react';`；`import type { A2UIClientEventMessage } from '@a2ui/react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/main.tsx#L1-L63)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/tailwind.config.js pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b643f6daeb62eb2551cb1f461e4c92a1dca2bb5251b9557ff7784a14311fe9f1 -->
**`jiuwenswarm/channels/web/frontend/tailwind.config.js`**

- 源码声明的类型、组件或调用边界：`color`, `translucentColor`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import typography from '@tailwindcss/typography';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/tailwind.config.js#L1-L204)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/vite.config.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d2bd61b48905f733521e4a87c781849f00fda7cd38223d04761e8ada0e197c85 -->
**`jiuwenswarm/channels/web/frontend/vite.config.ts`**

- 源码声明的类型、组件或调用边界：`ChildProcess`, `ConfigWithLogger`, `ErrorWithCode`, `SECRET_TOKENS`, `NON_SENSITIVE_KEY_OVERRIDES`, `looksSecretKey`, `tokens`, `setIntersect`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { Plugin } from 'vite'`；`import { defineConfig, searchForWorkspaceRoot } from 'vite'`；`import react from '@vitejs/plugin-react'`；`import svgr from 'vite-plugin-svgr'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/vite.config.ts#L1-L1492)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/hub_oauth.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1c2c8809a4fc6a2a12413c157080d1457f4742e9ee6103c0aedee87b8e829877 -->
**`jiuwenswarm/channels/web/hub_oauth.py`**

- 源码对模块职责的说明：Local handoff for SkillHub-hosted OAuth; no provider secret is stored here.。
- 调用入口 `start(provider, host)`；声明返回 `tuple[int, dict]`。
- 调用入口 `complete(query)`；声明返回 `tuple[int, dict]`。
- 调用入口 `result(flow, claim)`；声明返回 `tuple[int, dict]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import hmac`；`import json`；`import os`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/hub_oauth.py#L1-L130)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/share_image_export.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3d4ba1cdd09b6de0f4690b053d0bee12fde2594c02368802d230c25578084992 -->
**`jiuwenswarm/channels/web/share_image_export.py`**

- 源码对模块职责的说明：Isolated browser renderer and in-process job registry for share-image export.。
- `ShareImageRenderAuth` 定义类型边界。
- 调用入口 `render_share_image(base_url, job_id, output_path, on_phase, render_auth, init_timeout_seconds, idle_timeout_seconds, absolute_timeout_seconds, poll_interval_seconds)`；声明返回 `Path`。
- `ShareImageExportManager` 定义类型边界；方法入口：`__init__`, `create_job`, `get_status`, `get_active_status`, `get_snapshot_path`, `get_result`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import json`；`import logging`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/share_image_export.py#L1-L589)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/vite-env.d.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3ad26cf405e62cc9ab4c08c21ea6675f9a59129c210ce667c4389575fd6dc1fe -->
**`jiuwenswarm/channels/web/frontend/src/vite-env.d.ts`**

- 源码声明的类型、组件或调用边界：`ImportMetaEnv`, `ImportMeta`, `DesktopSaveResult`, `DesktopBlobSaveStartResult`, `Window`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/vite-env.d.ts#L1-L61)。
<!-- /kb:file -->
