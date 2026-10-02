---
title: "JiuwenMemory 进程内 SDK 接入：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/external_memory_builder.py:L30-L85, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/external_memory_config.py:L53-L73, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/config.py:L57-L76, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/external_memory_builder.py:L299-L331, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/external_memory_builder.py:L391-L402, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/external_memory_config.py:L31-L40, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/external_memory_builder.py:L431-L461, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/external_memory_builder.py:L299-L388, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/config.py:L79-L91, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/memory/test_external_memory_config.py:L117-L141, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/memory/test_external_memory_builder.py:L106-L133, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/JiuwenMemory-SDK接入.md:L494-L503", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/external_memory_builder.py:L47-L66, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/JiuwenMemory-SDK接入.md:L488-L512", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/external_memory_builder.py:L197-L208, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/JiuwenMemory-SDK接入.md:L469-L480"]
feature: "jiuwen-memory-sdk"
entry_points: ["jiuwenswarm/agents/harness/common/memory/external_memory_builder.py", "jiuwenswarm/agents/harness/common/memory/external_memory_config.py"]
source_globs: ["jiuwenswarm/agents/harness/common/memory/external_memory_builder.py", "jiuwenswarm/agents/harness/common/memory/external_memory_config.py"]
---

# JiuwenMemory 进程内 SDK 接入：实现深读

[功能概览](feature-jiuwen-memory-sdk.md) · [owner 入口](_index.md)

<!-- kb:depth feature=jiuwen-memory-sdk facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=056abfaed42decf70f59bc1175d2e5a530df6e3f3a4045742d61fc4b6a4a553a -->
**rail 装配入口的配置读取链**
build_external_memory_rail 以可选 config 字典为输入：先尝试从 openjiuwen.harness.rails 导入 ExternalMemoryRail（失败即返回 None），再调用 get_external_memory_config 取得 memory.external 段；该函数在未显式传入 config 时调用 _load_config 从 YAML（经环境变量解析并缓存）读取。产出为填好默认值的配置字典，供后续按 provider 字段分派构造 provider 与 rail。

调用路径：`jiuwenswarm/agents/harness/common/memory/external_memory_builder.py`（`build_external_memory_rail`） → `jiuwenswarm/agents/harness/common/memory/external_memory_config.py`（`get_external_memory_config`） → `jiuwenswarm/agents/harness/common/memory/config.py`（`_load_config`）

