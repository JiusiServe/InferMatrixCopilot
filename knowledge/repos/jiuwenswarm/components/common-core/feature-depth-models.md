---
title: "模型平台与 API 配置：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/model_config_validation.py:L70-L119, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/model_config_validation.py:L30-L67, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/model_config_validation.py:L70-L86, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/common/test_model_config_validation.py:L64-L86, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/common/test_model_config_validation.py:L116-L128, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/runtime/test_model_catalog.py:L72-L81, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/config.py:L1609-L1620, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/model_config_validation.py:L275-L278, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/model_catalog.py:L80-L89, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/config.py:L1593-L1606, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/model_config_validation.py:L70-L89, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/model_config_validation.py:L103-L117]
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

<!-- kb:depth feature=models facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ca6f12d451c021ff92681c565f622f3f0e0f5fe546cdfda95f666ff0cfd17c0d -->
**ModelCatalog 构建快照后按 model_id 查找**
__init__ 把 load_models_config(config if config is not None else get_config()) 存入 self.snapshot；load_models_config 深拷贝配置、解密 defaults、并入 agentos，并把非空 model_id 索引进 by_id。随后 get_model 命中 snapshot["by_id"] 即返回，未命中 raise ModelSelectionError(MODEL_SELECTION_NOT_FOUND, f"unknown model_id {model_id!r}")。

来源：[jiuwenswarm/common/model_catalog.py:L80–L89](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/model_catalog.py#L80-L89), [jiuwenswarm/common/config.py:L1593–L1606](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/config.py#L1593-L1606)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":89,"path":"jiuwenswarm/common/model_catalog.py","sha256":"bbfa67ba48cd3c8d989709638ca4293433f4a9586727925e408db6d74f4fb48e","start":80},{"end":1606,"path":"jiuwenswarm/common/config.py","sha256":"f041a89387da363fa727896cd6ece6094b05140a1d943da698ee3864eaaa2fa3","start":1593}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=models facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=96bc8a9150281ff7d6ceb8c4947198afc09954f5f2d811d08f2f8d794161cbb7 -->
**save_models_candidate 依赖 raise_if_invalid 前置校验后才写配置**
save_models_candidate 先 deepcopy 并 _ensure_model_business_ids，再函数内从 jiuwenswarm.common.model_config_validation 导入 raise_if_invalid，校验通过后才 update_config 替换 models 段；无效时抛 ModelSelectionError(MODEL_GROUP_INVALID, 以"; "连接的错误)，update_config 不会执行。

来源：[jiuwenswarm/common/config.py:L1609–L1620](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/config.py#L1609-L1620), [jiuwenswarm/common/model_config_validation.py:L275–L278](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/model_config_validation.py#L275-L278)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1620,"path":"jiuwenswarm/common/config.py","sha256":"37e2b4b6981d68ad407a6e729101bec4b18553d29c83071637ad7cd6a56d7aae","start":1609},{"end":278,"path":"jiuwenswarm/common/model_config_validation.py","sha256":"f1e06e59f8085b368650867c32476ce6d5f112b3111c663cb06d8876b5abdbf1","start":275}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=models facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=be432a45b26a826b77c69d272bbdf906cb8c2d98fdf73909a39f51a0f228ece3 -->
**probe_model_connection：空 token_limits 直接 ValueError；无输出按档重试、仅末档重抛**
token_limits 为空时 raise ValueError("token_limits must contain at least one value")。docstring 界定无 content、reasoning 或生成 token 用量的响应算失败尝试；_model_probe_output 判无输出即 raise ValueError("Empty response from model")，异常被逐次捕获，仅当 attempt + 1 >= len(limits) 才重抛，否则换下一档 max_tokens 重试并记 INFO 日志。

来源：[jiuwenswarm/common/model_config_validation.py:L70–L89](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/model_config_validation.py#L70-L89), [jiuwenswarm/common/model_config_validation.py:L103–L117](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/model_config_validation.py#L103-L117)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":89,"path":"jiuwenswarm/common/model_config_validation.py","sha256":"d6c08527d131d4f71ded9136fed80664632653dc2d75105ef729be41c0133cb1","start":70},{"end":117,"path":"jiuwenswarm/common/model_config_validation.py","sha256":"3da92b9f148702783a89a9c40ca4312a6fbe9bbada674bafd4c24de11497b806","start":103}],"trace":[]} -->
<!-- /kb:depth -->
