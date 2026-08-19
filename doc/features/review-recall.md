# 评审召回攻坚（v14/v15）

> **一览**
> | | |
> |---|---|
> | **状态** | ✅ 已实现，**默认开**，全部带 kill-switch |
> | **做什么** | 补齐召回：调查 duties（清单 13–23）、文档 claims-audit pass、考古工具、覆盖率驱动的第二轮、排序验证账本 |
> | **怎么开关** | `review_second_round`、`review_second_round_max_iters`；按 pass 路由用 `REVIEW_LENS_BACKENDS` |
> | **新增工具** | `diff_stat`、`file_at_base`、`show_commit`、`search_history`、`calc`——只读，经工具桥同样对 harness 后端可用 |
> | **实测** | [`../evaluation/EVAL-v14-v16-recall-campaign.md`](../evaluation/EVAL-v14-v16-recall-campaign.md) —— **Δrecall −.049 [−.097, −.001]，precision 打平**，成本约基线 1/3 |
> | **诚实结论** | 目标是"两项均超基线"，**没有达成**。召回缺口真实但小且集中：20 项里 6 项偏向 arm，单个 item（pr5978）贡献约三分之一 |
> | **前身** | [`strict-review-deep-engine.md`](strict-review-deep-engine.md)（v13） |

---

## 原始 RFC

- 状态：已实现，藏在 setting 之后（默认开）；经 wave-4 门测量 —— 见下方"实测结果"与
  `eval/dataset/results/model_comparison.md`
- 归属：评审流水线（`engine/steps/review/`、`review/planner.py`）
- 证据：wave-2 取证（3 个 trace 分析 agent 跑过已花光的 holdout）、
  train 分片上的 Claude Fable 5 **teacher 臂**
  （`eval/dataset/baselines/teacher_fable5/`）、
  `doc/evaluation/EVAL-goal-strict-vs-opus5.md`
- 前身：`doc/features/strict-review-deep-engine.md`（v13）

## 动机

在长期使用的 claude-sonnet-5 判官下，**每一个** v13 生成器（DS api、经 cursor 后端的
Composer/Grok、MoA）在严格计分的 recall 上都输给 CC+Opus 5
（约 0.29–0.35 vs 约 0.42–0.56），而 precision 打平。逐项分析显示损失集中在五个 wave-2
条目上（三个文档 PR + 5884 + 5550）；结合 GT 交叉引用的 trace 取证**精确定位**了损失：

1. **在 pass 阶段"读到了却没提出来"**（主因）：在每一个被诊断的漏掉里，
   **决定性证据就摆在某个 pass 面前** —— reducer/预算/验证均被排除嫌疑
   （到处都是 `dropped: 0`）。pass 接受了作者的框定（pr5550）、
   以确认模式重新推导数字（pr5863 的内存模型被放行；pr5840 自己的 R²=0.095 无人置评）、
   且**从未打开**那个新代码丢掉了其不变量的树内兄弟文件（pr5550 L1、pr5884 F2）。
2. **报告组装环节的切割**：Validated 渲染在 50+ 行里只按到达顺序留了 8 行；
   在修复后的快照上，**判官的召回质量恰好落在被切掉的 resolved-thread 确认里**。
   三条已验证确认的评论死在 cap-8 + 仅证据丰富才溢出的门上（pr5957）。
   锚点未解析的仓库侧评论渲染成 `file:?`，被判为含糊而扣分。
3. **文档饥饿**：纯文档 diff 被规划为 light（单 pass、无协议），而 holdout 的 30% 是
   文档 PR，其 GT 正是**主张订正**；**每一条臂在那里都只跑到基线约一半的 recall**。
4. **pass 死亡**：耗尽预算的深度 pass 有时会以**空消息**回答那次被强制的最终答复
   （pr5976：两个 pass、各 50 次工具调用、**交付零个候选**）。
5. **工具缺口**：那些判官决定性的基线动作 —— `git diff --stat base..HEAD`、
   读 base 版本的文件、`git show`/`log -S` 考古、评估 PR 自己的算术 ——
   **在只读工具集里根本无法表达**。

