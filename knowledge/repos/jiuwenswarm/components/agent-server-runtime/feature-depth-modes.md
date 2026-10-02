---
title: "Agent、Code 与 Team 模式：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/mode_catalog.py:L92-L101, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/mode_catalog.py:L21-L27, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/mode_matrix.py:L309-L326, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/mode_matrix.py:L219-L223, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/test_plan_entry_source_contract.py:L126-L163, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/test_plan_entry_source_contract.py:L72-L93]
feature: "modes"
entry_points: ["jiuwenswarm/runtime/mode_catalog.py", "jiuwenswarm/common/mode_matrix.py"]
source_globs: ["jiuwenswarm/runtime/mode_catalog.py", "jiuwenswarm/common/mode_matrix.py", "jiuwenswarm/server/runtime/agent_adapter/*.py"]
---

# Agent、Code 与 Team 模式：实现深读

[功能概览](feature-modes.md) · [owner 入口](_index.md)

<!-- kb:depth feature=modes facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=53a8a51625eb97ed03eba0649428ede198e65c3b2d4448e28aab65a40b0ea9bf -->
**resolve_mode_capability 的解析契约**
resolve_mode_capability(requested) 接受任意对象，经 deprecate_mode 归一并 strip 后，空值抛 ModeCatalogError("mode is required", code="BAD_REQUEST")，未在 _SINGLE_AGENT_MODES 中命中抛 ModeCatalogError("single-Agent mode not found", code="NOT_FOUND")；调用方必须处理这两个错误码而非期待返回 None。

来源：[jiuwenswarm/runtime/mode_catalog.py:L92–L101](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/mode_catalog.py#L92-L101), [jiuwenswarm/runtime/mode_catalog.py:L21–L27](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/mode_catalog.py#L21-L27)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/runtime/mode_catalog.py","start":92,"end":101,"sha256":"9dd1422e8583fb437a8f02b87edb5689be0b099108591c616e0fef1cf7c71162"},{"path":"jiuwenswarm/runtime/mode_catalog.py","start":21,"end":27,"sha256":"5462a2f0a26bb9c56e12fcdc145fccedded96b880a2ab146d841d8acea7a0ce0"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=modes facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b617bb49d8e5a6f3d23b21abe18031d51d1c9a41afc31b6f77e8c92f403b67c9 -->
**空 mode 的两级不同行为**
deprecate_mode 对 None/空串/空白串原样返回（不做空串回落），因此空值不会被误映射为 agent.work.normal；下游 resolve_mode_capability 据此抛 code="BAD_REQUEST"。而未经 deprecate_mode 的 normalize_mode_text 会把空值回落为 "agent"——绕过 deprecate_mode 直接判定的调用方与走完整归一的调用方行为不一致。

来源：[jiuwenswarm/common/mode_matrix.py:L309–L326](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mode_matrix.py#L309-L326), [jiuwenswarm/common/mode_matrix.py:L219–L223](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mode_matrix.py#L219-L223), [jiuwenswarm/runtime/mode_catalog.py:L92–L101](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/mode_catalog.py#L92-L101)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/common/mode_matrix.py","start":309,"end":326,"sha256":"bc8108e2b196f629e8c22e0f7f8fe79d4b220357a519cc5f6a9898b640ba4b38"},{"path":"jiuwenswarm/common/mode_matrix.py","start":219,"end":223,"sha256":"48f92281d067b3c6775b13464daee047d6f1dc22e05353a8fb90134f5ea73d3d"},{"path":"jiuwenswarm/runtime/mode_catalog.py","start":92,"end":101,"sha256":"9dd1422e8583fb437a8f02b87edb5689be0b099108591c616e0fef1cf7c71162"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=modes facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b82474fa12958066edefe61ec1c384feb511e079564a44fbc4269781cd6de2bc -->
**plan 入口字面量跨端契约测试**
tests/unit_tests/test_plan_entry_source_contract.py 用 test_explicit_plan_entry_accepts_known_sources / test_explicit_plan_entry_rejects_unknown_sources 断言 AgentWebSocketServer._is_explicit_plan_entry_request 只接受 slash_command 与 plan_toggle 两个已知字面量，空串、大小写偏差和非 dict params 均拒绝；并用正则解析 TUI/Web 的 .ts 常量与后端 PLAN_ENTRY_SOURCES 做 == 比对。

来源：[tests/unit_tests/test_plan_entry_source_contract.py:L126–L163](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/test_plan_entry_source_contract.py#L126-L163), [tests/unit_tests/test_plan_entry_source_contract.py:L72–L93](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/test_plan_entry_source_contract.py#L72-L93)

<!-- kb:depth-proof {"evidence":[{"path":"tests/unit_tests/test_plan_entry_source_contract.py","start":126,"end":163,"sha256":"9ef7385f46975b94a246b9d90bc8f8493a74588610e2e2640556f1eeb7843e1a"},{"path":"tests/unit_tests/test_plan_entry_source_contract.py","start":72,"end":93,"sha256":"9d12d9f5bb77aca3142a4a21beeb3a3c77f1312c725b24c30c8f30be8559aa5e"}],"trace":[]} -->
<!-- /kb:depth -->
