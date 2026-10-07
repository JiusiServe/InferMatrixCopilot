---
title: "Cross-Channel Session History Search Skill：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L301-L412, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L82-L89, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L304-L329, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L355-L367, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L16-L21, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/utils.py:L2337-L2338, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L142-L152, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L187-L189, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L381-L397, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L301-L367, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L120-L139, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L381-L416, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/SKILL.md:L20-L25, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/SKILL.md:L54-L67]
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

<!-- kb:depth feature=cross-channel-history-search-skill facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=85d38ec9919fddfdbd593ea34b2abb176ca0147375630795b71d0b03ef87b62a -->
**main() argparse CLI: --at/--start/--end window resolution and return 0 on report emission**
main() 通过 argparse 接受 --channel、--session-id、--query（空格分隔关键词）、可重复 --keyword、--start/--end/--at、--window-minutes（默认 120）、--timezone（默认 Asia/Shanghai）、--limit（默认 20）、--max-sessions（默认 200）、--auto-expand/--no-auto-expand。时间窗：有 --start/--end 时缺省端用 now-24h/now；否则 --at 取 center±window_minutes/2；都没有则最近 24 小时；start>end 时交换。窗口计算用 _parse_user_dt，它依次尝试三种 strptime 格式，再尝试 fromisoformat（Z 转 +00:00），无时区则补 tz，全部失败抛 ValueError("无法解析时间: …")。_emit_search_report 之后 return 0（本地返回值，非进程退出码断言）。

来源：[jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L301–L367](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py#L301-L367), [jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L120–L139](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py#L120-L139), [jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py:L381–L416](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py#L381-L416)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":367,"path":"jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py","sha256":"2867327a2cc85c8ee3d751e252e4e168d8bb57e74a6542dc30663c956c1271a6","start":301},{"end":139,"path":"jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py","sha256":"08de9c1466ced1381f430c56f82a8e48d03eace71dbe5947ff391ae444fbf912","start":120},{"end":416,"path":"jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/scripts/search_history.py","sha256":"d21897fd7c1bb85e557b6b316871193e799ee3dedcd5c141cd4abffa572f8cb2","start":381}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=cross-channel-history-search-skill facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b90b108223cc5c562b41b6073d821243909abde3b2570e889bf3781d9a96c445 -->
**Documented manual procedure: run search_history.py via mcp_exec_command and check SKILL/summary/context markers (NOT EXECUTED)**
文档中的人工验收步骤（本轮未执行）：

SKILL.md 记录的手工流程（未执行）：用 mcp_exec_command 运行 `python …/skills/cross-channel-history-retrieval/scripts/search_history.py --channel feishu --query … --start … --end … --limit 30`，预期脚本第一行固定输出 `SKILL=cross-channel-history-retrieval` 以便 grep 确认已执行，并输出 HISTORY_SEARCH_SUMMARY 与 HISTORY_CONTEXT_BLOCK 两个区块；无命中时应说明已检索的时间窗/频道/关键词并询问是否放宽。这只是文档化手工步骤，本次未实际执行，不构成运行验证。

来源：[jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/SKILL.md:L20–L25](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/SKILL.md#L20-L25), [jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/SKILL.md:L54–L67](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/SKILL.md#L54-L67)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":25,"path":"jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/SKILL.md","sha256":"c7e52776fc369467c9daf6ee1f27f9f4c078f3767a6a9d49c9f8c0acac02a7e0","start":20},{"end":67,"path":"jiuwenswarm/resources/agent/workspace/skills/cross-channel-history-retrieval/SKILL.md","sha256":"6f8582084f0654375c5d4b6343d76342c5f5ce44bedd5e5c650addb8132e5750","start":54}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
