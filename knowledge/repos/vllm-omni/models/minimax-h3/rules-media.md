---
title: "MiniMax H3 媒体输入与精度规则"
created: 2026-09-02
updated: 2026-09-02
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #5752", "PR #5829", "PR #5978", .buildkite/cuda/test-nightly.yml, vllm_omni/diffusion/models/minimax_h3/pipeline_minimax_h3.py, vllm_omni/diffusion/models/minimax_h3/reference_video.py, vllm_omni/entrypoints/openai/api_server.py, vllm_omni/entrypoints/openai/serving_video.py, vllm_omni/entrypoints/openai/video_api_utils.py, vllm_omni/inputs/data.py, tests/diffusion/models/minimax_h3/test_minimax_h3_contract.py, tests/e2e/accuracy/minimax_h3/test_minimax_h3_i2va_ref2va_similarity.py, tests/entrypoints/openai_api/test_video_server.py]
confidence: high
---

# MiniMax H3 媒体输入与精度规则

## MMH3-2a — task、reference、shape 与多输出必须作为一个输入矩阵维护

- 触发：H3 `t2va`/`fl2va`/`ref2va`、reference 计数、frame index、canvas、duration 或
  `num_outputs_per_prompt`。
- 强制：FL2VA 接受一张首/尾帧或两张有序首尾帧，signature 仅为 `[0]`、`[-1]`、
  `[0,-1]`，未显式给出时一张默认 `[0]`、两张默认 `[0,-1]`。Ref2VA 必须至少有一项
  image/video visual reference；image≤9、video≤3、standalone audio≤3、总数≤12，允许
  image-only 及 image/video/audio mixed matrix，但拒绝 audio-only。
- 强制：输出固定 24 FPS、32 kHz audio、duration 4–15 秒。省略 width/height 时
  `short_edge` 只能为 768；T2VA 即使同时给出 width/height，仍必须显式选择 `21:9`、
  `16:9`、`4:3`、`1:1`、`3:4`、`9:16`，因为 named ratio 在 explicit-dimension branch
  之前解析。FL2VA 跟随首图 geometry 并忽略通用 ratio override，Ref2VA 默认 `16:9`，
  `adaptive`/`auto` 是该默认的 alias。^[PR #5829]
- 强制：`num_outputs_per_prompt` 仅为 1–10，各输出 seed 是 `seed + output_index`；pipeline
  tensor output 与未被公开 caller 使用的 `generate_videos()` 保留 fan-out。此 pin 上 public
  async job 与 `/v1/videos/sync` 都调用 `generate_video_bytes()`，多输出时告警并只持久化/返回
  `artifacts.videos[0]`；不得把 recipe 的“async 返回全部”描述当成实现证据。
- 强制：Ref2VA video frames 和 embedded/standalone audio conditions 都以生成时域为上界：
  ffmpeg 用 `target_frame_count`；embedded audio 用
  `min(source_segment_duration,target_frame_count/24)`；standalone audio 用
  `num_frames/(sampling.fps or 24)`。source segment `duration_seconds` 仍单独保留作
  admission/metadata，不得被 bounded conditioning 覆盖。
- 禁止：把 partition 名当输入能力；FL2VA/Ref2VA 权重分区仍需与 task 匹配。
  `max_duration_seconds` 先转 float 并在任何 rank branch/collective 前拒绝 `<=0`；
  否则 rank 0 raise 可使其他 rank 卡在 broadcast。实现没有 `isfinite` 检查，
  NaN/+inf 可越过前置 guard 并在 rank 0 后续失败；这是多 rank 验收缺口。
- 验收：以 F1/F2、R1–R10、G1–G4 matrix 覆盖 mixed reference、audio-only、
  ratio/default、duration、fan-out/seed/public first-only；另覆盖 video/embedded/standalone audio
  的生成时域上界、frame-count/FPS 一致性与非零 rank 非正 duration 在 collective
  前 fail-fast。^[PR #5752] ^[PR #5978]

## MMH3-2b — media ingress 在解码前限界，request 错误保持 HTTP 400

- 触发：typed `image_reference`/`video_reference`/`audio_reference`、multipart
  `input_reference(s)`、URL/data URL 下载、ffprobe/transcode 或 `start_time_seconds`。
- 强制：typed 字段接受单对象或有序 list；multipart 按 MIME/suffix 分类并保持每种媒体顺序。
  仅 H3 multipart 在读取/解码前 bounded read：image≤30 MiB（JPEG/PNG/WEBP/HEIC/HEIF）、
  video≤50 MiB（MP4/MOV，H.264/H.265，audio 若有则 AAC/MP3）、audio≤15 MiB
  （WAV/MP3，PCM/MP3）。image/video dimension 256–5760、ratio 0.4–2.5、video FPS 23.976–60。
- 强制：每个 video/audio 2–15 s，video 总时长≤15 s，embedded+standalone audio
  conditioning 总时长≤15 s。`start_time_seconds` 在 source 内且剩余至少 2 s；
  只容忍官方双视频 container probe 的微小 rounding overflow 并裁到剩余时长，
  真实 overflow 仍拒绝。
- 强制：typed URL/data-URL video materialize 为 request-scoped MP4，成功/异常都清理；
  path-backed media 下载后由 model preparation 检 metadata。mixed image+video 只在 model
  metadata 声明 capability 时放行；非零 DiT rank 用已广播 `video_count` 判定 visual。
- reference transcode 用 `libx264rgb -crf 0 -pix_fmt rgb24`，让 Qwen3-VL 抽样和
  video VAE 消费同一 prepared RGB stream。sampling 对该 stream 只 decode 一次；
  测试必须同时断言完整 sampled arrays、block timestamps 和单次 decode，
  不得只测 call count。这证明相同 prepared pixels，不证明任意 decoder 的
  byte identity。^[PR #5978]
- 禁止：PIL/ffmpeg 转换后才检原格式/大小；让 request-facing `ValueError` 变 HTTP 500；
  用 fake engine 成功代替 source-path、cleanup/capability 证明。验收要覆盖非法计数、
  multipart 限界、path metadata/segment、typed URL/data URL、mixed、unsupported model、temp cleanup
  和多 rank video+audio，均在生成前给 `OmniClientError`/HTTP 400。typed URL/data URL
  仍先完整 download/base64 decode，typed image 仍丢原 size/format，故 multipart bounded
  证据不可外推；H3 API helper 仍有泛化重构债务。^[PR #5752]
- retained nightly 只有 I2VA（192 frames/8 s）和 Ref2VA（124 frames/5 s），共用
  1344×768@24 FPS、50 steps、seed 0、SSIM≥0.97/PSNR≥34 dB。这是 video-pixel
  similarity + AAC 32 kHz stereo container metadata gate，不比 audio samples/duration/content、
  lip sync 或 A/V alignment。assets 有 SHA-256，模型 revision 仍是 mutable `main`。
  nightly 声明 4×H100；PR 的 I2VA 0.975190/35.981286、Ref2VA 0.980577/
  42.650204 来自 4×B300 外部运行，不是 checked-in 结果。T2VA 因严格 gate
  未达标被删除，仅表示无 retained pixel-level gate，不表示功能不支持。^[PR #5978]
