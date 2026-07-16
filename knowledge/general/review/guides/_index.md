# 代码审查指南

| 遇到什么 | 查看哪里 |
|---|---|
| 独立 review、完整 diff review 或交给项目 owner 前验收 | [独立审查执行合同](review-execution-contract.md) |
| 区分框架补丁和算法修复 | [algorithm vs framework](algorithm-vs-framework-fix.md) |
| 写代码前检查整体品味 | [code taste](code-taste.md) |
| 审查公开参数和 API | [API surface](code-taste-api-surface.md) |
| 审查新增执行路径 | [review flow](code-taste-review-flow.md) |
| 避免在消费端写死生产端枚举 | [Codex review lessons](codex-review-lessons.md) |
| 避免调试时顺手扩大优化范围 | [narrow optimization scope](narrow-optimization-scope.md) |
| 理解四类维护者审查方法 | [reviewer lens audit](reviewer-lens-audit.md) |
| 查看审查案例 | [reviewer lens cases](reviewer-lens-cases.md) |
| 检查接口和生命周期约定 | [reviewer lens contracts](reviewer-lens-contracts.md) |
| 按风险选择审查门禁 | [reviewer lens gates](reviewer-lens-gates.md) |
| 使用可粘贴审查提示 | [reviewer lens prompt](reviewer-lens-prompt.md) |
| 算法判断前先读上游实现 | [upstream first](upstream-first-for-algorithm.md) |
