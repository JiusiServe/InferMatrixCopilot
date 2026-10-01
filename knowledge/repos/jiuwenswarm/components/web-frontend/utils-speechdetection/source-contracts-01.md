---
title: "utils-speechdetection 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# utils-speechdetection 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/speechDetection/silero.worker.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=86e02a4caadf5e2c5d789ef513e8c022b123ba946a75352478ffdfd2d23ffd0c -->
**`jiuwenswarm/channels/web/frontend/src/utils/speechDetection/silero.worker.ts`**

- 源码声明的类型、组件或调用边界：`scope`, `session`, `state`, `sampleRate`, `pending`, `gate`, `initialize`, `processAudio`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import * as ort from 'onnxruntime-web/wasm';`；`import modelUrl from '../../../node_modules/@ricky0123/vad-web/dist/silero_vad_v5.onnx?url';`；`import wasmUrl from '../../../node_modules/onnxruntime-web/dist/ort-wasm-simd-threaded.wasm?url';`；`import wasmModuleUrl from '../../../node_modules/onnxruntime-web/dist/ort-wasm-simd-threaded.mjs?url`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/speechDetection/silero.worker.ts#L1-L77)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/speechDetection/sileroVad.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a53b239353d048f15ec0e0420a2f3538ecc00b2a06e027b19b09762a6f4124d8 -->
**`jiuwenswarm/channels/web/frontend/src/utils/speechDetection/sileroVad.ts`**

- 源码声明的类型、组件或调用边界：`SileroVad`, `worker`, `timeout`, `fail`, `starting`, `latencyMs`, `inferenceMs`, `detection`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { SpeechDetection } from './speechGate';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/speechDetection/sileroVad.ts#L1-L176)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/speechDetection/speechGate.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b8eec58bb1962815d4f4ee658e9bf5a78ce36aa5f90d06d1fe377d4209704ee8 -->
**`jiuwenswarm/channels/web/frontend/src/utils/speechDetection/speechGate.ts`**

- 源码声明的类型、组件或调用边界：`SpeechDetection`, `SpeechGate`, `speech`, `state`, `confirmedFrames`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/speechDetection/speechGate.ts#L1-L57)。
<!-- /kb:file -->
