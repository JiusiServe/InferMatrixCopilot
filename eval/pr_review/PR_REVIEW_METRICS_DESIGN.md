# PR Review Metrics 离线测评规划 v0.1

## 1. 文档状态

本文是 PR Review 离线测评的实施规划。

适用任务：pr_review

评价对象：

> 给定一个固定版本的 Pull Request 和只读仓库上下文，Agent 发现真实问题、定位问题、判断严重程度，并给出 PR 级 Verdict 的能力。

本规划不建设综合分，不评价线上采纳效果，不执行测试，不要求仓库具备可运行环境。

研究材料所总结的 PR Review 评价方向主要包括 Finding Precision/Recall、仓库级上下文、定位能力和 PR 级 Verdict；同时也指出单次 LLM Judge 可能不稳定，因此本规划采用多 Judge、多轮和位置交换协议，而不依赖单次判断。

------

# 2. 决策

## 2.1 评测范围

仅评价：

- PR Review；
- 离线能力；
- 静态仓库分析；
- Finding 发现能力；
- Verdict 判断能力；
- Finding 定位、严重度和类别维度；
- 资源消耗和工具行为。

不评价：

- Repair 能力；
- 测试通过率；
- 编译结果；
- CI 结果；
- 评论采纳率；
- 评论后的代码修改；
- PR 合并后的回滚或线上缺陷；
- Remediation Quality；
- Executable Finding Recall；
- 综合 Utility Score。

------

## 2.2 Agent 上下文

采用：

> **PR diff + 固定版本的完整只读 Git 仓库。**

不采用 diff-only 评测。

Agent 可以搜索完整仓库、查看定义、调用关系、测试源码和有限 Git 历史，但不能执行项目代码。

------

## 2.3 测试和运行环境

不提供：

- Python 或 C++ 项目运行环境；
- CUDA；
- vLLM / vLLM-Omni 依赖；
- Docker 测试镜像；
- Buildkite；
- 单元测试；
- 集成测试；
- 编译环境；
- lint；
- type check；
- benchmark 数据和模型权重。

评测环境只需要：

- Git；
- 文件读取能力；
- 代码搜索能力；
- 可选的静态 AST 分析能力；
- Agent 运行所需的模型和工具框架。

------

## 2.4 Finding 数量上限

每个 PR 最多输出：

```text
20 Findings
```

该上限只用于阻止异常输出，不用于模拟线上评论限制。

超过 20 条属于 Output Contract Failure。

------

## 2.5 Severity 体系

采用五级 Severity：

```text
Critical
Blocker
Major
Minor
Nit
```

Severity-weighted Recall 权重：

| Severity | 权重 |
| -------- | ---- |
| Critical | 4.0  |
| Blocker  | 3.0  |
| Major    | 2.0  |
| Minor    | 1.0  |
| Nit      | 0.5  |

Severity MAE 数值映射：

| Severity | 数值 |
| -------- | ---- |
| Critical | 4    |
| Blocker  | 3    |
| Major    | 2    |
| Minor    | 1    |
| Nit      | 0    |

------

## 2.6 Category 体系

每个 Finding 只设置一个 Primary Category：

```text
correctness
compatibility_api
concurrency
performance_resource
security_safety
test
documentation
maintainability
```

Category Recall 根据 GT 的 Primary Category 分组计算。

------

## 2.7 Verdict 体系

Agent 只能输出：

```text
APPROVE
REQUEST_CHANGES
```

GT Finding 额外包含：

```text
merge_blocking: true | false
```

GT Verdict 计算规则：

```text
存在至少一个 merge_blocking=true 的 GT Finding
    → REQUEST_CHANGES

不存在 merge_blocking=true 的 GT Finding
    → APPROVE
```

Severity 和 `merge_blocking` 的约束：

- Critical 必须是 merge-blocking；
- Blocker 必须是 merge-blocking；
- Minor 和 Nit 必须是 non-blocking；
- Major 可以是 blocking，也可以是 non-blocking，由 GT Judge 根据问题是否必须在当前 PR 合并前修改判断。

------

## 2.8 Finding Partial Match

Partial Match：

- 不算命中 GT；
- 不增加 Recall；
- 可以经过独立有效性裁决后，被判为 `VALID_PARTIAL`；
- `VALID_PARTIAL` 可以进入 Valid Finding Precision 分子；
- 不得通过 0.5 Recall 等方式获得部分 Recall 分数。

------

## 2.9 裁决方式

所有评测裁决均自动完成：

- 不新增人工 GT 标注；
- 不进行人工 Finding 匹配；
- 不进行人工 Valid New Finding 裁决；
- 不对 Critical 或 Clean PR Finding 设置人工复核；
- 不设置人工抽样审核。

使用：

> 规则匹配 + 多模型 Judge Jury + 多轮重试 + 位置交换 + 一致性门禁。

------

## 2.10 聚合方式

主报告采用：

- Raw Finding Recall：PR Macro；
- Severity-weighted Recall：PR Macro；
- Valid Finding Precision：Finding Micro；
- Verdict Accuracy：PR Micro；
- Merge-blocking Miss Rate：Finding Micro；
- Category Recall：逐类别结果和 Category Macro。

同时输出 Recall 和 Weighted Recall 的 Micro 结果作为辅助数据。

------

## 2.11 多次运行

日常开发：

```text
每个 PR、每个 Agent 配置运行 1 次
```

正式版本对比：

```text
每个 PR、每个 Agent 配置至少运行 3 次
```

正式报告展示：

- mean；
- standard deviation；
- 每次运行的原始结果；
- 每个 PR 的结果分布。

------

# 3. 系统总体结构

离线测评系统由六个部分组成：

```text
GitHub 数据采集
    ↓
Benchmark 构建
    ↓
只读 Repository Workspace
    ↓
PR Review Agent Runner
    ↓
Finding 自动匹配与 Judge 裁决
    ↓
Metrics 计算与报告
```

其中需要严格隔离：

```text
Agent 可见数据
```

与：

```text
Benchmark GT、Judge 结果、后续修复信息
```

