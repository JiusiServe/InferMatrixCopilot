---
title: "MiniMax H3 规则"
created: 2026-08-04
updated: 2026-08-04
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #5691", "PR #5699", "PR #5709", vllm_omni/diffusion/models/minimax_h3/pipeline_minimax_h3.py, vllm_omni/diffusion/models/minimax_h3/reference_video.py, vllm_omni/diffusion/models/minimax_h3/encoder.py, tests/e2e/accuracy/minimax_h3/]
confidence: high
---

# MiniMax H3 规则

只有 `MMH3-数字字母` 是可审计规则 ID。

## Direct 代码快速入口

| PR 描述信号 | 规则组 | 第一批 live 源码 |
|---|---|---|
| T2VA/FL2VA/Ref2VA、partition、image/audio/video reference、batch | `task-conditioning`：`MMH3-1a` | checkpoint metadata → `pipeline_minimax_h3.py` task normalization/validation → public video dispatcher |
| fps、frame/latent alignment、audio rate、spatial shape、VAE dtype、condition pinning | `numerical-shape`：`MMH3-1b` | `time_request.py` → `pipeline_minimax_h3.py` → `vae.py` → `denoise_loop.py` |
| CFG、text-encoder TP、DiT TP、Ulysses、VAE tile parallel | `parallel-topology`：`MMH3-2a` | `pipeline_minimax_h3.py::_build_text_encoder_group` → encoder collectives → transformer/VAE validators |
| QKV、gate/up、retained encoder layer、FP8/quantization loader | `checkpoint-loading`：`MMH3-2b` | `encoder.py::{_map_weight_name,_load_weights}` → fused parameter `weight_loader` |
| torchaudio、TorchCodec、soundfile、ffmpeg、reference soundtrack | `reference-audio`：`MMH3-3a` | `reference_video.py::{load_audio_file,load_video_audio}` → pipeline `_load_audio` → audio VAE |
| official T2VA reference、golden revision、SSIM/PSNR、audio quality | `joint-accuracy`：`MMH3-4a` | `tests/e2e/accuracy/minimax_h3/` exact case → `/v1/videos/sync` → video/audio scorers |

| 审查组 | 什么时候触发 | 规则 ID |
|---|---|---|
| `core` | 每次 MiniMax H3 审查 | `MMH3-1a`, `MMH3-1b` |
| `task-conditioning` | task、partition、reference source、batch | `MMH3-1a` |
| `numerical-shape` | frame/audio/latent shape、dtype、condition rows | `MMH3-1b` |
| `parallel-topology` | 任一并行 axis 或 distributed reference encode | `MMH3-2a` |
| `checkpoint-loading` | mapper、fused parameter、retained layer、quantization | `MMH3-2b` |
| `reference-audio` | audio/video decode backend 或平台适配 | `MMH3-3a` |
| `joint-accuracy` | golden、revision、阈值、支持声明 | `MMH3-4a` |

## Task、shape 与 conditioning

### MMH3-1a — partition、task 和 conditioning source 作为一张矩阵校验

- 触发：修改 checkpoint task metadata、video API reference 字段、H3 task 路由或 batch。
- 强制：`FL2VA` partition 只接受无 media 的 T2VA 或恰好一张 image 的 FL2VA；
  `Ref2VA` partition 只接受“恰好一张 image + 一条 standalone audio”或“按表单顺序的一条
  及以上 video，使用各自 soundtrack 且无 standalone audio”；prompt 非空，当前 diffusion
  batch 只接受一个请求。公开入口必须按 [SERV-4i](../../components/serving/rules.md) 在 I/O
  前执行同一矩阵。
- 禁止：跨 partition/task fallback；混合 image/video source；multi-video 再带
  `audio_reference`；让非法组合进入 engine 后才失败。
