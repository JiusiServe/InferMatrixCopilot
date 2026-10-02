---
title: "Python 与 TypeScript SDK：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:sdks/python/src/jiuwenswarm_sdk/client.py:L38-L61, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:sdks/python/src/jiuwenswarm_sdk/client.py:L240-L249, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:sdks/python/src/jiuwenswarm_sdk/client.py:L299-L325, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:sdks/python/src/jiuwenswarm_sdk/client.py:L327-L356]
---

# Python 与 TypeScript SDK：实现深读

[功能概览](feature-sdk.md) · [owner 入口](_index.md)

<!-- kb:depth feature=sdk facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ca5a46c5139e130ecc576adc3a5668360d3bf65bfe4583efdcc5185533047a6f -->
**Client 构造参数的真实默认值与校验**
Client.__init__ 默认 command=("jiuwenswarm-process",)、shutdown_grace_seconds=30、max_record_bytes=8 MiB；command 必须是非空 argv 序列（传入 shell 字符串或空序列抛 ValueError），env 非空时与 os.environ 合并覆盖。max_record_bytes 同时作为 create_subprocess_exec 的 limit，超限的输出记录触发 ProtocolError。

来源：[sdks/python/src/jiuwenswarm_sdk/client.py:L38–L61](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/python/src/jiuwenswarm_sdk/client.py#L38-L61), [sdks/python/src/jiuwenswarm_sdk/client.py:L240–L249](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/python/src/jiuwenswarm_sdk/client.py#L240-L249)

<!-- kb:depth-proof {"evidence":[{"path":"sdks/python/src/jiuwenswarm_sdk/client.py","start":38,"end":61,"sha256":"43b66d7a6f4bc35d66492f81a128427f6b35a7bd4b2a1213bb65a434c8646df9"},{"path":"sdks/python/src/jiuwenswarm_sdk/client.py","start":240,"end":249,"sha256":"eca98a8798b4a6af84b76cc81301280bf418897d873cc1b02735862c0af4c4cc"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=sdk facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ccfaa137e6fb021a26949f070fcd5967c4ca9425720fe8e2c0010af2c07b40e8 -->
**优雅关闭超时后的强制回收**
若子进程在 shutdown_grace_seconds（默认 30 秒）内未完成清理，_Invocation.close 捕获 TimeoutError 后调用 force_stop：Windows 用 taskkill /PID <pid> /T /F 杀掉整棵进程树，POSIX 用 killpg 向进程组发 SIGKILL，最后再对进程本身 kill 兜底。

来源：[sdks/python/src/jiuwenswarm_sdk/client.py:L299–L325](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/python/src/jiuwenswarm_sdk/client.py#L299-L325), [sdks/python/src/jiuwenswarm_sdk/client.py:L327–L356](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/python/src/jiuwenswarm_sdk/client.py#L327-L356)

<!-- kb:depth-proof {"evidence":[{"path":"sdks/python/src/jiuwenswarm_sdk/client.py","start":299,"end":325,"sha256":"9df19654bcf698167f0b36860ca9350bf1c389a859b91809897e2e7552677f47"},{"path":"sdks/python/src/jiuwenswarm_sdk/client.py","start":327,"end":356,"sha256":"fc32df7bf00016fd74e28587e7f0198ceea161123b32d0d4050e025c1d1d23ec"}],"trace":[]} -->
<!-- /kb:depth -->