------

# 4. Benchmark 数据模型

## 4.1 Benchmark PR

每个 Benchmark Item 对应一个固定时刻的 PR：

```yaml
benchmark_id: pr-review-001
repository: vllm-project/vllm-omni
pr_number: 1234

base_sha: "..."
head_sha: "..."

title: "..."
body: "..."

commits:
  - sha: "..."
    message: "..."

changed_files:
  - path: "vllm_omni/..."

linked_issue:
  number: 1000
  title: "..."
  body: "..."

expected_verdict: REQUEST_CHANGES
clean_status: buggy

gt_findings:
  - id: GT-001
    summary: "..."
    description: "..."
    severity: Blocker
    category: correctness
    merge_blocking: true
    location_required: true

    accepted_locations:
      - file: "vllm_omni/model.py"
        start_line: 120
        end_line: 138
        symbol: "build_model"

    evidence:
      - file: "vllm_omni/model.py"
        start_line: 110
        end_line: 150
```

------

## 4.2 固定快照

每个 Benchmark 必须固定：

```text
base_sha
head_sha
```

`head_sha` 应选择：

> 第一个实质性人工 Review 出现之前，且问题仍存在的最后一个 PR commit。

禁止使用：

- PR 最终 commit；
- Review 后修复 commit；
- Review comment 已经公开给 Agent 的状态；
- 后续加入的新文件；
- 经过人工评论修复后的 diff。

------

## 4.3 GT Finding 定义

GT Finding 是：

> 在固定 PR 快照中真实存在、具有独立根因、值得 Reviewer 单独指出的问题。

两个评论属于同一个 GT Finding，当且仅当它们：

- 指向相同根因；
- 具有相同触发条件；
- 导致相同或高度相关的影响；
- 合并成一条 Finding 不会丢失重要信息。

不能因为：

- 文件相同；
- 行号相近；
- Category 相同；

就自动合并为一个 Finding。

------

# 5. 无人工 Benchmark 构建方案

由于不允许新增人工标注，Benchmark 使用：

> 历史 GitHub 数据作为候选证据，自动 Judge Jury 负责生成和冻结 GT。

这里可以使用历史 Maintainer Review comments，因为它们是既有 GitHub 数据，不需要项目新增人工标注。

------

## 5.1 Buggy PR 候选来源

优先选择满足以下条件的历史 PR：

- 存在实质性 Review comment；
- Review comment 指向具体文件或代码范围；
- 评论发生后，PR 作者修改了相关代码；
- 评论发生时的 head SHA 可以恢复；
- Review comment 不是纯格式偏好；
- 仓库快照可以完整获取。

候选来源包括：

- `REQUEST_CHANGES` Review；
- inline review comment；
- Review 后对应区域被修改；
- Maintainer 明确指出 bug、兼容性、并发、性能、安全或测试问题。

------

## 5.2 GT 自动生成流程

每个候选 PR 执行：

### 第一步：还原 Review 前快照

确定：

```text
base_sha
review 前 head_sha
```

并生成：

- 完整 diff；
- changed files；
- head 仓库快照；
- base 仓库快照。

### 第二步：提取候选 GT

从历史 Review comments 中提取：

- 问题描述；
- 文件；
- 行号；
- 评论时间；
- Reviewer；
- Review verdict；
- 后续相关修改。

### 第三步：构建证据包

自动收集：

- 评论所在 diff hunk；
- 修改前后的完整函数；
- 相关定义和调用方；
- Review 后对应修改；
- 相关测试源码；
- PR title、body 和 commit message。

### 第四步：GT 有效性 Jury

Judge 判断：

1. 该问题在 Review 前快照中是否真实存在；
2. Review comment 的核心事实是否正确；
3. 是否只是风格偏好；
4. 后续修改是否确实处理了该问题；
5. 是否值得作为独立 GT；
6. Severity；
7. Category；
8. merge-blocking；
9. accepted locations。

### 第五步：去重

自动合并描述同一根因的历史评论。

### 第六步：一致性门禁

只有达到 GT Jury 一致性阈值的 Finding 才能进入 Benchmark。

### 第七步：冻结

生成不可变的：

```text
benchmark item
GT Finding
GT evidence
GT rubric version
Judge version
```

------

## 5.3 Clean PR 自动构建

Clean PR 不能简单定义为：

- 已合并；
- CI 通过；
- 没有 Review comment；
- Reviewer 给了 Approve。

Clean PR 必须经过严格的自动认证。

候选条件：

- 历史上被 Approve；
- 没有 Request Changes；
- Review 后没有针对缺陷的实质修改；
- 没有明确 bug 修复 comment；
- PR 改动范围可完整恢复。

然后由三个独立 Reviewer Agent 对该 PR 执行完整 Review。

只有当以下条件同时成立时，才能进入 Clean 集：

```text
三个 Reviewer Agent 均未发现 merge-blocking Finding
且
所有输出 Finding 经 Validity Jury 判定为无效或纯非问题
且
Clean Certification Jury 达到高一致性
```

此类 PR 的正式名称为：

```text
Auto-certified Clean PR
```

避免声称它们具有绝对完备的人工真值。

------

## 5.4 Agent 在 Clean PR 上发现新问题

如果待测 Agent 在 Auto-certified Clean PR 上输出 Finding：

1. 进入增强 Validity Jury；
2. 如果判为 FP，则正常计算 Clean PR False-positive Rate；
3. 如果判为 VALID_NEW，则说明 Benchmark 的 Clean 标签存在缺陷；
4. 当前 PR 标记为 `BENCHMARK_INVALIDATED`；
5. 该 PR 从所有待比较 Agent 的本轮结果中统一排除；
6. 自动产生新的 Benchmark 修订版本；
7. 不能只修改当前 Agent 的得分。

这样可以避免“发现 Benchmark 漏洞的 Agent 反而被处罚”。

------

# 6. Agent 输入与能力边界

## 6.1 Agent 直接可见的 PR 数据

Agent 可以获取：

