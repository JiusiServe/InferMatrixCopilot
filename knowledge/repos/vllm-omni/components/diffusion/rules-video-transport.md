---
title: "Generated-video IPC ownership 规则"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, components]
sources: ["PR #7355"]
---

# Generated-video IPC ownership 规则

## DIFF-VIDEO-IPC-1a — Registered SHM 必须限定 video 并保留完整 cleanup 所有权

- 触发：修改 enable_registered_shm、diffusion pack/unpack、video_output_index 或 CUDA注册失败处理。
- 强制：开关默认 false 且必须 bool；仅 async NVIDIA CUDA D2H stream 的 typed video/明确标记 legacy video tuple 项可注册，其他媒体、latents、audio、CPU/HIP与sync保持原路。等待 producer event，再将原 bits copy 到注册 SHM，BF16用 uint16 view运输并view恢复。完成copy才unregister/发布handle；pack按完整成功才提交字段，失败unlink本次ownedsegments。CUDAcleanup不确定时保留mapping/source/stream引用到worker退出并拒绝新注册，不能unmap仍在用的地址。
- 禁止：把去掉hostcopies说成没有D2H；widen BF16在GPU额外分配FP32；提前清registered flag让失败重试遗漏；把一项video标记推广整个(video,audio)tuple；1MB routing门槛不是普遍性能阈值。
- 验收：video/nonvideo、marked/unmarked、BF16bits、CPU/HIP/sync、register/copy/unregister失败和多字段pack失败覆盖；copy完成前mapping仍live，失败不发布半包。大小payload分开评估，不能从历史大video样本宣称当前主线普遍加速。 ^[PR #7355]

## DIFF-VIDEO-IPC-1b — Borrowed receiver view 必须持有 mapping 到最后一个消费者

- 触发：修改 borrow_on_unpack、NumPy/Torch view 或 SHM name unlink。
- 强制：借用view以base owner携带SHM lease，unlink名称后mapping仍活；np.asarray、slice和torch.from_numpy继续持有owner直到最后消费者释放。普通路径仍copy后close/unlink；BF16view保留bitwidth/dtype。
- 禁止：只在ndarray subclass属性挂owner而被np.asarray丢掉；unlink立即close仍在消费的mapping；跨进程假定Python引用自动转移生命周期。
- 验收：删除原array后保留slice/torchview并消费、最后引用释放、fallbackcopy与dtypeview回归；同RGB和完整decodeMP4内容对照，不能仅校验descriptor。 ^[PR #7355]
