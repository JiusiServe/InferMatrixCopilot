---
title: "PPT 系统架构图原生形状渲染引擎：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/components.js:L1733-L1736, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/components.js:L17-L21, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/components.js:L1722-L1737, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/system-diagram.js:L797-L802, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/components.js:L10-L13, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/components/diagrams.js:L4-L17, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/system-diagram.js:L145-L158, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/components.js:L1728-L1737, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/system-diagram.js:L1-L10]
feature: "ppt-system-diagram-renderer"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/system-diagram.js"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/system-diagram.js", "jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/components.js"]
---

# PPT 系统架构图原生形状渲染引擎：实现深读

[功能概览](feature-ppt-system-diagram-renderer.md) · [owner 入口](_index.md)

<!-- kb:depth feature=ppt-system-diagram-renderer facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2be50fe17e83602cbb76d95758decebd3ab52254f4d4d2f4db73a2a97ff333a7 -->
**addSystemDiagram 按区域宽度选 density 后调用 renderSystemDiagram 画原生形状**
components.js 的 addSystemDiagram(pres, slide, {spec, x=0.5, y=1.05, w=9.0, h=3.6, density, heading}) 先校验 slide 并警告区域重叠；可选 heading 先画标题并从 h 中扣减标题高度；density 缺省时按宽度选 full(w>=8)/split(w>=4)/compact，把对应 fontMin/fontMax 合入 DEFAULT_THEME 后调用 system-diagram.js 的 renderSystemDiagram，返回布局描述符 {bounds, nodes, groups, edgeLabels, warnings}。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/components.js:L1728–L1737](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/components.js#L1728-L1737), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/system-diagram.js:L1–L10](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/system-diagram.js#L1-L10)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1737,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/components.js","sha256":"9b4be58da847d77fd7bc54bd7ccbd74fd6960239aff97c86270bc38be17bc64f","start":1728},{"end":10,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/system-diagram.js","sha256":"c659732132481837595ac205366639c38ca3f5db6e21cee56e18cdb4b06ed9f5","start":1}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-system-diagram-renderer facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1278a4c84d46c35aefe6ff7d7e376cc7729b7b880b4486716ea4afe0fcf5fc74 -->
**addSystemDiagram 契约：区域默认 (0.5, 1.05, 9.0, 3.6)，返回布局描述符**
签名 addSystemDiagram(pres, slide, { spec, x=0.5, y=1.05, w=9.0, h=3.6, density, heading })；调用方传入 Diagram IR spec，density 缺省按宽度自动选择，返回引擎布局描述符 { bounds, nodes, groups, edgeLabels, warnings } 供 QA 与 diagram-verifier 不重解析 PPTX 即可检查几何。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/components.js:L1722–L1737](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/components.js#L1722-L1737), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/system-diagram.js:L797–L802](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/system-diagram.js#L797-L802)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1737,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/components.js","sha256":"282495244d2747c45f9d4bc8b6615ddddd017c5091ac32182f2b0772288bc272","start":1722},{"end":802,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/system-diagram.js","sha256":"0cfff0b5428fc927d098b2b8cef05acda80b8c5b55d5345df702b190df294eb6","start":797}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-system-diagram-renderer facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=52c0d459e6b493cae50e3d3162cb1f18feb5aeb8a0098d53767688756ee37938 -->
**density 省略时按区域宽度自动选择：w>=8 为 full，w>=4 为 split，否则 compact**
默认区域 w=9.0 落入 full（fontMin 7 / fontMax 13）；split 限 6.5–11，compact 限 6–9.5；显式传入未知 density 时回退 DIAGRAM_DENSITY.full。字体制数覆盖 DEFAULT_THEME 同名字段。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/components.js:L1733–L1736](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/components.js#L1733-L1736), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/components.js:L17–L21](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/components.js#L17-L21)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1736,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/components.js","sha256":"bd98033f127b5d8f9eb907c96a9078ef9adf48aa787c34f7510827cf438de5a5","start":1733},{"end":21,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/components.js","sha256":"629b0f67856047222625dfac02f45cd79e9b548893674c93ef78ae5503b4d564","start":17}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-system-diagram-renderer facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=31ff1b5ff51c67c2ed8b7bb3e94f57fe204b6cd5ba8eaf150b1bb34f4c8ba85f -->
**components.js 同级 require system-diagram.js，diagrams.js 从 components.js 转口 API**
components.js 通过 require(path.join(__dirname, "system-diagram.js")) 取得渲染引擎并（经 addSystemDiagram 与构造器）供外部使用；components/diagrams.js 仅 require ../scripts/components.js 并转口 addSystemDiagram、addPipelineDiagram 等及 item/group/bandNode/groupBand，不导出 renderSystemDiagram 或 DEFAULT_THEME。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/components.js:L10–L13](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/components.js#L10-L13), [jiuwenswarm/resources/agent/workspace/skills/ppt-creation/components/diagrams.js:L4–L17](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/components/diagrams.js#L4-L17)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":13,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/components.js","sha256":"16e9d37b422761b8925ad55c9179d459c043d41c89cd4c594b79ef8704d9238e","start":10},{"end":17,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/components/diagrams.js","sha256":"71c0f9a037a6bea29236f974ab2e04c782de81bb13b651c8456d3e00d18d904d","start":4}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ppt-system-diagram-renderer facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=eb592ee1cd6ad1a043f7cfa7edf5125e3bbc5dcd76444625364282a4d0b65474 -->
**fail loud 拒绝 left_to_right：换取可测量性，代价是既有调用方必须改写**
实现注释（L145–L150）解释 left_to_right 被移除是因该路径不测量内容、top_to_bottom 装不下时报 OVER-CAPACITY 会把作者推向宽松路径，故选择 fail loud 并在错误中指引改用 addPipelineDiagram；代价是使用该 orientation 的调用方直接得到异常、需删字段或换 API。此取舍叙述来自源码注释，属实现的既述理由。

来源：[jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/system-diagram.js:L145–L158](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/system-diagram.js#L145-L158)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":158,"path":"jiuwenswarm/resources/agent/workspace/skills/ppt-creation/scripts/system-diagram.js","sha256":"41f06c7c5aabe349017e9f91c4958b2651f0360686678791e458de91e68e61b9","start":145}],"trace":[]} -->
<!-- /kb:depth -->
