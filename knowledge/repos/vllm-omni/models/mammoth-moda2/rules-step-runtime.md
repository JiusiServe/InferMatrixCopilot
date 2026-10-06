---
title: "MammothModa2 step runtime 规则"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, models, diffusion, scheduler]
sources: ["PR #7954"]
confidence: high
---

# MammothModa2 step runtime 规则

## MAMMO-STEP-1a — continuous batch 必须按 request 保存 scheduler、conditioning 与 CFG 进度

- 触发：修改 `prepare_encode/denoise_step/step_scheduler/post_decode`、Mammoth admission compatibility key 或 step deploy。
- 强制：admission 将模型实际解析的 step count 写回 sampling；step 模式按 height/width 分组，request 模式仍将 total steps 纳入 compatibility key。每个 `StepRequestState` 独占 seeded latents、timesteps、FlowMatch scheduler、step index、text/image conditioning、guidance scale 和 CFG range；encoding 从 step 0 重启，不宣称支持 mid-denoise resume。标准 text/negative tensors 放 InputBatch，AR image embeddings/masks 放 request extra，并在当前 batch 重新 pad；只有全部无 image layout 或全部完整 image layout 才可同批。每 request 只有一个 latent row；按其 `step_index/total_steps` 决定 CFG，混合 active/inactive 时仅替换 active rows。
- 禁止：因为 batch 中某 request 需要 CFG 就对全部 rows 强制 blend；共享 mutable scheduler/RNG 或用 batch-global进度；丢弃 resolved step count；将不同 spatial layout 或缺一半的 AR image condition 静默合批。
- 验收：交错 arrival、不同 total steps/CFG windows、不同 seeds 的请求对照独立执行；覆盖 mixed active CFG、negative fields、AR image layout 错误与一行一请求断言；每 request scheduler step 后递增自己的 index，final decode 使用其 latents 和 VAE scaling/shift。^[PR #7954]
