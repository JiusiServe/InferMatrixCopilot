# 2026-05-05 — 主观对图先于 grep 日志，导致 "FA3 是 bug" 误判

- 编号：`inc-2026-05-05-painterly-debug-methodology-misses-01`
- 归属：`repos/vllm-omni/models/hunyuan-image3`
- 状态：仅历史
- 搜索词：主观对图先于 grep 日志，导致 "FA3 是 bug" 误判
- 影响范围：repos/vllm-omni/models/hunyuan-image3

## 原文件说明

# Painterly bug — 调查方法上的踩坑

painterly 调查过程中**调查方法本身**反复犯的错。根因和总览见 [Painterly 错题索引](_index.md)。

---

**症状**：用 `DIFFUSION_ATTENTION_BACKEND=TORCH_SDPA` env override 后跑出来的图，跟之前 baseline run（理论 FA3）"看起来"猫更卡通，于是宣告"FA3 是 painterly 的主要源头"。

**根因**：`vllm_omni/diffusion/models/hunyuan_image3/pipeline_hunyuan_image3.py:341` 在 pipeline `__init__` 里硬编码 `os.environ["DIFFUSION_ATTENTION_BACKEND"] = "TORCH_SDPA"`，**HunyuanImage3 永远走 SDPA**，FA3 从来没被调过。两次 run 都是 SDPA，肉眼差别只是 NCCL all-reduce 顺序、worker 启动时间引入的 RNG 抖动。

**解法**：定位 attention backend 必须先 `grep "diffusion attention backend" /tmp/<run>.log`，看实际写到日志的字符串，再下结论。

**对未来的提醒**：
- 别用主观对图作为单一证据下结论。两次 run 的图就算同 seed，TP/NCCL 顺序差也会让小细节跳
- 走代码路径前，先在日志里搜真正被调的实现名（"Using XXX backend"、"FlashAttention"、"sdpa"）
- 如果看到怀疑的 baseline 改动让图变好/变坏，先用 `head -200 /tmp/<run>.log` 找配置 echo，确认改动真的生效

---
