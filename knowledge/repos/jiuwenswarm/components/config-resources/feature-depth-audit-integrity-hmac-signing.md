---
title: "符号审计完整性 HMAC 签名与信任验证（audit_integrity.py）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L697-L712, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L625-L635, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L654-L663, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L452-L458, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L520-L554, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L175-L180, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L466-L490, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L444-L503, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L537-L560, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L175-L176, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L466-L468, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L496-L498, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/SKILL.md:L60-L62, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/project-maintainer/SKILL.md:L57-L61]
feature: "audit-integrity-hmac-signing"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py"]
---

# 符号审计完整性 HMAC 签名与信任验证（audit_integrity.py）：实现深读

[功能概览](feature-audit-integrity-hmac-signing.md) · [owner 入口](_index.md)

<!-- kb:depth feature=audit-integrity-hmac-signing facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c02c8fb4f91c50203b764c68ffb694868168ba873ae9c86830d6d9c7e810216b -->
**verify_agent_record：对 agent_audited 记录做签名与哈希比对并归类信任结果**
verify_or_report 遍历 audit.status == "agent_audited" 的记录调用 verify_agent_record；该函数在记录缺 integrity.signature 或缺 batch_hash 时直接返回 "invalid_agent_audit"，否则比对 payload_hash 与 hmac_signature(secret, payload_hash)（hmac.compare_digest），任一 mismatch/untrusted_script_hash 置 invalid 并返回 "invalid_agent_audit"、closure_eligible=False；仅哈希类不一致（symbol/source/entry_doc_hash_changed）单独标记 stale，batch 重用超阈值标记 suspicious。这是函数返回值，不代表进程退出码。

