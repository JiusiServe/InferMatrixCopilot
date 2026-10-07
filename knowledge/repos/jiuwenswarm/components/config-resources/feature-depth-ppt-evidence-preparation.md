---
title: "Evidence Plan Preparation and Review Lifecycle：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py:L294-L316, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py:L95-L102, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py:L52-L53, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py:L322-L356, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py:L243-L253, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py:L134-L141, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py:L256-L260, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py:L346-L349, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py:L68-L70, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py:L324-L353, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/SKILL.md:L150-L168, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py:L231-L253]
feature: "ppt-evidence-preparation"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py"]
---

# Evidence Plan Preparation and Review Lifecycle：实现深读

[功能概览](feature-ppt-evidence-preparation.md) · [owner 入口](_index.md)

<!-- kb:depth feature=ppt-evidence-preparation facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d3ba61f6b4466ff882d6f9598420e3bc1ea3abf796ee12f1c490c6bb3eeeffeb -->
**main() prepares only preparable planned/retried items, then saves plan and builds contact sheet, returning 0**
With no --approve/--used/--reject, main() loops plan items; an item is prepared only when its status is in PREPARABLE_STATUSES {"planned", "acquiring", "needs-manual"} and it is planned, explicitly selected, or --force. After the loop it saves the plan, builds the contact sheet, logs warnings, and returns 0 from this function.

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py:L52–L53](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py#L52-L53), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py:L322–L356](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py#L322-L356)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":53,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py","sha256":"069dc4637bd7712f2163c29505b59fb9a069b1f7cb2a3201a68703f12136f6e4","start":52},{"end":356,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py","sha256":"ba13f30830657f64ea4e620978b51edf6e3d6896b74a43e1109c9cf328cb3503","start":322}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-evidence-preparation facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cd51276d75a48926af642ab92fb8c5492f462aa0e9e78845ea959f69329aaa1e -->
**use_item(): non-native items need an existing path (else FileNotFoundError) and review.status=="approved" (else ValueError)**
use_item marks native-chart/native-drawing items used directly; other items raise FileNotFoundError if the resolved path is missing, ValueError if review.status is not "approved", and only then set status to "used".

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py:L243–L253](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py#L243-L253)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":253,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py","sha256":"ac148bca76379504e82062c95a9f479a3fc93e3dc8b9abc90637c14dc4da2256","start":243}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-evidence-preparation facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=95b2f80c2b3ccf0738033947000c7e4ef6e675a13d7d9e0da515775f24f6108c -->
**CLI 默认值与目录默认：--plan 默认 evidence-plan.json，根目录缺省 assets/ 与 analysis/**
argparse 定义位置参数 project，--plan 默认 "evidence-plan.json"，--item/--approve/--used/--reject 为可重复列表，--force 为开关；plan 中的 asset_root 缺省回退到 root/"assets"，analysis_root 回退到 root/"analysis"，二者经 relative_to 校验必须位于项目根内，否则记日志并返回 1。paper 选择器的 min_confidence 默认 0.55。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py:L294–L316](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py#L294-L316), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py:L95–L102](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py#L95-L102)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":316,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py","sha256":"02cd32c44fb58c799faa4939268b458e1a1f27e9b9720d60e5e43aed37edb252","start":294},{"end":102,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py","sha256":"df044195eb41835c76096a8014ee51f155cd5e78895a476c3cb5408bf8c99b43","start":95}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-evidence-preparation facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8fa0f15408bc51677d7d9ceb54ad16a7a55484274598f2bb7335721061dc2175 -->
**prepare_paper shells out to sibling extractor with check=True; make_contact_sheet silently skips when PIL is missing**
prepare_paper runs extract_arxiv_visuals_v2_2.py via subprocess.run(check=True) with --force when force or the output dir exists, so an extractor failure raises; make_contact_sheet returns without output if PIL cannot be imported.

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py:L134–L141](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py#L134-L141), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py:L256–L260](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py#L256-L260)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":141,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py","sha256":"19c9a70bab488e44aa0d32df1a282f31a27453e73853cbade60b6d345e3a54dc","start":134},{"end":260,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py","sha256":"6d2d1584308659fb98e5468b6235b3676f2b4a423fa3a672d2920924b85f003d","start":256}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-evidence-preparation facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a84037a35fe8799f8e96cd125ba6bb63692319b61be5996840d1d774f625e2c6 -->
**Per-item exceptions are caught, set needs-manual, and continue the loop**
In main's item loop, any Exception during review/prepare (e.g. copy_asset raising FileNotFoundError at L69-70) is caught: the item's status becomes "needs-manual", review becomes {"status":"pending","notes":<error text>}, and the error string is appended to errors for later warning logging.

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py:L346–L349](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py#L346-L349), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py:L68–L70](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py#L68-L70)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":349,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py","sha256":"a16eda7c11b7a4f5a27642533000cef96a607901700097ce4a6d2a54dddf7367","start":346},{"end":70,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py","sha256":"065620cc2bc7256a47331e3693ef6e46fb67eee83b25f57e4c1378a1b053f037","start":68}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-evidence-preparation facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6a14f16e60ce18f6a5ff5f0206ba52383b84aa58ccaa4bbd71b2ae7fd5cf01c5 -->
**Per-item exception capture keeps the loop running but downgrades failures to warnings**
设计推断（非作者历史意图）：

Inference: inside the per-item loop, any Exception (e.g. from use_item/approve_item/prepare_item) sets that item's status to needs-manual with review notes recording the cause, appends an error message, and continues to the next item; the benefit is one failing item does not abort the remaining items, and the cost is that the failure surfaces only as a logged warning plus item-level notes within this loop.

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py:L324–L353](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py#L324-L353)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":353,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py","sha256":"3a911d890b168f3a439246b86ac09ae333f9ba9944d33b130acbc079f72b55f3","start":324}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-evidence-preparation facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f63a2c5993fddf03f8497f67bc5ea9266c236acba3410cb5076d1620efeb5bc3 -->
**Documented manual procedure: contact-sheet review then --approve/--used (NOT EXECUTED)**
文档中的人工验收步骤（本轮未执行）：

SKILL.md documents running prepare_evidence.py, then viewing analysis/evidence-contact-sheet.jpg (or the paper-specific contact sheet) before --approve <id> marks an item ready, and --used <id> recording placement into the PPT; statuses are limited to planned/acquiring/ready/used/needs-manual/skipped. This procedure is documented only; it was NOT EXECUTED here.

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/SKILL.md:L150–L168](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/SKILL.md#L150-L168), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py:L231–L253](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py#L231-L253)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":168,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/SKILL.md","sha256":"f0921b85f127e4efeca2a994d9cd556d5eef25633179229db7c85ecd2e35fb04","start":150},{"end":253,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/prepare_evidence.py","sha256":"d8fa94d6b0d9ca7ca7a58a4737c504aab2d1cca1c653c32210914ba64f90b2d0","start":231}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
