---
title: "一键成片流水线与质量门禁（finalize_deck.py）"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L100-L115, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L192-L197, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L104-L115, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L123-L130, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/merge_slides.py:L439-L449, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/merge_slides.py:L85-L122, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/merge_slides.py:L168-L212, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/fill_cover.py:L145-L181, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/make_blank_template.py:L11-L29, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L132-L163, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L60-L66, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L165-L188]
feature: "ppt-deck-finalize"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py", "jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/make_blank_template.py", "jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/fill_cover.py", "jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/opc/prune.py", "jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/merge_slides.py"]
---

# 一键成片流水线与质量门禁（finalize_deck.py）

<!-- kb:knowledge owner=feature-ppt-deck-finalize facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**命令行入口与输出契约**

`finalize_deck.py content.pptx out.pptx` 是公开入口：接收生成的 PptxGenJS 内容 PPTX 与输出路径，可选 `--template`、`--order`、`--cover-title`、`--cover-meta`、`--keep-workdir` 等参数。程序输出走 stdout、诊断走 stderr，两条流都经 logging 以纯 `%(message)s` 格式输出，便于下游解析。致命错误由 `FinalizeError` 表达，仅在 `main()` 入口转为带错误信息的 `SystemExit`，保持辅助函数可作库使用；成功时最终打印 `finalize_deck: OK`。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L100–L115](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py#L100-L115), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L192–L197](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py#L192-L197)

<!-- kb:knowledge owner=feature-ppt-deck-finalize facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**实际参数与默认值**

主要设置：`--template` 默认 `references/template.pptx`（相对技能根）；`--order` 默认 `"t1,s*,t5"`（模板封面 + 全部内容页 + 模板结尾），`s*` 在运行时展开为 s1..sN；`--template-layout` 默认 `slideLayout7.xml`（注意 merge_slides.py 自身的同名默认是 `slideLayout6.xml`，仅当通过 finalize_deck 调用时才是 7）；`--source-layout-mode` 取 `template`/`source`，默认 `template`。另有一致性约束：任务产物（content 与 out）不得位于技能目录内，否则直接报错。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L104–L115](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py#L104-L115), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L123–L130](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py#L123-L130), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/merge_slides.py:L439–L449](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/merge_slides.py#L439-L449)

<!-- kb:knowledge owner=feature-ppt-deck-finalize facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**支持行为与协作组件**

端到端支持：模板封面/结尾混排、跨画布坐标缩放（`scale_slide_xml` 调整 off/ext/chOff/字号/线宽）、图表与内嵌工作簿改名复制（规避 pptxgenjs 与模板同号 chart1.xml 冲突）、pptxgenjs 图表 XML 的 schema 修正（dPt/dLbls 顺序、悬空 axId）。封面填充由 `fill_cover.py` 完成：替换 ctrTitle 段落 runs、向 idx=1 占位符的 部门/汇报人/日期 标签后追加值。模板由 `make_blank_template.py` 生成，t1–t5 五页结构（封面/目录/两张空白/结尾），封面标题刻意留空并带 `<a:pPr>`，供 fill_cover 写入。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/merge_slides.py:L85–L122](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/merge_slides.py#L85-L122), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/merge_slides.py:L168–L212](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/merge_slides.py#L168-L212), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/fill_cover.py:L145–L181](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/fill_cover.py#L145-L181), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/make_blank_template.py:L11–L29](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/make_blank_template.py#L11-L29)

<!-- kb:knowledge owner=feature-ppt-deck-finalize facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**Orchestrated pipeline over unpacked OOXML intermediates**

finalize_deck.py is a process-level orchestrator: it unpacks the template and the generated content PPTX into a throwaway temp dir via subprocess calls to opc/unpack.py, expands the --order tokens (s* becomes s1..sN based on counted source slides), then runs merge_slides.py, optionally fill_cover.py, opc/prune.py and opc/pack.py, repacking into the final PPTX. Each child step runs via run(), which re-raises any non-zero exit as FinalizeError pointing at --keep-workdir for debugging; workdir is removed in a finally block unless kept. After packing, control returns to finalize_deck itself for post-hoc quality gates computed by reading the output zip (digest, cover_title_filled).

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L132–L163](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py#L132-L163), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L60–L66](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py#L60-L66), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py:L165–L188](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/finalize_deck.py#L165-L188)

