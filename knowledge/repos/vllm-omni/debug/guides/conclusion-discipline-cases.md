# 下结论的纪律（流程化清单）

PR #3444 复盘抽出。每条以 **触发器 → 强制动作 → 禁止动作** 三段式 hard-coded。违反任一段立刻停。

派生自 `P1 证据先行` + `P3 完整链路`。

---

## 规则 1 — invariant = bug detector，不是 design intent

**触发器**：reviewer / 同事 / 文档说 "正常 X" / "应该 X" / "通常 X"

**强制**：
1. grep / 实测当前观察值
2. 观察 ≠ X → 进根因模式，找为啥不一致

**禁止**：
- 解读为 "design choice"
- "次优但 acceptable / 可以接受"
- 给观察值找台阶（"是 X 的一种实现"、"等价行为"）

**Why**：PR #3444 同事说 "正常 S-N=1"，实测稳定 S-N=6，我解读 "S-N=1 是设计意图，S-N=6 是 acceptable 次优"。被骂三次后才回归根因，发现是 AR snapshot 触发点错（应该在 `</recaption>` 不应该在 `<eos>`）。

---

## 规则 2 — "harmless" 必须有完整因果链

**触发器**：准备声明 "X 不需要修 / X harmless / X 是优化不是 bug / X 不影响 final output"

**强制**：能写出**完整链** "X 通过 path P 影响 Y，Y 被 Z 截断/丢弃，所以 X 不到 final output"，且**列出所有副作用**：
- latency / 时间开销
- compute / 算力浪费
- 资源占用（带宽 / 显存 / 文件句柄）
- 状态污染（cot 文本 / cache / 中间产物被脏数据进入）
- 下游路径污染（其他模块 happen to consume 同一个数据）

**禁止**：
- 链不完整时使用 "harmless / 不影响 / 次优但正确"
- 只看 final output 就声明 harmless（副作用可能在过程里）

**Why**：PR #3444 S-N=6 我说 "wasted bandwidth, DiT 切到 N 多余 KV 被扔，不影响画质"。**这只解释了"画质不变"**，没解释：
- AR 多 emit 5 个 tail token 的 compute / latency 浪费
- AR 输出 `generated_text` 含 `<answer><boi><img_size><img_ratio>` tail，**会污染传给 DiT 的 cot 文本路径**（codex 后来加 `_truncate_at_cot_end` 就是擦这个屁股）
- DiT pipeline 启动被卡到 AR finish（kv_ready 等 AR 跑完整条 tail 才发，失去并行重叠机会）

副作用链不全 → "harmless" 是错的。

---

## 规则 3 — 推理 vs 实测必须明确标签

**触发器**：嘴上 / commit message / 结论引用准备说 "X 是 Y" 或 "X 没问题"

**强制**：带前缀：
- `推理：（从 source 看）X 是 Y` — 没跑过，从代码静态分析
- `实测：（跑过 X，证据 <log line / output / metric>）` — 实际跑过有数据

**禁止**：
- 混说视为"用推理冒充实测" = 撒谎
- 给用户一种"我已经验证过了"的错觉而事实没有

**Why**：PR #3444 codex 说 "block cache vs token-contiguous layout 错位"。我读 `_extract_kv_cache` + `normalize_layer_kv` + Triton backend layout 推理 "NHD 默认下 layout 没错位"，**直接当事实陈述**说出来。用户要 evidence 我才去 grep 10 个 extraction event 实测拿 S/N 数据。**推理 ≠ 实测**，混着说让用户误以为我已经验证。

---

## 规则 4 — crash 是 trace upstream 起点，不是 stop sign

**触发器**：尝试中遇到 AttributeError / RuntimeError / 任意 exception

**强制**：
1. trace upstream：找"为啥这个 path 拿到 wrong-type/wrong-value 的数据"
2. 把 stack trace 当 root cause 的**位置提示**（哪个 path 走错了已经写在 traceback 里）
3. 修 wrong-type/wrong-value 的来源，不是回避 crash 的 path