来源：[jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L444–L503](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py#L444-L503), [jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L537–L560](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py#L537-L560), [jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L175–L176](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py#L175-L176)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":503,"path":"jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py","sha256":"ea165bb82592c93fcd6637db9c198546cc9b7cceb12a8aaa3c1867820a5af88c","start":444},{"end":560,"path":"jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py","sha256":"2701af00b719926816421c797898d745bb9faa1ba4680822b4489538001cf1fe","start":537},{"end":176,"path":"jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py","sha256":"b6978cf90c4a6c66326c146fe4762606175a613030938d45f5aa1dde5ba77922","start":175}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=audit-integrity-hmac-signing facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4a4ee97435cf5872138ecbbc624a750b98768abb5f487666de66d5849e06ea70 -->
**main 按 command 分派，verify_or_report 在 verify 模式返回 0-4 区分退出码**
main(argv) 解析后分派 ensure-key/promote/verify/report；AuditIntegrityError 被捕获并以 JSON 打到 stderr 后 return 1。verify_or_report 在 verify_mode 下按 invalid/stale/suspicious/closure 未通过分别返回 1/2/3/4，report 模式恒 return 0。此返回值仅是函数局部返回值，不证明进程退出码。

来源：[jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L697–L712](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py#L697-L712), [jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L625–L635](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py#L625-L635)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":712,"path":"jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py","sha256":"c22d4299032503f5ab1dfb65d60f51f708aab851c3c4f507ccb18de45af646b3","start":697},{"end":635,"path":"jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py","sha256":"88edc3c4a752d5e2c353e37f2c92603f07e074cad23d4a9ee2cb6ca3155cf3e2","start":625}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=audit-integrity-hmac-signing facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e14985c282995f31ee34de46d12921d663c783a976b7621bff6413d68e95a29e -->
**add_repo_key_arguments：--repo-root 必填，签名密钥参数默认取常量**
解析器要求 --repo-root 与 --audit-map 必填；--signing-key-env 默认 DEFAULT_SIGNING_KEY_ENV、--key-id 默认 DEFAULT_KEY_ID、--strict 为 store_true 开关；这些默认常量的具体值不在所示行内。

来源：[jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L654–L663](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py#L654-L663)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":663,"path":"jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py","sha256":"7b106d59b475307a4de96e963448a274d55581e0da9d48023dc47cc837f41f80","start":654}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=audit-integrity-hmac-signing facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c95a782f773629ab9afa886435875924383bbe87cadc7e6867e0c99cf1d7f61f -->
**verify_agent_record 依赖 verify_or_report 传入的 signing_secret 密钥与 hmac/hashlib 实现**
verify_or_report 通过 signing_secret(args.signing_key_env, root, args.key_id) 取得密钥（L523），并作为 secret 传入 verify_agent_record（L548–L551）；该函数用 hmac_signature 以 HMAC-SHA256 计算 integrity.payload_hash 的期望签名（L487，定义见 L175–L176），并用 hmac.compare_digest 与记录中 signature 比较（L488）。同时依赖本脚本自身的 file_hash：integrity.script_hash 与 script_hash() 不一致时追加 untrusted_script_hash 并置 invalid=True（L466–L468）。

来源：[jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L520–L554](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py#L520-L554), [jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L175–L180](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py#L175-L180), [jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L466–L490](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py#L466-L490)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":554,"path":"jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py","sha256":"f1d8f1f4fb433654ab4877d7249ab55ddf4afe5ea0c2b50f11b0148151d2125d","start":520},{"end":180,"path":"jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py","sha256":"d4ff0ea2bca2fbb5efdb91c5de04b1bd64f9991b5a679f9f03811d5e4b47e4bc","start":175},{"end":490,"path":"jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py","sha256":"35a306085aaabe7c57fbc1a77fdcc86974c98f54c3a8bd56ac5b9a9a420650f4","start":466}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=audit-integrity-hmac-signing facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ebaf8e2bdf17b95ece7569d5bce31fd2b68f280ede0460718277fee01831d4f5 -->
**无签名或缺 batch_hash 的记录直接判 invalid_agent_audit**
verify_agent_record 开头两个守卫：integrity 非 dict 或无 signature 返回 ("invalid_agent_audit", ["unsigned_agent_audit","invalid_agent_audit"], False)；batch 缺 batch_hash 返回 missing_agent_call_signature 分支。此类记录不计入 closure eligible。

来源：[jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L452–L458](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py#L452-L458)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":458,"path":"jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py","sha256":"375ec77d0ed0c7b169f79a9b5c4beeac2b9e9c70a28a07da5771eb5c6a363a24","start":452}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=audit-integrity-hmac-signing facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cb4cd23c0f6455b7cc84f27198f926fdcfbb1a5eb64d41537ddcf2ec60e06885 -->
**按当前脚本哈希验证记录：换取篡改可检测，代价是脚本变更即失效**
设计推断（非作者历史意图）：

验证将记录内 script_hash 与当前运行的 script_hash() 比对，不一致即标记 untrusted_script_hash 并置 invalid（L466–L468），随后 L496–L498 返回 "invalid_agent_audit"。推断（非作者意图）：好处是脚本被改动后既有审计记录降级为不可信；成本是正常脚本更新也会使旧记录失效，且所示片段未含恢复路径。SKILL.md L62 本身将该密钥定位为非防篡改安全边界。

来源：[jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L466–L468](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py#L466-L468), [jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py:L496–L498](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py#L496-L498), [jiuwenswarm/resources/agent/workspace/skills/project-maintainer/SKILL.md:L60–L62](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/SKILL.md#L60-L62)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":468,"path":"jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py","sha256":"03cb12299c5e8b0c0f7aba1c079945e275de9ba3a71b2ae7fd025c4befc8417f","start":466},{"end":498,"path":"jiuwenswarm/resources/agent/workspace/skills/project-maintainer/scripts/audit_integrity.py","sha256":"0cc1e8832a9b991f9cd981ff6b10742a56f4eb8a4e963fef238e9721dbf53c38","start":496},{"end":62,"path":"jiuwenswarm/resources/agent/workspace/skills/project-maintainer/SKILL.md","sha256":"cd738a9ebb0ea35d3007e6a7253be2b7ba2b00d68ccfc922409537c057412194","start":60}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=audit-integrity-hmac-signing facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=55ff1ab4d6f6fdff59d06d978351b9a80b4c6df8628f04da770182801a52526b -->
**文档化的 preflight ensure-key 步骤（未执行）**
文档中的人工验收步骤（本轮未执行）：

SKILL.md L58–L61 记录：在 preflight 运行 `python <skill-dir>/scripts/audit_integrity.py ensure-key --repo-root <repo-root>`，默认密钥记录为 `.doc_project_maintainer/project/audit-signing-key.json`（PROJECT_MAINTAINER_AUDIT_SIGNING_KEY）；当环境变量缺失时脚本加载该工件密钥并在首次使用时创建，预期结果是后续 audit 命令前密钥已就绪。标注：NOT EXECUTED，本次仅复述文档，未运行。

来源：[jiuwenswarm/resources/agent/workspace/skills/project-maintainer/SKILL.md:L57–L61](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/project-maintainer/SKILL.md#L57-L61)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":61,"path":"jiuwenswarm/resources/agent/workspace/skills/project-maintainer/SKILL.md","sha256":"ee241e371b62793fd72bad30454ad1b916c5896bfc5548443c1131ec5b12fb04","start":57}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
