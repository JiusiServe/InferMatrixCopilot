---
title: "MCP Free/Paid Search Tools with Trusted-Search Provenance Lease：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/trusted_search_tool_adapter.py:L36-L71, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/trusted_search_tool_adapter.py:L57-L66, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/permissions/test_trusted_search_tool_adapter.py:L178-L186, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/permissions/test_trusted_search_tool_adapter.py:L135-L151, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/permissions/test_trusted_search_tool_adapter.py:L190-L216, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/permissions/test_trusted_search_tool_adapter.py:L219-L240, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/search_tools.py:L31-L33, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/search_tools.py:L534-L548, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/search_tools.py:L31-L39, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/trusted_search_tool_adapter.py:L36-L48, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/trusted_search_tool_adapter.py:L82-L99, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/trusted_search_tool_adapter.py:L110-L114, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/search_tools.py:L565-L583]
feature: "web-search-tools"
entry_points: ["jiuwenswarm/agents/harness/common/tools/trusted_search_tool_adapter.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/trusted_search_tool_adapter.py", "jiuwenswarm/channels/web/frontend/src/features/settings/modules/agent/AgentSettings.tsx", "jiuwenswarm/channels/web/frontend/src/features/settings/modules/agent/definition.ts", "jiuwenswarm/agents/harness/common/tools/search_tools.py"]
---

# MCP Free/Paid Search Tools with Trusted-Search Provenance Lease：实现深读

[功能概览](feature-web-search-tools.md) · [owner 入口](_index.md)

<!-- kb:depth feature=web-search-tools facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=880197d8f6cd594d58287abfda44d54a59192356a1c17bddae1a1075a6f8d0b4 -->
**mcp_free_search: strip query, clamp params, run provider in a thread, commit URLs, then render**
On invoke, the query is stripped (empty → "[ERROR]: query cannot be empty."), max_results is normalized and timeout clamped to [5,60]; run_free_search_structured runs via asyncio.to_thread, and on non-empty rows complete_trusted_search_producer(success=True, urls=...) commits row URLs before render_free_search_result returns the rendered string; a finally clause calls complete_trusted_search_producer(success=False).

