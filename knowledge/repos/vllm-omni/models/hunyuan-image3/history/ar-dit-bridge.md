## AR→DiT 数据桥接（2026-04-09 分析）

### 核心发现
HunyuanImage3 和 GLM-Image 的数据流本质不同：
- GLM-Image：AR → `prior_token_ids`（离散图像 token）→ DiT 直接解码
- HunyuanImage3：AR → CoT 文本（`<think>...<recaption>...`）→ 重新走 `apply_chat_template` → DiT 用重编码后的序列

### 当前状态：断的
`ar2diffusion()` 输出 `extra: {ar_token_ids, ar_generated_text}`，但 DiT pipeline `forward()` 完全不读 extra dict。

### 最小修复方案
1. `ar2diffusion`：把 `ar_generated_text` 同时作为 `"cot_text"` 顶层 key
2. DiT `forward()`：加 ~5 行从 `req.prompts[0]` dict 读 `cot_text` 和 `pil_image`

### 负责人
AR→DiT 桥接分给别人做，我们只关心 AR 侧。

**Why:** 这是 IT2I 端到端跑通的最大阻塞项。
**How to apply:** 不要尝试用 GLM-Image 的 token ID 传递模式，HunyuanImage3 必须传 cot_text 字符串。