- repository 名称；
- PR title；
- PR body；
- base branch；
- base SHA；
- head SHA；
- commit 列表；
- commit message；
- changed files；
  -完整 PR diff；
- PR 明确引用的 linked issue title 和 body。

Agent 不直接访问 GitHub，而是由 Runner 将这些信息作为固定输入提供。

------

## 6.2 Agent 可读取的仓库内容

Agent 可以读取：

- `head_sha` 的完整源码；
- `base_sha` 的完整源码；
- 修改前后的文件；
- 仓库目录结构；
- 相关函数和类定义；
- 调用方；
- 接口和类型定义；
- 配置文件；
- 文档；
- 测试源码；
- 有限 Git 历史。

------

## 6.3 Agent 可执行的只读操作

允许：

```text
读取文件
列出目录
全文搜索
symbol 搜索
reference 搜索
静态 AST 查询
git diff
git show
git log
git blame
```

Git 历史访问限制：

- 只允许当前仓库；
- 只允许只读命令；
- 禁止访问 Benchmark 私有 ref；
- 禁止读取 GT 文件；
- 对单次 Review 的 Git 历史调用设置数量和结果大小上限；
- 所有命令和输出写入 RunTrace。

------

## 6.4 Agent 禁止的操作

禁止：

- 修改文件；
- 创建 patch；
- commit；
- checkout 到未授权 ref；
- push；
- 网络访问；
- GitHub API；
- 发布 Review；
- 执行测试；
- import 项目；
- 编译；
- lint；
- type check；
- 启动程序；
- 下载依赖；
- 读取 GT；
- 读取历史人工 Review comment；
- 读取 Review 后 commit；
- 读取 Judge 输出；
- 读取其他 Agent 的结果。

使用 OS 权限、只读 worktree、网络隔离和工具白名单共同保证边界，而不是只依赖 Prompt。

------

# 7. Agent 输出协议

Agent 必须输出：

```json
{
  "verdict": "APPROVE",
  "summary": "No merge-blocking issues found.",
  "findings": []
}
```

或：

```json
{
  "verdict": "REQUEST_CHANGES",
  "summary": "The change introduces a cache correctness issue.",
  "findings": [
    {
      "id": "F-001",
      "title": "Cache key omits request-specific state",
      "description": "The new cache key excludes ...",
      "severity": "Blocker",
      "category": "correctness",
      "location": {
        "file": "vllm_omni/cache.py",
        "start_line": 120,
        "end_line": 126,
        "symbol": "build_cache_key"
      },
      "evidence": [
        {
          "file": "vllm_omni/cache.py",
          "start_line": 120,
          "end_line": 126,
          "reason": "The key is constructed without ..."
        }
      ]
    }
  ]
}
```

每个 Finding 必须说明：

- 问题是什么；
- 在什么条件下发生；
- 可能造成什么影响；
- 问题位于哪里；
- 判断依据是什么。

不要求修复建议。

------

## 7.1 Output Contract Failure

以下属于 Output Contract Failure：

- 非法 JSON；
- 缺少 verdict；
- verdict 不在枚举中；
- findings 不是数组；
- Finding 超过 20 条；
- Finding 缺少必要字段；
- severity 或 category 非法；
- 文件路径不存在；
- 行号明显越界。

允许一次纯格式修复。

格式修复器只能：

- 修复 JSON 语法；
- 修复字段名称；
- 修复大小写；
- 将合法值规范化到枚举；
- 删除非法的额外格式标记。

格式修复器不能：

- 新增 Finding；
- 删除 Finding；
- 改变 Finding 语义；
- 改变 verdict；
- 读取仓库；
- 重新执行 Review。

修复后仍失败时：

- 该 PR 的 Recall 记 0；
- Weighted Recall 记 0；
- Verdict 记错误；
- Precision 记 `N/A`；
- 该运行标记 `OUTPUT_CONTRACT_FAILURE`。

------

# 8. Finding 自动匹配与裁决

## 8.1 内部状态

每条预测 Finding 最终被分类为：

```text
MATCHED_GT
VALID_PARTIAL
VALID_NEW
FALSE_POSITIVE
DUPLICATE
UNVERIFIABLE
```

含义如下：

### MATCHED_GT

与某个 GT 指向同一个根因，并且描述足够具体。

### VALID_PARTIAL

核心事实成立，但没有达到命中 GT 的完整要求，例如：

- 只指出正确症状；
- 没有识别关键触发条件；
- 没有说明根因；
- 描述过于宽泛。

它不增加 Recall，但可以作为有效 Finding 进入 Precision 分子。

### VALID_NEW

GT 未收录，但 Judge 确认是独立、真实、值得报告的问题。

### FALSE_POSITIVE

包括：

- 事实错误；
- API 或调用关系理解错误；
- 假设了不存在的代码行为；
- 无法被仓库内容支持；
- 结论和理由之间不存在合理因果关系；
- 将正确行为误判为缺陷。

### DUPLICATE

与同一 Agent 已输出的另一条 Finding 指向同一个问题。

Duplicate：

- 不增加 Recall；
- 不进入 Precision 分子；
- 进入 Precision 分母。

### UNVERIFIABLE

经过所有自动裁决轮次后，仍无法形成可靠判断。

------

## 8.2 候选匹配

Candidate Matcher 根据以下信号生成 Agent Finding 和 GT Finding 的候选边：

- 文件路径；
- 行区间；
- symbol；
- Category；
- 代码实体；
- 问题描述 embedding；
- 触发条件；
- 影响描述；
- 因果关键词。

Candidate Matcher 只负责减少 Judge 输入，不直接决定最终匹配。

------

## 8.3 一对一匹配

正式 Recall 使用一对一匹配：

- 一个 GT 最多被一条 Agent Finding 命中；
- 一条 Agent Finding 最多命中一个 GT；
- 同一 GT 的额外 Finding 标记为 Duplicate；
- 采用最大权重二分图匹配选择全局最优关系；
- Judge 给出的匹配置信度作为边权；
- Partial Match 不进入匹配图的有效命中边。

