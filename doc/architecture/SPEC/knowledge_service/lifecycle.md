# knowledge_service/lifecycle.py —— 规范

<!-- verified-against: 2026-09-28 -->

`LOC ~330 · 规则页数据模型与生命周期尾注 · refactor-status: stable`

## 职责
把规则页解析为 frontmatter、head 与 `## ` 段（跳过代码围栏内的标题），未改动的页
解析再渲染逐字节相同。规则段可带 `<!-- kb:rule ... -->` 尾注（status、since、retired_at、
reason、evidence、supersedes、superseded_by、protected）；无尾注即 active。

## 公开契约
`Page.parse/render`、`Page.rules/rule/replace_section/append_section`、
`Page.sources/with_sources`（按页面原风格写 flow 或 block 列表）、`Section.footer/
with_footer/body_without_footer/content_sha256/citations`、`Footer.parse/render/check`、
`expected_sources`（旧列表 + active 规则新引用，只追加）、`visible_text`（去掉退役规则，
无退役规则时逐字节原样返回）。

## 不变量
- 仅依赖标准库与 PyYAML、不 import 包内其他模块：kb-gate 验证包原样携带。
- 尾注键未知、重复、格式错误或状态约束不满足时抛 `LifecycleError`。

## 测试
`test_knowledge_ops_l1.py`（全树逐字节往返、服务端隐藏退役规则）。
