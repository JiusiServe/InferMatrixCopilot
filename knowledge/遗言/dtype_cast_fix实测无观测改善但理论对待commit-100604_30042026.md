# 遗言：dtype cast fix 实测无观测改善但理论对，dtype fix commit pending

> 生成时间: 2026-04-30 10:06:04
> 项目路径: D:\vllm-omni\workflow-starter

## 项目背景

vLLM-Omni × HunyuanImage-3.0-Instruct。80B 多模态 MoE 模型。
本次会话场景：让 vllm-omni IT2I AR 输出与 HF 官方 baseline **对齐**——用户最初投诉 omni 离线 IT2I 输出"丢失描述细节"。
远端：`47.79.124.13:31230`，模型在 `/mnt/models/hub/models--tencent--HunyuanImage-3.0-Instruct/snapshots/2ec2c78bee7d4b94157341fba86c4c2c7b1858b2/`。
worktree：`D:/vllm-omni/wt-hunyuan-t2t-sdpa-fa`，分支 `feature/hunyuan-t2t-sdpa-fa`。

## 本次会话目标

排查 omni vs HF 输出差异的根因，逐项修复，做到尽可能 byte-identical 对齐。

## 已完成的工作

### Commit 推到 zuiho-kai + TaffyOfficial fork（共 4 笔有效修复 + 2 笔文档）

| commit | 内容 |
|---|---|
| `42ee44b6` | Siglip2ImageProcessorFast 在 transformers ≥5.x 返回 list 的 squeeze 崩溃修复 |
| `80617a1d` | T2T `build_prompt` 改 instruct 格式（早版） |
| `88d16caa` | 统一 i2t/it2i_*/t2i_* 用 instruct chat 模板，trigger 在 `Assistant:` 之后（**最关键修复**——main 分支 IT2I greedy 死循环 garbage 的根因）|
| `80e0237f` | `A:` → `Assistant:` 匹配 HF tokenizer 实际输出（token 72803）|
| `42c2f349` | 新增 `build_prompt_tokens()` 走 prompt_token_ids 路径，绕过 BPE 跨段 merge——文本 input_ids 与 HF byte-identical |
| `0a63ab5e` | docs：解释 `<timestep>` slot 用 `<img>` 占位与 HF 等价（embedding 层等价，单点改坏） |
| `a7a5ab3f` | docs：解释 image preprocessing 已对齐 HF（resize/crop math + VAE normalize 一致） |

### dtype cast fix（**改完未 commit**——这是 pending 状态）

`vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py`：
- `process_image()` line 876：删 `.to(dtype=torch_dtype)`，让 `vae_pixel_values` 保留 fp32
- `_vae_encode()` line 1424 入口加 cast：`if images.dtype != self.vae.dtype: images = images.to(dtype=self.vae.dtype)`
- 删 line 845 `torch_dtype = ...` 已不用的赋值

**实测**：pixel-level 数值与 HF byte-identical（fp32 mean=0.157296 完全一致）。但 VAE encoder 内部第一个 conv 层照样 cast 到 bf16，所以**最终 latent 与 cast 前 byte-identical**——greedy/sampling 输出都没观测变化。**理论对，工程上 0 退化 0 改善**。

### 数据点确认（保存在 `D:\vllm-omni\workflow-starter\it2i_t2t_outputs\`）

| 文件 | 来源 | 长度 | 状态 |
|---|---|---|---|
| `MAIN_BRANCH_omni.txt` | 主线 main 无 fix，greedy | 2267 | ❌ 无 `<think>`，`image_1` 死循环 6 次 |
| `MAIN_BRANCH_sample.txt` | 主线 main 无 fix，sampling | 8188 | ❌ "吐舌头" × N 完全 garbage |
| `DTYPE_FIX_omni.txt` / `T4571_omni.txt` | fix 后 greedy（含 dtype fix）| 2167 | ✅ 完整 think 分析，0 image_X |
| `SAMPLE_omni.txt` | fix 后 sampling | 2751 | ✅ think + recaption，1 个 image_2 幻觉 |
| `FINAL_hf.txt` | HF baseline greedy | 1354 | 标杆 |
| `SAMPLE_hf.txt` | HF baseline sampling | 1255 | 标杆 |

