---
title: "baoyu-image-gen-scripts 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# baoyu-image-gen-scripts 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/build-batch.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=862adec8c58f3f1d63b7034558f0a32ca2ddc9e122b78e484f527f0067e81590 -->
**`jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/build-batch.ts`**

- 源码声明的类型、组件或调用边界：`CliArgs`, `OutlineEntry`, `PromptReference`, `printUsage`, `parseArgs`, `args`, `i`, `current`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import path from "node:path";`；`import process from "node:process";`；`import { readdir, readFile, writeFile } from "node:fs/promises";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/build-batch.ts#L1-L239)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/codex-imagegen/cache.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f742faae1d97dabeeb99509774c32a7b990fac67a31264e1bb619451228c9e82 -->
**`jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/codex-imagegen/cache.ts`**

- 源码声明的类型、组件或调用边界：`cacheKey`, `h`, `r`, `lookupCache`, `entry`, `s`, `storeCache`, `entry`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { createHash } from "node:crypto";`；`import { mkdir, readFile, writeFile, copyFile, stat } from "node:fs/promises";`；`import { existsSync, openSync, closeSync } from "node:fs";`；`import path from "node:path";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/codex-imagegen/cache.ts#L1-L80)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/codex-imagegen/logger.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b14a85eda394c93d3821016cb0429a97b41b1989ee51309972095f5667587274 -->
**`jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/codex-imagegen/logger.ts`**

- 源码声明的类型、组件或调用边界：`LogEntry`, `JsonLogger`, `entry`, `line`, `jsonExtras`, `entries`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { appendFile, mkdir } from "node:fs/promises";`；`import path from "node:path";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/codex-imagegen/logger.ts#L1-L39)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/codex-imagegen/main.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ecf2ae088ed8f4c932e386813d454d44f8bcc0b36d031dc9e977b96b7de6189d -->
**`jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/codex-imagegen/main.ts`**

- 源码声明的类型、组件或调用边界：`CliOptions`, `HELP`, `SHELL_METACHAR`, `log`, `result`, `err`, `out`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { readFile, mkdir, copyFile, stat } from "node:fs/promises";`；`import { homedir } from "node:os";`；`import path from "node:path";`；`import process from "node:process";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/codex-imagegen/main.ts#L1-L332)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/codex-imagegen/parser.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b81cd7b9e720e4f2a19c35a9694c9da03ff942bd3e6c475d8ac15de77c62ba9f -->
**`jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/codex-imagegen/parser.ts`**

- 源码声明的类型、组件或调用边界：`parseEventStream`, `lines`, `threadId`, `agentMessage`, `usage`, `toolCallsById`, `line`, `event`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { CodexRunResult, ToolCall, TokenUsage } from "./types.ts";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/codex-imagegen/parser.ts#L1-L64)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/codex-imagegen/spawn.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=db923773ab1666771d66dfdd34141ca8875c13e9e58d16d15d1df5404c25f4e3 -->
**`jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/codex-imagegen/spawn.ts`**

- 源码声明的类型、组件或调用边界：`CodexRunResult`, `SpawnInput`, `runCodexExec`, `start`, `logDir`, `rawLogPath`, `args`, `img`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { spawn } from "node:child_process";`；`import { writeFile, mkdtemp } from "node:fs/promises";`；`import { tmpdir } from "node:os";`；`import path from "node:path";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/codex-imagegen/spawn.ts#L1-L81)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/codex-imagegen/types.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9972556623578074f0525eb6e7318879023229dfaba77d4c938638fd137accc3 -->
**`jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/codex-imagegen/types.ts`**

- 源码声明的类型、组件或调用边界：`CliOptions`, `ToolCall`, `TokenUsage`, `CodexRunResult`, `GenerateResult`, `ErrorKind`, `RETRYABLE`, `GenError`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/codex-imagegen/types.ts#L1-L79)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/codex-imagegen/validator.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=13ac88957471aff97ea654e9d971eaa10f395a1e664b9b76651cdea852399bba -->
**`jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/codex-imagegen/validator.ts`**

