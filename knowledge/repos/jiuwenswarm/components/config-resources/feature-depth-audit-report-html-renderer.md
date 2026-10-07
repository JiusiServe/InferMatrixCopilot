---
title: "自包含审计可视化 HTML 报告生成器：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py:L546-L555, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py:L42-L53, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py:L30-L39, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/render_audit_report.py:L512-L528]
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
