---
title: "Cross-Channel Session History Search Skill：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L301-L412, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L82-L89, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L304-L329, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L355-L367, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L16-L21, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/utils.py:L2337-L2338, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L142-L152, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L187-L189, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L381-L397]
feature: "cross-channel-history-search-skill"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py"]
---

# Cross-Channel Session History Search Skill：实现深读

[功能概览](feature-cross-channel-history-search-skill.md) · [owner 入口](_index.md)

<!-- kb:depth feature=cross-channel-history-search-skill facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c54f2dce04b900987230f21a3906361f59906861a2abac00b6f32ce8f6fc328b -->
**main(): parse args, resolve time window, scan sessions, optionally auto-expand, emit report**
main() parses CLI args, resolves tz (ZoneInfo(args.timezone), fallback UTC+8), builds start/end (default last 24h; --start/--end parsed, --at centered on --window-minutes), swaps if start>end, calls _search_once, and if no hits with --auto-expand and no explicit --start/--end re-runs over last 72h; then _emit_search_report and returns 0.

来源：[jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L301–L412](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py#L301-L412)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":412,"path":"jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py","sha256":"74d6f683a4263aaefa13c6d303744f202502bc5d1a8dab13744f64595a5e4321","start":301}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=cross-channel-history-search-skill facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dfa710e95ea29a156021c32b2dde3982dca8e8bd186465ef2ef306ab41f0245a -->
**Defaults: sessions root from jiuwenswarm or env, window 120min, timezone Asia/Shanghai, limit 20, max-sessions 200, auto-expand on**
--sessions-root default "" triggers _default_sessions_root(): get_agent_sessions_dir() when jiuwenswarm imports, else JIUWENSWARM_DATA_DIR/agent/sessions, else ~/.jiuwenswarm/agent/sessions. Defaults: --window-minutes 120, --timezone Asia/Shanghai, --limit 20, --max-sessions 200, --auto-expand True (--no-auto-expand disables); window_minutes/limit/max_sessions clamped to >=1.

来源：[jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L82–L89](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py#L82-L89), [jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L304–L329](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py#L304-L329), [jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L355–L367](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py#L355-L367)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":89,"path":"jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py","sha256":"b64995ed85a7084f2f34a71d4e2574dce8ab8367cd29bc8762acdb21ee86e62a","start":82},{"end":329,"path":"jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py","sha256":"95a63159eb897e3372fcffc67f74555cf144ce38ca52bde6be4b9a8719b93f45","start":304},{"end":367,"path":"jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py","sha256":"2699f44b56b15f740a2b5e9fb02a123c9e363884a2515fb0fff0c5d8571710d7","start":355}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=cross-channel-history-search-skill facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d2f0b2e5e7443667ced28f5b1fce307ebf34ba9f53c378ae7a9fbea583bd60e8 -->
**Optional jiuwenswarm import for sessions root; env-var and home-dir fallback**
The script tries to import get_agent_sessions_dir from jiuwenswarm.common.utils (utils.py returns get_agent_root_dir()/"sessions"); on ImportError _default_sessions_root falls back to $JIUWENSWARM_DATA_DIR/agent/sessions, else ~/.jiuwenswarm/agent/sessions. Consequence: sessions-root resolution differs by whether the package is importable.

来源：[jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L16–L21](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py#L16-L21), [jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L82–L89](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py#L82-L89), [jiuwenswarm/common/utils.py:L2337–L2338](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/utils.py#L2337-L2338)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":21,"path":"jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py","sha256":"5a24f3fddf098dcf9ba76befce7317e494f37dbb038b0c410b67bc0c04d6eace","start":16},{"end":89,"path":"jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py","sha256":"b64995ed85a7084f2f34a71d4e2574dce8ab8367cd29bc8762acdb21ee86e62a","start":82},{"end":2338,"path":"jiuwenswarm/common/utils.py","sha256":"fae4014bb2b988d3200a884a2d4012b8f7c1c6da47be17a6cd3e06e8ea2e97ef","start":2337}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=cross-channel-history-search-skill facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9b4649a0e286a90d9c74de38db45fa2bf49cb1e090d9486a6e0f5d9c54de0a83 -->
**Unreadable or malformed history.json yields an empty record list; missing sessions root yields no dirs**
_read_history_file catches read and json.loads exceptions and returns [] (also when data is not a list), so a corrupt file contributes no hits instead of failing the run; _iter_session_dirs returns [] when sessions_root does not exist.

来源：[jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L142–L152](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py#L142-L152), [jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L187–L189](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py#L187-L189)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":152,"path":"jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py","sha256":"b9c8268d2c0e1996e518a35d1c25acb4a231332fc16f394cb796e4fe7e9492d5","start":142},{"end":189,"path":"jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py","sha256":"6c0f80d52b8e1b674ecbe436a5045fff46766a8a7d9d00b013307556485f7a98","start":187}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=cross-channel-history-search-skill facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=379c320e9a928da98d671ce32b507bef643d584818b38b538eb27d5f84b08bbd -->
**Auto-expand retries with a fresh 72h window when the first pass finds no hits**
设计推断（非作者历史意图）：

Benefit: when auto_expand is true and neither --start nor --end was passed, a no-hit first _search_once triggers one retry over now-72h..now, improving recall without caller re-invocation. Cost (inference): the retry replaces the original window (e.g. an --at-centered one) rather than widening it, and only fires when no explicit start/end were given.

来源：[jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L381–L397](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py#L381-L397)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":397,"path":"jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py","sha256":"1f5d36013aa154187fd80a903e80c79eb8de7bd9696955cd4dfa9009a95d11a9","start":381}],"trace":[]} -->
<!-- /kb:depth -->