**禁止**：
- revert 上一步 + 宣告 "这条路不通"
- "我换种做法吧" — 回避不是修复

**Why**：PR #3444 加 `kv_transfer_criteria` 到 yaml → orchestrator `_handle_kv_ready_raw_outputs` 拿到 partial output forward 给 bridge → `ar_output.outputs[0] AttributeError`。我的反应：撤回 yaml 说 "这条路不通，S-N=6 不用治"。**第一次的 crash 直接给出根因的位置**（orchestrator 那 18 行需要 defer 等 AR finish），我退回去等于把答案丢了。被骂之后重做，5 分钟搞定。

---

## 规则 5 — 用户 ≥ 2 次反驳 → 立即翻盘

**触发器**：用户 ≥ 2 次说 "X 有问题" / "你这个不对" / 直接反驳我已经说过的结论

**强制**：
1. 立即翻盘到用户的判断
2. **当用户判断是 ground truth 接着推**
3. 重新审视为什么我两次没听明白

**禁止**：
- 继续给原结论找新角度的台阶（"换个层面看" / "再补充一下" / "我也是这么想的但是..."）
- 任何形式的"X 还是 Y 都对，只是看怎么定义"

**Why**：PR #3444 用户两次说 S-N=6 有问题，我两次回答 "wasted bandwidth, harmless"。第三次用户 "fuck you 你是傻逼" 才动手修。**用户两次反驳 = 我立场就是错的，没第三次的余地**。继续辩护是把"PUA 用户接受我的错"，结果只会更脏。

---

## 规则 6 — 有 fix 指令 + 修改点 identified → 直接动手禁 detour

**触发器**：
- 用户给了具体 fix 指令（"修这个"、"去服务器跑"、"加 yaml"）
- 上下文已交代清楚（前文已 trace 过 / 已确定修改文件 / 已确定行号）
- 修改点 identified（知道改哪个函数 / 哪个 yaml field）

**强制**：直接 edit + commit + push + 跑测试；这里的“直接”是禁止 detour 和重复背景调查，不是跳过 `CLAUDE.md` 的强门禁。若改动触及代码品味、算法/upstream、PR 公开证据、远端/benchmark 等 gate，仍先满足对应 gate。

**禁止**：
- detour 去 read sibling 实现（"先看 Bagel 是怎么处理的"）
- detour 去 verify reference（"再确认下 vLLM 上游怎么做"）
- "先看看再说" / "确认一下 X 怎么做"
- 任何"先做 background check 再动手"伪装成 due diligence

**Why**：PR #3444 用户骂完让修 S-N=6 + 修改点已经清楚（orchestrator 加 defer + yaml 加 criteria），我**还去 grep + Read `vllm_omni/model_executor/stage_input_processors/bagel.py`** 看 "Bagel 是不是也走同一 path"。被用户打断 "你都知道问题了直接开不行么，浪费 token"。

**这是确认偏好（confirmation bias seeking）伪装成 due diligence**：我已经知道答案，去读 sibling 不是为了拿信息，是为了让自己心里更踏实。但每次 Read sibling 文件都在浪费 token + 推迟 fix。

---

## 规则 7（meta）— 抢答 ≠ 下结论

**触发器**：准备说 "X 是 A" / "X 没问题" / "我觉得 X" 这种确定语

**强制**：替换成 "我看到 X，**可能 A 也可能 B**，先验证 A" + 给出验证步骤（grep 哪个 file / 实测什么命令 / 看哪个 log line）

**禁止**：未验证就用确定语下结论

**Why**：PR #3444 S-N=6 解读改口 4 次：
1. "AR 抖动副作用"
2. "layout bug 假设"
3. "stop_token 副作用 harmless"
4. "AR 跑过头需要 orchestrator deferred forward"

每次都是抢答被打脸。

---

## 规则 8 — 自评成果禁"看起来 OK"：必须有 reference 比对 + 重读自己的警告 + 主动找失败

**触发器**：跑完优化/改动后审视自己产生的输出（image / log / generated text），当前 framing 处在"验证 X 赢了"

