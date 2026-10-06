# knowledge_service/lifecycle.py —— 规范

<!-- verified-against: 2026-10-06 -->

深度区块的固定源码身份支持完整 SHA-1 或 SHA-256；旧区块正文、哈希及证明语义保持不变。

深度验证入口缺失证书的当前检测器为 `static-test-association-v2`；解析、证书工厂和
检索形状校验共用 `DEPTH_ABSENCE_DETECTOR`，算法升级不复用旧检测器身份。

`LOC ~330 · 规则页数据模型与生命周期尾注 · refactor-status: stable`

## 职责
把规则页解析为 frontmatter、head 与 `## ` 段（跳过代码围栏内的标题），未改动的页
解析再渲染逐字节相同。规则段可带 `<!-- kb:rule ... -->` 尾注（status、since、retired_at、
reason、evidence、supersedes、superseded_by、protected）；无尾注即 active。

## 公开契约

`DEPTH_FACETS`、`DEPTH_BLOCK` 和 `depth_sections` 是 init/audit 与检索共享的深读数据格式。
后者只返回正文哈希完整、facet 唯一且 proof evidence 形状合法的段落，隐藏 proof 注释，
不重新读取上游证据。固定源码验证仍由 `kb_service.knowledge_depth` 负责。
proof 的 basis 缺省 supported；verified_absent 要有形状完整的版本化 certificate，
返回结果显式携带 basis 与缺失范围。形状校验不能替代 source audit 的完整重放。
`Page.parse/render`、`Page.rules/rule/replace_section/append_section`、
`Page.sources/with_sources`（按页面原风格写 flow 或 block 列表）、`Section.footer/
with_footer/body_without_footer/content_sha256/citations`、`Footer.parse/render/check`、
`expected_sources`（旧列表 + active 规则新引用，只追加）、`visible_text`（去掉退役规则，
无退役规则时逐字节原样返回）。

## 不变量
- 仅依赖标准库与 PyYAML、不 import 包内其他模块。
- 尾注键未知、重复、格式错误或状态约束不满足时抛 `LifecycleError`。

## 测试
`test_knowledge_ops_l1.py`（全树逐字节往返、服务端隐藏退役规则）。
