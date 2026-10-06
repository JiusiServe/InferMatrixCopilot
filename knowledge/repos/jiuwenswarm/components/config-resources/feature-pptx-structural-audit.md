---
title: "PPTX 结构与可读性审计脚本（audit_pptx.py 及配套 QA 脚本）"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L511-L534, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_density.py:L9-L18, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_geometry.py:L459-L482, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L494-L534, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_density.py:L67-L111, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L303-L313, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_geometry.py:L1-L13, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_geometry.py:L229-L253, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_geometry.py:L442-L452, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L303-L336, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L344-L381, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_geometry.py:L229-L279]
feature: "pptx-structural-audit"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py", "jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_density.py", "jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_geometry.py"]
---

# PPTX 结构与可读性审计脚本（audit_pptx.py 及配套 QA 脚本）

<!-- kb:knowledge owner=feature-pptx-structural-audit facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**验证入口**

所提供的输入中没有针对这三个脚本的测试文件或测试调用；可观察到的验证方式是脚本自身的退出码契约（audit_pptx.py、qa_density.py、qa_geometry.py 均在有 error 时返回 1）和结构化 JSON 报告（--report / --json），供流水线消费。qa_geometry.py 支持 --slide 单页复查，qa_density.py 的文档字符串展示了带 --lock 的流水线用法示例。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L511–L534](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py#L511-L534), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_density.py:L9–L18](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_density.py#L9-L18), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_geometry.py:L459–L482](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_geometry.py#L459-L482)

<!-- kb:knowledge owner=feature-pptx-structural-audit facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**命令行入口、退出码与输出通道**

三个脚本均以 main() 作为 CLI 入口：audit_pptx.py 接受位置参数 pptx 及 --template/--lock/--evidence-plan/--report 与三个字号阈值选项。退出码契约是"有 error 返回 1，否则 0"（audit_pptx.py L534、qa_density.py L111、qa_geometry.py L470/L482）。报告正文（含 --json 载荷）经独立 stdout logger 输出、诊断走 stderr；audit_pptx.py 的 --report 则把完整 JSON 报告写入指定文件（先建父目录），不经过 stdout。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L494–L534](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py#L494-L534), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_density.py:L67–L111](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_density.py#L67-L111), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_geometry.py:L459–L482](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_geometry.py#L459-L482)

<!-- kb:knowledge owner=feature-pptx-structural-audit facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**独立于生成代码的包级解析流水线**

三个脚本都直接用 zipfile + XML 解析打开 .pptx 包，不依赖生成代码，对任意 pptx 可运行：audit_pptx.py 用 ElementTree 读 presentation.xml 确定画布与幻灯片顺序，再逐页检查；qa_geometry.py 自述为补上人眼 contact sheet 看不见的 0.1 英寸级问题。分工上 audit_pptx.py 管包结构、模板继承计数、字号与锁契约，qa_density.py 管每页文字量，qa_geometry.py 管重叠/遮挡/越界/轴线。注意 qa_geometry.py 虽为 layout/master 继承元素设 z=-1000，但这些元素只喂给 check_duplicate_chrome，参与文字碰撞与遮挡检查的仍只是页面自身元素。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L303–L313](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py#L303-L313), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_geometry.py:L1–L13](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_geometry.py#L1-L13), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_geometry.py:L229–L253](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_geometry.py#L229-L253), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_geometry.py:L442–L452](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_geometry.py#L442-L452)

<!-- kb:knowledge owner=feature-pptx-structural-audit facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**检查项与跨脚本协作**

audit_pptx.py 检查必需包部件缺失、幻灯片关系指向的部件存在性；与 --template 对比时画布需精确相等，但 master/layout 数量只要求不少于模板（>=，非相等）。--evidence-plan 启用论文配图溯源：按图片字节 sha256 匹配（对 merge_slides.py 的重命名免疫），命中配图而页面文本无"来源/Source:"式来源注记则报 error。qa_geometry.py 的 check_duplicate_chrome 消费 layout/master 继承元素，抓"页面自绘页脚 + 母版继承页脚"叠加的重复 chrome，与 audit_pptx.py 中 footer_mode=master 的文本级检查互补。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L303–L336](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py#L303-L336), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py:L344–L381](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/audit_pptx.py#L344-L381), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_geometry.py:L229–L279](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/qa_geometry.py#L229-L279)

