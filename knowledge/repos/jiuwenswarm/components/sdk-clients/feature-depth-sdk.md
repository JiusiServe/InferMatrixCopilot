---
title: "Python 与 TypeScript SDK：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:sdks/python/src/jiuwenswarm_sdk/client.py:L38-L61, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:sdks/python/src/jiuwenswarm_sdk/client.py:L240-L249, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:sdks/python/src/jiuwenswarm_sdk/client.py:L299-L325, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:sdks/python/src/jiuwenswarm_sdk/client.py:L327-L356, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:sdks/python/tests/test_client.py:L36-L42, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:sdks/python/src/jiuwenswarm_sdk/client.py:L128-L139, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:sdks/README.md:L121-L123, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:sdks/python/src/jiuwenswarm_sdk/client.py:L63-L99, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:sdks/python/src/jiuwenswarm_sdk/client.py:L101-L141, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:sdks/python/src/jiuwenswarm_sdk/client.py:L63-L80, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:sdks/python/src/jiuwenswarm_sdk/client.py:L111-L120, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:sdks/python/src/jiuwenswarm_sdk/client.py:L181-L194, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:sdks/python/src/jiuwenswarm_sdk/client.py:L316-L320, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:sdks/python/tests/test_client.py:L110-L113, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:sdks/python/tests/test_client.py:L19-L25]
feature: "sdk"
entry_points: ["sdks/python/src/jiuwenswarm_sdk/client.py"]
source_globs: ["sdks/python/src/jiuwenswarm_sdk/client.py", "sdks/*"]
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

<!-- kb:depth feature=sdk facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fb5675af093001eb5da060d3c352771709a47201d822b92f6481ec65235e639a -->
**Client.run→_execute：校验 deadline/request_id 后单次拉起 CLI 子进程**
run 复制 request 调 _execute(query=False)：deadline_seconds 非正或非有限抛 ValueError；补默认 schema_version/type/request_id 并要求非空字符串后 encode，经 create_subprocess_exec（stdin/stdout/stderr 三管道、limit=self.max_record_bytes）拉起 self.command 子进程；所示段内启动 OSError 包装为 TransportError，无重试。

