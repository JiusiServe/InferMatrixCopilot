---
title: "设备联系人搜索工具（search_contact）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py:L45-L96, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py:L28-L47, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py:L93-L102, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L76-L85, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py:L18-L25, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py:L56-L82, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L58-L62, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L87-L96, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py:L45-L49, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py:L98-L102, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L80-L85, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py:L45-L47, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L53-L55, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/agents/swarm/test_swarm_assembly.py:L1872-L1880, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/tools.py:L121-L150, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/swarm/providers/tools.py:L461-L469]
feature: "xiaoyi-contact-search"
entry_points: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py"]
---

# 设备联系人搜索工具（search_contact）：实现深读

[功能概览](feature-xiaoyi-contact-search.md) · [owner 入口](_index.md)

<!-- kb:depth feature=xiaoyi-contact-search facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bbdc861556e641cdf6c2c86f68b5a135d66775f4a11abccad2f6041680d04c3f -->
**search_contact 校验 name 后组装 SearchContactLocal 设备命令并格式化返回**
回调先校验 name 为非空字符串（否则抛 ToolInputError），strip 后记录日志，组装 namespace=Common/name=Action 的命令（intentName=SearchContactLocal、bundleName=com.huawei.hmos.aidispatchservice、timeOut=5、intentParam={"name": name_clean}），经 execute_device_command 取 outputs；非 dict 则包成 {"outputs": ...}，从 result.items 数出条数，返回 format_success_response(dict(outputs), f"搜索到联系人信息（{n} 条）")。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py:L45–L96](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py#L45-L96)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":96,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py","sha256":"210a70f9d776a72c4c8b70fb1ff08dc694a24ff80516231d09298324012d9183","start":45}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-contact-search facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cfc412b74797c471528cc7022b6eb6c46d82bebe73a4920606988709bbe05678 -->
**async def search_contact(name: str) -> Dict[str, Any]：单必填参数、成功返回设备 outputs 的包装**
经 openjiuwen @tool 注册为名为 "search_contact" 的工具，唯一参数 name（联系人姓名）；文档承诺 Returns 的 content[0].text 为设备 outputs 的 JSON 字符串。name 非字符串或去空白后为空时抛 ToolInputError（"缺少必填参数 name"）且不被兜底 except 吞掉（ToolInputError 直接 re-raise）。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py:L28–L47](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py#L28-L47), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py:L93–L102](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py#L93-L102)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":47,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py","sha256":"15d8cb7dabe36f329a1f1598373d7d7a915e1a01064354155f27fee11262dc05","start":28},{"end":102,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py","sha256":"6a62a6f4168ba24cbc4badae850cea084069a365e251ade16b491682bbe79c80","start":93}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-contact-search facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2e95944c089e0c9c73d21055ad098371ed856fa925ceed6515972d9f6d9ff7d6 -->
**命令字段硬编码、intentParam.name 为唯一变量，会话标识从 channels.xiaoyi 配置读取**
executeParam 中 intentName=SearchContactLocal、bundleName、timeOut:5 等均硬编码，仅 intentParam.name 取自入参；execute_device_command 的 timeout 形参默认 60.0 秒；session_id 从 config 的 channels.xiaoyi.last_session_id 读取，task_id 初始为空串。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py:L56–L82](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py#L56-L82), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L58–L62](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L58-L62), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L87–L96](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L87-L96)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":82,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py","sha256":"8339d94c6a5937337507155ded8ce1a14605b3e31a3f055b66fa2a0a1c3885df","start":56},{"end":62,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py","sha256":"4f2cb8daaa2351ec78e8a0669fb7d6cb39c5a649f780e71e0c1a4c25b565ce43","start":58},{"end":96,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py","sha256":"5d5f738cb2d2f079d6e11beb617a5791fd3b3a244bf1a8ce68135e66068615e4","start":87}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-contact-search facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8bbd668cab4063946b53f5ab37aaa391da69a1a625c94d36f8ae08f86bc8e088 -->
**依赖 get_runtime_xiaoyi_channel() 返回的活动会话通道**
execute_device_command 首先取 get_runtime_xiaoyi_channel()；返回 None 时直接抛 RuntimeError（"No active XY session found. {intent_name} tool can only be used during an active conversation."），即该工具只能在活动小艺会话期间使用。search_contact 本身依赖 openjiuwen 的 @tool 装饰器与 jiuwenswarm.common.utils 的 logger。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L76–L85](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L76-L85), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py:L18–L25](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py#L18-L25)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":85,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py","sha256":"aa2731cf8bfab24863f2db44e760456d49f8c7761fe96e0aac9e5746865a3d0e","start":76},{"end":25,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py","sha256":"026e517c675dafd5a7fbc2d48e56c8ef44b4175dab1f7549346786d954e7dcfd","start":18}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-contact-search facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7b0ff9ca592856d6b3762e9eb5bd2212ad3b960ae082aee22204c21159ffab9b -->
**空 name 抛 ToolInputError 原样上抛；无活动会话或设备执行异常时抛 RuntimeError**
name 非字符串或去空白后为空时抛 ToolInputError（status=400）并被 except ToolInputError: raise 原样传播；get_runtime_xiaoyi_channel() 返回 None 时抛 RuntimeError（无活动 XY 会话）；其余任意异常被捕获并包装为 RuntimeError("搜索联系人失败: …") 后抛出。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py:L45–L49](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py#L45-L49), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py:L98–L102](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py#L98-L102), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L80–L85](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L80-L85)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":49,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py","sha256":"b02556f618ddd97d80542338e8aea8f5a6d9e7fea7f4bc3275d8111b9db1829b","start":45},{"end":102,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py","sha256":"c3bd9b373d72e39d77b943b49ad767e844fccf58198d4e4ea030f93415af208a","start":98},{"end":85,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py","sha256":"b33bf89241b338094772deeaad4381dbe604aae0ec8b45b32fa1aa53563212b0","start":80}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-contact-search facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e411d72d4a5c4dfbe5abd152a4486ca8bc3e77cf3d05fffc4f230194beeffdef -->
**区分输入错误与执行失败，但以 RuntimeError 统一包装其他异常类型**
search_contact 对空白 name 抛出 status=400 的 ToolInputError 并原样上抛，使参数错误与设备执行失败在类型上可区分；代价是其余任何 Exception 都被改写为 RuntimeError（搜索联系人失败: …），原始异常类型仅通过 `from e` 的 cause 链保留。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py:L45–L47](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py#L45-L47), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py:L98–L102](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py#L98-L102), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L53–L55](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L53-L55)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":47,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py","sha256":"8dd8805921db181e71fe52263e2dd34e6cf578156c59ba823509e3c44e2191c1","start":45},{"end":102,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py","sha256":"c3bd9b373d72e39d77b943b49ad767e844fccf58198d4e4ea030f93415af208a","start":98},{"end":55,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py","sha256":"df0436e13e52fec31d53e79c25d3b73b8a5b55e57df64cd11aac6650a86c6d8a","start":53}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-contact-search facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=53a43fd41009a002bb733cf461aa4ed58d342210d645d3ab780ed2295335d507 -->
**既有 assembly 测试断言 phone_tools_enabled 开关下工具数量为 27 或 0（未执行）**
tests/agents/swarm/test_swarm_assembly.py:1872 的 test_xiaoyi_phone_tools_gated_by_config 实际调用 tools._build_xiaoyi_phone_tools：config 含 channels.xiaoyi.phone_tools_enabled=True 时断言返回 27 个工具，config 为空（默认 False，tools.py:464-468）时断言返回 []。生产元组 _XIAOYI_PHONE_TOOLS 显式含 search_contact（tools.py:129），故该开关覆盖其暴露；但断言仅为聚合计数，不校验 search_contact 的检索行为或设备交互。NOT EXECUTED。

来源：[tests/agents/swarm/test_swarm_assembly.py:L1872–L1880](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/agents/swarm/test_swarm_assembly.py#L1872-L1880), [jiuwenswarm/agents/swarm/providers/tools.py:L121–L150](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/tools.py#L121-L150), [jiuwenswarm/agents/swarm/providers/tools.py:L461–L469](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/swarm/providers/tools.py#L461-L469)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1880,"path":"tests/agents/swarm/test_swarm_assembly.py","sha256":"937552f24d47dad020214418cf9aa430b1b2216fcf692530e3cf03099a34a880","start":1872},{"end":150,"path":"jiuwenswarm/agents/swarm/providers/tools.py","sha256":"3676650a09a0441ad25e82a12fd8ebbe503b9960efb9475671b40b741fd2a722","start":121},{"end":469,"path":"jiuwenswarm/agents/swarm/providers/tools.py","sha256":"9b10b462d3ed8ef84ff21833831933c9f431f48a177788b8e433376d3794e913","start":461}],"trace":[],"validation_kind":"helper_unit"} -->
<!-- /kb:depth -->