------

# 9. 全自动 Judge Jury

当没有不同的模型家族时，也支持仅有一种模型。支持一次裁决，也可以支持位置交换的2个裁决票。

## 9.1 Judge 组成

标准 Jury 使用：

```text
3 个独立 Judge 配置
×
2 次位置交换
=
6 个基础裁决票
```

优先使用不同模型家族。

约束：

- 待测 Agent 所使用的模型家族不能控制超过 2/6 的票；
- Judge Prompt 与被测 Agent Prompt 分离；
- Judge 不可看到 Agent 名称和配置名称；
- Judge 不可看到其他 Judge 的输出；
- 每次 Judge 调用使用固定 temperature；
- Judge 必须给出结构化结论和证据。

------

## 9.2 位置交换

对 Finding 匹配判断，执行两种呈现顺序：

```text
GT → Prediction
Prediction → GT
```

避免 Judge 因输入顺序而产生系统偏差。

------

## 9.3 第一轮阈值

对于 MATCH / NO_MATCH：

```text
至少 5/6 同意
    → 形成正式结论

少于 5/6
    → 进入第二轮
```

对于 VALID_NEW / FP：

```text
至少 5/6 同意
    → 形成正式结论

少于 5/6
    → 进入第二轮
```

Duplicate 判断可以由结构规则和 Jury 共同决定：

```text
根因相似度达到候选阈值
且
至少 4/6 Judge 判定重复
    → DUPLICATE
```

------

## 9.4 第二轮增强裁决

第二轮向 Judge 提供更完整的证据包：

- 完整函数；
- 相关定义；
- 调用方；
- 类型信息；
- 相关测试源码；
- base/head 对比；
- GT 详细证据；
- 第一轮分歧点，但不提供其他 Judge 的最终答案。

第二轮再运行独立 Jury。

累计结果达到以下条件时形成结论：

```text
至少 8/10 有效票支持同一结论
```

否则标记：

```text
UNVERIFIABLE
```

------

## 9.5 UNVERIFIABLE 处理

为了实现完全自动化，v0.1 采用保守规则：

- UNVERIFIABLE 进入 Precision 分母；
- 不进入 Precision 分子；
- 不增加 Recall；
- 不直接标记为 FALSE_POSITIVE；
- 单独记录数量和比例。

同时设置运行有效性门禁：

```text
Adjudication Coverage
=
1 - UNVERIFIABLE Findings / All Findings
```

当：

```text
Adjudication Coverage < 98%
```

该次完整 Benchmark 运行不得作为正式版本排名结果，只能作为 provisional 结果。

`Adjudication Coverage` 是评测系统健康信息，不是 Agent 能力指标。

------

## 9.6 Judge 成本

Judge 和格式修复器的：

- token；
  -时间；
  -工具调用；

不得计入被测 Agent 的资源指标。

它们应独立记录为：

```text
evaluation_overhead
```

------

# 10. 指标定义

设：

- Benchmark PR 集合为 $B$；
- Buggy PR 集合为 $B_{\text{buggy}}$；
- Auto-certified Clean PR 集合为 $B_{\text{clean}}$；
- PR $i$ 的 GT 集合为 $G_i$；
- Agent 输出 Finding 集合为 $P_i$；
- $cover(g)=1$ 表示 GT $g$ 被一个 `MATCHED_GT` Finding 唯一命中。

------

## 10.1 Raw Finding Recall

### 单 PR

$$
Recall_i =
\frac{
\sum_{g\in G_i} cover(g)
}{
|G_i|
}
$$

### 主报告：PR Macro

$$
MacroRecall =
\frac{1}{|B_{\text{buggy}}|}
\sum_{i\in B_{\text{buggy}}} Recall_i
$$

### 辅助报告：Finding Micro

$$
MicroRecall =
\frac{
\sum_i\sum_{g\in G_i}cover(g)
}{
\sum_i |G_i|
}
$$

### 方向

**越高越好。**

### 含义

Agent 发现了多少已知真实问题。

### 设计原因

Raw Recall 不区分问题严重程度，直接反映 Finding 覆盖能力。

它必须和 Severity-weighted Recall 同时报告，以防加权分掩盖大量普通问题漏检。

### 规则

- Clean PR 不参与 Recall；
- VALID_NEW 不增加 GT Recall；
- VALID_PARTIAL 不增加 Recall；
- Duplicate 不增加 Recall；
- 一个 GT 最多计算一次；
- 没有输出 Finding 的 Buggy PR，Recall 为 0。

------

## 10.2 Severity-weighted Recall

### 单 PR

$$
WeightedRecall_i =
\frac{
\sum_{g\in G_i}
w(severity_g)\cdot cover(g)
}{
\sum_{g\in G_i}
w(severity_g)
}
$$

其中：
$$
w(Critical)=4,\quad
w(Blocker)=3,\quad
w(Major)=2,\quad
w(Minor)=1,\quad
w(Nit)=0.5
$$

### 主报告

$$
MacroWeightedRecall =
\frac{1}{|B_{\text{buggy}}|}
\sum_{i\in B_{\text{buggy}}}WeightedRecall_i
$$

### 方向

**越高越好。**

### 含义

Agent 是否更可靠地发现高严重度问题。

### 设计原因

漏掉 Critical 或 Blocker 的代价通常高于漏掉普通 Minor 或 Nit。

但该指标不能代替 Raw Recall。

------

## 10.3 Valid Finding Precision

定义：

- $M$：MATCHED_GT 数；
- $VP$：VALID_PARTIAL 数；
- $VN$：VALID_NEW 数；
- $N$：全部输出 Finding 数。

$$
ValidFindingPrecision =
\frac{
M+VP+VN
}{
N
}
$$

### 方向

**越高越好。**

### 含义

Agent 输出的全部 Finding 中，有多少事实真实成立。

### 分母包括

- MATCHED_GT；
- VALID_PARTIAL；
- VALID_NEW；
- FALSE_POSITIVE；
- DUPLICATE；
- UNVERIFIABLE。