来源：[jiuwenswarm/agents/harness/common/memory/external_memory_builder.py:L30–L85](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/external_memory_builder.py#L30-L85), [jiuwenswarm/agents/harness/common/memory/external_memory_config.py:L53–L73](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/external_memory_config.py#L53-L73), [jiuwenswarm/agents/harness/common/memory/config.py:L57–L76](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/config.py#L57-L76)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/memory/external_memory_builder.py","start":30,"end":85,"sha256":"198160c3c75b2be5d72862f96fc92f51c202c05f015ec2e62799b84b7a8dbda2"},{"path":"jiuwenswarm/agents/harness/common/memory/external_memory_config.py","start":53,"end":73,"sha256":"c71910f90765319e343d02f6e569405cfc0ac3768a873ecaafae4aed1373f0ba"},{"path":"jiuwenswarm/agents/harness/common/memory/config.py","start":57,"end":76,"sha256":"427734b0be705fcaf116017c9ae86a1d904542bfead1d30f99739205de5abef0"}],"trace":[{"path":"jiuwenswarm/agents/harness/common/memory/external_memory_builder.py","symbol":"build_external_memory_rail","start":30,"end":85},{"path":"jiuwenswarm/agents/harness/common/memory/external_memory_config.py","symbol":"get_external_memory_config","start":53,"end":73},{"path":"jiuwenswarm/agents/harness/common/memory/config.py","symbol":"_load_config","start":57,"end":76}]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=jiuwen-memory-sdk facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c6e9cd2362c15e00a47f4604216f65ca98dc97569ce69b2a850cec6544b53ae4 -->
**SDK 后端与引擎的代码默认值**
_build_jiuwen_sdk_config_dict 中 sdk 字段缺省为 kv_type=sqlite、vector_type=milvus、db_type=elasticsearch、embedder_dim=1024；_kv_spec 在 kv_type=sqlite 且 kv_url 含 "://"（如遗留 redis:// 值）时回落为文件 agent_memory.db。get_memory_engine 对 memory.engine 的缺省与非法值一律返回 builtin，因此外接记忆需显式 engine 为 external 或 both。

来源：[jiuwenswarm/agents/harness/common/memory/external_memory_builder.py:L299–L331](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/external_memory_builder.py#L299-L331), [jiuwenswarm/agents/harness/common/memory/external_memory_builder.py:L391–L402](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/external_memory_builder.py#L391-L402), [jiuwenswarm/agents/harness/common/memory/external_memory_config.py:L31–L40](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/external_memory_config.py#L31-L40)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/memory/external_memory_builder.py","start":299,"end":331,"sha256":"1b9ea7f8ed296d0c871376d7cf3d2b7e3f547445f1bc7d026642e34eedfe9082"},{"path":"jiuwenswarm/agents/harness/common/memory/external_memory_builder.py","start":391,"end":402,"sha256":"4c40b02c7b427cd3a1c522f123534ca4ad9484678639fbf0184c8682c7816967"},{"path":"jiuwenswarm/agents/harness/common/memory/external_memory_config.py","start":31,"end":40,"sha256":"aa3b71acd085003d8f1807762cfd8fddcea59dafd96e13e860a2832664cf6042"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=jiuwen-memory-sdk facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a5d4d882536139da8aa14fe7383c63954183be18910f8bb6d3d1b9ff6f36ba32 -->
**复用 jiuwenswarm 顶层 LLM/embed 配置**
_jiuwenswarm_llm_creds 从 full_config（缺省 _load_config()）的 models.defaults 列表取 is_default 条目；无 is_default 条目时回落取第一条，defaults 为 dict 时直接使用。凭据 api_key/model_name/api_base 齐全才写入 globals 并设置 llm target（dashscope 或 openai，按 api_base+client_provider 是否含 "dashscope" 推断）。embed 凭据来自 get_embed_config()，其 base_url 会去掉尾部 /embeddings 以适配 openai_embedder。

来源：[jiuwenswarm/agents/harness/common/memory/external_memory_builder.py:L431–L461](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/external_memory_builder.py#L431-L461), [jiuwenswarm/agents/harness/common/memory/external_memory_builder.py:L299–L388](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/external_memory_builder.py#L299-L388), [jiuwenswarm/agents/harness/common/memory/config.py:L79–L91](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/config.py#L79-L91)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/memory/external_memory_builder.py","start":431,"end":461,"sha256":"a662191ba5637ea2539ca46fca10bd97a34ee87762d50e3e4b738feb13101e77"},{"path":"jiuwenswarm/agents/harness/common/memory/external_memory_builder.py","start":299,"end":388,"sha256":"21f40c48a6296b0c4212c371d2ac37c7b5ab4ee8211edbcd5ba41f9ae3120233"},{"path":"jiuwenswarm/agents/harness/common/memory/config.py","start":79,"end":91,"sha256":"c845e27a4cfe33c77c0ec72ded3c697d167db2264a14740270acef3804256967"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=jiuwen-memory-sdk facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=96079af4dbb518a36131b5203a1fa5bfc3bac92d2b3194589be6b5c646ee8b55 -->
**现有单测入口**
tests/unit_tests/agentserver/memory/test_external_memory_config.py 的 test_engine_gates_truth_table（L123-126）断言 is_external_memory_allowed 在 builtin/external/both/none 下的真假表；test_external_config_defaults_when_missing（L133-141）断言 memory.external 缺省时 provider 为空串、user_id/scope_id 为 __default__。test_external_memory_builder.py 通过 _install_agent_core_stubs（L106-133）向 sys.modules 注入 _FakeRail/_FakeProvider 桩以便导入被测模块。此处仅记录断言内容，不声称测试当前已运行通过。

来源：[tests/unit_tests/agentserver/memory/test_external_memory_config.py:L117–L141](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/memory/test_external_memory_config.py#L117-L141), [tests/unit_tests/agentserver/memory/test_external_memory_builder.py:L106–L133](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/memory/test_external_memory_builder.py#L106-L133)

<!-- kb:depth-proof {"evidence":[{"path":"tests/unit_tests/agentserver/memory/test_external_memory_config.py","start":117,"end":141,"sha256":"ed917b33812f24808c6bf6a79ff6c134618c58041fe9a3e206d63788a402881a"},{"path":"tests/unit_tests/agentserver/memory/test_external_memory_builder.py","start":106,"end":133,"sha256":"362f1e409c6bd08123245d62d0e66d9cb23d46fb2d8f90828984f5cc9ee41b83"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=jiuwen-memory-sdk facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=110b3fd4d824556fb2d95da25afe6c85514f58f856cd85b631d18380b70693f7 -->
**SDK 后端 search/add：同步 recall/write 须经 asyncio.to_thread 调用**
search(query, top_k) 以 Scope(org=tenant_id, user=user_id)+Context(scope) 经 asyncio.to_thread 调 api.recall(..., top_k=k, disclosure=L2)——recall 同步且内部 asyncio.run()，故须丢到工作线程；add(content, infer, tags) 仅 infer 时附 metadata={"infer": "true"}，以 Modality.TEXT 经 asyncio.to_thread 调 api.write。

来源：[docs/zh/JiuwenMemory-SDK接入.md:L494–L503](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/JiuwenMemory-SDK%E6%8E%A5%E5%85%A5.md#L494-L503)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":503,"path":"docs/zh/JiuwenMemory-SDK接入.md","sha256":"2a2e05a1b518a58e790b58dc58b4edb14bff0df571cc4a1ddeaa3bda1e0e3263","start":494}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=jiuwen-memory-sdk facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fcd9161990b601c4758d28429df504de7d00f55c2a7b1dd145cb378d30bc7c58 -->
**jiuwenmemory provider 构建异常被 except Exception 兜住，函数局部返回 None**
触发：jiuwenmemory 分支 _build_jiuwen_provider 抛异常（文档：SDK assemble 失败抛 RuntimeError，agent-memory 未安装亦然）；守卫：except Exception 记 warning；恢复：return None，异常不外抛，记忆轨缺席、对话照常进行。

来源：[jiuwenswarm/agents/harness/common/memory/external_memory_builder.py:L47–L66](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/external_memory_builder.py#L47-L66), [docs/zh/JiuwenMemory-SDK接入.md:L488–L512](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/JiuwenMemory-SDK%E6%8E%A5%E5%85%A5.md#L488-L512)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":66,"path":"jiuwenswarm/agents/harness/common/memory/external_memory_builder.py","sha256":"d5e8a888b9730fdbd1a2a7ab629e716088b2fd4eee3bf3abc37090353adf54c5","start":47},{"end":512,"path":"docs/zh/JiuwenMemory-SDK接入.md","sha256":"1bae8fbd745035837fcfe01035e42e4bc055d890fccf6fcce44c9900e15bec8c","start":488}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=jiuwen-memory-sdk facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e82c0a6ea8c22c43999ece5e9341f1348ca395932ccc3ef8fd167e6cc14642e6 -->
**mode=="sdk" 进程内直调内核免 HTTP 跳数，代价是须已安装 agent-memory**
`_build_jiuwen_provider` 文档串写明：模式由 `memory.external.jiuwen.mode` 选择、默认 `server`；`mode=="sdk"` 经 `from api import assemble` 在进程内构建并直调 agent-memory 内核，无 HTTP 跳数（收益），代价是必须已安装 `agent-memory`（`pip install JiuwenMemory`）。

来源：[jiuwenswarm/agents/harness/common/memory/external_memory_builder.py:L197–L208](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/external_memory_builder.py#L197-L208), [docs/zh/JiuwenMemory-SDK接入.md:L469–L480](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/JiuwenMemory-SDK%E6%8E%A5%E5%85%A5.md#L469-L480)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":208,"path":"jiuwenswarm/agents/harness/common/memory/external_memory_builder.py","sha256":"20ce1baed2ab59458de28e24b1a20a03bbddcbd42994010c9131eb784654efc7","start":197},{"end":480,"path":"docs/zh/JiuwenMemory-SDK接入.md","sha256":"afeababacd4d72890dfb51184293f1513f8ab71d3ac47742c2e55ecbf5a3a153","start":469}],"trace":[]} -->
<!-- /kb:depth -->