→ **fix 后是 strict improvement**：从主线的"死循环 garbage"修到"完整结构 + 关键元素全覆盖"。

### memory 更新

- `memory/official_prompt_format.md` —— Instruct 模板细节、BPE 边界陷阱、`<timestep>` 展开差异
- `memory/hf_omni_alignment_method.md` —— 5 步排查方法 + sampler 不可对齐硬下界 + transformers 4.57.1 实测对 omni 输出 0 影响
- `memory/feedback_pr_test_path_audit.md` —— PR #2713/#3107/#2986 测试盲区分析
- `memory/feedback_alignment_debug_pitfalls.md` —— 本会话踩的 4 个对齐调试坑

### claudeception skill 增强

`~/.claude/skills/claudeception/SKILL.md` v3.0.0 → v3.1.0：retrospective 必须扫错误教训 + 容量自适应规模（2-4 / 5-8 / 9+）。

### vllm-omni venv 配置

把 `/root/venv` 的 transformers 从 5.6.2 降到 **4.57.1**（与 HF baseline 对齐）。实测：omni 输出与 5.6.2 时代 byte-identical（pixel preprocessing 不受 transformers 版本影响）。`/root/venv_hf` 仍是 4.57.1 不变。

## 未完成的工作

### 1. dtype cast fix 待 commit

文件 `vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py` 当前 dirty。改动：`process_image` 不 cast bf16 + `_vae_encode` 入口 cast。理论对、零退化、零改善。**用户最后问"要不要 commit"**，会话结束前未答复。

### 2. omni vs HF 仍有 800+ 字差异 + sampling 偶发 image_2 幻觉

**已确认不是**这些层面的问题：
- prompt 格式 ✓ 修了
- BPE 跨段 merge ✓ 修了
- transformers 版本 ✓ 验证 4.57.1 vs 5.6.2 输出 byte-identical
- pixel preprocessing 数值 ✓ fp32 byte-identical with HF
- attention backend ✓ FA = SDPA 验证过
- enforce_eager ✓ 已开（但只关 compile 不影响 model 实现）

**剩下根因（架构级，本会话不可修）**：
- vllm-omni 的 `HunyuanImage3ForCausalMM` 自己写的 forward vs HF 的 `modeling_hunyuan_image_3.py` —— 完全两套独立代码（PagedAttention vs 普通 cache、Triton fused MoE vs python loop、attention metadata 实现差异）
- vllm sampler ≠ transformers sampler —— RNG primitive、logits processor 顺序、Triton fused kernel 都不同 → 同 seed 下 token 序列必然不同（已写进 `hf_omni_alignment_method.md`）

## 关键决策与发现

1. **PR #2713 的 "first 30 token matched, BF16 expected" 是误导**：测试方法绕过了 `build_prompt`，把所有差异糊弄成"BF16 噪声"。本会话证伪——大部分差异是确定性代码 bug。
2. **enforce_eager: true 不让 omni 走 HF eager**——只关 torch.compile/CUDA graphs，model code 还是 vllm-omni 自己的实现。
3. **transformers 4.57.1 与 5.6.2 在 omni 输出上 byte-identical**：之前以为版本差是数值差异源，错了。
4. **Pixel-level fp32 cast 修好但不影响输出**：VAE encoder 内部 cast 抵消了。
5. **同 seed 下 vllm 和 transformers 的 sampler 不可对齐**：硬下界，不要再试。
6. **HunyuanImage3 image expansion 用 `<img>` 占 timestep slot 与 HF `<timestep>`等价**：embedding 层都被 timestep_emb(0) 替换。单点换 token id 会触发 image_2..N 幻觉（破坏 routing）。

