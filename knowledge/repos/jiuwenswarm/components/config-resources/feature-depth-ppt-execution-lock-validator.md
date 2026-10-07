---
title: "PPT 执行锁（execution-lock.json）语义校验器：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js:L201-L232, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js:L234-L247, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js:L249-L252, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js:L11-L19, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js:L11-L14, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js:L226-L231, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js:L16-L19, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js:L8-L9, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js:L183-L195, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js:L234-L241, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js:L74-L90, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/SKILL.md:L145-L151, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-evidence-plan.js:L106-L133]
feature: "ppt-execution-lock-validator"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js", "jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-evidence-plan.js"]
---

# PPT 执行锁（execution-lock.json）语义校验器：实现深读

[功能概览](feature-ppt-execution-lock-validator.md) · [owner 入口](_index.md)

<!-- kb:depth feature=ppt-execution-lock-validator facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=555e5059608825665a25831d987b33cfb22da2fbee0b0d7e488c5ca33f9cde9f -->
**以 --phase design|generate|deliver 运行时的校验路径：逐资产检查后汇总并按错误数退出**
argv 解析出 phase（默认 design）与 lock 路径后，脚本遍历 lock.assets 检查 id/kind/status/path 等，再校验每页 evidence_visual 引用，最后打印 [WARN]/[ERROR] 与统计行，并 process.exit(errors.length ? 1 : 0)。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js:L201–L232](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js#L201-L232), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js:L234–L247](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js#L234-L247), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js:L249–L252](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js#L249-L252)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":232,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js","sha256":"67e2a2db687b08b6a6fb622e7148d46b7689bfb998ae47ca87c334d6c40f38c5","start":201},{"end":247,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js","sha256":"df2af923be27aeecaa9f51c64d7153014ce59ea23fa37a51e831b29dd2a0f258","start":234},{"end":252,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js","sha256":"9d6b09497ab2d8775381e701b56877fae28f6262a0a6cf27fa5c04c1d0ea1aa9","start":249}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-execution-lock-validator facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fc9b24e3d26bf26f653f41bf9e0fe56e3408c7498c008158e5e18df6522b52e2 -->
**CLI 契约：形如 --phase 显式跟随值的调用；缺参或非法 phase 退出码 2，有错误退出码 1、否则 0**
调用方须传 lock 路径且 phase 属于 design|generate|deliver，否则输出 Usage 并 process.exit(2)。注意 lockArg 的查找会排除 --phase 本身及其后一个参数，因此实际调用应让路径不在这些位置。汇总后按 errors 数量退出 1 或 0。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js:L11–L19](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js#L11-L19), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js:L249–L252](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js#L249-L252)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":19,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js","sha256":"a4c990faa7f1f0480c54872244a6905aad4fb10efd997360067b1df6e53bf015","start":11},{"end":252,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js","sha256":"9d6b09497ab2d8775381e701b56877fae28f6262a0a6cf27fa5c04c1d0ea1aa9","start":249}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-execution-lock-validator facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=797a001a6c6a01a98edbbbaa4a3eca1cc3efe23c7cbf7dfa207068e2dff49a20 -->
**phase 默认 design；非 design 拒绝未就绪的必需资产，deliver 进一步要求 used**
--phase 缺省时 phase 为 "design"。phase !== "design" 且 asset.required 时，status 为 planned/acquiring/needs-manual 之一即报错；phase === "deliver" 时必需资产 status 非 used 报错。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js:L11–L14](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js#L11-L14), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js:L226–L231](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js#L226-L231)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":14,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js","sha256":"d3a98a3dae50e1611aed1fd7b90c700fc34867970ff6c7798717882bc2c86214","start":11},{"end":231,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js","sha256":"b451eb9db2f29fbf5de6c67a1fbd7f26a1d8057a689b80f2ac7f85f690adeea4","start":226}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-execution-lock-validator facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=33177778337e9dc2f3b98d3a3c3f7bc1820597029e04762583e15929217a3ced -->
**version 2 锁通过 require 的 validateEvidencePlan 复用 evidence-plan 校验**
脚本第 9 行 require ./validate-evidence-plan.js；当 lock.version === 2 且 evidence_plan 非空、文件存在时（L183–L190），调用 validateEvidencePlan(evidencePath, { phase, pageIds })（L191），将其 errors/warnings 并入自身输出（L193–L194），并用返回的 itemsById 检查每页 evidence_visual.asset_ids 是否已知且属于该页（L237–L240）。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js:L8–L9](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js#L8-L9), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js:L183–L195](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js#L183-L195), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js:L234–L241](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js#L234-L241)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":9,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js","sha256":"e2eec7500f8f8035528c004571941681f9348530ea742c26bf6207784f69a0de","start":8},{"end":195,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js","sha256":"b571cbc3ca8b05b2e69a9a163a22562b750de11408290dc478e30feb0030590f","start":183},{"end":241,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js","sha256":"088d0b9a55599a6514ab4684b7f052356f8c581fb43eea76341f364667eedf3e","start":234}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-execution-lock-validator facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1ed71cbd160178e1c5df935795b59ed79a619ec6a443721120d2c08f4022d58a -->
**缺参/非法 phase 走 Usage 分支退出 2；任意校验错误累积为 [ERROR] 并以退出码 1 传播**
lockArg 为空或 phase 不在 design|generate|deliver 时立即 console.error(Usage) 并 process.exit(2)；否则各检查通过 error() 记入 errors，结尾逐条打印并以 errors.length ? 1 : 0 退出，warning 仅打印不影响退出码。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js:L16–L19](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js#L16-L19), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js:L249–L252](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js#L249-L252)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":19,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js","sha256":"710df5df43ed223872724896226a60d4f5383336c0457d791628754362bda0c7","start":16},{"end":252,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js","sha256":"9d6b09497ab2d8775381e701b56877fae28f6262a0a6cf27fa5c04c1d0ea1aa9","start":249}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-execution-lock-validator facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fe2ad330bdd244dba068f5678d68e0e1f50e3492cc63ad204bc5d3105d48e48a -->
**十二个品牌常量硬编码为字面量，且注释声明需与另外两处文件保持同步**
设计推断（非作者历史意图）：

validate-execution-lock.js 在 L76–L89 将 brand.colors/typography/footer/summary_banner 共十二个键钉死为字面量并逐一 expect()（L90）；收益是锁内品牌块被精确校验，代价是 L74–L75 注释所述：换主题需同步修改本文件、base/execution-lock-reference.json 和 scripts/components.js 的 THEME 三处（此同步义务为注释声明，属事实引用；将其判定为设计取舍是本人的推断）。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js:L74–L90](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js#L74-L90)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":90,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js","sha256":"aae712f48463788f87eaa984049f81d76010d6ffd2fa0e6687a86b90749a8fe2","start":74}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-execution-lock-validator facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ffea96e2f0a6a3a008587ecd4bbbcde7413403dd889d38841079d70a6caccbe5 -->
**SKILL.md 记录的设计阶段双脚本校验流程与失败即禁止生成页面的规则（未执行）**
文档中的人工验收步骤（本轮未执行）：

文档操作（NOT EXECUTED，仅记录于 SKILL.md L145–L149）：运行 `node scripts/validate-evidence-plan.js <project>/evidence-plan.json --phase design` 与 `node scripts/validate-execution-lock.js <project>/execution-lock.json --phase design`；文档预期为校验未通过时不得开始页面生成。脚本侧行为（未运行）：evidence-plan 校验在参数缺失或 phase 不合法时 exit 2，plan 路径位于 skill 目录内时 exit 1，有错误时 exit 1 否则 exit 0（L106–L133）；execution-lock 校验打印汇总行后按 errors 数量 exit 1/0（L249–L252）。所示片段不含针对两校验器的自动化测试。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/SKILL.md:L145–L151](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/SKILL.md#L145-L151), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-evidence-plan.js:L106–L133](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-evidence-plan.js#L106-L133), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js:L249–L252](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js#L249-L252)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":151,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/SKILL.md","sha256":"13a430aca7e5735d7d842c461143620f608d100c0f07109146ab6107162d2b74","start":145},{"end":133,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-evidence-plan.js","sha256":"238a5e164aedd20b307338e76596672d35a265c80bbebbab536254fc8474532d","start":106},{"end":252,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/validate-execution-lock.js","sha256":"9d6b09497ab2d8775381e701b56877fae28f6262a0a6cf27fa5c04c1d0ea1aa9","start":249}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
