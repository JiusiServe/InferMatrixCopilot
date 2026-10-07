---
title: "设备闹钟 CRUD 工具（create/search/modify/delete_alarm）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py:L139-L169, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/runtime/test_runtime_xiaoyi_host_provider.py:L142-L161, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py:L593-L632, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py:L136-L163, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py:L603-L624, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L87-L97, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py:L626-L632, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L79-L85, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L168-L207, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py:L139-L159, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L168-L179, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L206-L207]
feature: "xiaoyi-alarm-crud"
entry_points: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py", "jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py", "jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/calendar_tools.py", "jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/contact_tools.py"]
---

# 设备闹钟 CRUD 工具（create/search/modify/delete_alarm）：实现深读

[功能概览](feature-xiaoyi-alarm-crud.md) · [owner 入口](_index.md)

<!-- kb:depth feature=xiaoyi-alarm-crud facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3b459e1f07a75ef32911208eef97ea6a328281eaa53cc8239d67643205f30eed -->
**delete_alarm：规范化输入后构造 DeleteAlarm 指令并等待设备响应**
delete_alarm 先调用 _normalize_delete_items 把 items/alarm_id 转成 entityId 列表，构造 bundleName 为 com.huawei.hmos.clock、intentName 为 DeleteAlarm 的 background 指令，再交给 execute_device_command 等待响应，随后经 raise_if_device_error 校验并取 result 组装成功返回。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py:L593–L632](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py#L593-L632), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py:L136–L163](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py#L136-L163)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":632,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py","sha256":"5c66eb15d425ee8e7db8d5b7bfdc965e89b9ca36b32259ab758f197fe2c22d02","start":593},{"end":163,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py","sha256":"87cac1814a3b3fa0a10ea63a581344b582f51e41e08839ffd0355a6afb8bec44","start":136}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-alarm-crud facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bd418cf1eb8c3bf903f4763a0cb6f06d39969edfaa01816d8119437b64da3712 -->
**_normalize_delete_items contract: alarm_id fallback only when items is None**
Items may be a JSON array string or a list; each element must be a dict with a non-empty string entityId or entity_id, and the result is never empty (empty list raises ToolInputError "items 不能为空").

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py:L139–L169](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py#L139-L169)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":169,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py","sha256":"c634d48a01b16665ac99ca837a37b7f28238ea7255ca805c32638a22b2af6b1f","start":139}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-alarm-crud facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e43dbf73c103d8e1c7a29d90197d8e836bdbdb36185c57390ad43b075bf38b76 -->
**delete_alarm 指令固定携带 timeOut: 5 与 executeMode: background**
delete_alarm 的指令不含可配置项：executeParam 硬编码 executeMode 为 "background"、timeOut 为 5、needUnlock 为 True；会话标识由 execute_device_command 从 config 的 channels.xiaoyi 下读取 last_session_id 与 last_task_id。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py:L603–L624](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py#L603-L624), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L87–L97](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L87-L97)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":624,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py","sha256":"a77a31df4899d7f306ce3938ad5916318178f574ed1323b52411e80908c6ccea","start":603},{"end":97,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py","sha256":"3601b10eb0b98b77ed77acefbe0b7242c079a647c570792b11867ff94287d680","start":87}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-alarm-crud facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=abf2f573bbac9964f7f9d480ffa8c12edc9dff6ffbeeca4e26dcfc6d878812df -->
**delete_alarm 依赖 execute_device_command 与运行时 Xiaoyi 通道**
delete_alarm 的设备交互完全委托给共享的 execute_device_command；该函数要求运行时存在 Xiaoyi 通道（否则 RuntimeError），并经 channel.send_xiaoyi_phone_tools_command 发送、以 intent_name 注册的数据事件处理器收响应，finally 中注销处理器。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py:L626–L632](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py#L626-L632), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L79–L85](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L79-L85), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L168–L207](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L168-L207)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":632,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py","sha256":"5c3cdd709264711f2b0a46c43b4de28e520c67c2efe4d1e4cf9956d438b747d7","start":626},{"end":85,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py","sha256":"80df937abfede83927866d920290baa6844266dc5b1b9ad21e7d596c6e782518","start":79},{"end":207,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py","sha256":"42ee64fede81ebd6d8ebf5db7e0874626dce86c7c65a473fb2cf5ef571271283","start":168}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-alarm-crud facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=80dfc4a6ee080271026b3d70778ec45eedb8701600bf42d28c6f1d31dd3c4be3 -->
**双形态 items 输入便于 LLM 调用，代价是本地规范化分支更多**
设计推断（非作者历史意图）：

（推断）接受 JSON 字符串或原生列表、并用 alarm_id 单删兜底，让模型可用任一形态表达删除目标；代价是必须在 _normalize_delete_items 中逐一校验每条路径并抛出区分的 ToolInputError。execute_device_command 每次调用注册/注销事件处理器（finally 保证清理），换取按 intent_name 匹配响应。

来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py:L139–L159](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py#L139-L159), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L168–L179](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L168-L179), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py:L206–L207](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py#L206-L207)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":159,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/alarm_tools.py","sha256":"176f0b5a74c1937bb96e98df9e559a703d4ceb922cde0f1a68b758709d5d42f1","start":139},{"end":179,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py","sha256":"c774b076b8755c1daa35b67ee3821d810eec928fd770b01b89fcbabb8160ef4a","start":168},{"end":207,"path":"jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/utils.py","sha256":"80b4642aa55a967424d1503a6f3efc288b499f9fa5cc0204993c8f369732c30c","start":206}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=xiaoyi-alarm-crud facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=98401b723c90dbd434d92fa89af13c94a10bed74fd9cceeca59cc4cf075c7a0a -->
**Runtime test: device command with no active channel raises RuntimeError before config read**
test_device_command_rejects_missing_runtime_xiaoyi_channel installs a provider returning None and a get_config that fails the test if called, then asserts pytest.raises(RuntimeError, match="No active XY session found") around await utils.execute_device_command("TestIntent", ...) and lookups == ["xiaoyi"]. This exercises the shared command path, not the alarm tools' own bodies.

来源：[tests/unit_tests/runtime/test_runtime_xiaoyi_host_provider.py:L142–L161](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/runtime/test_runtime_xiaoyi_host_provider.py#L142-L161)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":161,"path":"tests/unit_tests/runtime/test_runtime_xiaoyi_host_provider.py","sha256":"5913207d1fda0408b969aa67e837ff3d61dae3489fdc9074589b6656344a28ad","start":142}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