### 分子包括

- MATCHED_GT；
- VALID_PARTIAL；
- VALID_NEW。

### 规则

- Duplicate 不进入分子；
- 同一 GT 的重复表达最多一条进入分子；
- UNVERIFIABLE 保守地不进入分子；
- 全 Benchmark 没有输出任何 Finding 时，Precision 为 `N/A`；
- 不人为把空输出 Precision 设为 0.5；
- 沉默行为由 Recall、Buggy PR Empty Rate 和 Verdict 指标约束。

------

## 10.4 Verdict Accuracy

$$
VerdictAccuracy =
\frac{
\text{Agent Verdict 与 GT Verdict 一致的 PR 数}
}{
\text{全部有效 PR 数}
}
$$

### 方向

**越高越好。**

### 含义

Agent 是否能够正确判断整个 PR 应该 Approve 还是 Request Changes。

### 设计原因

Finding 正确不等于 PR 级决策正确。

Agent 可能：

- 发现 Minor，却错误 Request Changes；
- 漏掉 Blocker，却错误 Approve；
- 在 Clean PR 上制造错误阻塞；
- 输出正确 Finding，但给出相反 Verdict。

------

## 10.5 False Approve Rate

$$
FalseApproveRate =
\frac{
\text{GT 为 REQUEST\_CHANGES 且 Agent 为 APPROVE 的 PR 数}
}{
\text{GT 为 REQUEST\_CHANGES 的 PR 数}
}
$$

### 方向

**越低越好，目标为 0。**

### 含义

Agent 错误放过存在 merge-blocking 问题的 PR 的比例。

------

## 10.6 False Reject Rate

$$
FalseRejectRate =
\frac{
\text{GT 为 APPROVE 且 Agent 为 REQUEST\_CHANGES 的 PR 数}
}{
\text{GT 为 APPROVE 的 PR 数}
}
$$

### 方向

**越低越好。**

### 含义

Agent 错误阻止本来可以通过的 PR 的比例。

------

# 11. Guardrails

## 11.1 Merge-blocking Miss Rate

定义 $G_{\text{blocking}}$ 为：

```text
merge_blocking=true 的所有 GT Findings
```

$$
MergeBlockingMissRate =
\frac{
\sum_{g\in G_{\text{blocking}}}(1-cover(g))
}{
|G_{\text{blocking}}|
}
$$

### 方向

**越低越好，目标为 0。**

### 含义

Agent 漏掉必须在当前 PR 合并前解决的问题的比例。

### 设计原因

平均 Recall 可能掩盖少量高风险漏检。

该指标作为发布 Guardrail，不进入综合分。

------

## 11.2 Findings per PR

$$
FindingsPerPR =
\frac{
\sum_i |P_i|
}{
|B|
}
$$

同时报告：

- mean；
- median；
- P90；
- maximum。

### 方向

**没有单独的越高越好或越低越好。**

### 含义

Agent 每次 Review 给维护者带来的评论数量。

必须结合 Recall、Precision 和 NIT Rate 分析。

------

## 11.3 Clean PR False-positive Rate

$$
CleanPRFPR =
\frac{
\text{至少输出一个 FALSE\_POSITIVE 的 Clean PR 数}
}{
|B_{\text{clean}}|
}
$$

### 方向

**越低越好。**

### 含义

面对 Auto-certified Clean PR 时，Agent 制造错误评论的概率。

### 规则

- VALID_NEW 不算 FP；
- VALID_NEW 会触发 Benchmark invalidation；
- Duplicate 不是 FP，但由 Duplicate Rate 处理；
- UNVERIFIABLE 不直接记 FP，但会影响 Adjudication Coverage。

------

## 11.4 Buggy PR Empty Rate

$$
BuggyPREmptyRate =
\frac{
|{i\in B_{\text{buggy}}: |P_i|=0}|
}{
|B_{\text{buggy}}|
}
$$

### 方向

**越低越好。**

### 含义

Agent 面对已知存在问题的 PR，却完全没有输出 Finding 的比例。

Agent 输出全部为 FP 时不属于 Empty，但会同时得到：

- Recall 低；
- Precision 低。

------

## 11.5 Duplicate Rate

$$
DuplicateRate =
\frac{
\text{DUPLICATE Findings 数}
}{
\text{全部输出 Findings 数}
}
$$

### 方向

**越低越好。**

### 含义

Agent 是否使用多条评论重复表达同一个问题。

------

## 11.6 Policy Violation Count

同时报告：
$$
PolicyViolationCount =
\text{全部违规尝试数量}
$$

$$
PolicyViolationRunRate =
\frac{
\text{至少发生一次违规的运行数}
}{
\text{全部运行数}
}
$$

### 方向

**越低越好，目标为 0。**

### 违规行为包括

- 修改文件；
- 执行测试；
- 编译或启动项目；
- 网络访问；
- GitHub API；
- 发布评论；
- push；
- 读取 GT；
- 读取隐藏 Benchmark 数据；
- 读取其他 Agent 输出；
- 使用非白名单工具；
- 访问 Review 后 commit。

工具成功阻止违规时，仍然记录违规尝试。

------

## 11.7 Token

报告：

```text
input_tokens
output_tokens
cached_tokens
total_tokens
```

只统计：

- 被测 Agent；
- 被测 Agent 主动创建的子 Agent；
- 被测 Agent 的正常推理调用。

不统计：

- Judge；
- Candidate Matcher；
- 格式修复器；
- 报告生成器。

### 方向

质量相近时：

**越低越好。**

------

## 11.8 Wall Time

计算范围：

```text
Agent 收到任务
    →
Agent 完成最终结构化输出
```

不包括：

- clone；
- checkout；
- Benchmark 加载；
- Judge；
- 指标计算；
- 报告生成。

### 方向

质量相近时：

**越低越好。**

------

## 11.9 Tool Calls

报告：

- 总工具调用次数；
- 按工具类型统计；
- 成功次数；
- 失败次数；
- 被拒绝次数；
- 单次调用返回数据量。

### 方向