来源：[sdks/python/src/jiuwenswarm_sdk/client.py:L63–L99](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/python/src/jiuwenswarm_sdk/client.py#L63-L99), [sdks/python/src/jiuwenswarm_sdk/client.py:L101–L141](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/python/src/jiuwenswarm_sdk/client.py#L101-L141)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":99,"path":"sdks/python/src/jiuwenswarm_sdk/client.py","sha256":"57b8f70726f9a5c70c055ecf1a21870ce79a70b7164db53163f8e17fea026399","start":63},{"end":141,"path":"sdks/python/src/jiuwenswarm_sdk/client.py","sha256":"a9374a971802cca8ecb14fc6a054f533acb7c52d87d4f7e3755bd6a19a1a2d6a","start":101}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=sdk facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=175c2d51df6e2f8a5b341310bd68066e838552f556a3d90b9af4373a3ecbc70f -->
**Client.run：单个 request Mapping 加仅关键字选项，deadline_seconds 必须为正有限值**
run 复制请求 Mapping（dict(request)）并以 query=False 转发仅关键字的 on_event/on_interaction/cancel/deadline_seconds；_execute 对非正或非有限的 deadline_seconds 抛 ValueError，再 setdefault schema_version、type 与 request_id。

来源：[sdks/python/src/jiuwenswarm_sdk/client.py:L63–L80](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/python/src/jiuwenswarm_sdk/client.py#L63-L80), [sdks/python/src/jiuwenswarm_sdk/client.py:L111–L120](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/python/src/jiuwenswarm_sdk/client.py#L111-L120)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":80,"path":"sdks/python/src/jiuwenswarm_sdk/client.py","sha256":"7d31dc4e90b1e53d45678b959f10c7e3a5af6f7fbb26550578c8107b0005346a","start":63},{"end":120,"path":"sdks/python/src/jiuwenswarm_sdk/client.py","sha256":"421cc6d7e656b0af3fd432f5f8a034aae697281fb2cef392798e58dd839ced52","start":111}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=sdk facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d120a5c1b511291736e7ef55bf11d17b4112de5c370db0fc2b943739e1609c08 -->
**_Invocation 持有 Records 与所属 Client，清理时读取 client.shutdown_grace_seconds 作超时**
_Invocation.__init__ 接收并保存 protocol 的 Records 与所属 Client；所示清理路径用 asyncio.timeout(self.client.shutdown_grace_seconds) 包住 drain_and_wait，TimeoutError 时 await force_stop。

来源：[sdks/python/src/jiuwenswarm_sdk/client.py:L181–L194](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/python/src/jiuwenswarm_sdk/client.py#L181-L194), [sdks/python/src/jiuwenswarm_sdk/client.py:L316–L320](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/python/src/jiuwenswarm_sdk/client.py#L316-L320)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":194,"path":"sdks/python/src/jiuwenswarm_sdk/client.py","sha256":"ba4bfa1659ee1d429dfdfd590dc07fefb02d87499f2df522be839a79f4982461","start":181},{"end":320,"path":"sdks/python/src/jiuwenswarm_sdk/client.py","sha256":"01662ba824a673cb946ebd38eb4cda220118a48b162dc61f1d0df57791788665","start":316}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=sdk facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0ab9d422fc051c0fa4cc0831d85674613497729a45d77e74fa9f538fcd6a870a -->
**每次调用新起进程的隔离收益与启动及慢宿主代价（推断）**
设计推断（非作者历史意图）：

每次调用新起进程（两次 query 断言 pid 不同）：收益是调用间状态隔离、无常驻 stdio 服务（推断）；代价是每次调用的进程启动开销，且慢宿主在 TS 端按 256 条待投递上限 fail closed、Python 靠管道背压（推断：以失败换取宿主保护）。

来源：[sdks/python/tests/test_client.py:L36–L42](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/python/tests/test_client.py#L36-L42), [sdks/python/src/jiuwenswarm_sdk/client.py:L128–L139](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/python/src/jiuwenswarm_sdk/client.py#L128-L139), [sdks/README.md:L121–L123](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/README.md#L121-L123)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":42,"path":"sdks/python/tests/test_client.py","sha256":"7edf962c23f8b625cc91aa5d8b5b154741cfe636a3c20bc13bd4f60e201dc509","start":36},{"end":139,"path":"sdks/python/src/jiuwenswarm_sdk/client.py","sha256":"42f5d0ef3b0091e70b5f6e2999426de6544280826b034f351602f983aa3d2f65","start":128},{"end":123,"path":"sdks/README.md","sha256":"a62e8342776c84335c9e6d1d7f278af07054cc9c2aaaa8240208f7892c180dc7","start":121}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=sdk facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b0776374156eaec8c482c7b506bf7c286df2492e51a36d1fbb3bdcf774fbc3f9 -->
**test_no_automatic_approval 断言无 on_interaction 的 run 抛 InteractionRequired**
该 @pytest.mark.asyncio 测试用 client("ask")（真实 fixture 子进程，SDK_FIXTURE=ask）调用 run 且不传 on_interaction，以 pytest.raises 断言 InteractionRequired；此处为静态描述，未在本次执行。

来源：[sdks/python/tests/test_client.py:L110–L113](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/python/tests/test_client.py#L110-L113), [sdks/python/tests/test_client.py:L19–L25](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/python/tests/test_client.py#L19-L25)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":113,"path":"sdks/python/tests/test_client.py","sha256":"9ee1f017411c7efe674543af19949f6c08c254c1c907b07b2819c691b6d6b2ca","start":110},{"end":25,"path":"sdks/python/tests/test_client.py","sha256":"f5b4077078987b338c61ab4096d4bc4a168926dc74fe37fa146eb2a2679b659f","start":19}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