- 源码声明的类型、组件或调用边界：`PNG_MAGIC`, `codexHome`, `verifyImageGenWasInvoked`, `dir`, `entries`, `pngs`, `hasImageGenEvidence`, `verifyOutput`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { stat, readdir } from "node:fs/promises";`；`import { homedir } from "node:os";`；`import path from "node:path";`；`import { GenError } from "./types.ts";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/codex-imagegen/validator.ts#L1-L56)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/main.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f49d4e1a6165a63ac7146e28d85c8c58fe26b3e82608c5f7ab9fac1c24ec6ea2 -->
**`jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/main.ts`**

- 源码声明的类型、组件或调用边界：`ProviderModule`, `PreparedTask`, `TaskResult`, `ProviderRateLimit`, `LoadedBatchTasks`, `MAX_ATTEMPTS`, `DEFAULT_MAX_WORKERS`, `POLL_WAIT_MS`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import path from "node:path";`；`import process from "node:process";`；`import { homedir } from "node:os";`；`import { fileURLToPath } from "node:url";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/main.ts#L1-L1293)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/agnes.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=df8000b02304ae792759be1b2db9e8cb01aaa79c1c65f58be183baca1dd101fb -->
**`jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/agnes.ts`**

- 源码声明的类型、组件或调用边界：`DEFAULT_MODEL`, `DEFAULT_BASE_URL`, `DEFAULT_SIZE`, `AgnesResponse`, `getDefaultModel`, `getApiKey`, `key`, `getBaseUrl`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { readFile } from "node:fs/promises";`；`import path from "node:path";`；`import type { CliArgs } from "../types";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/agnes.ts#L1-L175)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/azure.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d7ceef31d30259dcbf095d508fb0655b2e1682eb14542716313b31aa35c945a6 -->
**`jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/azure.ts`**

- 源码声明的类型、组件或调用边界：`OpenAIImageResponse`, `AzureEndpoint`, `DEFAULT_AZURE_API_VERSION`, `AZURE_EDIT_IMAGE_EXTENSIONS`, `parseAzureBaseURL`, `parsed`, `trimmedPath`, `deploymentMatch`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import path from "node:path";`；`import { readFile } from "node:fs/promises";`；`import type { CliArgs } from "../types";`；`import { getOpenAISize, extractImageFromResponse } from "./openai.ts";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/azure.ts#L1-L192)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/codex-cli.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a15684ad788e4059183365fe9c9c7a15bbcceced5cf80f32050a62b342353201 -->
**`jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/codex-cli.ts`**

- 源码声明的类型、组件或调用边界：`PROVIDER_FILE`, `SCRIPTS_DIR`, `BUNDLED_WRAPPER`, `WrapperOkResult`, `WrapperErrorResult`, `WrapperResult`, `getDefaultModel`, `getDefaultOutputExtension`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import path from "node:path";`；`import { spawn } from "node:child_process";`；`import { fileURLToPath } from "node:url";`；`import { tmpdir } from "node:os";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/codex-cli.ts#L1-L197)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/dashscope.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=183aadfd6fda9acebede6f892c97c7ede176e5a67a04b5fbd3b937a30e3f6843 -->
**`jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/dashscope.ts`**

- 源码声明的类型、组件或调用边界：`DashScopeModelFamily`, `DashScopeModelSpec`, `DEFAULT_MODEL`, `MIN_QWEN_2_TOTAL_PIXELS`, `MAX_QWEN_2_TOTAL_PIXELS`, `SIZE_STEP`, `QWEN_NEGATIVE_PROMPT`, `QWEN_2_TARGET_PIXELS`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import path from "node:path";`；`import { readFile } from "node:fs/promises";`；`import type { CliArgs, Quality } from "../types";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/dashscope.ts#L1-L625)。
<!-- /kb:file -->
