---
title: "A2UI 生成式界面：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/control/a2ui_config.py:L39-L69, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/system_tests/test_a2ui_system_flow.py:L42-L100, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/a2ui/test_integration_bridge.py:L26-L32, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/a2ui/test_integration_bridge.py:L93-L109]
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
