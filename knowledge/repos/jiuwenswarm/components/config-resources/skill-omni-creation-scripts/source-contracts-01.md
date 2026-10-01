---
title: "skill-omni-creation-scripts 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# skill-omni-creation-scripts 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f3b9263f55cb28160e82cdc58cff770204f6bb2d132e8070660b1122c750125f -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py`**

- 源码对模块职责的说明：analyze_video.py — 下载视频并进行单阶段粗扫抽帧，供 agent 按顺序分析。
- 调用入口 `probe_duration(video_path)`；声明返回 `float`。
- 调用入口 `choose_fps(duration_seconds)`；声明返回 `float`。
- 调用入口 `extract_frames(video_path, frames_dir, fps)`；声明返回 `list[Path]`。
- 调用入口 `build_review_frames(frames, review_dir)`；声明返回 `list[Path]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import json`；`import logging`；`import subprocess`。
- 模块级配置或常量名称：`BASE_FPS`, `MAX_FRAMES`, `BATCH_SIZE`, `REVIEW_BATCH_STATE`, `REVIEW_PRIMARY_SIZE`, `REVIEW_FALLBACK_SIZE`, `REVIEW_JPEG_QUALITY`, `REVIEW_MIN_QUALITY`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py#L1-L400)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/common.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=27b7ffd124fabaf41772387cf055e974eb4830aef6d6c438e329aca5c403a955 -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/common.py`**

- 调用入口 `load_json(path)`；声明返回 `dict`。
- 调用入口 `write_json(path, data)`；声明返回 `None`。
- 调用入口 `strip_json_fence(text)`；声明返回 `str`。
- 调用入口 `encode_b64(data, mime)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import base64`；`import hashlib`；`import json`；`import logging`。
- 模块级配置或常量名称：`STEALTH_UA`, `SUPPORTED_EXTS`, `SUPPORTED_MIMES`, `MIME_TO_EXT`, `MIN_DIMENSION`, `MAX_IMAGE_BYTES`, `FETCH_WORKERS`, `FILTER_BATCH`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/common.py#L1-L454)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/download_images.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ab83b2fbd2b19459e2784556a24a079587616fe33f4bbba9e18f7777d964df93 -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/download_images.py`**

- 源码对模块职责的说明：download_images.py — Download and deduplicate image blocks from stage01.json.。
- 调用入口 `download_image_blocks(blocks)`；声明返回 `tuple[list[dict], dict[str, tuple[bytes, str]]]`。
- 调用入口 `main()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import hashlib`；`import io`；`import logging`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/download_images.py#L1-L164)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/environment_gate.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=015f48e37054bebbb54bc927d34973f0f86274ab0180687aae798d04e1bbcdf5 -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/environment_gate.py`**

- 源码对模块职责的说明：Cross-platform runtime gate for the web/image pipeline.。
- `EnvironmentGateError` 继承 `RuntimeError`。
- 调用入口 `select_interpreter(project_dir, create_venv)`；声明返回 `Path`。
- 调用入口 `ensure_environment(profile, project_dir, auto_install, create_venv, reexec)`；声明返回 `Path`。
- 调用入口 `main()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import importlib`；`import importlib.util`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/environment_gate.py#L1-L466)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/finalize_scripts.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d1cdc692ee099b3205648925d82b90de029b8e031a4bf1e0822fd11e195bb7f0 -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/finalize_scripts.py`**

- 源码对模块职责的说明：Finalize generated scripts after verification without blocking SKILL.md creation.。
- 调用入口 `main()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import logging`；`import sys`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/finalize_scripts.py#L1-L105)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/image_review.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=12e4594beb9fff2ae9974c7ab967c1ab784fbfec372e90ee8a3bfa67d411f283 -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/image_review.py`**

- 源码对模块职责的说明：Persist final KEEP/SKIP image decisions and print selected paths.。
- 调用入口 `main()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import json`；`import logging`；`import sys`。
- 模块级配置或常量名称：`ALLOWED`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/image_review.py#L1-L95)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/prepare_images.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e80933765bc471a8b677c4b388b2458997b40f5358148c078122e3163bd59218 -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/prepare_images.py`**

- 源码对模块职责的说明：Run the dependent web-image stages sequentially with the current interpreter.。
- 调用入口 `main()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import subprocess`；`import sys`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/prepare_images.py#L1-L33)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/print_blocks.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ecfd31eeb1812ffb1348e83526a916e020d3f8f065dec533b044801f25923d39 -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/print_blocks.py`**

- 源码对模块职责的说明：print_blocks.py — Print stage JSON blocks in a readable format for the agent.。
- 调用入口 `main()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import logging`；`import pathlib`；`import sys`。
- 模块级配置或常量名称：`VIEW_MAX_BLOCKS`, `VIEW_MAX_CHARS`, `VIEW_TEXT_FLOOR`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/print_blocks.py#L1-L224)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/save_images.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=81c261e34a1155cc85615469b6cb5295c6ece67797b1c807e7e2435b6d46f49f -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/save_images.py`**

- 源码对模块职责的说明：save_images.py — Copy agent-selected images to skills/&lt;slug&gt;/references/ and write stage03.json.。
- 调用入口 `main()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import json`；`import logging`；`import shutil`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/save_images.py#L1-L150)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=535d31313abb2e4389cf177c211565f81069a2efceb6328470965ef41d1c8949 -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py`**

- 调用入口 `is_platform_url(url)`；声明返回 `bool`。
- 调用入口 `is_xhs_url(url)`；声明返回 `bool`。
- 调用入口 `fetch_video_title(url, fallback)`；声明返回 `str`。
- 调用入口 `el_text(el)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import asyncio`；`import json`；`import logging`。
- 模块级配置或常量名称：`PLATFORM_PATTERNS`, `XHS_PATTERNS`, `COOKIE_SELECTORS`, `NOISE_IDS`, `NOISE_TABPANEL_LABELS`, `NOISE_CLASSES`, `CUSTOM_EDITOR_CLASSES`, `STRUCTURED_TEXT_LIMITS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/scrape_page.py#L1-L1002)。
<!-- /kb:file -->
