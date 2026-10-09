---
title: "web-frontend 审查规则"
created: 2026-10-09
updated: 2026-10-09
type: rule
tags: [jiuwenswarm, components]
sources: ["PR #7788"]
confidence: high
---

# web-frontend 审查规则

## JW-WEB-QUOTA-1a — 配额导航开关必须走完整 HTML 注入链并清理残留导航

- 触发：修改 dev-stable 的配额导航或 WORKSPACE_QUOTA_ENABLED Web 注入。
- 强制：同步 env 声明、nginx sub_filter、app_web 注入、index.html 占位符和 TS window 类型；agents 只在配额开启时显示，approvals 还需 enterprise。关闭/切换版本时残留 activeNav 回到 chat。
- 禁止：只隐藏按钮而保留不满足条件的 activeNav 页面；漏掉任一部署注入入口；将字符串 false 当真。
- 验收：个人/企业 × 开/关组合检查导航和残留会话恢复；两种 HTML 服务路径不残留占位符，前后端布尔语义一致。^[PR #7788]
