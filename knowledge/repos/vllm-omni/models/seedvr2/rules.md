---
title: "SeedVR2 restoration 规则"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #8102"]
confidence: high
---

# SeedVR2 restoration 规则

## Direct 代码快速入口

| PR 描述信号 | 规则组 | 第一批源码 |
|---|---|---|
| OOM、clip pixels、VAE tiling、Ulysses | SEED-1a | `diffusion/models/seedvr2/config.py`、`pipeline_seedvr2.py::validate_clip_size` |
| 长视频、overlap、loop、PTS | SEED-1b | `long_video.py::_window`、`_segment`、`_run` |
| CRF、lossless、loopback、color | SEED-1c / SEED-1f | `long_video.py::_restore`、`_encode` → `pipeline_seedvr2.py` 的 correction helpers |
| job restart、cancel、upload、TTL | SEED-1d / SEED-1e | `long_video.py::register_routes`、`_status`、`_cleanup` |

## SEED-1a — clip admission 必须按实际 padded 帧数和显存 profile 计算

- 触发：修改 SeedVR2 frame/pixel budget、VAE sharding 或环境变量 override。
- 强制：先把输入帧数补到 `4n+1`，用 padded 数检查 max frames、单帧 pixels 与总 clip
  pixels。sharded profile 同时要求 VAE tiling、height sharding、Ulysses degree≥4；自动
  budget 使用可见设备中最小显存并限制在校准边界内，无法读显存时取保守校准下界。
  显式正整数 `VLLM_OMNI_*` override 优先，承认其可超出经校准的 OOM 保护。
- 禁止：按未 padded 数放行；仅 degree 达标就启用放宽 budget；忽略异构设备中的最小
  显存；把某台卡的 clip calibration 当成所有 degree/硬件都不会 OOM。
- 验收：覆盖 padded 边界、各个 sharded 条件缺失、degree 4 与更高 degree、显存未知/
  异构、合法 override 与非法非正值；实际 GPU memory/质量另用目标 profile 核验。^[PR #8102]

## SEED-1b — 长视频窗口必须服从 admission，拼接必须保持目标帧数与连续时间轴

- 触发：修改 long-video window size、source loop、overlap blending 或 encoder PTS。
- 强制：窗口取 clip-pixel/max-frame/long-window 上限内最大的 `4n+1`，且大于四帧 overlap；
  不能按历史 PR 描述固定为 12 帧。窗口 stride 是实际 batch 长度减四，overlap 用
  `(offset+1)/5` 渐变；source 只在显式 loop 时回绕。输出由一个 encoder 连续写入，
  从 0 按 24 fps 编号，并断言最终写出目标帧数；每个 restored window 校验尺寸、fps、
  帧数与连续 PTS，最多两个待处理 future 保持内存有界。
- 禁止：按固定窗口 stride 跳/重复 source 帧；重置每段输出时间戳；以每段解码成功
  替代整片长度、边界 blend 和 source wrap 的验收。
- 验收：独立 oracle 检查多窗口、短尾段、显式 loop 与不 loop、动态预算变化及四帧
  overlap 的值/索引；输出恰好 N 帧且 PTS 单调连续。7200 帧上限不等于该长度的
  GPU E2E 已完成，长片真实验收另记录目标硬件与结果。^[PR #8102]

## SEED-1c — 内部 restoration hop 的 lossless 与最终视频压缩必须分别核验

- 触发：修改 long-video segment encode、内部 `/v1/videos/sync` 调用或最终 mux。
- 强制：当前 worker 经 loopback HTTP 调用同一 sync route，逐窗保持 lossless codec
  选项、one-step/CFG 1 和 color 参数；shared entrypoint 只通过模型的 `register_routes`
  hook 注册 model-specific 逻辑。source 含音频时保留音轨并转 AAC，音频是否回绕与显式
  `loop_input` 策略一致；无音轨时不补静音。
- 禁止：把已改为 qp=0 的中间 codec 说成 in-process 执行；因为中间 lossless 就保证
  最终 CRF18/yuv420p MP4 像素完全不变；把 loopback 的可达性推广成 TLS/UDS 部署支持。
- 验收：检查每窗调用参数和 restored 输出合同，再独立检查最终 codec、音频 loop、
  时长和色度变化；若改变 transport，覆盖真实 server binding/auth lifecycle。^[PR #8102]

## SEED-1d — 长视频作业必须有单一 owner，并按窗口边界完成取消

- 触发：修改 long-video submission、worker restart、GET/DELETE 或并发作业控制。
- 强制：提交前要求空 prompt、32-bit unsigned seed、1–7200 个目标帧与至少 16 且可被
  16 整除的尺寸，并验证动态窗口大于 overlap。只接受一个 API server process，且同时
  一个 active job；status 原子写入包含
  owner PID。GET 对 queued/running 但 PID 不属于当前 owner 的记录报告 failed。
  DELETE 创建取消标记并先返回 cancelling，worker 在下一窗口边界观察后停止。
- 禁止：重启后让旧 running job 永久显示仍执行；把取消 acknowledgement 当作当前
  GPU 工作已立即停止；取消时释放 owner 让第二个 job 进入尚未排空的资源。
- 验收：覆盖第二次 submission、多个 API server、stale PID、每个 window boundary
  前后取消与结束状态；必须区分 acknowledgement 与实际 worker 停止。^[PR #8102]

## SEED-1e — 上传、job 路径与文件回收必须各自有明确边界

- 触发：修改 long-video upload、job ID、result/status 文件、TTL cleanup 或错误响应。
- 强制：写盘时按 chunk 检查 8 GiB upload cap，空上传拒绝，失败上传清理已建目录；
  在任何 path 操作前验证 32 位 lowercase hex job ID。status 与最终 MP4 经临时文件
  rename 发布，完整 MP4 发布后才写 result marker，未有 result 不开放 download；不能
  把当前直接写出的 result JSON 误称原子提交。TTL sweep 由新 submission 触发，只清理到期 settled/stale-owner
  目录，不清理 active owner；内部异常只在日志保留细节，客户端接收安全分类错误。
- 禁止：用事后 size check 代替写盘限额；未验 job ID 就拼路径；把 submission-triggered
  TTL 写成后台定时回收；将原始 exception/auth/path 暴露到客户端。
- 验收：覆盖超限/空/中断上传、非法 ID、半成品结果、到期与 active 目录、内部错误
  分类；没有新 submission 时文件保留的行为必须符合实际 lifecycle。^[PR #8102]

## SEED-1f — color correction 参数必须从 admission 穿过每个窗口

- 触发：修改长视频 extra_params、color method 或 restoration 后处理。
- 强制：extra_params 是 JSON object；color method 只接受 lab/wavelet/adain/none，null
  使用默认 lab；admission 后对每个 window 保持同一选择。处理 frames 使用有界批次，
  RGB 值的 correction 与最终视频的 chroma subsampling 分别评价。
- 禁止：worker 默默换回默认方法；允许任意 method 在后台才失败；把颜色统计修正
  宣称为逐像素不变或由压缩视频直接证明原始 RGB 值保真。
- 验收：invalid method 在 submission 前拒绝，四种合法 method 分别核对 window forwarding；
  source/target reference 与 bounded batch 输出另用独立数值 oracle 比较。^[PR #8102]

公开 route 与 artifact readiness 见 [Serving 请求规则](../../components/serving/rules.md)；
分布式执行与 VAE ownership 见 [Diffusion 规则](../../components/diffusion/rules.md)。