来源：[jiuwenswarm/agents/harness/common/tools/trusted_search_tool_adapter.py:L36–L71](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/trusted_search_tool_adapter.py#L36-L71)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":71,"path":"jiuwenswarm/agents/harness/common/tools/trusted_search_tool_adapter.py","sha256":"ffcfeecb6c840bc81bdf226603293dddb9b06fc1b167ddc812e84850dc97fab4","start":36}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-search-tools facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4987c13e006d3d3a2dce16bc2d07c639fee9e3df21c9104d0f9a9b8aa4cedcd5 -->
**mcp_free_search: string-returning tool with empty-query and provider-failure error strings (only the structured-search call is caught)**
mcp_free_search(query, max_results=8, timeout_seconds=20) strips the query and returns "[ERROR]: query cannot be empty." when blank; only exceptions from the asyncio.to_thread(run_free_search_structured) call are caught and returned as "[ERROR]: free search failed: {exc}". Empty result rows return "No search results for: {query}"; on success it calls complete_trusted_search_producer(success=True, urls=...) before render_free_search_result, and a finally block always calls complete_trusted_search_producer(success=False).

来源：[jiuwenswarm/agents/harness/common/tools/trusted_search_tool_adapter.py:L36–L71](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/trusted_search_tool_adapter.py#L36-L71), [jiuwenswarm/agents/harness/common/tools/search_tools.py:L31–L33](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/search_tools.py#L31-L33)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":71,"path":"jiuwenswarm/agents/harness/common/tools/trusted_search_tool_adapter.py","sha256":"ffcfeecb6c840bc81bdf226603293dddb9b06fc1b167ddc812e84850dc97fab4","start":36},{"end":33,"path":"jiuwenswarm/agents/harness/common/tools/search_tools.py","sha256":"7214d556936b82e055ff8ad4a57c8ed10dd89910f8da6f18d1b65b1d44f241ba","start":31}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-search-tools facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3616036a4b86dc2f2c1a71c5e12e0936dba8688162c386a9877d158e18267b49 -->
**Paid-provider availability from {PROVIDER}_API_KEY env vars in fixed fallback order**
configured_paid_search_providers() returns providers ("bocha", "perplexity", "serper", "jina") whose {PROVIDER}_API_KEY env var, uppercased and stripped, is nonblank. run_paid_search_structured defaults to provider="auto", max_results=DEFAULT_SEARCH_MAX_RESULTS (8) and timeout_seconds=45; mcp_free_search clamps max_results via normalize_search_max_results to [MIN_SEARCH_MAX_RESULTS=1, MAX_SEARCH_MAX_RESULTS=20] and timeout_seconds to [5, 60].

来源：[jiuwenswarm/agents/harness/common/tools/search_tools.py:L534–L548](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/search_tools.py#L534-L548), [jiuwenswarm/agents/harness/common/tools/search_tools.py:L31–L39](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/search_tools.py#L31-L39), [jiuwenswarm/agents/harness/common/tools/trusted_search_tool_adapter.py:L36–L48](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/trusted_search_tool_adapter.py#L36-L48)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":548,"path":"jiuwenswarm/agents/harness/common/tools/search_tools.py","sha256":"0cdc297ec6ff1b0734192173c8a30cebc557f39e0741b98a710b02463b6b10ec","start":534},{"end":39,"path":"jiuwenswarm/agents/harness/common/tools/search_tools.py","sha256":"0cba93959b4b55725a8f2e434b61cb7b449a4bfe5af6ac7fb2c83d60d6c35b9f","start":31},{"end":48,"path":"jiuwenswarm/agents/harness/common/tools/trusted_search_tool_adapter.py","sha256":"e55a904e33c19f7713b0f1267dd57bbbe0ebf8848191ab555161a2ea8ba04bfd","start":36}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-search-tools facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8bd2b9b0fb92f47c169216891cc4ebe98164e066a0d776ada27443608ef6727e -->
**Paid search guards: blank query, invalid provider, and provider exceptions return [ERROR] strings**
In _run_paid_search, a query that strips to empty returns "[ERROR]: query cannot be empty."; a provider outside {auto,bocha,jina,serper,perplexity} returns "[ERROR]: provider must be auto or a configured search provider."; any exception from run_paid_search_structured is returned as f"[ERROR]: {exc}". In every case the finally block still calls complete_trusted_search_producer(success=False). run_paid_search_structured raises RuntimeError("no paid search API keys configured.") when no provider key is nonblank, ValueError for an unknown provider, and collects "provider runner unavailable" errors per skipped runner.

来源：[jiuwenswarm/agents/harness/common/tools/trusted_search_tool_adapter.py:L82–L99](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/trusted_search_tool_adapter.py#L82-L99), [jiuwenswarm/agents/harness/common/tools/trusted_search_tool_adapter.py:L110–L114](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/trusted_search_tool_adapter.py#L110-L114), [jiuwenswarm/agents/harness/common/tools/search_tools.py:L565–L583](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/search_tools.py#L565-L583)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":99,"path":"jiuwenswarm/agents/harness/common/tools/trusted_search_tool_adapter.py","sha256":"cf8f11da30b25d50780eb261ffc0a74bb22e2621bd16ba0917dfb7de6cc16b47","start":82},{"end":114,"path":"jiuwenswarm/agents/harness/common/tools/trusted_search_tool_adapter.py","sha256":"414789cf0287ae047b4542d5ab58697cf05723806a2be7ba319ee126186a624e","start":110},{"end":583,"path":"jiuwenswarm/agents/harness/common/tools/search_tools.py","sha256":"7802aabeaf0c74e92a8afa81b0ccadb417455befb739ff7dae52e38672aab985","start":565}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-search-tools facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9bcc7b9b788ff23cea04771a7cebb6fde44326bc39efe27e95801457702114ef -->
**Committing URLs before render survives render failure, at the cost of trusting URLs even if rendering then fails**
设计推断（非作者历史意图）：

Inference from the shown branch: success URLs are committed before render_free_search_result runs, so a render-time RuntimeError still leaves the URLs in the ledger (test raises "render failed" and then asserts ledger.contains(url)) — robust provenance, but committed URLs exist for output the caller never saw.

来源：[jiuwenswarm/agents/harness/common/tools/trusted_search_tool_adapter.py:L57–L66](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/trusted_search_tool_adapter.py#L57-L66), [tests/unit_tests/agentserver/permissions/test_trusted_search_tool_adapter.py:L178–L186](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/permissions/test_trusted_search_tool_adapter.py#L178-L186)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":66,"path":"jiuwenswarm/agents/harness/common/tools/trusted_search_tool_adapter.py","sha256":"23386ed892704c3237870c1df4013ef995cb4b5b15a6c2f6a82544f9788badc0","start":57},{"end":186,"path":"tests/unit_tests/agentserver/permissions/test_trusted_search_tool_adapter.py","sha256":"a86b3b5afa9b5ed2c003e9ed4d2613ce9e7c7f8d3aed9e190690a20b9c84daad","start":178}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=web-search-tools facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=52ce45be6e9e6061db9a02146184c79c78119e3f76e3b46a0336aaca318874e1 -->
**Automated runtime tests exercise both adapters' invoke with monkeypatched providers and assert lease/output state**
test_free_adapter_runs_normally_without_provenance_lease (lines 135-151) monkeypatches run_free_search_structured, awaits mcp_free_search.invoke({"query": "news"}), and asserts the URL appears in the result; test_provider_failure_consumes_lease_without_provenance (lines 219-240) asserts the "[ERROR]: free search failed: provider failed" string and len(ledger) == 0; test_paid_adapter_commits_only_structured_provider_urls (lines 190-216) asserts the exact rendered string and ledger.contains for both URLs.

来源：[tests/unit_tests/agentserver/permissions/test_trusted_search_tool_adapter.py:L135–L151](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/permissions/test_trusted_search_tool_adapter.py#L135-L151), [tests/unit_tests/agentserver/permissions/test_trusted_search_tool_adapter.py:L190–L216](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/permissions/test_trusted_search_tool_adapter.py#L190-L216), [tests/unit_tests/agentserver/permissions/test_trusted_search_tool_adapter.py:L219–L240](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/permissions/test_trusted_search_tool_adapter.py#L219-L240)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":151,"path":"tests/unit_tests/agentserver/permissions/test_trusted_search_tool_adapter.py","sha256":"1cb8df29f523d360d72bb85bdc62de328161ae7f45dcb7c7f642275dba052ebd","start":135},{"end":216,"path":"tests/unit_tests/agentserver/permissions/test_trusted_search_tool_adapter.py","sha256":"6ad61999bbe14b01f2aeb5f3c19b4792f664303d617aada3649a87d942b2d52b","start":190},{"end":240,"path":"tests/unit_tests/agentserver/permissions/test_trusted_search_tool_adapter.py","sha256":"53f4bdb67925494dc8fa7883475f3788af567195b57c6c4fd16c4ffd39dd9682","start":219}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
