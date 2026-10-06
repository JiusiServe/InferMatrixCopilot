---
title: "符号审计完整性 HMAC 签名与信任验证（audit_integrity.py）"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L654-L663, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L122-L154, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L681-L693, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L135-L154, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L466-L490, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L484-L490, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L235-L258, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L593-L623]
feature: "audit-integrity-hmac-signing"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py"]
---

# 符号审计完整性 HMAC 签名与信任验证（audit_integrity.py）

<!-- kb:knowledge owner=feature-audit-integrity-hmac-signing facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**密钥来源与命令行参数**

通用参数 `--repo-root`（必填）、`--signing-key-env`（默认 `PROJECT_MAINTAINER_AUDIT_SIGNING_KEY`）、`--key-id`（默认 `project-maintainer-local-v1`）、`--strict`；`--audit-map` 对 promote/verify/report 必填（L654–L663）。签名密钥优先取环境变量，只要其值为假值（包括空字符串）就回退到工件内密钥文件 `.doc_project_maintainer/project/audit-signing-key.json`，该文件不存在时自动生成 `secrets.token_urlsafe(32)` 的 hmac-sha256 密钥（L43、L122–L154）。verify/report 还有 `--batch-reuse-threshold`（默认 1）、`--scope`（默认 `default_health_audit`）、`--report-output`、`--require-closure`（L681–L693）。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L654–L663](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py#L654-L663), [jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L122–L154](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py#L122-L154), [jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L681–L693](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py#L681-L693)

<!-- kb:knowledge owner=feature-audit-integrity-hmac-signing facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**本地 HMAC 的安全边界**

Inference / 设计推断（非作者历史意图）：

工件内密钥文件与被保护数据同存一处（`.doc_project_maintainer/project/audit-signing-key.json`），且环境变量密钥优先于它（L135–L154）；所示代码没有任何机器或工作区绑定，因此能读到密钥的任何一方都可以用当前脚本重新签名记录。脚本自身哈希检查（`script_hash`）在验证时对比的是当前运行的脚本（L466–L468），其效果是脚本变更后既有 agent 审计的信任被判定失效，而不是阻止修改后的脚本重新签名——`promote` 总是用当前脚本哈希和新 HMAC 覆盖记录（L359、L383–L404）。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L135–L154](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py#L135-L154), [jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L466–L490](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py#L466-L490)

<!-- kb:knowledge owner=feature-audit-integrity-hmac-signing facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**校验行为与输入检查**

恒时比较只用于 HMAC 签名（`hmac.compare_digest`，L487–L488）；payload 哈希本身用普通 `!=` 比较（L484）。`promote` 前置校验入口文档：要求存在带内容的 `Actual Role` 标题且文本包含 `health:` 与 `overall:` 字段，并检查源文件与 JSON 输入存在性/结构（L235–L258、L345–L347）。验证报告输出状态计数、信任计数、closure 统计、批复用明细与逐记录 `records_detail`，并由 `recommended_action` 给出建议动作（L593–L623、L638–L651）。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L484–L490](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py#L484-L490), [jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L235–L258](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py#L235-L258), [jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L593–L623](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py#L593-L623)

