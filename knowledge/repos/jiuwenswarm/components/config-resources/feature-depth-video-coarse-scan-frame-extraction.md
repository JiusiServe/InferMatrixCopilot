---
title: "视频粗扫抽帧与审核批次门控（analyze_video.py）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L86-L88, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L359-L371, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L307-L323, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L325-L330, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L356-L356, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L52-L74, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L127-L146, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L152-L175, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L43-L49, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L152-L188, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L203-L210, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L343-L354, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L359-L396, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/SKILL.md:L144-L152]
feature: "video-coarse-scan-frame-extraction"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py"]
---

# 视频粗扫抽帧与审核批次门控（analyze_video.py）：实现深读

[功能概览](feature-video-coarse-scan-frame-extraction.md) · [owner 入口](_index.md)

<!-- kb:depth feature=video-coarse-scan-frame-extraction facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5310cd37f0c7f0daa76613078ca1db583c740e29c250dfecdf3edfc6b274ed44 -->
**slug 路径：候选视频须为非 .part 文件，全不合格时回退首候选并仅在不存在时退出**
main 中 slug 目标按 video.mp4、downloads/video.mp4、downloads/video.* 顺序取第一个 is_file() 且非 .part 的候选；无合格候选时回退 candidates[0]，仅当该回退路径不存在时 sys.exit(1)。随后依次 probe_duration、choose_fps、extract_frames、build_review_frames，帧数为 0 则 sys.exit(1)，最后写入 current_batch=1 状态并打印第 1 批路径。

来源：[jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L343–L354](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py#L343-L354), [jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L359–L396](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py#L359-L396)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":354,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py","sha256":"7b815145b58c40e09bd16fd56b49d81328d5bf1630aec642c9a6e13add6a0102","start":343},{"end":396,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py","sha256":"80f43dda831dc770c1dbdd7bf963a76d20fa35a2fd7e9e25199baffd1975a011","start":359}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=video-coarse-scan-frame-extraction facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e0bb1b602c954d7d77fb696aaf670c4011f794f27110e86d826d3169aa174000 -->
**CLI：target 必填，--title/--slug 可选，两个互斥批次旗标触发提前返回**
接受位置参数 target（视频 URL 或 slug）；--title 默认 None（L356 回退为 slug 的下划线替换为空格）；--slug 默认 None（URL 时经 common.resolve_work_slug_for_url 解析）。--current-review-batch 与 --next-review-batch 属互斥组，命中任一即调用 _show_or_advance_review_batch 并 return，不下载不抽帧。

来源：[jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L307–L323](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py#L307-L323), [jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L325–L330](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py#L325-L330), [jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L356–L356](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py#L356-L356)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":323,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py","sha256":"ae79703ad388e714bfd016187c9dcfb39cc6aefc565b6b1341e00eb2655109fd","start":307},{"end":330,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py","sha256":"231084080e68ccf1dbb84d73d02fc9c66b445e6aff5ba4043bc19cc1f1d82e87","start":325},{"end":356,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py","sha256":"1f14e0496031b08e06874bd4c7c0448959963f40ae9c96d580196e34bd182df0","start":356}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=video-coarse-scan-frame-extraction facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1321c297e514e0d41895f55e69d3b569bff7e41e45ad85be459be82fb9a54fa3 -->
**抽帧频率默认由时长自适应：min(BASE_FPS, MAX_FRAMES/时长)**
choose_fps 无可调参数，短视频用 BASE_FPS，长视频按 MAX_FRAMES/时长降频，使总帧数逼近上限；main 中 fps=choose_fps(duration)，interval=1/fps 仅用于日志展示。

来源：[jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L86–L88](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py#L86-L88), [jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L359–L371](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py#L359-L371)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":88,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py","sha256":"5a97c340c0e2e0e9398063462939374461340f9030407d6f5fad982ce7e407ec","start":86},{"end":371,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py","sha256":"4e9c043995ff1f5f22c30a339d7c5eb74868c7a05e5bef7e97146b23b8394a83","start":359}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=video-coarse-scan-frame-extraction facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=aa3ccf7355428579fd1066349656a48ea742062c00cfa13699d1a0432d53219d -->
**ffprobe/ffmpeg 经 subprocess 调用，PIL 用于审核 JPEG 编码**
probe_duration/extract_frames 以 subprocess.run 调用外部 ffprobe/ffmpeg（timeout=common.OPERATION_TIMEOUT_SECONDS），FileNotFoundError 与非零返回码被转换为 RuntimeError（超时异常未被捕获）；_encode_review_jpeg 用 PIL Image 打开、转 RGB、LANCZOS 缩放并保存 JPEG。二者不在系统内时脚本无法工作。

来源：[jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L52–L74](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py#L52-L74), [jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L127–L146](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py#L127-L146), [jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L152–L175](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py#L152-L175)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":74,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py","sha256":"2398b684ee348ffe82a5bbdd22926f351220091f2a1454becd1d5b020483d750","start":52},{"end":146,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py","sha256":"b0987d8de8bc191cf3ad7e23e15c8edfcb536b225a7c30f544f7536cf7712155","start":127},{"end":175,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py","sha256":"991c96ec90eb1409532a0ed98cff52e5399346bf5860206a2323f6756c403f66","start":152}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=video-coarse-scan-frame-extraction facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=60fb784f4c9c797e71ebc5ada01ded130d29f1c801807c12bf5b15bca464ab6b -->
**审核 JPEG 代理压低模型读取体积，代价是每帧/每批字节预算超限即 RuntimeError 失败**
设计推断（非作者历史意图）：

受益：原始 frames/ PNG 保持不变，审核走 480x270/384x216、quality 50-60 的 JPEG 代理以控制读取体积（推断自常量与注释）。成本：_encode_review_jpeg 四次尝试后仍超过 REVIEW_MAX_BYTES=45*1024 会抛 RuntimeError，build_review_frames 在任一批字节总和超过 REVIEW_BATCH_MAX_BYTES=225*1024 时抛 RuntimeError，阻断完成。

来源：[jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L43–L49](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py#L43-L49), [jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L152–L188](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py#L152-L188), [jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py:L203–L210](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py#L203-L210)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":49,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py","sha256":"f15f87fdd473647bfaa6805b6e921c42d83ebe0cae718043752c2f5b9d108acb","start":43},{"end":188,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py","sha256":"2fd94e3545135a4ee04c99cd78d3a5378a8dd093d2e94ea0c52c29bd67ef6cea","start":152},{"end":210,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/scripts/analyze_video.py","sha256":"66cc56b013caea434a993b2bc2279f98186f915560e5a9bad89d4f08a12e773d","start":203}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=video-coarse-scan-frame-extraction facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=adf55fac2bc32650f0bb7d68a13ad9242bb04db8455f2fb197b00f2b18e808a3 -->
**SKILL.md 记载的手动验证流程（未执行）**
文档中的人工验收步骤（本轮未执行）：

SKILL.md 给出具体命令：analyze_video.py "<video_url_or_slug>" --title "..."，并说明短视频 0.5fps、长视频均匀覆盖且总帧数最多 90、每批最多 5 帧，首次只打印第 1 批审核帧路径，完成后追加 --next-review-batch 获取下一批。这是文档记载的手动流程，本次未执行；未提供覆盖该脚本的自动化测试证据。

来源：[jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/SKILL.md:L144–L152](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/SKILL.md#L144-L152)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":152,"path":"jiuwenswarm/resources/agent/workspace/skills/skill-omni-creation/SKILL.md","sha256":"96378a8ce86fec06c64a903e67b79ce2e00d98dece8a2528fa6df7a4947704f6","start":144}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