## 下一步建议

**优先**：
1. 决定 dtype fix 是否 commit。建议 **commit**——理论对（pixel-level fp32 与 HF 一致）+ 零退化 + 不会成为 future deeper alignment 工作的瓶颈。Commit 后所有 5 个 fix commit 都在分支上。
2. 整理 PR 描述——把"main vs fix"对比作为 PR 说服力的核心证据，而不是"fix vs HF"（永远对不齐）。

**如果用户想继续深挖**：
- A. 跑多 seed sampling 统计 image_2 幻觉率（5+ seeds），评估这是 deterministic bug 还是 RNG 路径 luck
- B. dump 两边在 `</think>` 位置的 logits（top-20 token + 概率），看 omni 是不是把 `<|endoftext|>` 给的概率比 HF 低 —— 这是 forward 实现差异的最直接证据
- C. 不做了，承认架构级差异不可消除，按 sampling 模式跑生产 + 把 top_k 调到 50 抑制 sampling 尾部尾乱

## 关键文件清单

| 文件 | 作用 |
|---|---|
| `D:/vllm-omni/wt-hunyuan-t2t-sdpa-fa/` | 本次会话主 worktree，分支 `feature/hunyuan-t2t-sdpa-fa` |
| `D:/vllm-omni/wt-main/` | 本次会话新建的 origin/main worktree（用于对比基准）|
| `examples/offline_inference/hunyuan_image3/end2end.py` | `build_prompt` + 新增 `build_prompt_tokens` |
| `vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py` | dtype fix dirty 状态 + `_get_prompt_updates` + `embed_multimodal` + `_vae_encode` 全部已注释清楚 |
| `D:/vllm-omni/workflow-starter/it2i_t2t_outputs/` | 所有对比输出 + README + FINAL_README |
| `D:/vllm-omni/workflow-starter/memory/` | 4 个新增 / 更新的 memory 文件 |
| `~/.claude/skills/claudeception/SKILL.md` | 加强了错误教训扫描的 v3.1.0 |
| 远端 `/tmp/test_step1_e2e.py` | 主测试脚本（IT2I greedy）|
| 远端 `/tmp/test_it2i_omni_sample.py` | sampling 测试脚本 |
| 远端 `/tmp/it2i_ar_tp2.yaml` / `_v2.yaml` | greedy / sampling 配置（max_tokens=2048 v2 是 HF 对齐版） |
| 远端 `/tmp/input_0_0.png` | 测试用 demo image |
| 远端 `/root/venv` | omni venv，**已降到 transformers 4.57.1** |
| 远端 `/root/venv_hf` | HF baseline venv，transformers 4.57.1 |
| Branch on Github | `zuiho-kai/feature/hunyuan-t2t-sdpa-fa` + `TaffyOfficial/feature/hunyuan-t2t-sdpa-fa` 都已 push 到 commit `a7a5ab3f` |

## PR 描述要点（写给下次会话用）

**关键说服力**：
- main 分支 IT2I greedy 是结构性坏的（`MAIN_BRANCH_omni.txt` 2267 字 image_1 × 6 死循环）
- main 分支 IT2I sampling 是完全 garbage 的（`MAIN_BRANCH_sample.txt` 8188 字 "吐舌头" × N）
- fix 后 greedy 完整 think 分析（`DTYPE_FIX_omni.txt` 2167 字 0 幻觉）
- fix 后 sampling 完整 think + recaption（`SAMPLE_omni.txt` 2751 字 1 个 image_2 小幻觉，但比 main 强一个数量级）

**不要承诺的事**：
- byte-identical with HF —— 不可能（vllm sampler ≠ transformers sampler，PagedAttention ≠ contiguous cache）
- 消除 image_X 幻觉 —— 是 vllm-omni vs HF forward 实现差异的副作用，不是 prompt-level bug

**回归测试建议**：跑 `--modality text2text` 是 prompt 格式 bug 的最强 canary（无 DiT 兜底）。
