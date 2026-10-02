---
title: "模型平台与 API 配置：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/model_config_validation.py:L70-L119, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/model_config_validation.py:L30-L67, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/model_config_validation.py:L70-L86, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/common/test_model_config_validation.py:L64-L86, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/common/test_model_config_validation.py:L116-L128, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/runtime/test_model_catalog.py:L72-L81]
feature: "models"
entry_points: ["jiuwenswarm/common/model_catalog.py", "jiuwenswarm/common/model_config_validation.py"]
source_globs: ["jiuwenswarm/common/model_catalog.py", "jiuwenswarm/common/model_config_validation.py", "jiuwenswarm/common/model*.py"]
---

# 模型平台与 API 配置：实现深读

[功能概览](feature-models.md) · [owner 入口](_index.md)

<!-- kb:depth feature=models facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=97153988c98bfaf666d586f3a485f84d41703e1604ad55e7c1318b1f60ce4ed5 -->
**连接探测的默认 token 档位与外部超时**
probe_model_connection 默认 token_limits=(3, 16)，即先用 3 个输出 token 探测，失败后升到 16 重试一次；timeout_seconds 默认 None（不外加超时），传入时对每次完整调用单独计时，即使模型客户端自身忽略超时设置也能被截止。

来源：[jiuwenswarm/common/model_config_validation.py:L70–L119](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/model_config_validation.py#L70-L119)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/common/model_config_validation.py","start":70,"end":119,"sha256":"07af928f7f1fee8942671b08dbb124365e3e405730287e85d3f27759e949de70"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=models facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2bb374c72badcb066de7c130e0c6e84f0a83c0ba4aae421627789c44c590cb02 -->
**小 token 预算多档重试（推断）**
设计推断（非作者历史意图）：

推断：探测默认用 (3, 16) 两档极小 max_tokens，收益是探测请求便宜且快速；代价是推理模型可能把预算全花在 reasoning_content 上导致误判失败，代码因此同时接受 reasoning_content 非空或 usage_metadata.output_tokens>0 作为成功证据，并以第二档预算兜底。

来源：[jiuwenswarm/common/model_config_validation.py:L30–L67](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/model_config_validation.py#L30-L67), [jiuwenswarm/common/model_config_validation.py:L70–L86](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/model_config_validation.py#L70-L86)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/common/model_config_validation.py","start":30,"end":67,"sha256":"4b284d8612f4f0d3653aee38714a57f0ef13cc96457a94f57e1e9035b5589bb8"},{"path":"jiuwenswarm/common/model_config_validation.py","start":70,"end":86,"sha256":"b1e350270fc5aad32ea2cc41617d909676e1af4f95c00636047bcad83c7ef7d2"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=models facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e19b3bf209b4a01333693a44f1a6ae8f5ed8087d0a76f81973ff1459cd1abb65 -->
**探测与目录脱敏的单元测试入口**
tests/unit_tests/common/test_model_config_validation.py 中的 test_probe_model_connection_retries_with_supremum_tokens 验证失败后按 (3,16) 重试并透传 invoke_kwargs；..._enforces_invocation_deadline 验证 timeout_seconds 截止挂起的调用。tests/unit_tests/runtime/test_model_catalog.py 的 test_catalog_output_is_credential_and_endpoint_free 断言目录序列化结果不含 api_key、api_base、custom_headers 等敏感字段。

来源：[tests/unit_tests/common/test_model_config_validation.py:L64–L86](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/common/test_model_config_validation.py#L64-L86), [tests/unit_tests/common/test_model_config_validation.py:L116–L128](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/common/test_model_config_validation.py#L116-L128), [tests/unit_tests/runtime/test_model_catalog.py:L72–L81](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/runtime/test_model_catalog.py#L72-L81)

<!-- kb:depth-proof {"evidence":[{"path":"tests/unit_tests/common/test_model_config_validation.py","start":64,"end":86,"sha256":"04da94b6e6cdbf8a09d837b89db13d43d9d77f3e7aade9157e8d3d7bac6c55e1"},{"path":"tests/unit_tests/common/test_model_config_validation.py","start":116,"end":128,"sha256":"d8f0c01196a99acdee83856abbc827598f7a6cac54cb0d58a433da9c371ed3ee"},{"path":"tests/unit_tests/runtime/test_model_catalog.py","start":72,"end":81,"sha256":"35d0338135373bde08b78f98541e83410780d5402812a3f7acb4bc9098a0ce43"}],"trace":[]} -->
<!-- /kb:depth -->
