---
title: "CosyVoice3 规则"
created: 2026-09-04
updated: 2026-09-18
type: rule
tags: [vllm-omni, models]
sources: ["PR #5673", "PR #6955", vllm_omni/model_executor/models/cosyvoice3/code2wav_core/cfm.py, vllm_omni/model_executor/models/cosyvoice3/flow_estimator_trt.py, tests/model_executor/models/cosyvoice3/test_cosyvoice3_components.py, benchmarks/tts/benchmark_cosyvoice3_trt_streams.py]
confidence: high
---

# CosyVoice3 规则

## Direct 代码快速入口

| PR 描述信号 | 规则 |
|---|---|
| TensorRT CFM stream handoff 或 flow-estimator plan publication | `COSYVOICE3-1a`、`COSYVOICE3-1b` |

## COSYVOICE3-1a — TensorRT CFM 的跨 stream handoff 必须同时守住顺序和 allocator lifetime

- 触发：修改 CosyVoice3 `ConditionalCFM.forward_estimator` 的非-`torch.nn.Module`
  TensorRT 分支、`TrtContextWrapper` 的 context/stream pool，或 raw device-pointer
  输入/输出、dtype conversion 和 CUDA stream handoff。
- 强制：pool 中保存每个 execution context 配对的原始 `torch.cuda.Stream`；在 estimator
  stream 上先 `wait_stream(caller_stream)`，在其 raw `cuda_stream` handle 上 enqueue TRT，
  然后让 caller `wait_stream(estimator_stream)` 再消费输出。对每个以 raw pointer 绑定的
  CUDA input/output record estimator stream，且在返回/转换前对 output record caller stream。
  context 只有在地址已 enqueue 到其专属 stream 后才能归还同一个 pair。
- 禁止：以 host `synchronize()` 替代任一依赖；把 `torch.cuda.stream(...)` 的 context
  manager 当作 pool stream；只保护输出或只保护输入，使 caching allocator 能在 TRT 完成前
  重用 `.to(...).contiguous()` buffer；在未建立 consumer wait 前复用 CFG 的原地写入 buffer。
  不得把这个优化扩展为改变 `torch.nn.Module` estimator 路径，或静默改变
  `COSYVOICE3_TRT` 关闭和非-CUDA fallback。
- 验收：CPU fake-stream 回归断言零 `synchronize`、两个方向各一次 `wait_stream`、TRT 接到
  estimator raw handle，且 context/stream pair 原样回池；真实 CUDA/TensorRT 覆盖 raw-pointer
  input/output 的 allocator-lifetime 与数值 parity。性能报告要分开写 submission、engine 和
  E2E 指标：受控 handoff microbenchmark 只能证明消除了 host blocking，有限的 E2E 样本或
  engine 小幅变化不能声称模型吞吐/延迟提升。^[PR #5673]

## COSYVOICE3-1b — flow-estimator TRT plan 必须以自有临时文件原子发布

- 触发：修改 CosyVoice3 `flow_estimator_trt.py` 的 ONNX→plan 序列化、plan 缓存路径或
  `_write_plan_atomically` 发布流程。
- 强制：在 destination 同目录以 `<plan>.tmp.<pid>.<uuidhex>` 独占 `xb` 创建临时文件；写完并
  close 后才 `os.replace` 到 plan。并发成功者各自发布完整 artifact，最终允许 last-writer-wins。
  write 或 replace 失败时只清理本调用已创建的 tmp；cleanup 失败仅记录日志，必须重抛原始异常。
- 禁止：使用固定共享 `.tmp` 名称；在独占创建 collision 时删除 foreign tmp；把此发布合同扩展为
  `fsync`、目录持久化、锁、内容校验或事务保证，或把 CPU 文件系统测试表述为 TensorRT/GPU 行为证明。
- 验收：`tests/model_executor/models/cosyvoice3/test_flow_estimator_trt.py` 的五项 CPU 覆盖必须分别
  证明 replace 失败保留旧 plan、cleanup 失败保留 replace error、partial write 清理 owned tmp、
  collision 保留 foreign tmp，以及两条同步 publisher 使用不同 source path 且仅留下完整 final plan。
  ^[PR #6955]

## COSYVOICE3-1c — 流式 HiFT 必须在有界 mel 窗上增量计算并携带相位

- 触发：修改 CosyVoice3 `_stream_hift_from_feat`、`CausalHiFTGenerator`、`SineGen`/`SineGen2` 的 `phase_acc`，或 streaming chunk 的 noise/F0 cache。
- 强制：每个 chunk 只在有界 mel 窗上计算（末 64 帧再加上 F0 感受野历史），不得对累积全谱重跑。谐波相位用共享的边界 `phase_acc` 带入下一窗。noise 必须是固定、按位置索引的 buffer，不能用随 chunk 变化的 `torch.randn_like`。F0 predictor 的左因果卷积要吃 window 左侧的真实历史，不能零填充；这段 margin 属于 `cache_state`，在进入 SineGen/decode 前切掉，且短于感受野的 chunk 不得饿死下一次调用。finalize 除 `conv_pre_look_right` 外还要释放 predictor 自己扣下的 `trim`，否则流末约 3 个 mel 帧丢失。
- 禁止：用 PCM16 逐字节相等当正确性门槛（亚 LSB 的再结合误差会翻边界样本）；只测未触发 voiced 的随机权重；把 `scipy`/`s3tokenizer` 放回 dev extra——它们是 base install 的硬依赖，scipy 下限保持 `>=1.11.0`。
- 验收：相对全量重算，float64 应逐位一致；float32 用 `assert_close(atol=1e-6, rtol=1e-5)`。同时覆盖 SineGen（22050 Hz）与 SineGen2（24000 Hz）、强制 voiced，以及均匀 chunk 和单 mel 帧的小块。^[PR #7521]