- 验收：每个正向 cell 和所有相邻负向 cell 都经过 pipeline 与 sync/async 公开入口；
  错误为一致 4xx，且负向 case 未持久化文件、未启动 model generation。 ^[PR #5691]

### MMH3-1b — timing、latent shape 和 condition pinning 属于 checkpoint 数值合同

- 触发：修改 duration/frame 归一化、video/audio latent、spatial padding、VAE dtype、seeded
  preprocessing 或 denoise condition row。
- 强制：保持 24 FPS、frame 数 `17n+5`、video latent 长度 `5n+2`、audio latent 40 Hz、
  spatial dimension 对齐 32；video VAE 的 FP32 边界和每步重新 pin condition rows 必须由
  明确 checkpoint 证据才能改变。
- 禁止：用通用 `round()` 或相邻模型的公式替代 H3 对齐；为省显存静默降低 VAE 精度；
  只在初始 step 固定 conditioning 后允许后续 denoise 漂移。
- 验收：边界 duration/size 的 exact-vector 与 round-trip 测试覆盖 dtype 和 latent shape；固定
  seed 逐步断言 condition rows，最终 MP4 同时验证 24 FPS 和 32 kHz audio metadata。
  ^[PR #5691]

## 并行与 checkpoint

### MMH3-2a — 每个并行 axis 独立 fail fast，encoder subgroup 对所有 rank 都有定义

- 触发：修改 CFG、text-encoder TP、DiT TP、Ulysses/Ring、VAE parallel 或 distributed
  reference encode。
- 强制：CFG size 固定为 1；encoder TP 是前 N 个 DiT rank 的合法 subgroup，并满足
  attention head/KV divisibility；DiT TP 与 Ulysses 分别满足维度约束；VAE parallel 只用
  native tile 且 size 为 1 或完整 DiT group。所有 world rank 以同一顺序创建 group；成员
  获得 coordinator，非成员获得不访问 group membership/collective 的安全 handle。
- 禁止：把 `NON_GROUP_MEMBER` 包成要求当前 rank 属组的 coordinator；只在 N=world 时测
  encoder TP；让不同 rank 因 reference 类型不同而跳过 collective。
- 验收：多进程覆盖 N=1、N<world、N=world 和每个非法 axis；无 deadlock/非成员 crash，
  distributed hidden state 与单 rank 在 BF16 容差内一致，非法配置在模型加载前报出 axis、
  N 和 world size。 ^[PR #5691]

### MMH3-2b — fused encoder parameter 按 source shard 完整性记账

- 触发：修改 retained Qwen encoder 的 weight map、QKV/gate-up fusion、layer subset 或
  FP8/quantized loading。
- 强制：为每个 runtime parameter 声明所需 source shard ID；按 `(parameter, shard_id)`
  记账，只有 q/k/v 或 gate/up 全部到齐才标记 fused parameter 完成；明确裁掉的 layer/key
  与缺失 required shard 分开处理。
- 禁止：第一片到达后只按 `param_name` 标 loaded；对 `torch.empty` 中未初始化的 required
  slice 仅 warning 后继续；在该合同未通过前声明 FP8/quantized 支持。
- 验收：完整 checkpoint 逐 slice 对值；分别删除每个 q/k/v/gate/up source 都 fail fast
  并报告目标 parameter 与缺失 shard；允许丢弃的 layer/key 仍有显式正向测试。 ^[PR #5691]

## Reference audio

### MMH3-3a — 所有 decoder backend 保持同一 audio VAE 输入合同

- 触发：修改 H3 standalone/reference-video audio loading 或可选 media backend。
- 强制：torchaudio、soundfile 和 ffmpeg-demux fallback 都返回
  `(float32 waveform[C,T], native_sample_rate)`；soundfile 的 `[T,C]` 必须转置并 contiguous，
  32 kHz resampling 只由 audio VAE owner 执行；standalone 与 video soundtrack 共用该入口。
- 禁止：新增 direct `torchaudio.load` 旁路；泄漏 channels-last、在 loader 静默 resample，
  或把 TorchCodec/CUDA 可用性当作 NPU/CPU 前提。
- 验收：强制覆盖 torchaudio 成功、torchaudio 失败后 soundfile 成功、soundfile 失败后
  ffmpeg 成功及 subprocess 失败；mono/stereo 的 dtype、channel order、rate 与临时目录
  cleanup 都断言，direct audio 和 video-demux 路径结果一致。 ^[PR #5699]

## Joint video/audio accuracy

### MMH3-4a — official-reference oracle 必须 immutable 且覆盖两个 modality

- 触发：新增或修改 H3 official-reference accuracy test、golden、threshold 或支持声明。
- 强制：checkpoint 和 reference asset 分别 pin 到可解析的 immutable revision/digest；prompt、
  request 参数、执行 topology 与阈值绑定同一 exact case。video 做 metadata 与视觉相似度，
  audio 除 codec/rate/channel metadata 外还必须比较内容或质量。
- 禁止：用 `resolve/main` 作 golden；假定权重 revision 一定包含 asset；把 AAC/32 kHz/stereo
  metadata 通过当作 audio accuracy；用另一硬件的结果为当前 CI lane 背书。
- 验收：昂贵 server startup 前完成 revision/digest preflight；exact case 满足
  [DIFF-3a](../../components/diffusion/rules.md) 与 [VOMNI-CI-1b](../../ci/rules.md)，视觉和
  音频 scorer 都有正向结果及损坏单一 modality 的反例。 ^[PR #5709]