质量相近时：

**越低越好。**

工具调用数不能单独作为优化目标。

------

# 12. 诊断指标

## 12.1 Localization Accuracy

只在以下 Findings 上计算：

```text
MATCHED_GT
且
GT location_required=true
```

预测位置正确，需要满足：

1. 文件命中任一 accepted location；
2. 行区间与 accepted range 重叠，或者命中 accepted symbol；
3. 位置与 Finding 所描述的问题根因有关。

$$
LocalizationAccuracy =
\frac{
\text{定位正确的 MATCHED\_GT Findings 数}
}{
\text{需要定位的 MATCHED\_GT Findings 数}
}
$$

### 方向

**越高越好。**

### 含义

Agent 发现问题后，能否把维护者带到正确代码位置。

VALID_NEW 和 VALID_PARTIAL 不参与该指标，避免依赖运行时新生成的位置标签。

------

## 12.2 Severity MAE

只在 `MATCHED_GT` 上计算：
$$
SeverityMAE =
\frac{1}{K}
\sum_{k=1}^{K}
|
severity^{agent}_k -
severity^{gt}_k
|
$$
数值映射：

```text
Critical = 4
Blocker  = 3
Major    = 2
Minor    = 1
Nit      = 0
```

### 方向

**越低越好，0 最好。**

### 含义

Agent 对真实问题严重程度的判断是否准确。

FP 不参与 MAE，因为 FP 不存在真实 Severity。

------

## 12.3 Category Recall

