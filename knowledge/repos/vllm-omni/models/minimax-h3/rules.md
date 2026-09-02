---
title: "MiniMax H3 规则"
created: 2026-09-02
updated: 2026-09-02
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #5703", "PR #5737", "PR #5752", vllm_omni/diffusion/models/minimax_h3/minimax_h3_transformer.py, vllm_omni/diffusion/models/minimax_h3/pipeline_minimax_h3.py, vllm_omni/diffusion/models/minimax_h3/reference_video.py, vllm_omni/diffusion/models/minimax_h3/vae.py, vllm_omni/entrypoints/openai/serving_video.py, tests/diffusion/models/minimax_h3/test_minimax_h3_contract.py, tests/diffusion/models/minimax_h3/test_minimax_h3_quantization.py, tests/diffusion/models/minimax_h3/test_minimax_h3_quantization_quality.py, tests/entrypoints/openai_api/test_video_server.py, recipes/MiniMaxAI/MiniMax-H3.md, recipes/MiniMaxAI/MiniMax-H3-MUSA.md]
confidence: high
---

# MiniMax H3 规则

只有 `MMH3-数字字母` 是可审计规则 ID。

## Direct 代码快速入口

| PR 描述信号 | 规则 | 第一批源码 |
|---|---|---|
| online FP8、`ignored_layers`、component prefix | `MMH3-1a` | `pipeline_minimax_h3.py::_resolve_component_quant_config` → `MiniMaxH3DiTModel` linear prefix |
| grouped QKV、fused MLP、weight loader、TP | `MMH3-1a` | `minimax_h3_transformer.py::MiniMaxH3DiTModel.load_weights` → active vLLM loader |
| FP8 quality、audio metric、layerwise offload | `MMH3-1b` | quantization quality test → recipe/support matrix → nightly lane |
| FL2VA keyframe、Ref2VA mixed reference、shape/output matrix | `MMH3-2a` | `pipeline_minimax_h3.py::{_resolve_fl2va_keyframe_indices,_validate_ref2va_reference_counts,_resolve_shape}` |
| media limit、typed/multipart reference、HTTP 400、temp source | `MMH3-2b` | `api_server.py` video handlers → `serving_video.py::_run_and_extract` → `reference_video.py` |
| conditioned VAE、fixed seed、`fork_rng`、MUSA/device RNG | `MMH3-2c` | `pipeline_minimax_h3.py` condition encode caller → `vae.py::{encode_image,encode_video}` |

## MMH3-1a — component namespace 与 checkpoint transform 必须在 active loader 前闭合

- 触发：修改 H3 online FP8 覆盖范围、`ignored_layers`、linear prefix、QKV/MLP checkpoint
  变换或 TP loader。
- 强制：pipeline 先把 structured quantization config 解析到 `transformer` component，再构造
  DiT；因此内部 prefix 是 `blocks.*`、`token_refiner.*` 等 component-relative 名称，不带
  `transformer.`。每个 eligible linear 显式传 prefix/quant config，patch、timestep、final
  projection 显式保持非量化。grouped-QKV reorder 与 fused `fc1` gate/up split 在
  `MiniMaxH3DiTModel.load_weights()` 先完成，再调用当前 parameter 的 active weight loader，
  让 TP shard 与 FP8 `online_process_loader` 看到最终布局。
- 禁止：用 parent prefix 代替 exact leaf `ignored_layers`；一边已 resolve component、一边仍
  要求 `transformer.`；在 linear 构造后包掉 active loader，或把 reorder/split 放到 FP8
  wrapper 之后。
