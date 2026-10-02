---
title: "A2UI 生成式界面：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/control/a2ui_config.py:L39-L69, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/system_tests/test_a2ui_system_flow.py:L42-L100, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/a2ui/test_integration_bridge.py:L26-L32, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/a2ui/test_integration_bridge.py:L93-L109, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/a2ui/runtime/response_finalization.py:L51-L52, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/a2ui/runtime/response_finalization.py:L119-L124, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/a2ui/integration.py:L99-L110, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/a2ui/integration.py:L102-L106, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/a2ui/runtime/response_finalization.py:L22-L40, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/a2ui/runtime/response_finalization.py:L61-L76, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/a2ui/runtime/response_finalization.py:L152-L181]
feature: "a2ui"
entry_points: ["jiuwenswarm/server/runtime/a2ui/runtime/finalizer.py"]
source_globs: ["jiuwenswarm/server/runtime/a2ui/runtime/finalizer.py", "jiuwenswarm/server/runtime/a2ui/*"]
---

# A2UI 生成式界面：实现深读

[功能概览](feature-a2ui.md) · [owner 入口](_index.md)

<!-- kb:depth feature=a2ui facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e2c0ad487b04d02d089c52a84232093240e730ccb8dc1b5c9f790216fa1f04da -->
**a2ui 配置默认值与环境变量优先级**
get_a2ui_config 中 a2ui.enabled 默认 false，环境变量 JIUWENSWARM_A2UI_ENABLED 存在时覆盖 YAML 值；protocol_version 优先级为 JIUWENSWARM_A2UI_PROTOCOL_VERSION > YAML > 默认 "0.8"，不在 SUPPORTED_A2UI_PROTOCOL_VERSIONS 内时抛 ValueError；stream_validation_enabled 默认 true，non_web_fallback_enabled 默认 false。

