# 调试漏斗纪律

PR #3444 HunyuanImage-3.0 IT2I online 方图 bug 复盘。Codex 与我并行调同一个 bug：

| | 我 | Codex |
|---|---|---|
| 总耗时 | ~2h | ~10min |
| 远端启停次数 | 4 次（每次 ~2min model load）| 0 |
| 怀疑点 | 同时持有 5 个（stop set / target_h+w / image_size / M-RoPE / sampler 调用），每个都跑实测 | 收敛到 1 个：`serving_chat.py:2353` 找 AR stage 的判定字段跟 yaml 不一致 |
| 真因发现路径 | 改了 4 处代码全部 revert，才回到起点，再静态找 | 静态读 3 个文件：serving_chat / pipeline.py / yaml |

派生自 [P1 证据先行] + [P4 单变量隔离归因] + [B29 用户给 fix 指令直接动手] 的反向场景。

---

## 规则

**触发器**：debug bug 时同时持有 ≥2 个独立怀疑，或想 "重启服务跑一次试试"

**强制**：

### (a) grep 优先于实测

| 动作 | 成本 | 信息量 |
|---|---|---|
| 启动 server + 1 次 AR/DiT 实测 | ~2-3 min | 1 个 hypothesis 的 yes/no |
| `grep -rn <symbol> <dir>` | <1s | 全文件分布 |
| 读完整调用链（4 个文件 × 50 行）| ~3 min | 整条 path 的所有 fork 点 |

**规则**：连续 ≥2 次实测仍未定位 → **强制回静态**，禁止再启动服务，直到找到新的怀疑点。

### (b) 怀疑收敛到 1 个再动手

**禁止**：同时持有 ≥2 个独立怀疑时动手 fix 任何一个。

**强制流程**：
1. 列出所有怀疑点
2. 标相对概率排序（基于 grep 出的实际代码分支多少 / yaml 字段是否真存在 / 历史 commit 是否动过）
3. 静态二分排除：每个怀疑找一个**便宜的反证**（grep 一行能否证伪）
4. 收敛到 1 个 → 动手 fix
5. 不能收敛 → AskUserQuestion 让 user 给方向，**禁脑补**

**Why**：N 个怀疑里只有 1 个真，先 fix 错的 (N-1)/N 概率 = 80%（N=5）需要回滚的修改。今天 4 处全 revert 印证。

### (c) user 给诊断 ≠ user 给修法

| user 说 | 我应该做 |
|---|---|
| "改 X 文件的 Y 函数加 Z 参数" | **直接动手**（B29 适用）|
| "这个函数没验过 think_recaption 场景" | **先 framing 修法 scope**：是改这个函数 / 周边 / 还是别的层？AskUserQuestion 给 ≤3 个修法选项 |
| "之前修好了，现在又出来了" | **先 trace timeline**：什么时候修的、什么时候坏的，**禁猜测立刻改代码** |

**禁**：基于 user 单句诊断脑补"按上游真值表改函数 + 加 image_size 参数 + 改 2 处 call site"——这是**修法范围 inflation**，B29 不适用。

---

## 信号识别

- 列怀疑点超过 2 个，每个想"试试"
- 想"重启 server 验证一下" → 先问：能不能 grep 出答案？
- 想"按 X 修一下试试" → 先问：诊断闭环了吗？
- 想"等 Codex/user 给方向" → 先问：我的 grep 做完了吗？
- 修改 ≥3 个文件后才发现方向不对要 revert → 早期没收敛信号

---

## PR #3444 实测复盘

**用户报现象**：online `/v1/images/edits` 输出方图 1024x1024，offline 同 prompt 是 1216x832。

**我的 debug 路径**（错的）：
1. user 提"stop 差异" → 我钻 `resolve_stop_token_ids` 真值表，加 `image_size` 参数 + 2 处 call site → scp → 跑 → 行为没变 → revert
2. 又怀疑 `target_h/target_w` inject → 加 `model_arch != "HunyuanImage3ForCausalMM"` guard → scp → 跑 → PNG 字节完全一样 → revert
3. 加 init-time PROBE 打 `engine_output_type` 值 → 跑 → 显示 "latent" / generation mode 都正确 → 死路
4. 加 sample-time PROBE 打 `last_token` / `forced` → 准备跑

**Codex 的 debug 路径**（对的）：
1. 从最近的 `incidents/` 查相似错误
2. 读 `end2end.py` (offline) 和 `serving_chat.py` (online) 找 stop 覆盖逻辑
3. 看到 offline `for sp in params_list: if hasattr(sp, "stop_token_ids"): sp.stop_token_ids = ...` 是"对所有非 diffusion stage 覆盖"
4. 看到 online `for stage in stage_configs: if is_comprehension: comprehension_idx = idx` 是"找 is_comprehension=True"
5. 看 yaml `is_comprehension: false` → online 找不到 AR stage → stop 不覆盖 → 钉死

**根因**：`vllm_omni/deploy/hunyuan_image3.yaml:25` `is_comprehension: false`。"`is_comprehension`" 在 vllm-omni 内部语义是"tokenizer-owning AR stage"，不是用户视角的 comprehension task。yaml 写错。