- 验收：枚举默认 quantized/full-precision prefix 集合，逐个验证 exact ignored leaf；QKV
  与 gate/up sentinel 断言传给 active loader 的顺序和 shard id，至少覆盖 TP 与 online FP8。
  ^[PR #5737]

## MMH3-1b — joint video/audio quality 与 offload 兼容性必须一起验收

- 触发：改变 H3 FP8 layer scope、kernel/loader、quality threshold、offload 或 nightly lane。
- 强制：H3 online FP8 与 layerwise offload 当前标为 incompatible；resident FP8 可与 TP、VAE
  tiling 组合。BF16/FP8 A/B 使用同一 immutable checkpoint、prompt、seed、size、frames、
  steps 与并行/资源设置；joint output 同时检查 video LPIPS 和 32 kHz audio 的 spectral
  cosine/RMS ratio。PSNR、MAE 与 peak memory 是 report-only 指标，不能冒充 gate。
- 禁止：只验视频就宣称 H3 joint-output quality；把一次 22% memory observation 写成稳定
  上界；让 FP8+layerwise offload 到 Cutlass kernel 才因 flattened-weight stride 失败。
- 验收：当前 2x H100 case 的 gates 是 LPIPS <= 0.20、audio spectral cosine >= 0.80、
  RMS ratio 在 0.50–2.00，且 sample rate 为 32000；单测还要证明 phase-tolerant metric
  接受相移但拒绝 spectral drift。 ^[PR #5737]

## MMH3-2a — task、reference、shape 与多输出必须作为一个输入矩阵维护

- 触发：H3 `t2va`/`fl2va`/`ref2va`、reference 计数、frame index、canvas、duration 或
  `num_outputs_per_prompt`。
- 强制：FL2VA 接受一张首/尾帧或两张有序首尾帧，signature 仅为 `[0]`、`[-1]`、
  `[0,-1]`，未显式给出时一张默认 `[0]`、两张默认 `[0,-1]`。Ref2VA 必须至少有一项
  image/video visual reference；image≤9、video≤3、standalone audio≤3、总数≤12，允许
  image-only 及 image/video/audio mixed matrix，但拒绝 audio-only。
- 强制：输出固定 24 FPS、32 kHz audio、duration 4–15 秒。省略 width/height 时
  `short_edge` 只能为 768；T2VA 必须显式选择 `21:9`、`16:9`、`4:3`、`1:1`、`3:4`、
  `9:16`，FL2VA 跟随首图 geometry 并忽略通用 ratio override，Ref2VA 默认 `16:9`，
  `adaptive`/`auto` 是该默认的 alias。
- 强制：`num_outputs_per_prompt` 仅为 1–10，各输出 seed 是 `seed + output_index`；pipeline
  tensor output 与未被公开 caller 使用的 `generate_videos()` 保留 fan-out。此 pin 上 public
  async job 与 `/v1/videos/sync` 都调用 `generate_video_bytes()`，多输出时告警并只持久化/返回
  `artifacts.videos[0]`；不得把 recipe 的“async 返回全部”描述当成实现证据。
- 禁止：把 partition 名当输入能力；FL2VA/Ref2VA 权重分区仍需与 task 匹配。不得把长
  reference clip 截成输出长度；reference 自己的 segment/duration 合同由 MMH3-2b 约束。
- 验收：以 F1/F2、R1–R10、G1–G4 matrix 覆盖正反例，包含 mixed reference、audio-only、
  ratio/default、duration 边界、pipeline fan-out、seed 顺序与两个 public endpoint 的 first-only
  行为；文档与实现冲突必须显式暴露。 ^[PR #5752]

## MMH3-2b — media ingress 在解码前限界，request 错误保持 HTTP 400

- 触发：typed `image_reference`/`video_reference`/`audio_reference`、multipart
  `input_reference(s)`、URL/data URL 下载、ffprobe/transcode 或 `start_time_seconds`。
- 强制：typed 字段接受单对象或有序 list；multipart 按 MIME/suffix 分类并保持每种媒体的
  顺序。仅 H3 multipart `input_reference(s)` 在读取/解码前执行 bounded read 与 allowlist：
  image≤30 MiB（JPEG/PNG/WEBP/HEIC/HEIF）、
  video≤50 MiB（MP4/MOV，H.264/H.265，若有 audio 则 AAC/MP3）、audio≤15 MiB（WAV/MP3，
  PCM/MP3）。image/video dimension 为 256–5760、ratio 为 0.4–2.5；video FPS 23.976–60。
- 强制：每个 video/audio reference 时长 2–15 秒；video 总时长≤15 秒，embedded video
  audio 与 standalone audio 合并后的 conditioning 总时长也≤15 秒。每个 video 的
  `start_time_seconds` 必须落在 source duration 内并剩余至少 2 秒。只容忍官方双视频
  container probe 的微小 rounding overflow，并裁到剩余总时长；真实 overflow 仍拒绝。
- 强制：typed URL/data-URL video 必须 materialize 为 request-scoped 临时 MP4 source，再交给
  只收 path 的 preparation，成功/异常都清理；path-backed typed video/audio 在下载后由模型
  preparation 检查 file metadata。mixed image+video 只有 model metadata 明示 capability 才放行；
  分布式非零 DiT rank 用已广播的全局 `video_count` 判断 visual 是否存在。
- 禁止：PIL/ffmpeg 转换后才检查原始格式/大小；把 request-facing `ValueError` 变成 HTTP 500；
  用 fake engine 的成功代替 source-path、cleanup 或 cross-model capability 证明。
- 验收：非法计数、multipart 格式/大小及 path-backed media metadata/segment 均在生成前返回
  `OmniClientError`/HTTP 400；覆盖 typed URL/data URL、multipart mixed、unsupported model、
  temp cleanup 和多 rank video+audio。此 pin 的 typed URL/data URL helper 仍先完整
  download/base64 decode；typed image
  还会丢失原始 size/format，因此 multipart 的 bounded/predecode 证明不可外推，属于验证与
  hardening 缺口。API server 中的 H3 专用 helper 也仍有 reviewer 指出的后续泛化重构债务。
  ^[PR #5752]

## MMH3-2c — conditioned VAE 的固定种子必须按实际设备隔离并恢复

- 触发：修改 H3 image/video reference 的 VAE encode、固定 keyframe seed、`fork_rng`、设备
  generator 或 accelerator backend 支持。
- 强制：`encode_image()`/`encode_video()` 在采样前暂时把 VAE 转成 FP32，在
  `torch.random.fork_rng(devices=...)` 内同时播种 CPU default generator 与 active-device
  generator，退出时恢复 RNG state，并在 `finally` 恢复原 dtype；image path 还必须恢复
  `parallel_tiling`。这个 seed 是 conditioned VAE 的固定内部 seed，不能描述成 request seed。
- 禁止：把 PR 文本中的 CUDA+MUSA allowlist 当成目标实现。目标代码实际以
  `parameter.device.type != "cpu"` 为条件，把所有非 CPU device 交给 `torch.get_device_module()`；
  现有实机证据只覆盖 CUDA/MUSA，不能外推 XPU、NPU 或 ROCm RNG 语义。也不能因
  `fork_rng` 最终恢复 state 就宣称并发安全：context 内仍会暂时改写 process-global CPU/device
  generator，重叠调用需要序列化或独立并发证明。
- 验收：同 seed 的 image/video condition latent 可重复，正常和 encode 异常后 CPU、目标设备
  RNG state、dtype 及 image tiling state 都恢复；CPU 与每个声称支持的 accelerator 分支分别
  覆盖，并加入重叠调用 fence。PR 中拟议的专用 VAE 单测按 review 被删除，目标 commit 没有
  新增测试；PR body 的 focused/实机结果只能作为外部验证，不能冒充已提交回归覆盖。
  ^[PR #5703]

共享 component quantization、checkpoint mapping 与 quality evidence 见
[Diffusion rules](../../components/diffusion/rules.md)。
