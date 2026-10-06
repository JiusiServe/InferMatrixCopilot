---
title: "LLM Wiki 知识库（wiki_ingest/query/lint 子代理）"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L195-L233, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L242-L258, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L318-L347, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L368-L415, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L470-L485, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agents/test_wiki_tools_runtime_config.py:L30-L74, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agents/test_wiki_tools_runtime_config.py:L77-L94, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agents/test_wiki_tools_runtime_config.py:L97-L125]
feature: "llm-wiki-knowledge-base"
entry_points: ["jiuwenswarm/agents/harness/common/tools/wiki_tools.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/wiki_tools.py"]
---

# LLM Wiki 知识库（wiki_ingest/query/lint 子代理）

<!-- kb:knowledge owner=feature-llm-wiki-knowledge-base facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**LLMWiki 包装 DeepAgent 的分层结构**

LLMWiki 是核心类：构造时把 workspace 划分为 sources/、wiki/、schema/ 三个目录（L195-201），并通过 create_deep_agent 创建一个内部 DeepAgent（L216-233）；ingest/query/lint 都是把自然语言指令拼成 query 后调用 self.agent.invoke，共享同一个 Session（L340、L354、L365）。ensure_initialized 幂等地创建目录并写入 schema/AGENT.md、wiki/index.md、wiki/log.md 的初始内容（L242-308）。ingest 按 SHA-256 去重（force=False 且已记录则跳过），仅当结果不含 "error" 且 output 不以 "[ERROR" 开头时才把哈希写入 manifest——即代码只保证显式失败时不新增记录，不保证失败后可重试（L318-346）。

Sources / 来源：[jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L195–L233](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/wiki_tools.py#L195-L233), [jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L242–L258](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/wiki_tools.py#L242-L258), [jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L318–L347](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/wiki_tools.py#L318-L347)

<!-- kb:knowledge owner=feature-llm-wiki-knowledge-base facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**workspace 解析与模型来源**

workspace 由 _resolve_workspace 规范化：空串或等于 DEFAULT_WIKI_DIR 时映射到 base_dir/DEFAULT_WIKI_DIR；相对路径挂在 get_agent_workspace_dir() 之下；若路径末段不是 DEFAULT_WIKI_DIR 则追加该目录名（L398-415）。三个工具入口的模型固定来自 _get_default_model()（L478、L537、L570），该函数从默认模型配置取值并补齐 api_key/api_base/client_provider/model_name 等缺省以防 ValidationError（L368-395）；而 LLMWiki 类本身接受调用方传入的 model 并直接使用（L176、L217）。

Sources / 来源：[jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L368–L415](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/wiki_tools.py#L368-L415), [jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L470–L485](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/wiki_tools.py#L470-L485)

<!-- kb:knowledge owner=feature-llm-wiki-knowledge-base facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**现有单测覆盖 _create_llm_wiki 与会话 lineage**

tests/unit_tests/agents/test_wiki_tools_runtime_config.py 有三个用例：test_create_llm_wiki_propagates_runtime_policy_and_parent_lineage 通过 monkeypatch 假配置与会话，断言 enable_read_image_multimodal=False 被透传、session_id 形如 "{owner}:subagent:wiki:{workspace_scope}" 且 parent_session_id 指向父会话，并断言亲和配置的 enable_kv_cache_affinity 为 True（L30-74）；test_llm_wiki_session_exposes_provider_cache_lineage 构造真实 LLMWiki（stub 掉 create_deep_agent）后调用 resolve_session_lineage 验证内部 Session 的 lineage 解析结果（L77-94）；第三个用例验证 OpenAI affinity 模型同样得到启用亲和的 kv_cache_affinity_config（L97-125）。这些测试断言的是配置构造与 lineage，不涉及 ingest/query/lint 的运行时行为。

Sources / 来源：[tests/unit_tests/agents/test_wiki_tools_runtime_config.py:L30–L74](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agents/test_wiki_tools_runtime_config.py#L30-L74), [tests/unit_tests/agents/test_wiki_tools_runtime_config.py:L77–L94](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agents/test_wiki_tools_runtime_config.py#L77-L94), [tests/unit_tests/agents/test_wiki_tools_runtime_config.py:L97–L125](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agents/test_wiki_tools_runtime_config.py#L97-L125)

