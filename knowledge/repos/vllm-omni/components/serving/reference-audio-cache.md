---
title: "Speech reference-audio cache 的存储与所有权"
created: 2026-10-09
updated: 2026-10-09
type: guide
tags: [vllm-omni, components, serving]
sources:
  - "https://github.com/vllm-project/vllm-omni/pull/7781"
  - "https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/entrypoints/openai/serving_speech.py"
  - "https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/tests/entrypoints/openai_api/test_ref_audio_cache.py"
confidence: high
---

# Speech reference-audio cache 的存储与所有权

本页七维解释限定于源码 `2e3c7fe2c171cd3429298094d175a64eacbdb341`，不把该版本的
默认容量覆盖到后来的 [speech cache 配置规则](../configuration/rules-speech-cache.md)。
API resolved waveform cache 属于 serving process；模型的 speaker/ref-code artifact cache
属于 [Qwen3-TTS owner](../../models/qwen3-tts/mrv2-pipeline.md)，两者没有共同的内存总额保证。

## flow

`_resolve_ref_audio_array()` 先按 locator 和允许的本地路径生成 key，命中时更新 LRU 并返回
缓存 waveform。miss 经 `MediaConnector.fetch_audio_async()`，再由
`_finalize_fetched_ref_audio()` 转为 float32、按需混合声道、检查时长，复制出自有的 C-contiguous
数组并计算 artifact key。fetch 后重新核对文件 metadata；一致才入缓存，改变则有界重试，
连续改变最终跳过缓存。该方法返回的第三项是 resolve cache key，不能直接当 artifact key。

来源：[finalize](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/entrypoints/openai/serving_speech.py#L1225-L1244)、
[resolver](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/entrypoints/openai/serving_speech.py#L1255-L1337)。

## api

array resolver 的返回值可与缓存共享 storage；调用方进行 in-place 处理前需复制。该合同
依赖调用方遵守，数组没有因此变成强制只读。legacy `_resolve_ref_audio()` 调用 array resolver
后执行 `tolist()`，因此每次返回独立 list。最终版本的 `_put_resolved_ref_audio()` 用
`np.asarray(..., dtype=float32)`，只在非连续时转为 contiguous；它保留已 finalize ndarray 的
identity，而 list caller 转换后与缓存隔离。缓存边界不再无条件复制 ndarray。

来源：[双 resolver API](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/entrypoints/openai/serving_speech.py#L1246-L1273)、
[cache insertion](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/entrypoints/openai/serving_speech.py#L1362-L1390)。

## configuration

该快照 API waveform cache 默认 1024 entries、512 MiB；任一上限非正即不插入缓存。
单条 `waveform.nbytes` 超过 byte 上限时拒绝缓存，仍可完成当前 resolver 调用。多条按
LRU 淘汰到同时满足 entry 与 byte 上限。这里计的是 float32 数组的 payload bytes，
不包含 Python 对象、临时 list、解码器工作内存或模型 GPU artifacts。

来源：[默认值](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/entrypoints/openai/serving_speech.py#L113-L114)、
[双上限与淘汰](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/entrypoints/openai/serving_speech.py#L1362-L1390)。

## dependencies

resolve cache key 对允许的本地文件纳入 mtime/size，远程 URL 仍按 locator 缓存；远程
内容原地改变不会自动刷新。artifact key 则由 sample rate、样本数和 float32 waveform bytes
生成。不同 locator 可引用同一 artifact；替换/淘汰一条 resolve entry 后，只有没有其他
entry 引用该 artifact 时才清理 readiness。readiness 还带 `x_vector_only` mode，不能把
waveform cache hit 当作 ICL/ref-code artifact 已准备好的证明；模型能力边界见
[Qwen3-TTS 规则](../../models/qwen3-tts/rules.md)。

来源：[key 语义](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/entrypoints/openai/serving_speech.py#L1159-L1223)、
[artifact 哈希与引用](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/entrypoints/openai/serving_speech.py#L1339-L1417)。

## failure_modes

直接缓存 decoded array 的 view 可能保留远大于 `nbytes` 的 backing allocation，因而
finalize 明确复制自有 buffer。相反，cache insertion 已接受自有的 finalized array，继续
复制会破坏 array resolver 的 identity 合同。两条边界承担不同职责。直接把外部可变 ndarray
送入 insertion 并随后修改不受该合同保护；legacy list 的隔离测试不能证明 ndarray 也隔离。
metadata 重试只减少本地文件 key/content 不一致，不建立远程内容 freshness 保证。

来源：[finalize 所有权](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/entrypoints/openai/serving_speech.py#L1241-L1244)、
[共享合同](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/entrypoints/openai/serving_speech.py#L1255-L1273)、
[insertion 转换](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/entrypoints/openai/serving_speech.py#L1362-L1390)。

## tradeoffs

设计推断：缓存 compact float32 payload 减少 Python float list 的长期驻留，并让 array
consumer 复用 finalized buffer；legacy consumer 仍在每次调用时分配 list。entry 容量与
byte 容量共同限制可复用 reference 集合，命中率还依赖样本长度和 locator 分布。因此仅
对齐 entry 数量不足以证明 benchmark 的 cache representation、转换开销或模型缓存一致。
源码没有提供本页可独立复核的 RSS 或延迟测量，不把存储形式直接换算成吞吐收益。

推断依据：[legacy 转换](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/entrypoints/openai/serving_speech.py#L1246-L1253)、
[payload byte 计数](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/vllm_omni/entrypoints/openai/serving_speech.py#L1362-L1390)。

## validation

已检查的 [cache 回归](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/tests/entrypoints/openai_api/test_ref_audio_cache.py#L38-L95)
断言默认容量、float32/nbytes、插入 list 与返回 list 的 mutation isolation、entry/byte 淘汰、
oversized entry 拒绝，以及仍有 alias 引用时保留 artifact readiness。666 references 的用例
只证明短小 fixture 的容量，不证明真实 reference 工作负载都能装入 512 MiB。
[waveform 所有权与 identity 回归](https://github.com/vllm-project/vllm-omni/blob/2e3c7fe2c171cd3429298094d175a64eacbdb341/tests/entrypoints/openai_api/test_reference_waveform_cache.py#L18-L57)
另外断言 finalize 的 `owndata`、不共享 decoded storage、array resolver/cache identity 与临时 list 隔离。
本轮未执行这些 upstream 测试；知识树校验通过也不等于 serving 性能或共享 ndarray 的
所有 caller 都已满足不修改合同。
