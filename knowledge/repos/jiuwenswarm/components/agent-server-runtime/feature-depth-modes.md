---
title: "Agent、Code 与 Team 模式：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/mode_catalog.py:L92-L101, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/mode_catalog.py:L21-L27, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/mode_matrix.py:L309-L326, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/mode_matrix.py:L219-L223, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/test_plan_entry_source_contract.py:L126-L163, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/test_plan_entry_source_contract.py:L72-L93, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/mode_catalog.py:L59-L84, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/mode_matrix.py:L219-L229, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/模式系统.md:L39-L43", "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/模式系统.md:L67-L69"]
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

<!-- kb:depth feature=modes facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=158d0afa5531eef1335bd14916bacfa64a3e0fd1d4b69ff29fd284e0c60cad19 -->
**canonical 归一与单 Agent 目录匹配调用链**
输入请求携带的 mode 串（如旧串 agent）：resolve_mode_capability 先调用 deprecate_mode；deprecate_mode 经 canonicalize_mode_text 得到规范文本并查 DEPRECATION_MAP，把 agent 映射为 agent.work.normal；canonicalize_mode_text 内部先由 normalize_mode_text 做小写化与空值回落 agent，再查 MODE_ALIASES。resolve_mode_capability 最后在 _SINGLE_AGENT_MODES 的四个 agent.* 描述符中精确匹配，命中返回 RuntimeModeDescriptor，team 等非单 Agent 串抛 ModeCatalogError(code=NOT_FOUND)，空串抛 code=BAD_REQUEST。

调用路径：`jiuwenswarm/runtime/mode_catalog.py`（`resolve_mode_capability`） → `jiuwenswarm/common/mode_matrix.py`（`deprecate_mode`） → `jiuwenswarm/common/mode_matrix.py`（`canonicalize_mode_text`） → `jiuwenswarm/common/mode_matrix.py`（`normalize_mode_text`）

来源：[jiuwenswarm/runtime/mode_catalog.py:L92–L101](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/mode_catalog.py#L92-L101), [jiuwenswarm/runtime/mode_catalog.py:L59–L84](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/mode_catalog.py#L59-L84), [jiuwenswarm/common/mode_matrix.py:L309–L326](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mode_matrix.py#L309-L326), [jiuwenswarm/common/mode_matrix.py:L219–L229](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mode_matrix.py#L219-L229)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":101,"path":"jiuwenswarm/runtime/mode_catalog.py","sha256":"9dd1422e8583fb437a8f02b87edb5689be0b099108591c616e0fef1cf7c71162","start":92},{"end":84,"path":"jiuwenswarm/runtime/mode_catalog.py","sha256":"bacd39c1091377c82563f9711e265dead996eeb87d313a0dc8b6fb7f2aa402dd","start":59},{"end":326,"path":"jiuwenswarm/common/mode_matrix.py","sha256":"bc8108e2b196f629e8c22e0f7f8fe79d4b220357a519cc5f6a9898b640ba4b38","start":309},{"end":229,"path":"jiuwenswarm/common/mode_matrix.py","sha256":"12bbbbd9562e3ab0bbd6ae21aa739020396d6967539dcbf2c3c436ea94bf3e20","start":219}],"trace":[{"end":101,"path":"jiuwenswarm/runtime/mode_catalog.py","start":92,"symbol":"resolve_mode_capability"},{"end":326,"path":"jiuwenswarm/common/mode_matrix.py","start":309,"symbol":"deprecate_mode"},{"end":229,"path":"jiuwenswarm/common/mode_matrix.py","start":226,"symbol":"canonicalize_mode_text"},{"end":223,"path":"jiuwenswarm/common/mode_matrix.py","start":219,"symbol":"normalize_mode_text"}]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=modes facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cecb0a15e0ea23e8d1bfbdd8a502bf7b36c7bae3ae3008bf165d4aa1ea1d1a7e -->
**旧串静默映射的兼容收益与观测代价**
设计推断（非作者历史意图）：

文档记载迁移策略：旧串经 deprecate_mode() 静默映射到新串，不抛错、不告警，旧客户端继续发旧串也能正常工作。代码中映射仅在文本变化时输出一条 logger.debug。推断：收益是旧客户端零改动即可兼容；代价是仍在使用旧串的流量在生产日志里几乎不可见，迁移退场进度难以度量。

来源：[docs/zh/模式系统.md:L39–L43](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%A8%A1%E5%BC%8F%E7%B3%BB%E7%BB%9F.md#L39-L43), [docs/zh/模式系统.md:L67–L69](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%A8%A1%E5%BC%8F%E7%B3%BB%E7%BB%9F.md#L67-L69), [jiuwenswarm/common/mode_matrix.py:L309–L326](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mode_matrix.py#L309-L326)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":43,"path":"docs/zh/模式系统.md","sha256":"6899a6b7b8aa1fa07979bcb27a4a2a3759796bde8301d9fcb7c987d5d7be36f6","start":39},{"end":69,"path":"docs/zh/模式系统.md","sha256":"89517270e05e74622ff2f3c1daa53656a75b12e7438777d7187de794f52da556","start":67},{"end":326,"path":"jiuwenswarm/common/mode_matrix.py","sha256":"bc8108e2b196f629e8c22e0f7f8fe79d4b220357a519cc5f6a9898b640ba4b38","start":309}],"trace":[]} -->
<!-- /kb:depth -->
