---
title: "skill-gen-4-enterprise-doc-scripts 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# skill-gen-4-enterprise-doc-scripts 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c1a5eca50f634045ea6918b6fbb18bd370ccc1df1d43419d4c53b1ad3c7226cd -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/__init__.py`**

- 源码对模块职责的说明：SOP and URL ingest helpers for skill-gen-4-enterprise-doc.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from .models import SOPStep, SOPStepDict, SOPStructure`；`from .sop_fallback import build_fallback_sop_structure, build_intent_fallba`；`from .sop_parser import DEFAULT_SINGLE_SHOT_BUDGET, parse_sop_file, parse_s`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/__init__.py#L1-L21)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/models.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5e404d1e25e265c1a807aabf8a1a5617535c5a6b9b8622eaa6083bc4d1f71040 -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/models.py`**

- 源码对模块职责的说明：Data models for SOP structure (skill-gen extraction).。
- `SOPStepDict` 继承 `TypedDict`。
- `SOPStep` 定义类型边界；方法入口：`to_dict`, `from_dict`。
- `SOPStructure` 定义类型边界；方法入口：`to_dict`, `from_dict`, `step_summary`, `knowledge_summary`, `full_summary`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass, field`；`from typing import Any, TypedDict`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/models.py#L1-L166)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_chunk_merge.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d5a7b46e42d69a3b93b639d17d72927eddcb10d7dd54c90b60ea0e40bccc8e3e -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_chunk_merge.py`**

- 源码对模块职责的说明：Long SOP: budget-aware chunking, map-reduce merge, optional reconcile.。
- 调用入口 `split_semantic_chunks(text, max_chunk_chars, overlap_chars)`；声明返回 `list[dict[str, Any]]`。
- 调用入口 `merge_partial_dicts(partials)`；声明返回 `dict[str, Any]`。
- 异步入口 `extract_structure_chunked(raw_text, invoke_llm_json, max_context_chars, safety_margin, max_chunk_chars, chunk_overlap, run_reconcile)`；声明返回 `tuple[SOPStructure, dict[str, Any]]`。
- 异步入口 `extract_structure_single_shot(raw_text_for_prompt, invoke_llm_json, full_prompt_template, single_shot_budget, prompt_truncated)`；声明返回 `tuple[SOPStructure, dict[str, Any]]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import logging`；`import re`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_chunk_merge.py#L1-L586)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_fallback.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=564942f89ad2e651161e8e0e06fda9c85818cd53767a264118f39446eeabe33d -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_fallback.py`**

- 源码对模块职责的说明：Intent-only fallback when no SOP plain text is available.。
- 调用入口 `build_fallback_sop_structure(user_intent, skill_name_hint)`；声明返回 `tuple[SOPStructure, dict[str, Any]]`。
- 异步入口 `enrich_fallback_sop_with_llm(sop, user_intent, invoke_llm_json, trace_tag)`；声明返回 `tuple[SOPStructure, dict[str, Any]]`。
- 异步入口 `build_intent_fallback_sop(user_intent, skill_name_hint, invoke_llm_json)`；声明返回 `tuple[SOPStructure, dict[str, Any]]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import logging`；`import re`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_fallback.py#L1-L477)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b1e6249f4b442668e932fcd9d1bb787e221d147081749bf4f7ea19826e93963c -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py`**

- 源码对模块职责的说明：SOP document ingestion and structured extraction.。
- 异步入口 `parse_sop_raw_text(raw_text, invoke_llm_json, parse_options, source_label)`；声明返回 `tuple[SOPStructure, dict[str, Any]]`。
- 异步入口 `parse_sop_file(file_path, invoke_llm_json, parse_options)`；声明返回 `tuple[SOPStructure, dict[str, Any]]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from pathlib import Path`；`from typing import Any, Callable`。
- 模块级配置或常量名称：`DEFAULT_SINGLE_SHOT_BUDGET`, `DEFAULT_MAX_CHUNK_CHARS`, `DEFAULT_CHUNK_OVERLAP`, `DEFAULT_MAX_CONTEXT_CHARS`, `DEFAULT_SAFETY_MARGIN`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py#L1-L455)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=583b5ddbc9756ddbac8623a098f40e603eee80c42aa23b3a350b1a19ea163063 -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/__init__.py`**

- 源码对模块职责的说明：HTTP(S) and WeChat URL fetch helpers for SOP / skill draft input (httpx + bs4).。
- 调用入口 `fetch_url_as_plaintext(pages, join_sep)`；声明返回 `str`。
- 异步入口 `validate_fetch_and_flatten(url, timeout, user_agent, verify, client)`；声明返回 `tuple[str, List[FetchedPage]]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import ssl`；`from typing import List`；`import httpx`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/__init__.py#L1-L63)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/models.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ad9cd83b5f667185eceaea19de075120702e12313b933f24cccdfc919a4c47dd -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/models.py`**

- 源码对模块职责的说明：Datatypes produced by URL ingest (''FetchedPage'').。
- `FetchedPage` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass, field`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/models.py#L1-L20)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/router.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6f8809cfc3d716b6a4816bc8ecc9be925c470a42c612a424753f6180180e2e8a -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/router.py`**

- 源码对模块职责的说明：Dispatch one URL to the WeChat or generic web fetcher.。
- 异步入口 `fetch_pages_from_url(url, timeout, user_agent, verify, client)`；声明返回 `List[FetchedPage]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import ssl`；`import uuid`；`from typing import List`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/router.py#L1-L41)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/url_safety.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b333d5de077eaf950b5e065683c66e339806d56fdfb741835d6b6477175c829b -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/url_safety.py`**

- 源码对模块职责的说明：Reject disallowed URLs before HTTP fetch (''ValueError'' on failure).。
- 调用入口 `check_url_allowed_for_fetch(url)`；声明返回 `None`。
- 调用入口 `is_likely_public_http_url(url)`；声明返回 `bool`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import os`；`import re`；`import socket`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/url_safety.py#L1-L59)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/web_page.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1304f78a756e635cc6e3f1ca4f05defa250c9f4e8a15578d659da5688e6090a7 -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/web_page.py`**

- 源码对模块职责的说明：Fetch and parse generic HTTP(S) page URLs into ''FetchedPage''.。
- 异步入口 `fetch_web_page(url, doc_id, timeout, user_agent, verify, client)`；声明返回 `List[FetchedPage]`。
- 调用入口 `supports_generic_web_url(url)`；声明返回 `bool`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import re`；`import ssl`。
- 模块级配置或常量名称：`HTTP_URL_PATTERN`, `DEFAULT_USER_AGENT`, `DEFAULT_TIMEOUT`, `MAIN_CONTENT_SELECTORS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/web_page.py#L1-L157)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/wechat_article.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=abcdcc658de0ae609ee3d99724f57c4de42307a5c4f027722e8832190cc2a41a -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/wechat_article.py`**

- 源码对模块职责的说明：Fetch and parse WeChat official-account article URLs into ''FetchedPage''.。
- 调用入口 `is_wechat_article_url(url)`；声明返回 `bool`。
- 异步入口 `fetch_wechat_article(url, doc_id, timeout, user_agent, verify, client)`；声明返回 `List[FetchedPage]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import re`；`import ssl`。
- 模块级配置或常量名称：`WECHAT_MP_URL_PATTERN`, `DEFAULT_USER_AGENT`, `DEFAULT_TIMEOUT`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/wechat_article.py#L1-L127)。
<!-- /kb:file -->
