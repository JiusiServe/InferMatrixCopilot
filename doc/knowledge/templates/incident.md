<!-- TEMPLATE: a retro / historical write-up for an incidents/ dir.
     RENAME this file to YYYY-MM-DD-short-name.md (lowercase, a-z0-9-).
     The five `- 编号/归属/状态/搜索词/影响范围` fields are validator-required;
     状态 must be one of 待归类 / 处理中 / 已验证 / 已提炼 / 仅历史; 编号 must be
     unique across the tree. Link it from the sibling incidents/_index.md, then
     delete this comment. Add an incident only when a rule can't carry the
     evidence chain — the default retro output is a rule, not an incident. -->
# <人能读懂的现象标题>

- 编号：`inc-<YYYY-MM-DD>-<short-name>`
- 归属：`<repos/<repo>/<topic> or general/<topic>>`
- 状态：处理中
- 搜索词：<term1>、<term2>、<term3>
- 影响范围：<what breaks>

## 现象

- <the observed symptom, with live evidence>

## 根因（live 证据）

- <the verified cause: source / diff / log>

## 修复

- <what actually fixed it>

## 验收

- <the minimal check proving the fix holds>

## 已提炼的规则

- 见 [<owner> rules](../rules.md#<rule-id>)