**修法**：`is_comprehension: true` + 6 行注释解释字段语义。1 文件 7 行。

---

---

## PR #3611 (graph mode) 实测复盘

**现象**：HunyuanImage3 AR 开 `enforce_eager: false` 报：
```
ConstraintViolationError: Constraints violated (L['inputs_embeds'].size()[0], L['positions'].size()[0])
You marked L['inputs_embeds'].size()[0] as dynamic but your code specialized it to be a constant (32768)
```

**我的 debug 路径**（错的）：
1. 抓第一行"两个 size 不一致" → 加 `torch._check(inputs_embeds.size(0) == positions.size(0))` 直接进 forward override → 跑 → dynamo `Eq(s59, s80)=False` 新错
2. 切到 `shape_invariants` hook（grep 发现 llama_model_invariants 就抄）→ 跑 → 退回原错
3. 准备开 `TORCH_LOGS=+dynamic` 深挖

**Codex 的 debug 路径**（对的，4 行 fix）：
1. 看报错第二行"specialized to constant 32768"→ 问 32768 哪来的 = yaml `max_num_batched_tokens`
2. 问 positions 实际 shape 是什么 = `(3, num_tokens)` MRoPE
3. 看 `@support_torch_compile` 默认行为 = 把每个 Tensor 参数 dim 0 标 dynamic
4. 对照 = positions dim 0 是常量 3 不是 num_tokens，**装饰器配错位**
5. grep 兄弟模型 `dynamic_arg_dims.*positions` → Qwen2/Qwen3/Ming 都传了 `"positions": -1`
6. 补 `dynamic_arg_dims={"positions": -1, ...}`，4 行结束。10.7× 提速

**我具体哪里失败**：

| 失败点 | 我做的 | 该做的 |
|---|---|---|
| 报错多层信息抓错层 | 抓第一行的 size 名字，框定成 "tie 它们" | 抓第二行的 "specialized to N"，N 是哪来的 → 哪个 dim 声明错 |
| 没看数据 | 默认 positions 跟 input_ids 一样是 `[num_tokens]` | grep yaml `mrope_section` 或 `rotary_emb(positions...)` 调用方就发现 (3, T) |
| pattern match 过快 | grep `shape_invariants` 找到 llama 例子就抄，没想 llama positions 是 1D 而我是 2D | grep 应该是 `dynamic_arg_dims.*positions`，兄弟 MRoPE 模型才是对照 |
| 重复失败没切 framing | 第二次 fail 后继续在 "tie them" 思路上变 API | 同方向 2 次 fail = framing 错，回退到 "为什么会报不一致——是声明错还是真不等" |

**派生规则**：

### (d) 多层报错信息抓深层不抓表层

torch.compile / dynamo / 类型推断报错经常有两层：
- 表层："X 和 Y 关系错"（命名两个具体 entity）
- 深层："某个声明被某段代码烤成常量 N"（指向声明配置 / 调用代码哪里坏了）

**规则**：报错里出现"specialized to constant N" / "marked dynamic but ... constant"，先 trace N 是哪来的（一般是某个 yaml config / max size），从那条链反推**哪个 dim 在源头标错**。**禁**先做"让 X == Y 在运行时成立"的 runtime check——那是表层 fix。

### (e) framework 错误前先 sanity check tensor 真实形状

调 torch.compile / fx / dynamo 错误前，先确认每个被命名 tensor 的 runtime shape，**不**按"标准 LLM tensor shape 约定"假设。多模态模型（MRoPE / interleaved attention / cross-modal positions）经常打破"dim 0 = num_tokens"约定。

**规则**：torch.compile 报错前问 3 件事：
1. 这些 tensor 的 runtime shape 是什么？（不是看类型注解，看实际 forward 调用方）
2. 装饰器自动推断的 dynamic dim 跟实际 shape 哪一维是 num_tokens 一致吗？
3. 兄弟模型（同 attention family / 同模态架构）的 `@support_torch_compile` 调用模板是什么？

---

## How to apply

**debug 开始时**：
1. 列怀疑点 + 相对概率
2. 看每个怀疑点能不能 1 行 grep 证伪
3. 二分到 ≤1 个再动手

**实测之前自审**：
- 我现在多少个未排除候选？≥2 个 → 停，回去 grep
- 上次实测验证了哪个 hypothesis？答不上来 → 那次实测白跑

**user 说话后自审**：
- user 说的是现象 / 诊断 / 修法？
  - 现象 → 我去 trace
  - 诊断 → 我先 framing 修法 scope（AskUserQuestion），别脑补
  - 修法 → 直接动手（B29）

---

## 链接

- 上位原则：P1（证据先行）、P4（单变量隔离）
- 相邻：[execution principles](../../../../framework/debug/guides/execution-principles.md)（用户给方案直接执行）、[conclusion discipline](../../../../framework/debug/guides/conclusion-discipline.md)（推理 vs 实测前缀）、[style bias debug](style-bias-debug.md)（静态 diff > dump）
- 反向：[B29] user 给具体 fix 指令禁 detour（这条管的是给 fix 指令的场景，本规则管诊断不给 fix 的场景）
- 派生硬规则：CLAUDE.md B32
