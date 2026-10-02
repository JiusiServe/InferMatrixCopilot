---
title: "Harness Package 与热激活：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L221-L263, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L169-L178, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L38-L40, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L157-L166, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L86-L96, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L321-L331]
---

# Harness Package 与热激活：实现深读

[功能概览](feature-rsi-packages.md) · [owner 入口](_index.md)

<!-- kb:depth feature=rsi-packages facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1592d6bb1d1f9bcfdbaf9b556951b936f344e0db60710fb6e58e9fc20038c93c -->
**发布 refs 解析链路**
parse_published_harness_refs 以引擎产出的最终 refs 文件与 task_run_root 为输入：先把 refs 与 run 根目录解析为绝对路径并用 _ensure_inside 约束边界，随后调用 _load_refs。_load_refs 读取 YAML（OSError/UnicodeError/YAMLError 均归一为 _invalid 错误）并要求结果是 mapping，最终供上层校验 harness_refs 唯一 role 并返回 PublishedHarnessRef。

调用路径：`jiuwenswarm/agents/harness/common/rsi/harness_activation.py`（`parse_published_harness_refs`） → `jiuwenswarm/agents/harness/common/rsi/harness_activation.py`（`_load_refs`）

来源：[jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L221–L263](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/harness_activation.py#L221-L263), [jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L169–L178](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/harness_activation.py#L169-L178)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/rsi/harness_activation.py","start":221,"end":263,"sha256":"f4e28160649b0b80d1037dc885a43ac4a9b996be15ed0aa52793ab8cdc8d214c"},{"path":"jiuwenswarm/agents/harness/common/rsi/harness_activation.py","start":169,"end":178,"sha256":"a1ade19510f2a2536b7eb468b30f0008842bbb76dd94770f65ee1fa134659b62"}],"trace":[{"path":"jiuwenswarm/agents/harness/common/rsi/harness_activation.py","symbol":"parse_published_harness_refs","start":221,"end":263},{"path":"jiuwenswarm/agents/harness/common/rsi/harness_activation.py","symbol":"_load_refs","start":169,"end":178}]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=rsi-packages facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0f3398adc2140dc0476ea1dfed89cfdb6c3da5fa3f3a5e454b25ee1378c699ff -->
**manifest 名称与原生基线配置**
包 manifest 按 _MANIFEST_NAMES = ("manifest.json", "harness_config.yaml", "expert_harness.yaml", "harness.yaml") 查找；无插件时的基线是模块同目录的 harness_config.yaml（_NATIVE_HARNESS_BASELINE_CONFIG）。resolve_native_harness_baseline 在该文件不存在或其目录未通过 _validate_engine_manifest（抛 RsiHarnessInvalid）时返回 None，否则返回其 resolve 后的绝对路径。

来源：[jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L38–L40](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/harness_activation.py#L38-L40), [jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L157–L166](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/harness_activation.py#L157-L166)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/rsi/harness_activation.py","start":38,"end":40,"sha256":"eac74cb141235ecab5ee055a42d43675b3f3e64da6af97418cc7de61902c997e"},{"path":"jiuwenswarm/agents/harness/common/rsi/harness_activation.py","start":157,"end":166,"sha256":"7a5351d27ed1738fb99890e55296b4c11a90354bb335718cc53a0119fa42c2ce"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=rsi-packages facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3d105cb72f9932d60400397b6bc74e69d4095a9d2815776b98dabd7c6e10168c -->
**具体失败触发与传播**
refs 文件缺失/不可读/非 mapping 时 _load_refs 抛 _invalid（RsiHarnessInvalid 类错误）；包内符号链接解析到包外时 _ensure_package_tree_inside 以 "Harness 包含越界软链接" 拒绝；RsiHarnessActivationStore._validate_runtime_path 对不在 activation root 内的 runtime_path 抛 ValueError，require_exists 且目录不存在时返回 None 而非报错。

来源：[jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L169–L178](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/harness_activation.py#L169-L178), [jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L86–L96](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/harness_activation.py#L86-L96), [jiuwenswarm/agents/harness/common/rsi/harness_activation.py:L321–L331](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/harness_activation.py#L321-L331)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/rsi/harness_activation.py","start":169,"end":178,"sha256":"a1ade19510f2a2536b7eb468b30f0008842bbb76dd94770f65ee1fa134659b62"},{"path":"jiuwenswarm/agents/harness/common/rsi/harness_activation.py","start":86,"end":96,"sha256":"b56c221cf2b03da4bf42ad96b74329bf8bfa244d2d653bdc2c764c672cbe4e69"},{"path":"jiuwenswarm/agents/harness/common/rsi/harness_activation.py","start":321,"end":331,"sha256":"9b12f2dad693138a4dd3b0a68a46546c18c5bec5242aede99ad732bab3f1fdba"}],"trace":[]} -->
<!-- /kb:depth -->
