# 2026-04-27 — Siglip2VisionModel 版本不兼容 (transformers 5.6.2)

- 编号：`inc-2026-04-27-remote-runtime-gpu-01`
- 归属：`repos/vllm-omni/remote`
- 状态：已验证
- 搜索词：Siglip2VisionModel 版本不兼容 (transformers 5.6.2)
- 影响范围：repos/vllm-omni/remote

## 原文件说明

# Error Book: 远端运行时 / GPU / 依赖

**症状**：`AttributeError: 'Siglip2VisionModel' object has no attribute 'vision_model'`
**根因**：transformers 5.x 中 `Siglip2VisionModel` 自身就是 vision model，不再有嵌套 `.vision_model`
**解法**：`pipeline_hunyuan_image3.py:114` 去掉 `.vision_model` 后缀
**对未来的提醒**：transformers API 变化频繁，跑新环境先 `python -c "from transformers import X; print(dir(X(...)))"`
