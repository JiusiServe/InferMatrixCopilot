---
title: "LLM Wiki 知识库（wiki_ingest/query/lint 子代理）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L536-L556, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L398-L415, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L42-L43, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L445-L459, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L20-L21, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L539-L558, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L569-L591, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agents/test_wiki_tools_runtime_config.py:L30-L74, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L530-L558]
feature: "llm-wiki-knowledge-base"
entry_points: ["jiuwenswarm/agents/harness/common/tools/wiki_tools.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/wiki_tools.py"]
---

# LLM Wiki 知识库（wiki_ingest/query/lint 子代理）：实现深读

[功能概览](feature-llm-wiki-knowledge-base.md) · [owner 入口](_index.md)

<!-- kb:depth feature=llm-wiki-knowledge-base facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3a6bd55be8861251ac53008da4d4cd3c5c71044d0e08626bba3310b0421affa1 -->
**wiki_query 工具：解析 workspace → 构造 LLMWiki 子代理 → 调用 query 返回 output**
wiki_query 先用 _get_default_model() 取默认模型、_resolve_workspace(workspace) 解析出绝对路径；若该路径不存在则直接返回未初始化错误，否则经 _create_llm_wiki 构造 LLMWiki、ensure_initialized() 后调用 wiki.query(question=query)，结果含 "output" 键时返回其字符串形式。

来源：[jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L536–L556](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/wiki_tools.py#L536-L556)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":556,"path":"jiuwenswarm/agents/harness/common/tools/wiki_tools.py","sha256":"3077620eda571b52818c69e3ec24f9184333dd8cea76db515d3648fcd0c720c4","start":536}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=llm-wiki-knowledge-base facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=48969ff70e9a645e75ccd18c112e850f49b3a205066e52fe761ed5817d28c8de -->
**wiki_query 的输入校验与返回契约（局部返回分支）**
wiki_query(query, workspace="") 在 query 为空白时立即返回 "Error: Query cannot be empty."；workspace 解析后不存在时返回提示先用 wiki_ingest 初始化的错误字符串；否则调用 wiki.query 并按 result 中的 "output"/"error" 键返回字符串，兜底 JSON 序列化；异常被捕获并作为 "Wiki Query Error: ..." 字符串返回。

来源：[jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L530–L558](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/wiki_tools.py#L530-L558)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":558,"path":"jiuwenswarm/agents/harness/common/tools/wiki_tools.py","sha256":"296f20125c1f444220972751d204c9ea5cdeacac62dd641e2f3315c4da782bea","start":530}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=llm-wiki-knowledge-base facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=41d5b39887ab433b9732f4a909e8aab16c149accc3a9f064b3a495659967171f -->
**_resolve_workspace：空或等于 ".llm_wiki" 时回落到基础目录下的默认 wiki 目录**
workspace 字符串先 strip；为空或恰为 DEFAULT_WIKI_DIR（".llm_wiki"）时返回 get_agent_workspace_dir()/.llm_wiki 的 resolve 结果；相对路径拼接到 base_dir，目录名不是 .llm_wiki 时追加该子目录，最终返回绝对路径。

来源：[jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L398–L415](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/wiki_tools.py#L398-L415), [jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L42–L43](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/wiki_tools.py#L42-L43)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":415,"path":"jiuwenswarm/agents/harness/common/tools/wiki_tools.py","sha256":"c1d08705edf02430afe947a26b68fdf8a2479ed5756cb99b8fc35789ecb27101","start":398},{"end":43,"path":"jiuwenswarm/agents/harness/common/tools/wiki_tools.py","sha256":"1ff2456bc20b4680351be1a9d6722c110e5b33905784c54dc64c87ef3583b1d1","start":42}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=llm-wiki-knowledge-base facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0e40916c7e799d1b08b999ff2f943cb318807c01b41d05d8fed9141ce4fec2d4 -->
**_create_llm_wiki 依赖 openjiuwen 会话上下文派生子代理 session 血缘**
_create_llm_wiki 用 resolve_session_lineage(get_current_session()) 取 owner_session_id；存在时按 workspace 绝对路径 sha256 前 12 位拼出 "{owner}:subagent:wiki:{scope}" 作为 session_id 并传入 parent_session_id，再连同 workspace/model/sys_operation 传给 LLMWiki 构造器。

来源：[jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L445–L459](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/wiki_tools.py#L445-L459), [jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L20–L21](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/wiki_tools.py#L20-L21)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":459,"path":"jiuwenswarm/agents/harness/common/tools/wiki_tools.py","sha256":"6c4b5ff64c704064104f0805123ea9cbac018039a970bc1b225a828658661657","start":445},{"end":21,"path":"jiuwenswarm/agents/harness/common/tools/wiki_tools.py","sha256":"2ef36ac0547510b62919ba093344514e323f8d6d33d810bb078e24360fed3b58","start":20}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=llm-wiki-knowledge-base facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=362924f8b2c0523dc4c5f8604bcd2107cf9841f954cac3baddcc53459a5bd21d -->
**wiki_query/wiki_lint 的异常分支：workspace 缺失返回错误字符串，异常被捕获为错误文本**
两个工具在 final_workspace.exists() 为假时返回 "Error: The workspace ... does not have an initialized LLM Wiki."（不抛出）；整体包在 try/except Exception 中，任何异常（含模型构造失败）被转为 "Wiki Query Error: {e}" / "Wiki Lint Error: {e}" 字符串返回给调用方。

来源：[jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L539–L558](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/wiki_tools.py#L539-L558), [jiuwenswarm/agents/harness/common/tools/wiki_tools.py:L569–L591](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/wiki_tools.py#L569-L591)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":558,"path":"jiuwenswarm/agents/harness/common/tools/wiki_tools.py","sha256":"d486e09bc7cdd353961e5ce30aeb4ae7739f3925d22587712f302a738c896031","start":539},{"end":591,"path":"jiuwenswarm/agents/harness/common/tools/wiki_tools.py","sha256":"f5c9a0d4a8b27b46866f74349646df401cf6a3ec78a4ace6a37bcd95cebc4782","start":569}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=llm-wiki-knowledge-base facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a012501e2f11dac9d09d510d5c38e3f1e3f635e772f77d5dc8b6683abf279548 -->
**_create_llm_wiki 的参数传播有 monkeypatch 单测覆盖（helper 级）**
test_create_llm_wiki_propagates_runtime_policy_and_parent_lineage 用 monkeypatch 替换 LLMWiki 捕获 kwargs，断言 enable_read_image_multimodal 为 False、session_id 为 "product-session:subagent:wiki:{workspace哈希前12位}"、parent_session_id 为 "product-session"、kv_cache_affinity_config.enable_kv_cache_affinity 为 True。LLMWiki 本体被 mock，测试只覆盖 _create_llm_wiki 这一 helper，不覆盖 wiki_ingest/query/lint 的运行时集成；未在本批次执行。

来源：[tests/unit_tests/agents/test_wiki_tools_runtime_config.py:L30–L74](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agents/test_wiki_tools_runtime_config.py#L30-L74)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":74,"path":"tests/unit_tests/agents/test_wiki_tools_runtime_config.py","sha256":"300e739f57e2ae8aa0818820082a4a09bce1b02b1eeea3016e9ae179d4ff9930","start":30}],"trace":[],"validation_kind":"helper_unit"} -->
<!-- /kb:depth -->
