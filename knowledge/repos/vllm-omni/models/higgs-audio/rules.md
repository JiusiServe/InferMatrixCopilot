---
title: "Higgs-Audio 规则"
created: 2026-09-05
updated: 2026-09-05
type: rule
tags: [vllm-omni, models, model-executor]
sources: ["PR #6422", "PR #7065", vllm_omni/entrypoints/openai/serving_speech.py, vllm_omni/model_executor/models/higgs_audio_v3/higgs_audio_v3_talker.py, vllm_omni/model_executor/models/higgs_audio_v3/higgs_audio_v3_tokenizer.py, vllm_omni/worker/gpu_model_runner.py, tests/entrypoints/openai_api/test_serving_speech.py, tests/model_executor/models/higgs_audio_v3/test_higgs_audio_v3.py, tests/e2e/online_serving/test_higgs_audio_v3.py]
confidence: high
---

# Higgs-Audio 规则

## Direct 代码快速入口

| PR 描述信号 | 规则 |
|---|---|
| request RNG/decode state | `HIGGS-1a` |
| voice-clone sentinel、placeholder positions 或 chunked prefill | `HIGGS-2a` |

## HIGGS-1a — V3 codec sampling 与 decode state 必须按 request 所有

- 触发：Higgs-Audio V3 seeded sampling、八 codebook flatten/compaction、GPU decode delay 或 replacement request。
- 强制：每个 logical request 的八个 contiguous codebook rows 必须在一次 multinomial 中使用该
  request row 的 `SamplingMetadata.generators[req_idx]`；generator 由 vLLM request lifecycle 提供，
  talker 不按 request ID 另建 RNG。`has_codes`、last codes、delay/EOC countdown 与 done state 必须由
  request ID 映射到 pool row；reorder/condense 前保存旧 row、再恢复新顺序。finished ID 先释放映射，
  slot 复用时重新初始化；即使 `previous_req_ids == req_ids`，当前 ID 缺 pool entry 也必须重同步。
- 禁止：共享/global RNG、把一个 generator 按八行独立重采样、按临时 batch row 保存 decode state，
  或把 finished callback 描述成会清零 tensor（fresh allocation 才初始化）。`transcript_expected_text`
  只是在 control-token request 与 spoken reference 不同的测试 helper 中覆盖 assertion，默认取
  `input`；它不是 OpenAI request 字段或 runtime 模型语义。
- 验收：覆盖同 seed 单独/带邻居 batch、异 seed、reorder/condense 连续性、finish、distinct-ID slot
  reuse 与 same-ID replacement，并验证 runner 把 live `input_batch.req_ids` 传入 decode metadata。
  ROCm 配置测试只证明 V3 Stage 0 的 `TRITON_ATTN` overlay/collection；作者报告的单次 MI300X case
  不构成通用确定性、音质、吞吐或跨平台支持。^[PR #6422]

## HIGGS-2a — voice-clone 占位语义必须在词表校验边界外显并保持位置对应

- 触发：修改 Higgs-Audio V3 的 voice-clone prompt、`ref_audio` metadata、engine token
  validation、prefill/chunked-prefill embedding substitution，或 offline/online prompt producer。
- 必须：仅在模型本地 `build_prompt` 中保留负值 sentinel；每个提交给 vLLM 的 token ID 必须
  属于 tokenizer vocabulary。adapter 必须同时把 sentinel 替换为不触发 audio-continuation
  sampler 状态的有效 filler（当前为 `<|tts|>`），并记录按 prompt 顺序排列的绝对
  `audio_placeholder_positions`。online serving 与 offline example 都必须传递这些位置和
  delay-pattern reference codes；talker 必须在 transformer layers 前按每个 request span 的
  absolute positions 选择对应 code rows，因而 full 与 chunked prefill 都能注入正确 embedding。
  仅供绕过 engine validation 的 legacy internal caller 保留 `-100` substitution fallback。
- 禁止：把负 sentinel 直接送过共享 token validation；用 `<|audio|>` 或任何会触发采样
  continuation 语义的 filler；按当前 chunk 的局部索引、token identity 或未对齐的 code row
  猜测参考音频位置；只修 online serving 而遗漏 offline producer；删除 legacy fallback 却未
  迁移其 internal caller。
- 验收：prompt smoke 断言 engine IDs 全部非负、每个 placeholder filler 为 `tts_id` 且不为
  `audio_id`，并保留 position metadata；单元测试分别证明完整 prefill、只含 reference span
  一部分的 chunked prefill 和 legacy `-100` caller 注入正确 code rows；serving smoke 证明相同
  路径重写时 cache salt 仍变化。H100 voice-clone E2E 未在该 PR 的 lanes 运行，不能把 unit
  coverage 宣称为 end-to-end 证据。^[PR #7065]
