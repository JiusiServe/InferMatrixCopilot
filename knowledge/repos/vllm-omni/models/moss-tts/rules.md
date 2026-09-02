---
title: "MOSS-TTS 规则"
created: 2026-09-02
updated: 2026-09-02
type: rule
tags: [vllm-omni, models, model-executor]
sources: ["PR #5635", vllm_omni/model_executor/models/moss_tts/modeling_moss_tts_codec.py, vllm_omni/model_executor/models/moss_tts/audio_tokenizer.py]
confidence: high
---

# MOSS-TTS 规则

只有 `MOSSTTS-数字字母` 是可审计规则 ID。

## Direct 代码快速入口

| PR 描述信号 | 规则 | 第一批源码 |
|---|---|---|
| codec v1/v2、`number_channels`、missing weights | `MOSSTTS-1a` | `modeling_moss_tts_codec.py::MossTTSCodecDecoder._build_codec` → Stage-1 weight loader |
| `_ProjectedTransformer`、`in_proj`/`out_proj`、Identity | `MOSSTTS-1a` | `audio_tokenizer.py::_ProjectedTransformer` → codec checkpoint parameter names |

## MOSSTTS-1a — codec 代际与 module topology 必须由 checkpoint 原始结构决定

- 触发：MOSS Stage-1 codec config 解析、v1/v2 类选择、vendored tokenizer module 或
  checkpoint missing/shape-mismatch validation。
- 强制：先用 `MossAudioTokenizerV2Config.get_config_dict(codec_path)` 读取 raw config；只有
  raw `number_channels >= 2` 才尝试 v2 config/model。字段缺失按 `1` 判为 v1，直接使用
  `MossAudioTokenizerConfig`/`MossAudioTokenizerModel`，不能让两代共享的 `model_type` 或 v2
  config 的默认双通道值替 checkpoint 决定代际。
- 强制：v2 config/model 构造失败时记录异常并显式回退 v1；raw config 读取本身在选择前完成，
  其失败不得伪装成某一代成功。`_ProjectedTransformer` 的 `in_proj` 仅在
  `input_dimension != d_model` 时为无 bias `Linear`，否则为 `Identity`；`out_proj` 对
  `output_dimension != d_model` 使用同一规则。module topology 与 checkpoint parameter 集必须一致。
- 禁止：总是先实例化 v2 来“探测”版本；用偶然通过的 frame-rate validation 证明类正确；
  dimensions 相等时额外创建 checkpoint 不含的 learned projection，或无条件用 Identity
  丢掉 dimensions 不等时的权重。
- 验收：覆盖 raw config 字段缺失/单通道/v2 双通道、v2 构造失败回退、equal/unequal input
  与 output dimensions，并断言 model class、projection 类型、参数名、weight completeness 和
  forward shape。PR 只提供 Ascend NPU 手工 load/audio 验证，未新增这些自动化回归。 ^[PR #5635]

共享 loader 的 dtype/config 最小读取合同见
[Model Executor rules](../../components/model-executor/rules.md)。
