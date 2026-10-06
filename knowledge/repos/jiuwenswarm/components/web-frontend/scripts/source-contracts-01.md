---
title: "scripts 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: []
---

# scripts 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=10b308cfe6f4b431c0575b1dc433fcbbe007d8d67a719888865f87084c872d3c -->
**`jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs`**

- 源码声明的类型、组件或调用边界：`cwd`, `git`, `args`, `base`, `repoRoot`, `prefix`, `changed`, `eslint`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { execFileSync } from 'node:child_process';`；`import { readFile } from 'node:fs/promises';`；`import path from 'node:path';`；`import { fileURLToPath } from 'node:url';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/scripts/lint-changed.mjs#L1-L81)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/scripts/test-a2ui-action-defaults.mjs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e1e0e5029bdf6158815b5bcbe01e8321d48bf3fa85a991cf1b69ff8864f308ce -->
**`jiuwenswarm/channels/web/frontend/scripts/test-a2ui-action-defaults.mjs`**

- 源码声明的类型、组件或调用边界：`root`, `sourceUrl`, `helperUrl`, `tempDir`, `transpileTsModule`, `source`, `transpiled`, `outputPath`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import assert from 'node:assert/strict';`；`import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';`；`import { tmpdir } from 'node:os';`；`import { join } from 'node:path';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/scripts/test-a2ui-action-defaults.mjs#L1-L541)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/scripts/test-a2ui-interaction-guards.mjs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=46ec5cfe95c850fade1fa3d05c8db19ba246630e82382648ad769bf875e57a54 -->
**`jiuwenswarm/channels/web/frontend/scripts/test-a2ui-interaction-guards.mjs`**

- 源码声明的类型、组件或调用边界：`root`, `tempDir`, `moduleMap`, `rewriteLocalImports`, `transpileTsModule`, `sourceUrl`, `source`, `transpiled`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import assert from 'node:assert/strict';`；`import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';`；`import { tmpdir } from 'node:os';`；`import { join } from 'node:path';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/scripts/test-a2ui-interaction-guards.mjs#L1-L150)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/scripts/test-input-area-permission-merge.mjs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c882685b1a6554a18d895e1d86d26ba5e8aae45b39946a8108ef6c77a5b9e2ff -->
**`jiuwenswarm/channels/web/frontend/scripts/test-input-area-permission-merge.mjs`**

- 源码声明的类型、组件或调用边界：`root`, `result`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { build } from 'esbuild';`；`import { spawnSync } from 'node:child_process';`；`import { fileURLToPath } from 'node:url';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/scripts/test-input-area-permission-merge.mjs#L1-L57)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/scripts/test-permission-answer-transport.mjs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5f25cc83d69c4de9cadf8554159771444fc9904988c4a05062bb081732ce3da1 -->
**`jiuwenswarm/channels/web/frontend/scripts/test-permission-answer-transport.mjs`**

- 源码声明的类型、组件或调用边界：`root`, `result`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { build } from 'esbuild';`；`import { spawnSync } from 'node:child_process';`；`import { fileURLToPath } from 'node:url';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/scripts/test-permission-answer-transport.mjs#L1-L35)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/scripts/test-project-create-error-localization.mjs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=88758ab6957861464009025149da9b1fcb421a6087aa133305d86f90846ec055 -->
**`jiuwenswarm/channels/web/frontend/scripts/test-project-create-error-localization.mjs`**

- 源码声明的类型、组件或调用边界：`sourcePath`, `source`, `compiled`, `moduleUrl`, `zh`, `en`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import assert from 'node:assert/strict';`；`import { readFile } from 'node:fs/promises';`；`import { transform } from 'esbuild';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/scripts/test-project-create-error-localization.mjs#L1-L32)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/scripts/test-skill-package-prompt.mjs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=17f766f9d7c8c715658cec7bad39bd119931242b33495a33fac046e3057c1495 -->
**`jiuwenswarm/channels/web/frontend/scripts/test-skill-package-prompt.mjs`**

- 源码声明的类型、组件或调用边界：`root`, `result`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { build } from 'esbuild';`；`import { spawnSync } from 'node:child_process';`；`import { fileURLToPath } from 'node:url';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/scripts/test-skill-package-prompt.mjs#L1-L33)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/scripts/test-team-a2ui-render-path.mjs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b8a58631303ca8e3333c21a335aeedc11a13e689fbad3898c3597c33a07f7e01 -->
**`jiuwenswarm/channels/web/frontend/scripts/test-team-a2ui-render-path.mjs`**

- 源码声明的类型、组件或调用边界：`root`, `sourceUrl`, `source`, `between`, `start`, `end`, `teamLeaderRenderer`, `teamEventBranch`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import assert from 'node:assert/strict';`；`import { readFile } from 'node:fs/promises';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/scripts/test-team-a2ui-render-path.mjs#L1-L65)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/scripts/generate-agent-folders.js pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=92fe2b6266246a458d9d5871ea4a7645502923067fc15f378d455aa4825b126e -->
**`jiuwenswarm/scripts/generate-agent-folders.js`**

- 源码声明的类型、组件或调用边界：`fs`, `path`, `scriptDir`, `envRoot`, `agentFromEnv`, `packageAgentFromResources`, `agentRoot`, `outputPath`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`const fs = require('fs');`；`const path = require('path');`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/scripts/generate-agent-folders.js#L1-L112)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/scripts/watch-folders.js pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=73c7e6c086512c07a4b7038fa1bbf58a57721155ae4d9e0585982cdcecbcb01b -->
**`jiuwenswarm/scripts/watch-folders.js`**

- 源码声明的类型、组件或调用边界：`path`, `generate`, `child`, `chokidar`, `envWorkspace`, `homeDir`, `userAgentDir`, `fallbackRepoAgentDir`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`const { spawn } = require('child_process');`；`const path = require('path');`；`const chokidar = require('chokidar');`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/scripts/watch-folders.js#L1-L48)。
<!-- /kb:file -->
