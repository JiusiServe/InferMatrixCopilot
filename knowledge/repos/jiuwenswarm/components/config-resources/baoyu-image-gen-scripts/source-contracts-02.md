---
title: "baoyu-image-gen-scripts 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# baoyu-image-gen-scripts 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/google.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=23e96272d7ac27e299cb60b307fdce67f6179b23c29f7596bc60830f4bb4f6df -->
**`jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/google.ts`**

- 源码声明的类型、组件或调用边界：`GOOGLE_MULTIMODAL_MODELS`, `GOOGLE_IMAGEN_MODELS`, `getDefaultModel`, `normalizeGoogleModelId`, `isGoogleMultimodal`, `normalized`, `isGoogleImagen`, `normalized`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import path from "node:path";`；`import { readFile } from "node:fs/promises";`；`import { execFileSync } from "node:child_process";`；`import type { CliArgs } from "../types";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/google.ts#L1-L351)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/jimeng.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3c1eb52daa42a4dc7099c8c28c31119742e3cdad8fabee9f8ef8ece4a3627a4c -->
**`jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/jimeng.ts`**

- 源码声明的类型、组件或调用边界：`JimengSizePreset`, `getDefaultModel`, `getAccessKey`, `getSecretKey`, `getRegion`, `getBaseUrl`, `resolveEndpoint`, `baseUrl`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { CliArgs } from "../types";`；`import * as crypto from "node:crypto";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/jimeng.ts#L1-L467)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/minimax.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=733adc9d5a70a68b12e149e3d442f43cda3a5171e09ade14e61678b0893fa817 -->
**`jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/minimax.ts`**

- 源码声明的类型、组件或调用边界：`DEFAULT_MODEL`, `MAX_REFERENCE_IMAGE_BYTES`, `SUPPORTED_ASPECT_RATIOS`, `MinimaxSubjectReference`, `MinimaxRequestBody`, `MinimaxResponse`, `getDefaultModel`, `getApiKey`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import path from "node:path";`；`import { readFile } from "node:fs/promises";`；`import type { CliArgs } from "../types";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/minimax.ts#L1-L220)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/openai.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ce366d8daa59cc5714b256fab2680712a595b2ccb368ed11ca8829b7fba76490 -->
**`jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/openai.ts`**

- 源码声明的类型、组件或调用边界：`getDefaultModel`, `OpenAIImageResponse`, `parseAspectRatio`, `match`, `w`, `h`, `SizeMapping`, `OpenAIGenerationsBody`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import path from "node:path";`；`import { readFile } from "node:fs/promises";`；`import type { CliArgs, OpenAIImageApiDialect } from "../types";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/openai.ts#L1-L444)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/openrouter.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b951904b3e8dda81ae4248944a48efce3c0fc9b42796f77ca05f4edc3ffd702b -->
**`jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/openrouter.ts`**

- 源码声明的类型、组件或调用边界：`DEFAULT_MODEL`, `COMMON_ASPECT_RATIOS`, `GEMINI_EXTENDED_ASPECT_RATIOS`, `OpenRouterImageEntry`, `OpenRouterMessagePart`, `OpenRouterResponse`, `getDefaultModel`, `normalizeModelId`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import path from "node:path";`；`import { readFile } from "node:fs/promises";`；`import type { CliArgs } from "../types";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/openrouter.ts#L1-L372)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/replicate.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f4b90d2a71b4fa285e1e9fe1df84a15a4c50414d2d59a96c0ea6ac88a9459dd0 -->
**`jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/replicate.ts`**

- 源码声明的类型、组件或调用边界：`DEFAULT_MODEL`, `SYNC_WAIT_SECONDS`, `POLL_INTERVAL_MS`, `MAX_POLL_MS`, `DOCUMENTED_REPLICATE_ASPECT_RATIOS`, `ReplicateModelFamily`, `PixelSize`, `Seedream45Size`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import path from "node:path";`；`import { readFile } from "node:fs/promises";`；`import type { CliArgs } from "../types";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/replicate.ts#L1-L616)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/seedream.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=447379622c49cf4a2f3e1f00962d18a235e1b5027c0c90c33679eead092b5695 -->
**`jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/seedream.ts`**

- 源码声明的类型、组件或调用边界：`SeedreamModelFamily`, `SeedreamRequestImage`, `SeedreamRequestBody`, `SeedreamImageResponse`, `getDefaultModel`, `getApiKey`, `getBaseUrl`, `parsePixelSize`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import path from "node:path";`；`import { readFile } from "node:fs/promises";`；`import type { CliArgs } from "../types";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/seedream.ts#L1-L341)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/zai.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4a09f66f88306cede17c0ba95c5679e414568d7bc69bf318d5cb6b3f945a31c3 -->
**`jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/zai.ts`**

- 源码声明的类型、组件或调用边界：`ZaiModelFamily`, `ZaiRequestBody`, `ZaiResponse`, `DEFAULT_MODEL`, `GLM_MAX_PIXELS`, `LEGACY_MAX_PIXELS`, `GLM_SIZE_STEP`, `LEGACY_SIZE_STEP`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { CliArgs, Quality } from "../types";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/providers/zai.ts#L1-L306)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/types.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=29e4b89e5308fe6a68b1e0a7d11ebb0f56964531c357e7954e74139ca076d7b0 -->
**`jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/types.ts`**

- 源码声明的类型、组件或调用边界：`Provider`, `Quality`, `OpenAIImageApiDialect`, `ResponseFormat`, `CliArgs`, `BatchTaskInput`, `BatchFile`, `ExtendConfig`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/baoyu-image-gen/scripts/types.ts#L1-L97)。
<!-- /kb:file -->