在 train 分片上跑的 Claude Fable 5 **teacher 臂**（与基线用同一套 pinned CC harness）
确认了这些类别并补充了更多；它的共享契约 producer 普查抓到了 pr4870 的 GOLD 潜在缺口
（正是人工评审漏掉的 #4910 双轴机制）。teacher 和 Opus **都表现出这些职责**；
而我们的 v13 prompt **一条也没有编码** —— 这支持"**流水线缺口**"而非"模型能力缺口"。

## 设计

### 1. 调查职责（prompts.py checklist 13–21 + pass 聚焦）

从 Opus/Fable 动作的**并集**蒸馏而来，每条都配一个实测范例：
主张账本（核验 PR 正文里每一条可核查的主张；`[claim-verified]`/`[claim-refuted]`
findings 行）；兄弟对照（新增类/文件 → 读树内的孪生体；不变量增量；具体的去重提案）；
PR 自己的数字（用 `calc` **证伪**，**绝不确认模式**）；合并态重校验（语义合并审计）；
producer/consumer 契约普查（含 dummy-run/平台孪生体）；模式/变体矩阵与大声失败检查；
死旋钮重算 + 注释审计；缓存病理；分发链路守卫（teacher 唯一一次误报，
被编码成一条**precision 保护**）。resolved-thread 确认成为一等输出（`[resolved]` 前缀）：
在被修订过的 head 上，**读者拿评审去核对的大部分正是它们**。

### 2. 文档 pass（`_REVIEW_DOCS_PASS`）+ planner 深度

纯文档/文档为主的 diff：**只有确实很小时**才 light；中等 → standard，大 → full
（planner 规则；资产/配置附带项不再把文档 PR 推进灰区）。深度引擎把代码形状的广度 lens
换成一个文档 pass：主张审计（对着代码树**证伪**事实性/量化陈述）、
用户路径走查（命令端到端、下载模式 vs 重启碰撞）、
两种渲染约定下的链接/pin/导航机制，以及缺失警告的适用范围。

### 3. 考古 + 数值工具（`review/repo_tools.py`）

`diff_stat`、`file_at_base`、`show_commit`、`search_history`（git，固定 argv、
输入受校验、输出有界）与 `calc`（AST 白名单算术）。它们作为 step 提供的额外工具出现在
**每个评审 pass 和验证 pass** 上；对 harness 后端则由桥侧从 `scope.root` 重建
（补上了 provider-registry M1 那块"额外工具"缺口的这一片）。

### 4. 覆盖率驱动的第二轮（v13 RFC 未决问题 3；`review_second_round`）

在 reduce+promote 之后，那些**既无评论、也无 findings 行**的改动文件 ——
外加一个"主张未核验"信号 —— 播种**一次**有界的 pass
（`review_second_round_max_iters` 16），它必须对每个空洞**要么提出一条已验证评论，
要么记下 `[validated]`/`[resolved]`**。对已保留评论有近重复守卫；新增项同样要过逐条
评论的验证 pass。

### 5. 报告组装修复

Validated 账本改为**排序**（`[resolved]`/`[claim-*]` 在前）并封顶 14，
而不是按到达顺序在 8 处截断；即使评审不"丰富"，溢出也会渲染那些被切掉的已验证确认评论
（未验证的尾部仍需过丰富门）；锚点未解析的评论渲染成 `file:~declared` 而不是 `file:?`
（发布时仍按仅正文处理）；仓库侧发现的验证 pass 证据**必须携带**
"本 diff 未改动、存在于 PR-time 树中"的证明，好让**只看 diff 的判官**能对它分类。

### 6. 循环稳健性

在**真实发生过工具调用之后**出现的空模型回复，会得到**恰好一次**大声的追问
（循环中途以及预算耗尽的强制最终答复处）——
**一个空的最终答复，是唯一严格劣于任何部分答案的结果**。
覆盖率提升的 prompt 去掉了模棱两可：被提升的缺陷保持**指令性力度**
（"could you confirm…?" 这种措辞**实测**把一个命中 GT 的关切变成了一个不计分的提问）。

## 成本

文档 PR 从 light 移到 standard/full（约 15% 的条目上约 2–3 倍）；
第二轮在有覆盖空洞的条目上至多加 1 个 pass；工具是子进程级的廉价。
**这条臂仍然远低于基线 $/项的一半。**

