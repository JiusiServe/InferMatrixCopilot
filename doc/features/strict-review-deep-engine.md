# Strict 评审：深度 pass、逐条验证、自证据

> **一览**
> | | |
> |---|---|
> | **状态** | ✅ 已实现，**默认全开**（v13 期） |
> | **做什么** | 面向强生成器重做评审流水线：深度调查/对抗 pass、每条评论一次 agentic 验证、端到端的逐字引用自证据 |
> | **怎么开关** | `review_deep_engine`、`review_deep_max_iters`、`review_verify_comments` |
> | **实测** | [`../evaluation/EVAL-goal-strict-vs-opus5.md`](../evaluation/EVAL-goal-strict-vs-opus5.md) —— val 首胜 8—7，冻结 test 7—8，combined **15—15** |
> | **最大的一课** | 判官是**无工具**的：仓库侧的发现若不带逐字引用的证明，一律被当作臆测扣分。把证据变成自证据是本轮最大的单点收益（4—11 → 8—7） |
> | **后继** | [`review-recall.md`](review-recall.md)（v14/v15） |

---

## 原始 RFC

- 状态：已实现，藏在开关之后（全部默认开）；在 20-PR 战役分片上测量
  （val + 一次性冻结 test）
- 归属：评审流水线（`engine/steps/review/`、`review/planner.py`）
- 证据：`doc/evaluation/EVAL-goal-strict-vs-opus5.md`、
  `eval/dataset/judgments/goal_v13_val/`、`eval/dataset/judgments/goal_v13_test/`

## 动机

Strict 评审流水线当初是**围绕一个弱生成器**设计的：四个窄 lens 在模板里逼出枚举、
紧的工具预算、一个无工具的 reducer，以及 5 条评论的严重度上限。换上官方的
`deepseek-v4-pro`（相对 `[1m]` preview 是一次大的能力跃升）之后，
**那套脚手架本身变成了瓶颈** —— 跨多轮判分扫描测到的症状：

1. **召回损失是机械性的，不是分析性的**：预算上限**删掉了 reducer 已保留的维护者关切**；
   深度规划把小而爆炸半径大的 diff 误路由到不带 ensemble 的 light 档；
   一个 170k 字符的 diff 因 120k 证据上限**丢了 30% 的 hunk**；
   整类问题（爆炸半径、依赖下限、测试完整性、abort 时的生命周期）**没有任何 lens 认领**。
2. **precision 在五种不同配置下都卡在 0.54–0.56**，而 recall 在 0.55–0.86 之间摆动
   —— 因为盲评判官是**无工具**的：它只看得见 diff 和人类 thread，
   所以任何仓库侧的发现（别处的 consumer、CI 通道规则、版本下限）
   **只要评论本身不携带可核验的证明，就会被判为臆测**。

## 设计

三个机制，与既有的 ensemble/reducer 机器组合：

### 1. 混合 pass 集合（`review_deep_engine`，默认开）

full 深度跑两个**深度 pass** —— `investigator`（核心改动优先的自由调查；先验证再断言；
预算纪律：把最后几轮留给归档）和 `adversary`（对那些**系统性被漏掉的类别**做独立搜捕）
—— **外加**两个价值最高的广度 lens（`behavior`、`verification`）。
standard 深度跑 investigator+behavior。light 不变。深度 pass 拿到
`review_deep_max_iters`（32）轮工具回合；**单独测**时它们把主张锚定得很好
（最难的 train 条目上 precision .82）但**覆盖不足**（val recall .55）；
**与广度 lens 一起测**时能守住 recall .71–.86。

### 2. 逐条评论的 agentic 验证（`review_verify_comments`，默认开）

每条合并后的草稿评论都会走一个小工具循环（4 轮、并发 6、共享 diff 缓存前缀），
它必须在 PR-time 树上**重新推导**那条主张：`refuted` 丢弃、`unverifiable` 降一级严重度、
`confirmed` 可以收紧措辞/位置 —— 而**验证失败会保留这条评论**
（这一趟**只能提高 precision，绝不静默地删掉召回**）。
跳过/失败原因被记 trace（`review_comments_verified` / `review_coverage_skipped`）。

### 3. 自证据（起草 + 验证 + 渲染）