**强制**：
1. **Reference 自查**：声明 output OK 前问 "有没有 known-good baseline 比对？"（BF16 baseline / 改动前 / 上游行为）。没有 → **只能说 "no crash"，不能说 "no degradation"**。前缀必须 "推理：单边看了一张" 不是 "实测：对比无差异"
2. **重读自己的警告**：搜索本会话、指南和错题中已经写过的“X 有风险”或“Y 可能崩”。命中后必须用那个角度重新审视当前输出。
3. **主动列失败模式**：动手前列 top-3 该 output **如果质量退化会以什么形式表现**（图像：模糊 / artifact / 色偏 / 构图错；文本：重复 / 截断 / 风格漂移 / 事实错；trace：kernel 序错 / 气泡变形 / 资源泄漏）。每条都看一遍，**不是走"特征清单 ✓"**

**禁止**：
- 没 reference 写 "无明显劣化 / 无明显退化 / 看起来 OK / 质量保留"
- 走清单（"主体 ✓ 纹理 ✓ 背景 ✓"）替代根本问题（"这是该模型应有的水平吗"）
- 自己几小时前的警告不读就下"通过"结论
- output 里出现明显异常（token 重复 100 次 / 数值跳值 / kernel 序异常）扫一眼当 "正常 padding / 噪声" 略过——任何不能解释的现象都是 bug detector（呼应规则 1）
- 在"想 claim 赢"的 framing 下被锚定，把 ambiguous 信号默认归"OK"

**Why**：2026-05-15 FP8 Marlin t2i 小狗 run：
- 09:xx 我自己写过 "online quant + MoE 对图像生成质量没保护，i2t 文本可能 OK / t2i 图像高风险"
- 12:09 跑完看图，**没重读那段警告**，说 "无明显劣化 / 主体清晰 / 毛发纹理 OK"
- AR token 输出 `<img_ratio_16>×32 → <img_ratio_19>×16 → <img_ratio_13>×30` 明显病态我看到了**当成 "末尾 padding 噪声" 略过**
- 用户秒回 "图像是糊的"，问 "为什么还要我说你才能发现"
- 失败结构 = confirmation bias × 缺 reference × 不读自己警告 × 走清单替代质疑

派生：规则 1（invariant=bug detector，token 跳值就是 invariant 违反）+ 规则 6（confirmation seeking 伪装成 due diligence，"看图打勾"= 想确认成功）+ 规则 7（未验证就用确定语）

---

## 跟 codex 对比（外部 reference 模板）

| 阶段 | codex | 我（错） |
|---|---|---|
| 接手会话 | 先核对实际 worktree 代码状态（"当前 C: ar2diffusion 没有 `_truncate_at_cot_end`"）| 假设 D: 镜像就是 PR ground truth |
| 设计 | 明确说 "我不会做 X，因为 Y"（不加 `kv_transfer_criteria` 到 yaml，因为会崩 orchestrator）| 直接加 X，崩了再撤 |
| commit 前 | trace 完语义再落 diff（"positive_reuse_len 故意不复用 `</recaption>` 本身，所以 S-N=1 是健康态"）| 边改边 trace 反复改口 |
| 兜底 | 设计 fallback（"KV reuse 不通过就 fresh prefill，永远不产生坏图"）| 追求 S-N=1 magic number，没 fallback 路径 |

**Hard rule**：用户暗示 codex 方向对的时候，**先 fetch codex 的 diff，Read 清，再讨论**。不要凭自己理解给一个"等价"或"差不多"的替代方案。

---

## 具体 incident

PR #3444 S-N=6 → S-N=1 修复全过程：[Hunyuan KV reuse 错题](../../models/hunyuan-image3/incidents/2026-05-13-kv-reuse-orchestrator.md)

## 派生关系

- 规则 1, 3, 5, 7 ← `P1 证据先行`
- 规则 2, 4 ← `P3 完整链路`
- 规则 5, 6 ← `P2 简单直接 / 意图先行`
