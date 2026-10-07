---
title: "skill-gen CLI（sop-text / url-fetch 子命令）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_generator_cli.py:L61-L96, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py:L444-L455, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_generator_cli.py:L61-L65, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_generator_cli.py:L84-L88, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/web_page.py:L126-L141, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_generator_cli.py:L81-L96, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_generator_cli.py:L47-L58, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/router.py:L31-L41]
feature: "skill-generator-cli"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_generator_cli.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_generator_cli.py", "jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/web_page.py", "jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/__init__.py", "jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/models.py", "jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/router.py", "jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/wechat_article.py"]
---

# skill-gen CLI（sop-text / url-fetch 子命令）：实现深读

[功能概览](feature-skill-generator-cli.md) · [owner 入口](_index.md)

<!-- kb:depth feature=skill-generator-cli facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c8d3de106194d22da13a22cf075389a0d739500db0f1961364958b98fc0fb8e1 -->
**url-fetch with a non-WeChat URL: trimmed input routed to the generic fetcher, pages serialized, return 0**
In _cmd_url_fetch, a stripped-empty --url logs "error: empty --url" and returns 2 locally; otherwise fetch_pages_from_url is awaited, each FetchedPage is converted via asdict to indent=2 JSON, written to --out-json (parent dirs created) or emitted to stdout by the dedicated stdout_payload logger (INFO, propagate disabled), and the handler returns 0. The router strips the URL, generates a uuid4 doc_id, and dispatches to fetch_web_page when is_wechat_article_url is false.

来源：[jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_generator_cli.py:L81–L96](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_generator_cli.py#L81-L96), [jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_generator_cli.py:L47–L58](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_generator_cli.py#L47-L58), [jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/router.py:L31–L41](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/router.py#L31-L41)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":96,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_generator_cli.py","sha256":"84382d37dc8e0e80529f34d265ea63c7fa8d9e6a61b8faf0b59c75da2760c0dc","start":81},{"end":58,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_generator_cli.py","sha256":"c6f440d160e9405239869a69518b90d599925d94f32ef052aee873bf8d7c0fab","start":47},{"end":41,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/router.py","sha256":"2adde8d87931a83f7ccf2298992774c127679a643ba2e36e468cd926b8c95fdd","start":31}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skill-generator-cli facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=be1ff77adc82cebc3955a2416765fe474054595841ebf07fde45f248185a6fc9 -->
**sop-text extracts raw text; url-fetch fetches pages as JSON**
_cmd_sop_text takes --sop-file (expanded/resolved), and with --print-raw-chars logs len(raw) and returns 0; with --out-text writes the file (mkdir parents) and returns 0; otherwise logs raw text. _cmd_url_fetch requires a non-empty --url, awaits fetch_pages_from_url, and writes or logs json.dumps of [asdict(p)] with --out-json.

来源：[jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_generator_cli.py:L61–L96](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_generator_cli.py#L61-L96)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":96,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_generator_cli.py","sha256":"a516f70669eba3e18300ded54688f1d40af6c462401ddd84a9946ca0db5597dc","start":61}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skill-generator-cli facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5711b93354709c52f25cb799d030fbf024453f8eea5bd28ee9a5d8086eb1db73 -->
**CLI 两个前置守卫返回 2；fetch_web_page 的抓取异常被改写为 ValueError 且 _cmd_url_fetch 不捕获**
_cmd_sop_text 中 expanduser/resolve 后非普通文件则 logger.error 并 return 2；_cmd_url_fetch 中空白 --url 同样 return 2（均为函数返回值）。fetch_web_page 的 try 块把 HTTPStatusError（含状态码）与 RequestError 等异常改写为带 URL 的 ValueError；_cmd_url_fetch 未捕获 ValueError，异常沿 await 上抛。解析后正文节点缺失或文本不足 50 字符也抛 ValueError。

来源：[jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_generator_cli.py:L61–L65](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_generator_cli.py#L61-L65), [jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_generator_cli.py:L84–L88](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_generator_cli.py#L84-L88), [jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/web_page.py:L126–L141](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/web_page.py#L126-L141)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":65,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_generator_cli.py","sha256":"12fbd0f79ed343815ba0d895515b12bafe9a24d811e962fb4eb338769a5af1c7","start":61},{"end":88,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_generator_cli.py","sha256":"655e2a2fb304f292ff3acd18bc35005cc36998980645c7b2ba34064926abaa64","start":84},{"end":141,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/url_ingest/web_page.py","sha256":"6353e73bd80d094a00fef03543ce9f8cbb3dc63be8b746cce8be2aa89b62dc5e","start":126}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=skill-generator-cli facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dd56597fab7e492e8456d40f39f9d198fa29609ff96bab6b72ef7639d6688b86 -->
**Optional parser dependency: graceful fallback vs format loss**
设计推断（非作者历史意图）：

Inference: making AutoFileParser optional (ImportError fallback to plain read) lets sop-text run without agent-core, but costs support for non-text suffixes, which raise "无法解析 SOP 文件..." telling the user to install agent-core or provide .md/.txt.

来源：[jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py:L444–L455](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py#L444-L455)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":455,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-gen-4-enterprise-doc/scripts/skill_gen/sop_parser.py","sha256":"8e9bfaf7299404f81fcc812a27b814b397322361a03e8a558cacca433f396a37","start":444}],"trace":[]} -->
<!-- /kb:depth -->