**测出来最大的单点杠杆**（val 门从 4—11 变成 8—7）：每条评论的 `evidence` 字段
必须带 file:line **逐字引用**那几行决定性代码，好让一个**只拿着评审和 diff** 的读者
就能核对这条主张。它在起草契约里被强制，由验证器**从它真正读过的代码**重新发出，
渲染时原样保留。

随本 RFC 一起发布的配套改动：`value_flips` diff 信号（**默认值翻转永远不能裁为 light**）、
把 verification lens 放进 planner 的兜底集合、证据上限 120k→260k / reducer 60k→280k、
证据包里加入 commit 时间线 + 确定性的改动符号 consumer sweep（`git grep -nw`）+
逐文件 hunk 定位分页目标、跨 lens 佐证标签与 reducer 的受保护类丢弃规则、
评论预算 8 + 仅证据丰富时才溢出、覆盖率提升 pass（从本次 run 自己的
findings/blockers 里挖出未被覆盖的受保护类关切）、经新的 adapter manifest 键
`knowledge.review_checklist` 注入的知识页
`repos/vllm-omni/review/guides/strict-review-checklist.md`，
以及把 vllm-omni 的模块映射扩到 17 个模块、7 个风险分层。

## 实测结果（盲评 gpt-5.6 判官，3 replicate，对照已录制的 CC+Opus 5）

| 门 | 配置 | 正面交锋（arm—opus） | arm r/p | opus r/p |
|---|---|---|---|---|
| 战役前 | preview 模型，4 lens | 1—4 | .42/.51 | .82/.54 |
| v8 | 官方模型，lens | 3—12 | .86/.56 | .79/.66 |
| v12 | 混合，叙述式证据 | 4—11 | .71/.55 | .81/.66 |
| **v13 val** | 混合 + 自证据 | **8—7** | .857/.555 | .889/.589 |
| **v13 冻结 test**（一次性） | 同上 | 7—8 | .689/.687 | .762/.719 |

新鲜裁决合计：**15—15**，成本约为基线的 1/3
（约 $0.75–1.2/项 vs 约 $1.5–3）。GOLD 潜在缺口条目：pr4810 2/3、
pr4834 三次全清。rubric 均值的差距（.03–.07）**处于同一批基线评审上实测判官漂移的
量级**（±.05–.10）。

## 考虑过的替代方案

- **用更强成员重测 MoA** —— 按 owner 指示排除。
- **只跑深度 pass**（不带广度 lens）：precision 迁移过来了，但 val recall 塌到 .55；
  已否决（门 v11，2—13）。
- **只调预算/reducer**：五种配置把 precision 挪动了 ≤.02；
  **那道缺口是结构性的（无工具判官），不是校准性的**。

## 上线 / 兼容性

三个机制都藏在带 kill switch 的 setting 之后（`review_deep_engine`、
`review_verify_comments`；旧的 lens 集合**逐字保留**，深度引擎关闭时使用）。
离线测试覆盖 pass 选择、验证裁决处理（drop/demote/tighten/fail-open）、
预算/溢出、佐证排序、提升、以及 planner 信号；全套测试和两个知识 validator 都绿。
成本约为旧 lens 流水线的 2–3 倍每项，且**仍比基线便宜约 3 倍**。
`run_copilot_arm.py` 里的 `ARM_JOBS` 支持条目级并行扫描
（端点在 v4-pro 上允许 500 并发请求）。

## 未决问题

1. **两个调参分片都已花光**（8 次 val 提交、1 次冻结 test）。进一步迭代需要 wave-2
   条目（`gt/pr5957*`、`gt/pr5976*`、`build_wave2.py`）在**同一套协议**下判分。
2. 判官协议的**无工具性**如今已经在**塑造评审本身**（冗长的引用式证据）。
   如果产品的真实受众是**维护者**而不是一个没有仓库的判官，
   那么证据的冗长程度应当变成一个**渲染选项**，而不是固定行为。
3. `pr4762`/`pr4954` 那一类损失（宽泛的多关切 PR）仍然存在：**基线在逐条发现上仍然读得
   比 arm 深**。下一个结构性杠杆，是一次**由覆盖率驱动的第二轮调查** ——
   由 reducer 那份"未覆盖 GT 类"checklist 播种，而不是固定的 pass 数。
