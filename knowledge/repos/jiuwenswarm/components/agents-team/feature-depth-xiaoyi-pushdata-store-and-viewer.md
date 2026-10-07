---
title: "推送记录持久化与查询 (pushdata_manager + view_push_result)：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py:L34-L51, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py:L67-L69, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py:L136-L152, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py:L49-L69, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py:L94-L134, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py:L18-L19, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py:L54-L66, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py:L49-L51, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py:L56-L66, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py:L49-L51, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py:L14-L18, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py:L49-L62, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py:L112-L141, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/agents/swarm/test_swarm_assembly.py:L1872-L1880, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/tools.py:L121-L150, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/tools.py:L461-L469]
feature: "xiaoyi-pushdata-store-and-viewer"
entry_points: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py", "jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py", "jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py"]
---

# 推送记录持久化与查询 (pushdata_manager + view_push_result)：实现深读

[功能概览](feature-xiaoyi-pushdata-store-and-viewer.md) · [owner 入口](_index.md)

<!-- kb:depth feature=xiaoyi-pushdata-store-and-viewer facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=85d095335151c2fc62f3578d5e5ef45409fefcfeaf4654cda4f44b2225e7b890 -->
**view_push_result 关键词查询路径：剥离空白、全量/搜索取数、按 time 倒序后截断**
调用 view_push_result(keywords, limit) 时，先用 min(limit or 10, 50) 求 effective_limit，keywords 为非空字符串时取 strip 后的关键词；有关键词走 search_push_data，否则 get_all_push_data；结果按 item.get("time", "") 倒序排序后截取前 effective_limit 条，非空时逐条格式化为 pushDataId 前 8 位、fullPushDataId、time、dataDetail 超过 200 字符截断加 "..."、fullLength，并以 success/count/totalMatched/items/message 的 JSON 文本返回。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py:L49–L69](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py#L49-L69), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py:L94–L134](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py#L94-L134)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":69,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py","sha256":"fe1ac1344b8a6869130a44dd4b314185659b7dc1a1c5b26e2eb02d915519336a","start":49},{"end":134,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py","sha256":"72a2363defde5a4bbad3c1be2b5ee322fe4888dabcbfb298e249d2e191152172","start":94}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-pushdata-store-and-viewer facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2f6e723fef7d8799fade4802bb2c695f97a9f0d7d8a204d64ee075d539a0337e -->
**存储路径固定为 ~/.openclaw/pushData.json，写入选用最后 MAX_PUSHDATA_ITEMS=1000 条；查询条数默认 10、上限 50**
模块级常量 PUSHDATA_FILE = os.path.expanduser("~/.openclaw/pushData.json")、MAX_PUSHDATA_ITEMS = 1000；_write_pushdata_list 写入 items[-1000:]，超出时记录 info 日志。view_push_result 中 effective_limit = min(limit or 10, 50)，即 limit 为 None 或 0 时取 10，任何超过 50 的值被压到 50。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py:L18–L19](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py#L18-L19), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py:L54–L66](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py#L54-L66), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py:L49–L51](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py#L49-L51)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":19,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py","sha256":"66b6319208118be43c96698e3b637a335df13149ef41edb7a4ccc0592627e324","start":18},{"end":66,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py","sha256":"893d8d873c7c918de72ff801c1736d76d12bc1aa49b1ba03abaf11e225db5c76","start":54},{"end":51,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py","sha256":"fda3b510392ace90ff5bcd62296006952ac7ff9f4480eae90f57bca6db4e35f6","start":49}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-pushdata-store-and-viewer facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3b7f816c11a1659f432715abcba671efe62586f62cc621ec730243c010c1faa4 -->
**读失败降级为空列表、写失败上抛；工具层 except 兜底返回 success=False**
_read_pushdata_list 捕获 (json.JSONDecodeError, OSError) 记 error 日志并 return []；_write_pushdata_list 捕获 OSError 记日志后 raise；view_push_result 的 try 包住全部逻辑，任何 Exception 返回 {success: False, error: str(e), message: "查询推送记录失败"}。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py:L34–L51](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py#L34-L51), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py:L67–L69](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py#L67-L69), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py:L136–L152](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py#L136-L152)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":51,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py","sha256":"212f4cbfc3d7448d787a6397f8f5c1eb9d29fb2bcb1b1b56e7bbba9f72ee24c4","start":34},{"end":69,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py","sha256":"8d9615772bd9cfe6654a4c82fea0d0727b46d8c42069cf77c1837590e99da5c8","start":67},{"end":152,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py","sha256":"f88f3b1e9fada3a4c685f0fcd05ddff12ebf4f7f7d6deebfe13ca956596acff3","start":136}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-pushdata-store-and-viewer facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cba92a4bd4fef4db3746cc3b946cfc23624bb19bcb16dec9085f4b72bd5ace14 -->
**记录条数封顶 1000 防止列表无限增长，但采用直接覆盖写（推断：非原子）且限制条数而非文件大小**
设计推断（非作者历史意图）：

写入限制在最后 1000 条（items[-MAX_PUSHDATA_ITEMS:]），防止记录无限累积（fact）。代价（推断）：open(..., "w") 直接截断重写整个文件，进程中断可能留下部分写入的 JSON，后续读取会因 JSONDecodeError 降级为 []；且限制的是条数而非 dataDetail 长度，单条超长时文件仍可能很大。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py:L56–L66](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py#L56-L66), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py:L49–L51](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py#L49-L51)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":66,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py","sha256":"35cca36ebe2a7bc001a67ff142d8e6449c1ed2d9333e85c5e774fd9b7d68fe6e","start":56},{"end":51,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py","sha256":"d754402ece68dff8ddc2d05abd9a9be5cc01d3e20cabdf50091033bdadde8479","start":49}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-pushdata-store-and-viewer facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=596f279480df7bfcea3a0ad790da84c2095b94017fdf05e6ac44c1170c536d82 -->
**push_result_tool 从同包 pushdata_manager 导入并按 kw 分发到 search/get_all**
push_result_tool.py L18 `from .pushdata_manager import search_push_data, get_all_push_data` 建立同包耦合；view_push_result 内 `results = search_push_data(kw) if kw else get_all_push_data()`（L58）依据剥离空白后的 kw 决定数据源。search_push_data 与 get_all_push_data 均调用 _read_pushdata_list()（L121/L139），读取端共享同一实现。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py:L14–L18](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py#L14-L18), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py:L49–L62](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py#L49-L62), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py:L112–L141](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py#L112-L141)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":18,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py","sha256":"89e6882423e9e11254a78816b8d8652219093b090d77dee9ef8dc1dc865bee7c","start":14},{"end":62,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/push_result_tool.py","sha256":"1cccd3dc0a5277182715c473cd50af58c52aaf0fbb53905588fac51ec6584b64","start":49},{"end":141,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/pushdata_manager.py","sha256":"d53cc43e7cd36002dd543f12d61c891e4bef57dd226d56534babf97abe024629","start":112}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-pushdata-store-and-viewer facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=43295008175cabdcc1f8405802f1cf5556dbcf77f35c035d260d7a7e377f4fc7 -->
**既有 swarm 装配测试运行 _build_xiaoyi_phone_tools 并断言开关两态的工具数量（helper 单元级）**
tests/agents/swarm/test_swarm_assembly.py 的 test_xiaoyi_phone_tools_gated_by_config 实际调用 tools._build_xiaoyi_phone_tools：config 为 {"channels":{"xiaoyi":{"phone_tools_enabled":True}}} 时断言返回 27 个工具，空 config 时断言返回 []。生产元组 _XIAOYI_PHONE_TOOLS 显式包含 view_push_result，故该测试覆盖查看工具经配置开关暴露的装配路径；断言仅为聚合计数，不校验单个工具身份，pushdata_manager 存储侧不在该测试内。该验证属 helper 单元级，且本次未执行。

来源：[tests/agents/swarm/test_swarm_assembly.py:L1872–L1880](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/agents/swarm/test_swarm_assembly.py#L1872-L1880), [jiuwenswarm/agents/swarm/providers/tools.py:L121–L150](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/tools.py#L121-L150), [jiuwenswarm/agents/swarm/providers/tools.py:L461–L469](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/tools.py#L461-L469)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1880,"path":"tests/agents/swarm/test_swarm_assembly.py","sha256":"937552f24d47dad020214418cf9aa430b1b2216fcf692530e3cf03099a34a880","start":1872},{"end":150,"path":"jiuwenswarm/agents/swarm/providers/tools.py","sha256":"3676650a09a0441ad25e82a12fd8ebbe503b9960efb9475671b40b741fd2a722","start":121},{"end":469,"path":"jiuwenswarm/agents/swarm/providers/tools.py","sha256":"9b10b462d3ed8ef84ff21833831933c9f431f48a177788b8e433376d3794e913","start":461}],"trace":[],"validation_kind":"helper_unit"} -->
<!-- /kb:depth -->
