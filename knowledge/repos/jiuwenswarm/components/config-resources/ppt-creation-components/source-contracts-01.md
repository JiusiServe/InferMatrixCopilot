---
title: "ppt-creation-components 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# ppt-creation-components 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/ppt-creation/components/brand.js pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=631e94c43011914e29b0531d047bdb1dab957a926deabdbeab1eaad1c0dca7b9 -->
**`jiuwenswarm/resources/agent/workspace/skills/ppt-creation/components/brand.js`**

- 源码声明的类型、组件或调用边界：`C`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`const C = require("../scripts/components.js");`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/components/brand.js#L1-L18)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/ppt-creation/components/charts.js pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e708ff2e159e54d96ab94b4f11d2e01d06d7d7199532872e4eaac7d5333bb6ca -->
**`jiuwenswarm/resources/agent/workspace/skills/ppt-creation/components/charts.js`**

- 源码声明的类型、组件或调用边界：`C`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`const C = require("../scripts/components.js");`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/components/charts.js#L1-L12)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/ppt-creation/components/content.js pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ae152a556a7dcc2588d8aa5b433d61346bbdbc86980755c480a5a7a89f6acdcf -->
**`jiuwenswarm/resources/agent/workspace/skills/ppt-creation/components/content.js`**

- 源码声明的类型、组件或调用边界：`C`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`const C = require("../scripts/components.js");`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/components/content.js#L1-L18)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/ppt-creation/components/diagrams.js pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b0be4e864ffcf3f16164610164a61357fed91e0b5f5542c8bdf9e7d66da7b9cc -->
**`jiuwenswarm/resources/agent/workspace/skills/ppt-creation/components/diagrams.js`**

- 源码声明的类型、组件或调用边界：`C`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`const C = require("../scripts/components.js");`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/components/diagrams.js#L1-L17)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/ppt-creation/components/index.js pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a3a0619537f572ca7e3f5e7c02444a523728dc33929547019dc769cea31510b3 -->
**`jiuwenswarm/resources/agent/workspace/skills/ppt-creation/components/index.js`**

- 集成边界的导入/加载声明：`...require("./brand.js"),`；`...require("./charts.js"),`；`...require("./diagrams.js"),`；`...require("./content.js"),`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/ppt-creation/components/index.js#L1-L9)。
<!-- /kb:file -->
