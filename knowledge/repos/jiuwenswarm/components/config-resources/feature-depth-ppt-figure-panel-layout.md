---
title: "PPT 图表面板布局引擎（figure-panel.js）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js:L1-L7, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js:L17-L21, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js:L34-L35, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js:L82-L101, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js:L42-L75, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js:L82-L88, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js:L26-L37, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js:L83-L87]
feature: "ppt-figure-panel-layout"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js"]
---

# PPT 图表面板布局引擎（figure-panel.js）：实现深读

[功能概览](feature-ppt-figure-panel-layout.md) · [owner 入口](_index.md)

<!-- kb:depth feature=ppt-figure-panel-layout facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=289e68c283e5e64597c9bbdc70841b4911b926219e922682844ed44b36b3b5e2 -->
**renderFigurePanel：读尺寸→layoutFigures 分行缩放→逐图贴图并按需加标签**
renderFigurePanel 对每个 figure 调 pngSize 得宽高比，layoutFigures 在 bounds.w×h 内分行并整体缩放，随后内容不足时垂直居中（oy），逐 rect 调 slide.addImage，仅当 f.label 存在才 slide.addText 居中中文标签，返回 layoutFigures 的结果。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js:L82–L101](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js#L82-L101)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":101,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js","sha256":"eba4a1fac821e8ffe0ec288014f882e94195c44ea50fbf9786a7fa6e83c27c34","start":82}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-figure-panel-layout facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8b93f90526b655c674c4057da0ee028203add23bc3450d8c791e266ea2d1a2e9 -->
**layoutFigures(figs, w, h) 纯几何返回 {rects, rows, scale, totalH}；renderFigurePanel({slide, figures, bounds})**
figs 需带 ar 字段；返回 rects（含 i,x,y,w,h,labelY，相对区域左上角）、行数 rows、scale=min(1, 可用高/自然高和)、累计 totalH。renderFigurePanel 只接 slide（无 pres 参数），figures 元素需 path 与可选 label，bounds 需 x,y,w,h，返回布局结果。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js:L42–L75](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js#L42-L75), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js:L82–L88](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js#L82-L88)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":75,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js","sha256":"edab8f9189ffe0cb23724cf3580c9df477cbd22d1f8c28cc27f829c3dd4f3335","start":42},{"end":88,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js","sha256":"5ee3bee8eef705a3171f6db96f32dc279a6a82806fa9c9bca6c1b634d734a177","start":82}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-figure-panel-layout facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=747ea29a541477fdd4bf94e5b03a8e9849c4ba50a0801a292db0e1c07a5b5fd4 -->
**非 PNG 或缺 IHDR 时同步 throw；文件描述符由 finally 保证关闭**
pngSize 先 openSync 再 try/finally closeSync；签名不是 0x89504e47 抛 `not a PNG: <path>`，offset 12–16 非 "IHDR" 抛 `not a PNG: missing IHDR: <path>`。异常沿 renderFigurePanel 同步上抛，无捕获分支。仅校验 24 字节头部，不证明完整 PNG 有效性。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js:L26–L37](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js#L26-L37), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js:L83–L87](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js#L83-L87)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":37,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js","sha256":"82989608c7114b85b74bdbb387acfa94e85ce304decfcf5b288f6d4e239e2e0c","start":26},{"end":87,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js","sha256":"7636ac016aaa3165473453306ce48d571f85e6fde6d97f4a336d65193b977248","start":83}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-figure-panel-layout facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e60936995a6a252b03076b14fd387125622f75df23749586b5f1ee04645250d0 -->
**全同步几何引擎换取可顺序调用；常量复制带来漂移风险（推断）**
设计推断（非作者历史意图）：

收益：全部同步使 slides.js 能按顺序调用组件、无需异步图片解码（注释明确此意图）。成本（推断）：LABEL_FONT/LABEL_COLOR 复制自 components.js 而非共享来源，两处可能不同步漂移；且 pngSize 只认 IHDR 在固定偏移的 PNG，其他图片格式直接抛错。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js:L1–L7](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js#L1-L7), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js:L17–L21](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js#L17-L21), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js:L34–L35](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js#L34-L35)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":7,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js","sha256":"7cba52ab467df06baec56a26becac01fcd37901612ecbc2fa80538b38ffb01bf","start":1},{"end":21,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js","sha256":"f07809fa1b601f5778759d3f3f389bd46c7ea07d0a3c5166eec023bda222a88e","start":17},{"end":35,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/figure-panel.js","sha256":"026b1e5be1d24f21ad95370568ffb69e986b44d970f1adaeb6fd0a5df8306325","start":34}],"trace":[]} -->
<!-- /kb:depth -->
