---
title: "skill-creator-normal-assets 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# skill-creator-normal-assets 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/assets/eval_review.html pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ce477dcc74dc1c0d1d3352646a79167b5a63634e936b1019160025065974e452 -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/assets/eval_review.html`**

- 源码声明的类型、组件或调用边界：`EVAL_DATA`, `evalItems`, `render`, `tbody`, `sorted`, `lastGroup`, `group`, `headerRow`；这是词法声明索引，不把局部变量当成对外导出 API。
- 页面装配边界：body, link, script 标签；资源装载与宿主连接取决于对应属性和脚本实现。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/assets/eval_review.html#L1-L146)。
<!-- /kb:file -->