## 上线

一切都藏在 setting 之后（`review_second_round`，以及既有的深度引擎/验证开关）；
**旧路径原封不动**。离线测试覆盖新的 planner 规则、文档 pass 选择、
第二轮（触发/跳过/近重复）、溢出门、账本排序、锚点回退、循环追问，
以及每一个新工具（含 calc 的沙箱）。知识 checklist 页按 teacher 蒸馏出的仓库先验重写
（注入上限 4k→7k 字符）。

## 实测结果（在各道门之后补记）

train 探针（v14，2 个 sonnet replicate）：7—12—1，arm r .608 vs opus .609
（**recall 打平** —— 此前被 sonnet 判分的臂都在约 .28–.35），arm p .785 vs .765。
**wave-3 门第 1 次尝试测到的是坏掉的机器，不是这套设计**：pass 的最终答复死在 16k
补全上限上（一个文档 pass 恰好吐出 16,000 token），修复轮在 8k 处**再次截断**且只有
头部窗口，而灰区 LLM planner **自官方推理模型上线以来一直在静默失败**
（它的思考吃完了 400-token 上限、一个字都没吐出来 ——
**两个战役里每一个灰区条目都掉进了 2-pass 的 standard**）。
第 2 次尝试（机器已修）：5—25，损失被重新定位到"职责 vs GT 不匹配"上，
随后被 wave-3 取证刻画出来（**验证偏置倒置**：主张账本**赞许地**记下了那些 GT 事实；
test/gate 认知论、文档信息架构、CI 经济性这几类无人认领）。
v15 编码了那些类别（checklist 22–23、文档 IA 扩展、账本残余提升、逐 hunk 第二轮），
外加 reducer 失败路径的坍缩。

wave-4 干净门，三次 DS-core 提交（v15 r1、把 cheap seat 放在 v4-flash 上的 v15 r2、
把 Fable 放进 adversary 和第二轮座位的 v16），外加一行 Composer cursor 后端。
原始胜负计数 10—20、11—19、6—23—1、4—24—2。

**统计上正确的读法（见 `eval/dataset/paired_analysis.py` 和结果表）是
"在测量精度内打平"，不是"更优"。** 在这里跨判分集比较原始 rubric 均值是**无效的**：
基线自己的 recall 均值在**给同一批基线评审打分**的三组里读作 .335 / .338 / .416
（±.08 的判官漂移）。在每条 verdict 内部配对、并按 item 聚类 replicate 之后，
在 90 条 verdict 上汇总得到 Δrecall −.070 [−.161, +.021]、
Δprecision +.015 [−.025, +.055] —— **两个区间都跨零**。
本 RFC 的一个早期修订版曾从原始均值宣称 precision 高于基线；**该主张已撤回**。

这轮战役**确实**建立的：这条臂在约 1/3 的成本下达到打平（$0.97/项 vs $3.09）；
总体 recall 差距由 10 个条目里的 3 个承担（其余 7 个在 ±.06 内）；
v15 偏 precision（在两次独立 replicate 上 Δp +.029/+.022，**符号一致**），
而 v16 偏 recall（新鲜分片上最好的 recall .336）并在**流水线内部**复现了 pr4870 的
GOLD 缺口捕获；以及在实测的 item 级 sd（.127）下，分辨 .07 的差异需要约 32 个条目
—— 这正是 wave 5 去扩充新鲜池、而不是再跑一次 10 条目裁决的原因。
一次 v15 replicate 曾因 DeepSeek 402 余额中断而作废（已隔离），充值后重跑。

## 未决问题

1. wave-3（`build_wave3.py`，分片 `holdout3`）是晋升门；wave-2 已花光
   （为这轮取证打开了 GT/理由），**只能做冒烟**。
2. 第二轮目前按 文件覆盖 + 主张覆盖 播种；**reducer 的丢弃原因仍未接线**
   （未来某轮的候选种子）。
3. 修复后快照上的 GT 测的是**对 resolved thread 的参与度**，不是找 bug；
   `[resolved]` 通道正是瞄准这一点 —— **判官在规模上是否给它计分，正是那道门要测的。**
