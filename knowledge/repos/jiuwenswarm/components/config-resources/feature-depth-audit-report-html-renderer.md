---
title: "自包含审计可视化 HTML 报告生成器：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py:L546-L555, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py:L42-L53, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py:L30-L39, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py:L512-L528, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/SKILL.md:L198-L210, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py:L208-L227, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py:L534-L543, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py:L42-L50, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py:L462-L499]
feature: "audit-report-html-renderer"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py"]
---

# 自包含审计可视化 HTML 报告生成器：实现深读

[功能概览](feature-audit-report-html-renderer.md) · [owner 入口](_index.md)

<!-- kb:depth feature=audit-report-html-renderer facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=90d8378bc5c0fa6fe138fd9a423c11a31f4df877c15c6cbcfb4dad7505c6f472 -->
**main parses argv, renders report, prints JSON output path and returns 0 locally**
main(argv) 解析参数并调用 generate_report；成功时打印 json.dumps({"output": ...}) 并 return 0。这是函数局部返回值，不是进程退出码断言。

来源：[jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py:L546–L555](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py#L546-L555)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":555,"path":"jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py","sha256":"ec646ee3d58cf680e096038bacc1782dd3c062be6bf3e379d4a21223f357ab3f","start":546}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=audit-report-html-renderer facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=724ea69026e51479dadb0d2d576740e2cd979332fa75b13d0c3967aede0d2517 -->
**generate_report reads two JSON maps and writes the HTML file itself**
generate_report(args) resolves paths, reads coverage-map.json and symbol-audit-map.json, builds the model, and writes HTML to the resolved output path (creating parent dirs) before returning that path; main prints {"output": path} JSON on success.

来源：[jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py:L512–L528](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py#L512-L528), [jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py:L546–L555](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py#L546-L555)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":528,"path":"jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py","sha256":"b794a4d10bc621a203abc8d075aad541d3a6e896240002320d78aa8f3e24e006","start":512},{"end":555,"path":"jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py","sha256":"ec646ee3d58cf680e096038bacc1782dd3c062be6bf3e379d4a21223f357ab3f","start":546}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=audit-report-html-renderer facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=829c7f6e1c04e8ada639ffa94cad71f2eeacdd3012e5eaaed6f1b074ae1169a6 -->
**resolve_paths falls back to artifact_root/project defaults when CLI args absent**
coverage-map.json、symbol-audit-map.json、audit-integrity-report.json 和 audit-report.html 默认位于 (artifact_root 或 repo_root/DEFAULT_ARTIFACT_ROOT)/project/ 下，显式参数优先。

来源：[jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py:L42–L53](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py#L42-L53)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":53,"path":"jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py","sha256":"3a980b0134bb842fd511f8f9f2b2e5281c07abb08699e5354a6a4df6d264bfa5","start":42}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=audit-report-html-renderer facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=130d73417370166e59636bc205c4e080003b876429bbd7af6aee07d716407065 -->
**read_json wraps missing, invalid, and non-object JSON as AuditReportError; main prints to stderr and returns 1**
FileNotFoundError、JSONDecodeError 及顶层非 dict 分别抛出带 label 与 path 的 AuditReportError；main 捕获后打印到 stderr 并 return 1（局部返回值），否则正常输出。

来源：[jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py:L30–L39](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py#L30-L39), [jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py:L546–L555](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py#L546-L555)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":39,"path":"jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py","sha256":"495d60953210bafaa62de683f4b4bf7f5edef3ab20e53bff8432db91ee7cc921","start":30},{"end":555,"path":"jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py","sha256":"ec646ee3d58cf680e096038bacc1782dd3c062be6bf3e379d4a21223f357ab3f","start":546}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=audit-report-html-renderer facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7fb7c3c5ec3ef20976d99638068f7f40a47312e7a27ce773c30d6d43d567b164 -->
**Integrity refresh subprocess forwarding default flags with repo_root cwd**
The renderer invokes a child process via subprocess.run with cwd=paths["repo_root"], forwarding --scope (value ALL_SCOPE), --report-output, --signing-key-env (argparse default "PROJECT_MAINTAINER_AUDIT_SIGNING_KEY") and --batch-reuse-threshold (default 1); on nonzero returncode it returns a failed integrity state instead of the report. Input maps default under artifact_root/project (coverage-map.json, symbol-audit-map.json) when not overridden.

来源：[jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py:L208–L227](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py#L208-L227), [jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py:L534–L543](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py#L534-L543), [jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py:L42–L50](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py#L42-L50)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":227,"path":"jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py","sha256":"128a1de17a63c1773daa78bef890a7e95654a16f5bd59904d82570e442814bf0","start":208},{"end":543,"path":"jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py","sha256":"636b607bc44c61686b419d7cb1cc7b7ac30fbeb039115899fb297060f4493a96","start":534},{"end":50,"path":"jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py","sha256":"2e31addbf156bbe2c2ea283282014c643e05f93a8078278794d2ab99721b1f3a","start":42}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=audit-report-html-renderer facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dc23177fbb54de5d5dbf7ad4c3f272db57af26b0bc68a593c61feef383762051 -->
**Client-side innerHTML rendering with per-field escapeHtml: interactive at the cost of safety resting on escaping**
设计推断（非作者历史意图）：

Inference: the report's applyFilters/sortBy/renderTable callbacks do all filtering, sorting and table assembly in the browser by concatenating HTML strings into innerHTML. Benefit: search, risk/status filtering and click-to-sort re-render without any server round trip. Cost: every interpolated field (name, kind, source, line, auditStatus, trustResult, riskLevel, suggestedAction) must pass through escapeHtml individually — one missed field is an injection path, and correctness depends on fields outside the shown span.

来源：[jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py:L462–L499](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py#L462-L499)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":499,"path":"jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py","sha256":"b413f7b689999196724c9be2eb3627b4b1f173e43b97f1ca5eb24f8ff0259bc4","start":462}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=audit-report-html-renderer facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bd218ef6e32120ec6716ccc216444bd6a94b709c8e023df8627a4e84c583f53f -->
**Documented manual procedure: run render_audit_report.py and treat HTML as presentation-only (NOT EXECUTED)**
文档中的人工验收步骤（本轮未执行）：

Documented manual steps, NOT EXECUTED: confirm .doc_project_maintainer/project/coverage-map.json and symbol-audit-map.json exist; run `python <skill-dir>/scripts/render_audit_report.py <repo-root>`; the generator refreshes trust classification via audit_integrity.py report unless --skip-integrity-refresh is passed; expected result is project/audit-report.html, a presentation artifact only, with the JSON maps remaining source of truth. If maps are refreshed afterwards, the report reflects older data.

来源：[jiuwenswarm/resources/agent/workspace/skills/project-maintainer/SKILL.md:L198–L210](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/SKILL.md#L198-L210)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":210,"path":"jiuwenswarm/resources/agent/workspace/skills/project-maintainer/SKILL.md","sha256":"b999fb9d393691fb444cd2488f2f509d8915164b060844cc821c1cda622b6b24","start":198}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
