---
title: "分页 PDF 文本读取工具（read_pdf）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L24-L26, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L117-L122, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L143-L143, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agents/test_pdf_tools.py:L146-L159, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L239-L262, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L263-L275, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L125-L130, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L92-L101, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L143-L163, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L201-L208, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L86-L109, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L112-L116, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L274-L275, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L257-L275, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L112-L122, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L125-L145]
feature: "pdf-reading-tool"
entry_points: ["jiuwenswarm/agents/harness/common/tools/pdf_tools.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/pdf_tools.py"]
---

# 分页 PDF 文本读取工具（read_pdf）：实现深读

[功能概览](feature-pdf-reading-tool.md) · [owner 入口](_index.md)

<!-- kb:depth feature=pdf-reading-tool facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0cebccf4fac270da2382e129557f51ced820c417a300fe2f95d4108f2f988396 -->
**异步工具签名：必填 pdf_path，可选 pages 与 max_chars，返回 str**
read_pdf(pdf_path: str, pages: Any = None, max_chars: int = DEFAULT_MAX_CHARS, **kwargs) 为 @tool 注册的异步函数，返回 str；任何异常被捕获并返回 "[ERROR]: read_pdf failed: {exc}"，kwargs 被忽略。

来源：[jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L239–L262](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/pdf_tools.py#L239-L262), [jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L263–L275](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/pdf_tools.py#L263-L275)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":262,"path":"jiuwenswarm/agents/harness/common/tools/pdf_tools.py","sha256":"4b63048a1e248b4634df6217343fa044ac82a824a7551329b2fb16d66f8b108c","start":239},{"end":275,"path":"jiuwenswarm/agents/harness/common/tools/pdf_tools.py","sha256":"9b3916731a72ea2cbf58ff329183779695338708b005a1a350fd87f090e0f23b","start":263}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=pdf-reading-tool facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=64c0342b400a502fcfefe9a07e58a237647d391d71c54caba3c94e9d83d121d6 -->
**max_chars 默认 50_000，被钳制到 [1_000, 200_000]，每次调用最多 100 页**
DEFAULT_MAX_CHARS = 50_000，_MAX_CHARS_CEILING = 200_000，_MAX_PAGES_PER_CALL = 100。_normalize_request 里 max_chars 取整失败回退默认值，再经 max(1_000, min(max_chars, 200_000)) 钳制；页选择在 _read_pdf_sync 中被 selected[:_MAX_PAGES_PER_CALL] 截断。

来源：[jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L24–L26](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/pdf_tools.py#L24-L26), [jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L117–L122](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/pdf_tools.py#L117-L122), [jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L143–L143](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/pdf_tools.py#L143-L143)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":26,"path":"jiuwenswarm/agents/harness/common/tools/pdf_tools.py","sha256":"7acdf9368aeeb80fd09bff04c42b3442a24659633086826d1d648a6e2ccffbce","start":24},{"end":122,"path":"jiuwenswarm/agents/harness/common/tools/pdf_tools.py","sha256":"ef484f22a42538227e442b4816c85b6a8b4675e9269bb730dcf2a81faee5ab7b","start":117},{"end":143,"path":"jiuwenswarm/agents/harness/common/tools/pdf_tools.py","sha256":"bcf4300016b9ad59bd757cd5bf7c528f02860677280b5e85108f92f87ff54409","start":143}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=pdf-reading-tool facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e371ef20cdca1b21e17b71f7d28fd1b8f8216083ca9482e1e4b0ac5d780f907e -->
**pdfplumber 延迟导入；相对路径依赖 openjiuwen get_workspace**
_read_pdf_sync 在路径校验之后才 import pdfplumber，使缺依赖环境仍能先报路径错误；_resolve_pdf_path 对非绝对路径导入 openjiuwen.core.sys_operation.cwd.get_workspace 拼接，取不到 workspace 时抛 ValueError。

来源：[jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L125–L130](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/pdf_tools.py#L125-L130), [jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L92–L101](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/pdf_tools.py#L92-L101)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":130,"path":"jiuwenswarm/agents/harness/common/tools/pdf_tools.py","sha256":"c5a67ec1d3a818d005c7e60125d6c42e2657ec02a2db15fb611c1e3212e9a3a5","start":125},{"end":101,"path":"jiuwenswarm/agents/harness/common/tools/pdf_tools.py","sha256":"f8c650e15e6a4860d04ff37f499cc0196b811b5daccd5d69527e27188819b574","start":92}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=pdf-reading-tool facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=30fad209f6d78e6f7868134b8043df6afe1bf665fd525103aab1f291e8b35d3d -->
**每调用最多 100 页的上限换来输出有界，代价是超大文档必须分多次调用**
设计推断（非作者历史意图）：

selected 截断到 _MAX_PAGES_PER_CALL(100)，被跳过的页会触发披露说明：当总页数不超过 100 时建议省略 pages 整读，否则提示从第一个未读页继续调用（推断：该设计以多次调用的代价控制单次返回规模）。

来源：[jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L143–L163](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/pdf_tools.py#L143-L163), [jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L201–L208](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/pdf_tools.py#L201-L208)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":163,"path":"jiuwenswarm/agents/harness/common/tools/pdf_tools.py","sha256":"89c307b1ebe4f2d93cd5347c023fb8cd63b506f53b1216636fc95a3b995b47f6","start":143},{"end":208,"path":"jiuwenswarm/agents/harness/common/tools/pdf_tools.py","sha256":"ccd4bf22a002b8744b3a68ea77a7e2bb1a97466b334b2128a78d8d4bd30a4318","start":201}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=pdf-reading-tool facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=737112efb1db6eea27abd4bde0880a896723cba45237337abe9219e066483d75 -->
**运行时单测直接 await read_pdf.invoke 断言输出内容**
test_read_pdf_extracts_pages_and_flags_blank 构造 3 页 PDF 后 await read_pdf.invoke({"pdf_path": ...})，断言 "total pages: 3"、"--- Page 1 ---"、页文本和 "no text layer" 均在结果中（pdfplumber 缺失时 importorskip 跳过）。此为证据所述测试内容，非本次执行结果。

来源：[tests/unit_tests/agents/test_pdf_tools.py:L146–L159](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agents/test_pdf_tools.py#L146-L159)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":159,"path":"tests/unit_tests/agents/test_pdf_tools.py","sha256":"8baf987f28ac5aea4e8dcd918f1b42c44e79d4f729a5ce3709f8d9c8c53f7782","start":146}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->

<!-- kb:depth feature=pdf-reading-tool facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f3b2f2041f216163fc84a84205680ed419a61c9f6d455b4b9ee2c12391831c23 -->
**read_pdf 归一化入参后经 asyncio.to_thread 执行同步提取，异常转为错误字符串返回**
async 入口 read_pdf 将三个入参交给 _normalize_request：pdf_path 去首尾空白后为空即抛 ValueError；max_chars 先按 int() 转换，仅在转换抛出 TypeError 或 ValueError 时回退 DEFAULT_MAX_CHARS，再被夹在 [1_000, _MAX_CHARS_CEILING] 区间。随后 logger.info 记录归一化后的 path/pages/max_chars，并通过 asyncio.to_thread 把 _read_pdf_sync 卸载到线程；该同步函数先调用 _resolve_pdf_path 校验路径，再 import pdfplumber 并 open 文件，按 total_pages 过滤出 selected 页（超出总页数的请求页归入 out_of_range），selected 再被截断到 _MAX_PAGES_PER_CALL，随后开始构造 header 字符串。以上任何一步抛出的 Exception 都被 read_pdf 的 except 捕获，函数返回字符串 "[ERROR]: read_pdf failed: {exc}"。

来源：[jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L257–L275](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/pdf_tools.py#L257-L275), [jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L112–L122](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/pdf_tools.py#L112-L122), [jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L125–L145](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/pdf_tools.py#L125-L145)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":275,"path":"jiuwenswarm/agents/harness/common/tools/pdf_tools.py","sha256":"7e679b4c07e1b1ee89c2ff0f10d76218fb4222e62c2bdd3c3b5e53f2e1c64782","start":257},{"end":122,"path":"jiuwenswarm/agents/harness/common/tools/pdf_tools.py","sha256":"784998bcc3e6284735cb8435e9196f7898893e4194b65e085b7e13f5dc94d91d","start":112},{"end":145,"path":"jiuwenswarm/agents/harness/common/tools/pdf_tools.py","sha256":"d03104f5e89580acabf865c07125b51b6639afa3b077be79988684008971e167","start":125}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=pdf-reading-tool facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=968019ff4d4bb775e8c8b4c4d091bdd3e601e27d0a2d6c147139d0ffe8057d75 -->
**路径/规整阶段抛出的 ValueError 与 FileNotFoundError 在 read_pdf 内被 except Exception 转为错误字符串返回**
_resolve_pdf_path 对空值抛 ValueError("pdf_path cannot be empty")，相对路径在 get_workspace() 失败或为空时抛 ValueError("read_pdf runtime workspace is unavailable")，文件不存在抛 FileNotFoundError，非文件或后缀非 .pdf 抛 ValueError；_normalize_request 对空 pdf_path 抛 ValueError。这些异常在 read_pdf 的 except Exception 分支被捕获并作为字符串 "[ERROR]: read_pdf failed: {exc}" 返回给调用者；该分支仅捕获 Exception，不代表所有可抛对象都被转换。

来源：[jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L86–L109](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/pdf_tools.py#L86-L109), [jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L112–L116](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/pdf_tools.py#L112-L116), [jiuwenswarm/agents/harness/common/tools/pdf_tools.py:L274–L275](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/pdf_tools.py#L274-L275)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":109,"path":"jiuwenswarm/agents/harness/common/tools/pdf_tools.py","sha256":"31923d675bdbe08a4359d5bd93a77871943a2fa18e43f0ea76a39d9aec4804d7","start":86},{"end":116,"path":"jiuwenswarm/agents/harness/common/tools/pdf_tools.py","sha256":"75af93a59a4134f9b47405cd81559d128880be59581da02e22eda3010f30eeba","start":112},{"end":275,"path":"jiuwenswarm/agents/harness/common/tools/pdf_tools.py","sha256":"3062b830190c073ca6a6028c6df34480d9f38aff01a5bf3badb160cd4f69c279","start":274}],"trace":[]} -->
<!-- /kb:depth -->
