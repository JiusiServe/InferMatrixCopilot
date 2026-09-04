---
title: "模型引用路由规则"
created: 2026-09-04
updated: 2026-09-04
type: rule
tags: [vllm-omni, components, config]
sources: [vllm_omni/config/config_factory.py, vllm_omni/config/pipeline_registry.py, tests/config/test_config_factory.py, "PR #5036", "PR #6624"]
---

# 模型引用路由规则

## Direct 代码快速入口

- **CONF-7a — 模型引用解析。** 从 `config_factory.py::{_materialize_object_storage_configs,_name_match_candidate,StageConfigFactory._try_infer_model_type}` 直达 `pipeline_registry.py::OMNI_PIPELINES`；cache-shape 回归从 `tests/config/test_config_factory.py::TestNameMatchCandidateSnapshotPaths` 开始。

### CONF-7a — 模型引用解析必须物化对象存储配置，并只从受控名称组件匹配

- 触发：父进程在 stage-specific `ModelConfig` 初始化前，需要从 `s3://`、`gs://` 或上游 `is_runai_obj_uri` 支持的对象存储 URI 推断模型类型、读取 HF 配置或解析 `model_index.json`。
- 强制：通过 `is_runai_obj_uri` 将对象存储模型的 `*.model`、`*.py`、`*.json` 轻量文件按 URI 缓存一次到确定性的 `model_streamer/<hash>` 目录；`get_config`、`config.json` 和 `model_index.json` 的读取统一使用该本地目录，同时让各 stage 继续接收原始 URI 以保留 `model_weights` 的流式加载语义。最后的 name-based fallback 通常只比较末个路径组件；唯一例外是有效 HF hub cache snapshot 的尾形 `models--<org>--<name>/snapshots/<revision>` 或 legacy `models--<name>/snapshots/<revision>`，此时只恢复 repo 的 `<name>`，不能让组织名参与匹配。
- 禁止：把原始对象存储 URI 交给 Hugging Face 仓库解析；把临时 `model_streamer/<hash>` 路径传播成 stage 的模型身份；用完整 URI、bucket 或组织名参与模型类型名称匹配；把普通 `.../snapshots/<revision>` 或 malformed `models--...` 误认成 HF cache（它们必须继续取末个组件）。
- 验收：用 mock 覆盖对象存储 URI 的单次物化、配置驱动的 pipeline 选择、`model_index.json` 回退和欺骗性 bucket 名；参数化覆盖 namespaced/legacy HF cache snapshot、trailing slash、普通路径与 malformed cache segment，断言只从允许的 repo-name 段恢复名称。空 `config.json` 的 snapshot 必须仍能由 `try_infer_model_type` 选中注册的 CosyVoice3 pipeline。PR #6624 的真实 H20 E2E 和 config-suite 结果由作者报告，未在本次知识审计环境复跑；其后续 review 还指出两个 consumer 注释仍称“basename-only”，这是文案漂移而非该提交已改动的行为。^[PR #5036] ^[PR #6624]
