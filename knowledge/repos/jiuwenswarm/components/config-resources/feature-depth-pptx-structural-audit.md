---
title: "PPTX 结构与可读性审计脚本：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L494-L534, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L506-L509, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L59-L64, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L511-L517, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L295-L308, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L2-L7, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L268-L274, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L11-L20, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L55-L56, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L494-L503, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L528-L534, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L292-L308, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/base/quality-gates.md:L97-L110]
feature: "pptx-structural-audit"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py", "jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_density.py", "jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_geometry.py"]
---

# PPTX 结构与可读性审计脚本：实现深读

[功能概览](feature-pptx-structural-audit.md) · [owner 入口](_index.md)

<!-- kb:depth feature=pptx-structural-audit facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0d048282201cce8abcb21c23d6dfa162cf42f0d68f88e146bc7fb0b89041c257 -->
**main 解析参数后调用 audit，报告写入/输出并以错误数决定返回值**
main 配置 stderr 日志、解析参数，调用 audit(args)；成功时可选写 --report JSON，逐条输出 warnings/errors 及汇总行，仅当 report["errors"] 非空时返回 1，否则返回 0。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L494–L534](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py#L494-L534)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":534,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py","sha256":"e812e5b81dfcbb45fdd485cebc7147d5ef76b191e5fbb05b3d8ea93791c77aaa","start":494}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=pptx-structural-audit facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a80ebdaca11f9ef571f8ad7f26729f3fc16532d8d0fb97d3fb1ede9cc64e61a9 -->
**字号下限默认 24/10/7 可由 CLI 覆盖；幻灯尺寸缺省 12192000x6858000 EMU**
--title-min-font、--body-min-font、--absolute-min-font 的 argparse 默认分别为 24.0、10.0、7.0；slide_size 在 presentation.xml 缺少 p:sldSz 节点或属性时回退到 12192000x6858000 EMU（16:9）。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L506–L509](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py#L506-L509), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L59–L64](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py#L59-L64)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":509,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py","sha256":"fae317ff394ee709151c53defd22c96cdce19dfe6a7b7dd759adeca87c6ec445","start":506},{"end":64,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py","sha256":"e51b80fe108d2e734e1c9313a0438dec729e5a2fd6df1fe32ccc0e92b6a8a6ff","start":59}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=pptx-structural-audit facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e86af610de0f6de11c5d7d85811ad7445d704e08c25a6f7d8d5eea8b0a795a3e -->
**audit_pptx.py depends only on the Python standard library and reads the PPTX as a ZIP of XML**
Imports are argparse, hashlib, json, logging, posixpath, re, sys, zipfile, pathlib and xml.etree.ElementTree only; the xml() helper parses parts via ET.fromstring(zf.read(name)), so the audit runs without python-pptx or other third-party packages.

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L11–L20](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py#L11-L20), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L55–L56](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py#L55-L56)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":20,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py","sha256":"0207bd2c2e44bdac978df7c155ed36fcfc688a9435071339838c01dbe29cfea5","start":11},{"end":56,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py","sha256":"59b4444a6b8dabfe56bcd24dd76a7e6b10d0cb155da17029ac60ea75b7e482ee","start":55}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=pptx-structural-audit facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=27b0cf7411c8eab9eef35f5356edb2de4e3ab6f0301b6ccfce99125386deacb0 -->
**输入/解析异常被捕获并返回 1；缺失包部件记为 errors**
main 捕获 (OSError, ValueError, zipfile.BadZipFile, ET.ParseError)，日志输出 "audit failed: ..." 并返回 1；audit 内部对不存在的 pptx 路径抛 FileNotFoundError，对缺失的必需包部件（如 ppt/presentation.xml）追加到 errors 列表而非立即抛出。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L511–L517](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py#L511-L517), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L295–L308](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py#L295-L308)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":517,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py","sha256":"a26745ef16adf991d448575c50f2e822f6fa678cee17f59a8b14c1593d14c12c","start":511},{"end":308,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py","sha256":"4d868466028170c725438c68827d71dccea038e1040c2172fbfd17c57fdb3f27","start":295}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=pptx-structural-audit facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c1502c84a2e840f3358924e354b8f8baef2f90c2684fa660fd2ecbf8c804afe1 -->
**主题色外置到 lock 便于换肤，但视觉验收仍需人工/Agent**
设计推断（非作者历史意图）：

收益：summary_band 的期望填充色来自锁文件而非硬编码，重主题化 deck 不需要修改检查。成本：docstring 明确视觉 contact sheet 仍需 Agent 目检，脚本只覆盖结构与可读性维度。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L2–L7](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py#L2-L7), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L268–L274](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py#L268-L274)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":7,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py","sha256":"9d061ca6a53ff56dfef15f19bbc9b29bc3813308dba2eb10f173b4b9de4ae63e","start":2},{"end":274,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py","sha256":"458cf922de9380303329cb9f8aaf63a54b7baaf9e3e9ae401aec050ae8565129","start":268}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=pptx-structural-audit facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=69721edda240c75e53836daccc0d48c575cd86a164ed2c0340a047b69cf2c14c -->
**main() 以位置参数 pptx 加 --template/--lock/--evidence-plan 选项运行，有 error 时返回 1**
main() 声明位置参数 pptx 与可选 --template、--lock、--evidence-plan（后者启用论文图来源注检查）；日志走 stderr。结束时 emit 汇总 error/warning 数与 slides/masters/layouts/font_min_pt，并 `return 1 if report["errors"] else 0`（这是 main 的返回值，非进程退出码的直接证明）。audit() 前置条件：pptx 路径不存在时抛 FileNotFoundError；传入 --lock 时按 UTF-8 JSON 读取锁文件。zip 内缺 [Content_Types].xml、ppt/presentation.xml、ppt/_rels/presentation.xml.rels 任一部件即追加 error。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L494–L503](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py#L494-L503), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L528–L534](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py#L528-L534), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L292–L308](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py#L292-L308)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":503,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py","sha256":"a6e45554af430e64103ab1896cfa1223eb6e7ac0a40fa4b2442a6889331cdcbb","start":494},{"end":534,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py","sha256":"ad506ad1c807e464c344d3d825e9241fb24f98850e614fd3435af14669ca434a","start":528},{"end":308,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py","sha256":"db96a96d2592a5f3485864dc187b01604e479af0aa33988a53d42d065a1b0934","start":292}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=pptx-structural-audit facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=91d36cdc564227ad6b5c20ea7687a6fb90e84faf8d1195f1742d770ede00df71 -->
**文档化手动验证：带 --evidence-plan 运行 audit_pptx.py，缺“来源：…”文本时 error 并以退出码 1 结束（NOT EXECUTED）**
文档中的人工验收步骤（本轮未执行）：

quality-gates.md 的“常用命令”给出具体操作：`python scripts/audit_pptx.py output.pptx --template references/template.pptx --lock execution-lock.json --evidence-plan evidence-plan.json --report qa/structure.json`，并记录预期结果：--evidence-plan 打开论文图来源硬校验，按图片字节哈希定位嵌入论文原图的页面，该页若无 addSourceNote 画出的“来源：…”文本则报 error 并以退出码 1 结束。此为文档记载的步骤，本次未执行；提供的输入中无针对该脚本的自动化测试。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/base/quality-gates.md:L97–L110](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/base/quality-gates.md#L97-L110)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":110,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/base/quality-gates.md","sha256":"35ea38d8ee01e03dd66dd576afda1965b7d5683a2439b3db8ab35b8ef1153612","start":97}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
