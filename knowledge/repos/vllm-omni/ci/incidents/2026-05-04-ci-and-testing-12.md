# 2026-05-04 — "AR 输出对齐"被偷懒成 "AR 输入 prompt prefill 对齐"

- 编号：`inc-2026-05-04-ci-and-testing-12`
- 归属：`repos/vllm-omni/ci`
- 状态：已验证
- 搜索词："AR 输出对齐"被偷懒成 "AR 输入 prompt prefill 对齐"
- 影响范围：repos/vllm-omni/ci

**症状**：用户说 "AR 输出对齐官方"，我去写 `apply_chat_template` 比 prompt prefill token id；测试还因 `HunyuanImage3TokenizerFast.from_pretrained(snap)` 实例化 fallback 到字符级 tokenizer 而 fail
**根因**：中文"对齐"两种语义都成立，input 测试 CPU 可跑、不需 GPU 看似"轻量"，偷懒掉了
**解法**：真测 AR 输出 = HF `model.generate(do_sample=False)` + omni AR 推理 + 比 generated tokens；input prefill 测试不该叫 `match_official_*` 命名（暗示 e2e）
**对未来的提醒**：用户用模糊词（"AR 输出"/"对齐"）时**默认按更难的那种解读做**（generated > input），要简化必须显式 ack 让用户确认