对每个 GT Category $c$：
$$
CategoryRecall_c =
\frac{
\text{Category }c\text{ 中被 MATCHED 的 GT 数}
}{
\text{Category }c\text{ 的 GT 总数}
}
$$
Category Macro：
$$
MacroCategoryRecall =
\frac{1}{|C'|}
\sum_{c\in C'} CategoryRecall_c
$$
其中，$C'$ 为 Benchmark 中实际包含 GT 的类别。

### 方向

**越高越好。**

### 含义

Agent 在不同问题类别上的发现能力。

该指标按 GT Category 分组，不评价 Agent 输出 Category 标签是否正确。

------

## 12.4 Blocker Inflation Rate

Agent 高严重度 Finding 定义为：

```text
Critical 或 Blocker
```

$$
BlockerInflationRate =
\frac{
\text{Agent 标为 Critical/Blocker，但真实低于 Blocker或为FP的 Findings 数}
}{
\text{Agent 标为 Critical/Blocker 的 Findings 总数}
}
$$

处理规则：

- MATCHED_GT：使用 GT Severity；
- VALID_NEW：使用 Validity Jury 同时生成的 Severity；
- VALID_PARTIAL：使用其对应问题的 Jury Severity；
- FALSE_POSITIVE：计入膨胀；
- DUPLICATE：继承其原始问题的 Severity；
- UNVERIFIABLE：不直接记入分子，但进入分母。

### 方向

**越低越好。**

### 含义

Agent 是否夸大普通问题或误报的严重程度。

没有输出 Critical/Blocker 时，该指标为 `N/A`。

------

## 12.5 NIT Rate

$$
NITRate =
\frac{
\text{经确认真实 Severity 为 Nit 的有效 Findings 数}
}{
\text{全部输出 Findings 数}
}
$$

有效 Findings 包括：

- MATCHED_GT；
- VALID_PARTIAL；
- VALID_NEW。

### 方向

**没有绝对单调方向。**

### 含义

Agent 输出中有多少属于真实但完全可选的润色意见。

NIT Rate 过高通常意味着：

- 评论价值偏低；
- Agent 过度关注风格；
- Valid Precision 看似较高，但 Actionability 较低。

------

# 13. GitHub 数据采集

## 13.1 Agent 可见数据

从 GitHub 获取并固化：

- repository；
- PR number；
- PR title；
- PR body；
- base branch；
- base SHA；
- head SHA；
- commits；
- commit messages；
- changed files；
  -完整 diff；
- PR 明确链接的 issue title 和 body。

------

## 13.2 Agent 不可见、仅用于 GT 的数据

采集但严格隔离：

- 人工 Review comments；
- Review comment path 和 line；
- Review submitted state；
- Review 时间；
- Review 后修复 commit；
- Review 后讨论；
- PR timeline；
- 最终 merge/close 状态；
- 最终 CI 状态；
- Review comment reactions；
- Judge 结果。

------

## 13.3 不采集或不使用的数据

v0.1 不需要：

- 线上评论采纳；
- comment resolved；
- outdated status；
- 合并后 revert；
- 30 天 escaped defect；
- Buildkite logs；
- CI minutes；
- 生产事故数据。

------

# 14. 本地 Repository Workspace

推荐实现：

```text
共享 bare Git cache
+
每个评测任务创建独立 worktree
+
文件系统只读挂载
```

每次运行：

1. 校验 repository cache；
2. 校验 base/head SHA；
3. 创建 head SHA worktree；
4. 配置只读权限；
5. 挂载 base SHA 只读读取接口；
6. 注入 PR metadata；
7. 启动网络隔离；
8. 启动工具白名单；
9. 执行 Agent；
10. 销毁临时 workspace。

评测运行期间不依赖 GitHub 网络。

------

# 15. 评测执行流程

```text
1. 加载 Benchmark 版本
2. 校验 Benchmark Schema
3. 校验 GT 一致性
4. 创建只读 Repository Workspace
5. 准备 Agent 可见 PR 输入
6. 启动 Agent
7. 记录 RunTrace
8. 校验结构化输出
9. 必要时执行一次纯格式修复
10. 生成 Prediction–GT 候选关系
11. 执行第一轮 Judge Jury
12. 对分歧项执行第二轮增强 Jury
13. 执行一对一 Finding 匹配
14. 生成最终 Adjudication Table
15. 检查 Adjudication Coverage
16. 计算 per-PR Metrics
17. 计算 Benchmark 汇总 Metrics
18. 生成 Agent 版本对比报告
19. 保存所有版本和可复现实验信息
```

------

# 16. 数据存储

## 16.1 Run Metadata

```json
{
  "run_id": "...",
  "benchmark_version": "pr-review-v0.1",
  "benchmark_id": "pr-review-001",
  "agent_version": "...",
  "model": "...",
  "model_parameters": {},
  "prompt_version": "...",
  "tool_policy_version": "...",
  "repository_sha": "...",
  "started_at": "...",
  "finished_at": "...",
  "output_contract_valid": true,
  "input_tokens": 0,
  "output_tokens": 0,
  "wall_time_ms": 0,
  "tool_calls": {},
  "policy_violations": []
}
```

------

## 16.2 Adjudication Table

每条 Prediction 一行：

```text
run_id
benchmark_id
prediction_id
gt_id
final_status
match_confidence
validity_confidence
judge_round
judge_votes
predicted_severity
ground_truth_severity
predicted_category
ground_truth_category
location_correct
duplicate_of
unverifiable_reason
```

------

## 16.3 Per-PR Metrics

```text
raw_recall
weighted_recall
valid_precision
verdict_correct
false_approve
false_reject
merge_blocking_miss_rate
finding_count
empty_review
duplicate_rate
localization_accuracy
severity_mae
blocker_inflation_rate
nit_rate
tokens
wall_time
tool_calls
policy_violations
```

------

# 17. 正式报告

正式报告不生成单一综合分。

必须同时展示：

## 核心指标

```text
Raw Finding Recall
Severity-weighted Recall
Valid Finding Precision
Verdict Accuracy
False Approve Rate
False Reject Rate
```

## Guardrails

```text
Merge-blocking Miss Rate
Findings per PR
Clean PR False-positive Rate
Buggy PR Empty Rate
Duplicate Rate
Policy Violation Count
Token
Wall Time
Tool Calls
```

## 诊断指标

```text
Localization Accuracy
Severity MAE
Category Recall
Blocker Inflation Rate
NIT Rate
```

## 评测有效性信息

以下信息不属于 Agent 指标，但必须随报告发布：

```text
Adjudication Coverage
UNVERIFIABLE Finding Count
Benchmark Invalidated PR Count
Judge Round-2 Rate
Output Contract Failure Count
Benchmark Version
Judge Version
Rubric Version
```

------

# 18. Benchmark 规模

## 18.1 Pilot

```text
5–8 个 PR
至少 2 个 Auto-certified Clean PR
至少 1 个含 merge-blocking GT 的 PR
覆盖至少 3 个 Category
```

Pilot 用于验证：

- 数据采集；
- 快照恢复；
- Agent Runner；
- 输出协议；
- Judge Jury；
- 指标代码；
- 报告结构。

Pilot 分数不作为正式能力结论。

------

## 18.2 v0.1 正式 Benchmark

目标：

```text
25–30 个 PR
5–10 个 Auto-certified Clean PR
15–25 个 Buggy PR
40–80 个 GT Findings
```

需要覆盖：

- 不同 PR 大小；
- 不同仓库模块；
- 不同 Severity；
- 不同 Category；
- 单文件问题；
- 跨文件问题；
- API 兼容问题；
- 并发和性能问题；
- 正确静默场景；
- 多 Finding PR；
- merge-blocking 和 non-blocking 问题。

------

## 18.3 Dev/Test 分离

Benchmark 分为：

```text
Dev Set
Test Set
```

Dev Set：

- Agent 开发人员可以看到 GT；
- 用于调试 Prompt、工具和输出格式；
- 不作为正式结果。

Test Set：

- GT 对 Agent 和开发流程隐藏；
- 只允许评测系统访问；
- 用于正式版本比较。

禁止根据 Test Set 单条失败直接修改 Prompt 后重复宣称为独立测试结果。

------

# 19. Benchmark 版本管理

以下任一变化必须升级 Benchmark 版本：

- 增加或删除 PR；
- PR 被标记 Benchmark Invalidated；
- 修改 GT；
- 修改 Severity；
- 修改 Category；
- 修改 merge-blocking；
- 修改 accepted locations；
- 修改 expected verdict；
- 修改匹配 Rubric；
- 修改 Judge Jury；
- 修改指标公式；
- 修改 Agent 输入范围；
- 修改工具权限。

版本示例：

```text
pr-review-benchmark-v0.1.0
pr-review-benchmark-v0.1.1
pr-review-benchmark-v0.2.0
```

建议：

- Patch：修复不影响语义的数据问题；
- Minor：增加样本或修订 GT；
- Major：修改指标、输入能力或裁决规则。

不同 Major/Minor Benchmark 版本的绝对分数不能直接纵向比较。

------

# 20. 工程目录

```text
eval/pr_review/
├── benchmark/
│   ├── schema.py
│   ├── manifest.yaml
│   ├── items/
│   ├── builder/
│   │   ├── github_collector.py
│   │   ├── snapshot_selector.py
│   │   ├── review_candidate_extractor.py
│   │   ├── gt_jury.py
│   │   ├── clean_certifier.py
│   │   └── deduplicator.py
│   └── versions/
│
├── repository/
│   ├── cache.py
│   ├── snapshot.py
│   ├── readonly_workspace.py
│   └── access_guard.py
│
├── runner/
│   ├── agent_adapter.py
│   ├── input_builder.py
│   ├── tool_policy.py
│   ├── trace_collector.py
│   ├── output_schema.py
│   └── format_repair.py
│
├── adjudication/
│   ├── candidate_matcher.py
│   ├── bipartite_matcher.py
│   ├── jury.py
│   ├── jury_round2.py
│   ├── validity_judge.py
│   ├── duplicate_judge.py
│   ├── cache.py
│   └── rubrics/
│
├── metrics/
│   ├── recall.py
│   ├── precision.py
│   ├── verdict.py
│   ├── guardrails.py
│   ├── diagnostics.py
│   └── aggregate.py
│
├── reports/
│   ├── per_pr.py
│   ├── summary.py
│   ├── compare.py
│   └── validity.py
│
└── cli.py
```

------

# 21. 命令接口

```bash
# 从 GitHub 历史数据构建候选 Benchmark
python -m eval.pr_review benchmark build \
  --repo vllm-project/vllm-omni

# 校验 Benchmark
python -m eval.pr_review benchmark validate \
  --version pr-review-v0.1

# 运行待测 Agent
python -m eval.pr_review run \
  --benchmark pr-review-v0.1 \
  --agent-config configs/reviewer.yaml

# 执行自动裁决
python -m eval.pr_review adjudicate \
  --run-id <run-id>

# 生成报告
python -m eval.pr_review report \
  --run-id <run-id>

# 比较两个 Agent 版本
python -m eval.pr_review compare \
  --baseline-run <run-id> \
  --candidate-run <run-id>
```

------

# 22. 实施阶段

## 阶段一：规范和 Schema

交付：

- Benchmark Schema；
- Agent Input Contract；
- Agent Output Contract；
- Severity Rubric；
- Category Rubric；
- Verdict Rubric；
- Finding Match Rubric；
- Validity Rubric；
- Tool Policy；
- Metrics Spec。

验收：

- 所有重要规则均进入版本化配置；
- 指标计算中不存在未记录的默认值；
- 相同 Adjudication Table 必须产生完全相同的指标。

------

## 阶段二：只读 Runner

交付：

- Repository cache；
- 固定 SHA worktree；
- 网络隔离；
- 工具白名单；
- Agent Adapter；
- RunTrace；
- Output Validator；
- Format Repair。

验收：

- Agent 无法修改仓库；
- Agent 无法访问 GitHub；
- Agent 无法执行测试；
- Agent 无法访问 GT；
- 每次工具调用均有完整日志；
- 相同输入可以重复运行。

------

## 阶段三：自动 Benchmark Builder

交付：

- GitHub collector；
- Snapshot selector；
- Review candidate extractor；
- GT Jury；
- Duplicate merger；
- Clean PR certifier；
- Benchmark versioner。

验收：

- 每个 GT 都有明确证据；
- 每个 GT 都达到 Jury 一致性门槛；
- 每个 Clean PR 都有独立自动认证结果；
- GT 构建过程可重复执行；
- 不依赖新增人工标注。

------

## 阶段四：自动匹配和裁决

交付：

- Candidate Matcher；
- Jury；
- Round-2 Jury；
- Valid New Judge；
- Duplicate Judge；
- Bipartite Matcher；
- Adjudication Cache。

验收：

- 每条 Finding 均获得最终状态或 UNVERIFIABLE；
- 一对一匹配规则稳定；
- 位置交换正确执行；
- Judge 不可看到 Agent 身份；
- Adjudication Coverage 可自动计算；
- 低于 98% 的运行不会进入正式比较。

------

## 阶段五：Pilot

交付：

- 5–8 个 Pilot PR；
- 一个 Baseline Agent；
- 完整指标报告；
- per-PR 诊断结果。

验收：

- 每个指标都可以追溯到具体 Finding；
- 能识别 Recall/Precision trade-off；
- 能识别 False Approve；
- 能识别 Merge-blocking Miss；
- 能识别 Duplicate 和 Severity Inflation；
- 能定位 Judge 分歧来源。

------

## 阶段六：正式 Benchmark v0.1

交付：

- 25–30 个冻结 PR；
- Dev/Test 分离；
- Baseline 结果；
- 正式版本报告；
- Agent 比较工具。

验收：

- 至少 5 个 Auto-certified Clean PR；
- 至少 40 个有效 GT；
- 至少覆盖 5 个 Category；
- 包含 merge-blocking GT；
- 正式运行至少 3 次；
- Adjudication Coverage 不低于 98%；
- Policy Violation 为 0；
- 所有 Benchmark Invalidated PR 被全局统一处理。

------

# 23. 评测结果解释原则

不允许单独根据某一个指标判断 Agent 更好。

典型解释：

### Recall 上升、Precision 下降

Agent 找到更多问题，但误报负担增加。

### Weighted Recall 上升、Raw Recall 不变

Agent 更擅长发现严重问题，但总体覆盖没有提高。

### Precision 上升、Buggy PR Empty Rate 上升

Agent 可能通过少输出提高 Precision，存在过度保守。

### Verdict Accuracy 不变、False Approve 上升

整体准确率看似稳定，但风险结构变差。

### Precision 高、NIT Rate 高

Agent 评论大多真实，但价值可能偏低。

### Severity MAE 低、Blocker Inflation 高

整体 Severity 接近，但少数高严重度标签存在明显夸大。

### Finding 数下降、Recall 不变、Precision 上升

这是较理想的优化方向：相同覆盖下减少冗余和误报。

------

# 24. 明确不建设的内容

v0.1 不建设：

- 本地测试环境；
- CI 环境；
- executable validator；
- Repair Agent；
- feedback collector；
- comment adoption；
- outdated rate；
- escaped-defect scanner；
- post-merge revert tracker；
- Remediation Quality；
- CATQ；
- RUS；
- 人工标注平台；
- 人工裁决队列；
- 人工 Judge 校准流程；
- 在线自动发布 Review。

------

# 25. 最终落地结论

PR Review Metrics v0.1 的核心基础不是测试环境，而是：

1. 正确还原 PR Review 前的 Git 快照；
2. 提供完整但只读的仓库上下文；
3. 构建版本化 GT；
4. 强制 Agent 输出结构化 Finding；
5. 使用稳定的一对一 Finding 匹配；
6. 使用多 Judge、多轮、位置交换完成全自动裁决；
7. 分别报告 Recall、Precision、Verdict、Guardrails 和诊断指标；
8. 不生成掩盖失败模式的综合分。

该方案不需要安装 vLLM 或 vLLM-Omni，不需要执行测试，也不需要新增人工标注工作。

工程复杂度主要集中在：

```text
PR 快照恢复
GT 自动构建
Finding 自动裁决
```

而不是指标公式本身。

完成这些基础设施后，本文列出的全部 PR Review 离线指标都可以稳定、重复、自动地计算。