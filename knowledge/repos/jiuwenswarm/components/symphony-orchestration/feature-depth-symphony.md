---
title: "Symphony 检索与图谱编排：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/symphony/service.py:L264-L321, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/symphony/config.py:L12-L33, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/symphony/config.py:L127-L151, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/symphony/test_config.py:L6-L30, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/symphony/test_config.py:L50-L118, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/symphony/service.py:L808-L819, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/symphony/config.py:L112-L120, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/config.py:L237-L244, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/symphony/build.py:L139-L154, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/symphony/adapter.py:L91-L122]
feature: "symphony"
entry_points: ["jiuwenswarm/symphony/service.py"]
source_globs: ["jiuwenswarm/symphony/service.py", "jiuwenswarm/symphony/*.py"]
---

# Symphony 检索与图谱编排：实现深读

[功能概览](feature-symphony.md) · [owner 入口](_index.md)

<!-- kb:depth feature=symphony facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5cff7dff18a80a4a0eabd55d9c7e556f4bac3d434b4e12a6bad3fa218655d564 -->
**服务启动时的配置加载链**
SwarmSymphonyService.start() 在启用开关检查前先调用 load_symphony_config()；load_symphony_config 在未传入 config 时调用 get_config() 读取并解析 config.yaml（含环境变量解析与归一化），返回的字典再经 symphony_config_from_dict 转成 SymphonyConfig，start 据此判断 config.enabled 与 evolution_flow_enabled 决定是否继续 Flow 恢复。

调用路径：`jiuwenswarm/symphony/service.py`（`SwarmSymphonyService.start`） → `jiuwenswarm/symphony/config.py`（`load_symphony_config`） → `jiuwenswarm/common/config.py`（`get_config`）

来源：[jiuwenswarm/symphony/service.py:L808–L819](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/symphony/service.py#L808-L819), [jiuwenswarm/symphony/config.py:L112–L120](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/symphony/config.py#L112-L120), [jiuwenswarm/common/config.py:L237–L244](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/config.py#L237-L244)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/symphony/service.py","start":808,"end":819,"sha256":"07965a1cbe0d8c13cdc2d6e8d6824b0070a46e434183241da2fed47b4eca889f"},{"path":"jiuwenswarm/symphony/config.py","start":112,"end":120,"sha256":"609786d5bcbfaf227d097fe87c5ef496a31c440f6a979a8647c54ab4587586df"},{"path":"jiuwenswarm/common/config.py","start":237,"end":244,"sha256":"5ef680b085e74776575ebc948be5d277192e0c744c84d90cf49237b5a032e1f9"}],"trace":[{"path":"jiuwenswarm/symphony/service.py","symbol":"SwarmSymphonyService.start","start":808,"end":819},{"path":"jiuwenswarm/symphony/config.py","symbol":"load_symphony_config","start":112,"end":120},{"path":"jiuwenswarm/common/config.py","symbol":"get_config","start":237,"end":244}]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=symphony facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=665a85b643d4acb47d6050eb307c36bbb7912d845663c9ff6a7d420378663b16 -->
**start_refresh_graph 的后台复用契约**
start_refresh_graph(force=...) 在 _build_guard 保护下复用未完成的 symphony-graph-build 任务：若已有任务在跑，直接返回 {"success": true, "background": true, "build_status": "running"}；否则重置 build_log.jsonl、记录 update.start 并创建新任务。调用方义务是用 build_status/build_progress 轮询，而不是假定启动即完成。

来源：[jiuwenswarm/symphony/service.py:L264–L321](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/symphony/service.py#L264-L321)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/symphony/service.py","start":264,"end":321,"sha256":"47057132014608ba8de55c93836b73c1844a474d4748f13d10d9e3a9b5008782"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=symphony facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4febee037345fccb6a9194e6adc0e7ee22dc56be3f496d0d6005186e71409500 -->
**默认值与 flow 开关回退**
代码默认 symphony.enabled=false、orchestration.mode="fast"、min_edge_confidence=0.5；evolution.flow.enabled 缺省时回退读取旧位置 evolution.enabled（symphony_config_from_dict 中 flow_enabled 为 None 时取 evolution.get("enabled")）。路径缺省落在 get_agent_workspace_dir() 下的 skills 与 symphony/graph。

来源：[jiuwenswarm/symphony/config.py:L12–L33](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/symphony/config.py#L12-L33), [jiuwenswarm/symphony/config.py:L127–L151](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/symphony/config.py#L127-L151)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/symphony/config.py","start":12,"end":33,"sha256":"8cdc11a9687330a75da3479e9bfb84875ab168537862bea4c3e245fef620484d"},{"path":"jiuwenswarm/symphony/config.py","start":127,"end":151,"sha256":"3399d958b6ed149987a453e0100f8e8d9378440e905d02b17f0a48629e69ce18"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=symphony facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=437da8d413e8bb90156084515a5f696fe7d8bd6603b31a54d51e995cf1052a23 -->
**构建期把本地适配器注入核心 FingerprintService**
GraphBuildRuntimeFactory.fingerprint_service 构造核心 openjiuwen 的 FingerprintService 时，把扫描结果包装成 ScanResultCapabilityProvider 作为能力来源，并在提供 llm_config 时注入 FingerprintLLMAdapter、用 fingerprint_settings_from_swarm 翻译本地配置。这层耦合决定了本地 Symphony 配置（workers、batch_size 等）如何进入核心指纹提取流程。

来源：[jiuwenswarm/symphony/build.py:L139–L154](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/symphony/build.py#L139-L154), [jiuwenswarm/symphony/adapter.py:L91–L122](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/symphony/adapter.py#L91-L122)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/symphony/build.py","start":139,"end":154,"sha256":"4c361efd314cf502732b8f6e0ea0139f1d43a292377bbf51ec716c61dfc180f7"},{"path":"jiuwenswarm/symphony/adapter.py","start":91,"end":122,"sha256":"d128a24c8d0bf2a3f72885e3a17c7fe5f463ed5521cbd92b46a3b442b82df2a0"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=symphony facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d143590b1b08f6f518e8d27473482089e98d49512feeb723ce4de34ab898a3a4 -->
**tests/unit_tests/symphony/test_config.py 的断言范围**
test_symphony_config_defaults_paths 断言空配置时 skills/graph 默认路径、batch_size=12、mode="fast"、enabled=False；test_symphony_config_normalizes_values 断言字符串数字归一与 min_edge_confidence 越界夹取（2→1.0、-1→0.0）；test_symphony_config_rejects_non_llm_orchestration_modes 断言非 fast/beam 模式抛 ValueError。这些是断言所锻炼的行为入口，不代表本次已运行通过。

来源：[tests/unit_tests/symphony/test_config.py:L6–L30](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/symphony/test_config.py#L6-L30), [tests/unit_tests/symphony/test_config.py:L50–L118](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/symphony/test_config.py#L50-L118)

<!-- kb:depth-proof {"evidence":[{"path":"tests/unit_tests/symphony/test_config.py","start":6,"end":30,"sha256":"a2c4159e5e46bc3982495a35f06701fc3aaf1baffa8de5ab239f2ef562f5febf"},{"path":"tests/unit_tests/symphony/test_config.py","start":50,"end":118,"sha256":"5f0d7b11f0108e0dd934b8c593bd6da027a7caf4aacfa55d98c7da3f9b235c8a"}],"trace":[]} -->
<!-- /kb:depth -->