来源：[jiuwenswarm/server/control/a2ui_config.py:L39–L69](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/control/a2ui_config.py#L39-L69)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/server/control/a2ui_config.py","start":39,"end":69,"sha256":"c328e28bb9c967d4a83b28e188cd2c608543997e35a013ca302f493df6ad3832"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=a2ui facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0622019997ff3474730eb13cd6b80a2aa2f3f2d080e259cfdb75e473015da7e4 -->
**系统流与桥接单测断言**
tests/system_tests/test_a2ui_system_flow.py::test_a2ui_system_flow_accepts_event_and_valid_response 以合法 <a2ui-json> 响应调用 A2UIResponseFinalizer().finalize，repair_call 设为 pytest.fail，断言 finalized 原样返回且 get_protocol_spec().validate_response 为 valid，即有效响应不触发修复。tests/unit_tests/a2ui/test_integration_bridge.py::test_a2ui_channel_policy_is_web_only 断言 is_a2ui_channel 仅对 web（含大小写）为 True；test_message_handler_fallback_skips_a2ui_import_without_marker 通过拦截 __import__ 断言无标记的 gateway 热路径不导入 A2UI integration。这些是测试断言的行为，不代表当前已运行通过。

来源：[tests/system_tests/test_a2ui_system_flow.py:L42–L100](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/system_tests/test_a2ui_system_flow.py#L42-L100), [tests/unit_tests/a2ui/test_integration_bridge.py:L26–L32](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/a2ui/test_integration_bridge.py#L26-L32), [tests/unit_tests/a2ui/test_integration_bridge.py:L93–L109](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/a2ui/test_integration_bridge.py#L93-L109)

<!-- kb:depth-proof {"evidence":[{"path":"tests/system_tests/test_a2ui_system_flow.py","start":42,"end":100,"sha256":"a75aadc0dbed60aaa13b4a5a50930d448bba0f4a988871cae89c3cf873d3c746"},{"path":"tests/unit_tests/a2ui/test_integration_bridge.py","start":26,"end":32,"sha256":"605266e77edf8317d7d9014b2e783973c74465eaacc59efffc2cade70685c505"},{"path":"tests/unit_tests/a2ui/test_integration_bridge.py","start":93,"end":109,"sha256":"40ee9f341e7760fbde172128ac20c2526bc47a59ad8e40fd02d0602e93e00c9b"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=a2ui facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ba917e9c855ec9830a20f9de19996ad1cceab17cc4c145c1bbe2a746e1e7a89a -->
**finalize_a2ui_assistant_content：守卫命中原样返回 content；retry 回调可同步或可等待**
当 not a2ui_enabled、content 非字符串或无 A2UI 标记时原样返回 content；retry_without_a2ui_call 以 str(user_query or "") 调用，结果为 awaitable 时先 await。

来源：[jiuwenswarm/server/runtime/a2ui/runtime/response_finalization.py:L51–L52](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/a2ui/runtime/response_finalization.py#L51-L52), [jiuwenswarm/server/runtime/a2ui/runtime/response_finalization.py:L119–L124](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/a2ui/runtime/response_finalization.py#L119-L124)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":52,"path":"jiuwenswarm/server/runtime/a2ui/runtime/response_finalization.py","sha256":"0b39c5db92f3655c3ae9b7956b83bd012fbb42752c72b8aa279f5665e9a9e953","start":51},{"end":124,"path":"jiuwenswarm/server/runtime/a2ui/runtime/response_finalization.py","sha256":"88587aa73e72237b1193f0876277f7c9dcac19ed3532b524aa138d5343d66aeb","start":119}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=a2ui facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=55f9c7578b26ac8800c0cf540489e6aed645577fda68e568552310e22f896808 -->
**integration.py 把 response_finalization 导入推迟到 channel 与配置守卫通过之后**
包装函数在 is_a2ui_channel(channel) 通过且 _get_runtime_a2ui_config() 成功后才 import finalize_a2ui_assistant_content；非 A2UI channel 在该导入前即 return content。

来源：[jiuwenswarm/server/runtime/a2ui/integration.py:L99–L110](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/a2ui/integration.py#L99-L110)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":110,"path":"jiuwenswarm/server/runtime/a2ui/integration.py","sha256":"2b424be2fe01bd5a46c9a8b07f0f56d91faec2fa911c33d6ff40a9e27823c2d1","start":99}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=a2ui facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=879f4c75cae18aeb13db1d1a055b25ac4132e10a388698ec5aedf6ee3d662a3d -->
**A2UI finalize 包装：_get_runtime_a2ui_config() 异常时跳过 finalization 原样返回**
触发条件为 _get_runtime_a2ui_config() 抛异常；except Exception 分支以 debug 记录 "A2UI response finalization skipped: config lookup failed" 并 return content，异常在该分支内不再向上传播。

来源：[jiuwenswarm/server/runtime/a2ui/integration.py:L102–L106](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/a2ui/integration.py#L102-L106)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":106,"path":"jiuwenswarm/server/runtime/a2ui/integration.py","sha256":"251997757abfe1980cfafabe8672d782825881d7d621a49db35cefa87e4a4cfc","start":102}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=a2ui facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3aeba94f59ea08d554ae5271c767b536c67dbffbc3ff29b219776bb636c8e2c0 -->
**5.0s 有界 fast path 校验：有效内容免进 finalizer，超时降级为文本 fallback**
设计推断（非作者历史意图）：

fast path 仅对含 parseable tagged block 的内容在线程中以 5.0s wait_for 执行 spec.validate_response：校验有效则原样返回、不进入 finalizer 修复流程；超时则直接返回 _a2ui_timeout_fallback 文本，放弃修复尝试。

来源：[jiuwenswarm/server/runtime/a2ui/runtime/response_finalization.py:L22–L40](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/a2ui/runtime/response_finalization.py#L22-L40), [jiuwenswarm/server/runtime/a2ui/runtime/response_finalization.py:L61–L76](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/a2ui/runtime/response_finalization.py#L61-L76), [jiuwenswarm/server/runtime/a2ui/runtime/response_finalization.py:L152–L181](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/a2ui/runtime/response_finalization.py#L152-L181)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":40,"path":"jiuwenswarm/server/runtime/a2ui/runtime/response_finalization.py","sha256":"12b000dc1f88a26f43991f284e70b1470465051879cdecc6e074beac5e9fd59f","start":22},{"end":76,"path":"jiuwenswarm/server/runtime/a2ui/runtime/response_finalization.py","sha256":"be6eb57d57a0d01ae1221c10c5737c09c1171d3bc2d8d0969a405f8963811c20","start":61},{"end":181,"path":"jiuwenswarm/server/runtime/a2ui/runtime/response_finalization.py","sha256":"7c03e450485d6e964cbf8a6cc1117169d46e40adfc6a5264e6c23067f1f8b857","start":152}],"trace":[]} -->
<!-- /kb:depth -->
